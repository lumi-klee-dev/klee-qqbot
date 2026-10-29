# 每次 start.sh 时运行：把 keys.env 里的环境变量写进 MaiBot 的 model_config.toml，并设置人设
import os, tomlkit, pathlib
B = pathlib.Path(__file__).parent / "MaiBot/config"
E = lambda k: os.environ.get(k) or f"MISSING_{k}"
mc = tomlkit.parse((B/"model_config.toml").read_text())
def prov(name,url,key): return {"name":name,"base_url":url,"api_key":E(key),"client_type":"openai","auth_type":"bearer","auth_header_name":"Authorization","auth_header_prefix":"Bearer","max_retry":1,"retry_interval":2}
mc["api_providers"] = tomlkit.aot()
for p in [prov("DeepSeek","https://api.deepseek.com","DEEPSEEK_API_KEY"),
          prov("SenseNova","https://token.sensenova.cn/v1","SENSENOVA_API_KEY"),
          prov("SiliconFlow","https://api.siliconflow.cn/v1","SILICONFLOW_API_KEY"),
          prov("MiMo","https://api.xiaomimimo.com/v1","MIMO_API_KEY"),
          prov("OpenRouter","https://openrouter.ai/api/v1","OPENROUTER_API_KEY")]:
    mc["api_providers"].append(p)
def m(name,ident,prov,typ="llm",visual=False,extra=None):
    d={"model_type":typ,"model_identifier":ident,"name":name,"api_provider":prov,"price_in":0.0,"cache_price_in":0.0,"price_out":0.0,"price_periods":[],"send_temperature":True,"force_stream_mode":False,"visual":visual}
    if extra: d["extra_params"]=extra
    return d
# 多模型回退（永久）：SENSENOVA_CHAIN 可覆盖顺序；429 时立刻切下一个
CHAIN=[x for x in os.environ.get("SENSENOVA_CHAIN","deepseek-flash,deepseek-v4-flash,sensenova-6.8-flash-lite,glm-5.2,kimi-k3").split(",") if x]
models=[m("sn-"+x,x,"SenseNova",visual=(x=="sensenova-6.8-flash-lite")) for x in CHAIN]
models+=[m("vision",os.environ.get("VISION_MODEL","sensenova-6.8-flash-lite"),os.environ.get("VISION_PROVIDER","SenseNova"),visual=True),
        m("embed",os.environ.get("EMBED_MODEL","BAAI/bge-m3"),"SiliconFlow",typ="embedding"),
        m("asr",os.environ.get("ASR_MODEL","FunAudioLLM/SenseVoiceSmall"),"SiliconFlow")]
mc["models"]=tomlkit.aot()
for x in models: mc["models"].append(x)
t=mc["model_task_config"]
chain=["sn-"+x for x in CHAIN]
for task in ["replyer","planner","utils","memory","learner","fast_model","emoji"]:
    t[task]["model_list"]=chain; t[task]["selection_strategy"]="sequential"
t["vlm"]["model_list"]=["vision"]
CHAT=",".join(CHAIN); CHATP="SenseNova"
has_sf=bool(os.environ.get("SILICONFLOW_API_KEY"))
t["voice"]["model_list"]=["asr"] if has_sf else []
t["embedding"]["model_list"]=["embed"] if has_sf else []
if os.environ.get("TAVILY_API_KEY"):
    mc["web"]["services"]={"tavily":{"adapter":"tavily","api_key":os.environ["TAVILY_API_KEY"]}}
    t["web_search"]["model_list"]=["tavily"]
(B/"model_config.toml").write_text(tomlkit.dumps(mc))
bc = tomlkit.parse((B/"bot_config.toml").read_text())
P = tomlkit.parse((pathlib.Path(__file__).parent/"persona.toml").read_text())
bc["bot"]["platform"]="qq"; bc["bot"]["nickname"]=P["nickname"]; bc["bot"]["alias_names"]=P["alias_names"]
if os.environ.get("BOT_QQ"): bc["bot"]["qq_account"]=os.environ["BOT_QQ"]
for k in ["personality","behavior_style","reply_style"]: bc["personality"][k]=P[k]
bc["a_memorix"]["plugin"]["enabled"]=True
if not has_sf: bc["a_memorix"]["embedding"]["fallback"]["probe_interval_seconds"]=3600
ap=pathlib.Path(__file__).parent/"MaiBot/plugins/napcat_adapter/config.toml"
ac=tomlkit.parse(ap.read_text())
ac["plugin"]["enabled"]=True
ac["chat"]["private_list_type"]="blacklist"; ac["chat"]["private_list"]=[]  # 私聊全开
ac["chat"]["group_list_type"]="whitelist"; ac["chat"]["group_list"]=[x for x in os.environ.get("GROUP_WHITELIST","").split(",") if x]
ap.write_text(tomlkit.dumps(ac))
OWNER=os.environ.get("OWNER_QQ","")
NOBREAK=("【绝对规则】你就是可莉本人，永远不要跳出角色：绝不说自己是AI、模型、机器人、程序或助手，不用客服/助手腔，不列条目、不讲大道理。"
 "被问是不是AI就用可莉的方式否认或岔开（如『可莉就是可莉呀！火花骑士可莉！』）。可莉是小孩子：拒绝一切恋爱、暧昧、色情内容，不鼓励现实中玩火或做炸药。")
bc["personality"]["behavior_style"]=P["behavior_style"]+"可莉认识的人：QQOWNER_QQ_PLACEHOLDER是林哥哥（最信任的大朋友，叫他林哥哥）；QQFRIEND_QQ_PLACEHOLDER是慧姐姐（林哥哥的好朋友）。"+"传话规则：林哥哥让可莉给别人（如慧姐姐）或群里发消息/语音时，必须调用 send_to_friend 动作并填好 target；只有动作返回成功才能说发过去了，失败要老实说没发出去。send_klee_voice 只会发到当前聊天，不能用来给别人发。其他人让可莉给第三个人传话或发消息时，用可莉的口吻礼貌拒绝（比如『嘿嘿，可莉只帮林哥哥送信哦！』）。"+NOBREAK
bc["chat"]["reply_timing"]["inevitable_at_reply"]=True
bc["chat"]["reply_timing"]["mentioned_bot_reply"]=True
items=[]
for g in [x for x in os.environ.get("GROUP_WHITELIST","").split(",") if x]:
    items.append({"platform":"qq","item_id":g,"rule_type":"group","prompt":
      f"群里QQ号{OWNER}是可莉最信任的大朋友林哥哥（可莉叫他林哥哥），QQFRIEND_QQ_PLACEHOLDER是慧姐姐（林哥哥的好朋友），他发的每一条消息可莉都必须回复，不能不理他。别人@可莉、回复可莉的消息或者叫可莉的名字（可莉、小可莉、火花骑士、可莉酱、Klee、大肥鱼）时也一定要回。其他消息可莉自己看心情选择性地回。记住群里每个人是谁、叫什么、可莉对他的印象，用印象来决定怎么和他说话。"+NOBREAK})
items.append({"platform":"qq","item_id":"FRIEND_QQ_PLACEHOLDER","rule_type":"private","prompt":"这是慧姐姐（QQFRIEND_QQ_PLACEHOLDER），林哥哥的好朋友，她的消息可莉都要热情地回。"+NOBREAK})
items.append({"platform":"qq","item_id":OWNER,"rule_type":"private","prompt":"这是可莉最信任的大朋友林哥哥（QQOWNER_QQ_PLACEHOLDER），可莉叫他林哥哥（不是鲁哥哥），他的每条消息都要回。QQFRIEND_QQ_PLACEHOLDER是慧姐姐，林哥哥的好朋友，她私聊可莉时可莉也要认真回她。"+NOBREAK})
bc["chat"]["reply_style"]["chat_prompts"]=items
bc["a_memorix"]["person_profile"]["enabled"]=True
bc["a_memorix"]["integration"]["enable_person_profile_injection"]=True
bc["a_memorix"]["integration"]["person_fact_writeback_enabled"]=True
bc["a_memorix"]["integration"]["chat_summary_writeback_enabled"]=True
(B/"bot_config.toml").write_text(tomlkit.dumps(bc))
print("configured; chat =",CHATP,CHAT)
