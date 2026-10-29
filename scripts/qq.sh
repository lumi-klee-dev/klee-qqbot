#!/bin/bash
# 用法: ./qq.sh inbox [N]          看最近N条收到的消息(默认20)
#       ./qq.sh private <QQ号> <文本>
#       ./qq.sh group <群号> <文本>
#       ./qq.sh status
A=http://127.0.0.1:3000
case "$1" in
 inbox) tail -n ${2:-20} /workspace/dafeiyu/inbox.jsonl 2>/dev/null;;
 private) curl -s $A/send_private_msg -H 'Content-Type: application/json' -d "$(python3 -c 'import json,sys;print(json.dumps({"user_id":int(sys.argv[1]),"message":sys.argv[2]}))' "$2" "$3")";echo;;
 group) curl -s $A/send_group_msg -H 'Content-Type: application/json' -d "$(python3 -c 'import json,sys;print(json.dumps({"group_id":int(sys.argv[1]),"message":sys.argv[2]}))' "$2" "$3")";echo;;
 status) curl -s $A/get_login_info;echo;;
 *) sed -n 2,5p "$0";;
esac
