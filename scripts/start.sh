#!/bin/bash
cd /workspace/dafeiyu
set -a; . ./keys.env; set +a
export EULA_AGREE=8e6e7d647f7f82d6ea98456b73908656 PRIVACY_AGREE=91e5db7659c560bc3545e63859b6ebc0
MaiBot/.venv/bin/python configure.py
screen -ls | grep -q napcat || screen -dmS napcat bash -c "NAPCAT_DISABLE_MULTI_PROCESS=1 xvfb-run -a $HOME/Napcat/opt/QQ/qq --no-sandbox ${BOT_QQ:+-q $BOT_QQ} >> /workspace/dafeiyu/napcat.log 2>&1"
pgrep -f inbox_ws.py >/dev/null || nohup MaiBot/.venv/bin/python inbox_ws.py >> inbox_ws.log 2>&1 &
pgrep -f "python bot.py" >/dev/null || (cd MaiBot && nohup .venv/bin/python bot.py >> ../maibot.log 2>&1 &)
screen -ls | grep -q "\.watchdog" || screen -dmS watchdog ./watchdog.sh
screen -ls | grep -q "\.klee_proactive" || screen -dmS klee_proactive bash -c "MaiBot/.venv/bin/python proactive.py >> proactive.log 2>&1"
sleep 3; echo "started. 日志: napcat.log maibot.log"
