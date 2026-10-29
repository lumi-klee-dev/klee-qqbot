import asyncio,json,time,websockets
F="/workspace/dafeiyu/inbox.jsonl"
async def main():
    while True:
        try:
            async with websockets.connect("ws://127.0.0.1:3001") as ws:
                print(time.strftime("%T"),"connected",flush=True)
                async for raw in ws:
                    e=json.loads(raw)
                    if e.get("post_type") in ("message","message_sent"):
                        open(F,"a").write(json.dumps({"t":time.strftime("%F %T"),"type":e.get("message_type"),"group":e.get("group_id"),"user":e.get("user_id"),"name":(e.get("sender") or {}).get("nickname"),"text":e.get("raw_message"),"id":e.get("message_id")},ensure_ascii=False)+"\n")
                    elif e.get("meta_event_type")=="lifecycle": print("lifecycle",e,flush=True)
        except Exception as x: print("err",x,flush=True); await asyncio.sleep(5)
asyncio.run(main())
