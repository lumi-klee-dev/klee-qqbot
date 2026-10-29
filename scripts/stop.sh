#!/bin/bash
pkill -f "python bot.py"; screen -S napcat -X quit; pkill -f Napcat/opt/QQ/qq; echo stopped
