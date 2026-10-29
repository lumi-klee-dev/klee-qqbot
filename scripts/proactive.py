"""可莉主动性：群冷场时开话题、偶尔私聊主人。通过 NapCat HTTP 发送，每次最多 1 次 LLM 调用，失败则不发。
import os
调频率改下面 CONFIG 后: screen -S klee_proactive -X quit; ./start.sh"""
import json, random, time, datetime, base64, os, urllib.request
from pathlib import Path
D = Path("/workspace/dafeiyu")
CONFIG = dict(
    GROUP=int(os.environ.get("GROUP_ID","0")), OWNER=int(os.environ.get("OWNER_QQ","0")), SELF=int(os.environ.get("BOT_QQ","0")),
    GROUP_QUIET_MIN=90,      # 群里安静多少分钟算冷场
    GROUP_MAX_PER_DAY=4, GROUP_MIN_GAP_MIN=120, GROUP_HOURS=("09:00", "22:30"),
    PRIV_MAX_PER_DAY=2, PRIV_MIN_GAP_MIN=300, PRIV_HOURS=("08:30", "22:30"),
    PRIV_CHANCE=0.03,         # 每次检查(5分钟)私聊触发概率
    GROUP_CHANCE=0.25,        # 冷场后每次检查触发概率
    VOICE_CHANCE=0.3, CHECK_SEC=300)
C = CONFIG; STATE = D / ".proactive_state.json"; TZ = datetime.timezone(datetime.timedelta(hours=8))
POOL_G = ["可莉今天又去星落湖边找鱼玩啦，可是琴团长说不许炸鱼……你们今天都在做什么呀？", "嘿嘿，可莉做了一颗新的蹦蹦炸弹，是心形的哦！不过只是给大家看看，不会扔的啦~",
          "大家怎么都不说话了呀？可莉一个人好无聊……谁来陪可莉玩！", "可莉刚刚在读冒险日记，下次大家一起去冒险好不好？", "今天的天气，好适合去野餐！你们喜欢吃什么呀？可莉最喜欢煎蛋啦！",
          "可莉被关禁闭的时候，画了好多画！谁想看可莉画的嘟嘟可？"]
POOL_P = ["早上好！可莉起床啦，今天也要元气满满哦！", "可莉想你了！你在干什么呀？", "嘿嘿，可莉刚才想到你啦，所以就来找你说话~", "今天有没有好好吃饭呀？可莉在帮你监督哦！"]
def now(): return datetime.datetime.now(TZ)
def inhours(h): t = now().strftime("%H:%M"); return h[0] <= t < h[1]
def load():
    s = json.loads(STATE.read_text()) if STATE.exists() else {}
    if s.get("day") != now().strftime("%F"): s.update(day=now().strftime("%F"), g=0, p=0)
    s.setdefault("sent", []); s.setdefault("lg", 0); s.setdefault("lp", 0); return s
def save(s): s["sent"] = s["sent"][-60:]; STATE.write_text(json.dumps(s, ensure_ascii=False))
def api(ep, body):
    r = urllib.request.Request("http://127.0.0.1:3000/" + ep, json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=20).read())
def recent_group(n=30):
    out = []
    for l in (D / "inbox.jsonl").read_text("utf-8").splitlines()[-2000:]:
        try: m = json.loads(l)
        except Exception: continue
        if m.get("group") == C["GROUP"]: out.append(m)
    return out[-n:]
def last_group_ts():
    try:
        r = api("get_group_msg_history", {"group_id": C["GROUP"], "count": 1}); ms = r["data"]["messages"]
        if ms: return ms[-1]["time"]
    except Exception: pass
    g = recent_group(1)
    return time.mktime(time.strptime(g[-1]["t"], "%Y-%m-%d %H:%M:%S")) if g else 0
CHAIN = ["deepseek-flash", "deepseek-v4-flash", "sensenova-6.8-flash-lite", "glm-5.2", "kimi-k3"]
def llm(prompt):
    env = dict(l.split("=", 1) for l in (D / "keys.env").read_text().splitlines() if "=" in l and not l.startswith("#"))
    chain = [x for x in env.get("SENSENOVA_CHAIN", "").strip().split(",") if x] or CHAIN
    for model in chain:
        body = {"model": model, "messages": [
            {"role": "system", "content": (D / "persona.toml").read_text("utf-8") + "\n主人QQOWNER_QQ_PLACEHOLDER是林哥哥，可莉叫他林哥哥。你就是可莉，只输出要发出的那一句话(30字以内)，不要引号、不要解释、绝不承认自己是AI。"},
            {"role": "user", "content": prompt}], "max_tokens": 600, "temperature": 0.9}
        r = urllib.request.Request("https://token.sensenova.cn/v1/chat/completions", json.dumps(body).encode(),
            {"Content-Type": "application/json", "Authorization": "Bearer " + env["SENSENOVA_API_KEY"].strip()})
        try:
            t = json.loads(urllib.request.urlopen(r, timeout=60).read())["choices"][0]["message"].get("content") or ""; t = t.strip()
        except Exception as e: print(now(), "llm失败", model, e, flush=True); continue
        t = t.split("</think>")[-1].strip().strip('"“”')
        if 4 <= len(t) <= 80: return t
    return None
def compose(kind, s):
    h = now().hour; tod = "早上" if 6 <= h < 11 else "中午" if 11 <= h < 14 else "下午" if 14 <= h < 18 else "晚上"
    try:
        if kind == "g":
            hist = "\n".join(f'{m["name"]}({m["user"]}): {m["text"][:60]}' for m in recent_group(20) if "CQ:" not in m["text"][:4])
            p = f"现在是{tod}{now():%H:%M}，唠叨小窝群已经安静好一会儿了。下面是之前的群聊：\n{hist}\n请你主动开个新话题（比如今天做了什么、炸鱼、蹦蹦炸弹、问问某个认识的群友之前聊过的事、或者{tod}问候），自然可爱，别重复：{s['sent'][-8:]}"
        else:
            p = f"现在是{tod}{now():%H:%M}，你想主动私聊你最信任的大朋友（主人），说一句话（比如问候、可莉想你了、分享今天的事）。别重复：{s['sent'][-8:]}"
        t = llm(p)
        if t and t not in s["sent"]: return t
    except Exception as e: print(now(), "llm失败", e, flush=True)
    return None  # LLM 失败就什么都不发
def voice():
    idx = json.loads((D / "klee/voice_pack/index.json").read_text("utf-8")); h = now().hour
    want = "morning" if 6 <= h < 11 else "noon" if h < 14 else "evening" if h >= 18 else "random"
    c = [x for x in idx if want in x.get("tags", [])] or idx; f = D / "klee/voice_pack" / random.choice(c)["file"]
    return {"type": "record", "data": {"file": "base64://" + base64.b64encode(f.read_bytes()).decode()}}
def send(kind, text):
    msg = [{"type": "text", "data": {"text": text}}]
    if kind == "g": api("send_group_msg", {"group_id": C["GROUP"], "message": msg})
    else: api("send_private_msg", {"user_id": C["OWNER"], "message": msg})
    if random.random() < C["VOICE_CHANCE"]:
        time.sleep(2); k = {"group_id": C["GROUP"]} if kind == "g" else {"user_id": C["OWNER"]}
        api("send_group_msg" if kind == "g" else "send_private_msg", {**k, "message": [voice()]})
    print(now(), "主动发送", kind, text, flush=True)
def tick():
    s = load(); t = time.time()
    if inhours(C["GROUP_HOURS"]) and s["g"] < C["GROUP_MAX_PER_DAY"] and t - s["lg"] > C["GROUP_MIN_GAP_MIN"] * 60:
        lt = last_group_ts()
        if lt and t - lt > C["GROUP_QUIET_MIN"] * 60 and random.random() < C["GROUP_CHANCE"]:
            x = compose("g", s)
            if x: send("g", x); s["g"] += 1; s["lg"] = t; s["sent"].append(x)
    if inhours(C["PRIV_HOURS"]) and s["p"] < C["PRIV_MAX_PER_DAY"] and t - s["lp"] > C["PRIV_MIN_GAP_MIN"] * 60 and random.random() < C["PRIV_CHANCE"]:
        x = compose("p", s)
        if x: send("p", x); s["p"] += 1; s["lp"] = t; s["sent"].append(x)
    save(s)
if __name__ == "__main__":
    import sys
    if "--dry-run" in sys.argv:
        s = load(); print("hours g/p", inhours(C["GROUP_HOURS"]), inhours(C["PRIV_HOURS"]), "quiet_min", round((time.time()-last_group_ts())/60), "state", s)
        print("示例(不发送):", compose("g", s)); sys.exit()
    while True:
        try: tick()
        except Exception as e: print(now(), "err", e, flush=True)
        time.sleep(C["CHECK_SEC"])
