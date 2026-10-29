#!/bin/bash
# 只重启 MaiBot，不动 NapCat/QQ 登录
cd /workspace/dafeiyu; pkill -f "python bot.py"; sleep 3; /workspace/klee_tts/start_tts.sh; ./start.sh
