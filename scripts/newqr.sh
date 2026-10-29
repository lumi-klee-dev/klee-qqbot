#!/bin/bash
# 杀掉 QQ、清掉旧会话缓存（~/.config/QQ，会备份），重启 NapCat，等新二维码出来并复制+放大
cd /workspace/dafeiyu; Q=$HOME/Napcat/opt/QQ/resources/app/app_launcher/napcat/cache/qrcode.png
screen -S napcat -X quit; pkill -9 -f "opt/QQ/qq"; pkill -9 Xvfb; sleep 2
[ -d ~/.config/QQ ] && mv ~/.config/QQ ~/.config/QQ.bak-$(date +%m%d%H%M%S)
: > napcat.log; T0=$(date +%s)
screen -dmS napcat bash -c "NAPCAT_DISABLE_MULTI_PROCESS=1 xvfb-run -a $HOME/Napcat/opt/QQ/qq --no-sandbox >> /workspace/dafeiyu/napcat.log 2>&1"
for i in $(seq 60); do sleep 1; [ -f $Q ] && [ $(stat -c %Y $Q) -ge $T0 ] && break; done
cp $Q napcat-qr.png; MaiBot/.venv/bin/python -c "from PIL import Image;i=Image.open('napcat-qr.png');i.resize((i.width*8,i.height*8),Image.NEAREST).save('napcat-qr-big.png')"
echo "QR @ $(date -r napcat-qr.png +%T)"; grep -a "解码URL" napcat.log | tail -1
