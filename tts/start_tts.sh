#!/bin/bash
cd /workspace/klee_tts
pgrep -f "klee_tts/server.py" >/dev/null && exit 0
TQDM_DISABLE=1 nohup .venv/bin/python /workspace/klee_tts/server.py >> /workspace/klee_tts/server.log 2>&1 &
