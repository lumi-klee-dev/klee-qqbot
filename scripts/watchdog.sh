#!/bin/bash
# 可莉看门狗：每60秒检查 NapCat 与 MaiBot。用法: ./watchdog.sh [--once|--dry-run]
cd /workspace/dafeiyu
LOG=watchdog.log; HIST=.watchdog_restarts; MAXR=3; WIN=1800
DRY=0; ONCE=0; [ "$1" = "--dry-run" ] && DRY=1 && ONCE=1; [ "$1" = "--once" ] && ONCE=1
log(){ echo "$(date '+%F %T') $*" >> $LOG; [ $ONCE = 1 ] && echo "$*"; }
napcat_ok(){ screen -ls | grep -q '\.napcat' && curl -s -m 8 http://127.0.0.1:3000/get_login_info | grep -q '"retcode":0'; }
brain_ok(){ pgrep -f "python bot.py" >/dev/null; }
can_restart(){ now=$(date +%s); touch $HIST; awk -v n=$now -v w=$WIN '$1>n-w' $HIST > $HIST.t; mv $HIST.t $HIST; [ $(wc -l < $HIST) -lt $MAXR ]; }
do_restart(){ # $1=原因 $2=命令
  if ! can_restart; then log "BACKOFF: 30分钟内已重启${MAXR}次，跳过 ($1)"; return; fi
  log "RESTART: $1 -> $2"; [ $DRY = 1 ] && { log "(dry-run，未执行)"; return; }
  date +%s >> $HIST; $2 >> $LOG 2>&1
  if [ "$2" = ./start.sh ]; then sleep 45
    if ! napcat_ok; then tail -n 80 napcat.log | grep -qiE '二维码|qrcode|扫码' && log "NEED_QR: 快速登录失败，需要扫码（未清除任何数据）" || log "NapCat 重启后仍未就绪"; fi
  fi; }
fail=0
while true; do
  if napcat_ok; then fail=0; else fail=$((fail+1)); log "NapCat 检查失败 ($fail/2)"; fi
  [ $fail -ge 2 ] && { do_restart "NapCat 连续两次失败" ./start.sh; fail=0; }
  curl -s -m 5 -o /dev/null http://127.0.0.1:8765/ || { log "TTS 不在，重启"; [ $DRY = 1 ] || /workspace/klee_tts/start_tts.sh >> $LOG 2>&1; }
  brain_ok || do_restart "MaiBot 进程不在" ./restart-brain.sh
  [ $DRY = 1 ] && { napcat_ok && echo napcat=OK || echo napcat=DOWN; brain_ok && echo brain=OK || echo brain=DOWN; }
  [ $ONCE = 1 ] && exit 0; sleep 60
done
