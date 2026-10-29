"""可莉语音包：按场景挑选 bwiki 中文原声，发 QQ 语音。索引 /workspace/dafeiyu/klee/voice_pack/index.json"""
import asyncio, base64, json, random, re, time, urllib.parse, urllib.request
from pathlib import Path
from maibot_sdk import Action, Field, MaiBotPlugin, PluginConfigBase
from maibot_sdk.types import ActivationType

PACK = Path("/workspace/dafeiyu/klee/voice_pack")
COOLDOWN = 300
SITUATIONS = "greet,first_meet,morning,noon,evening,goodnight,birthday,praised,happy,bomb,fish,scolded,jean,sad,thanks,rain,thunder,wind,food,random"
KW = {"早上好": "morning", "早安": "morning", "中午": "noon", "晚上好": "evening", "晚安": "goodnight", "睡": "goodnight",
      "生日": "birthday", "真棒": "praised", "厉害": "praised", "夸": "praised", "开心": "happy", "炸弹": "bomb", "蹦蹦": "bomb",
      "炸鱼": "fish", "鱼": "fish", "禁闭": "scolded", "骂": "scolded", "琴": "jean", "团长": "jean", "难过": "sad", "哭": "sad",
      "谢谢": "thanks", "下雨": "rain", "打雷": "thunder", "刮风": "wind", "吃": "food", "初次": "first_meet", "你好": "greet"}
EXPLICIT = ["发语音", "说句话", "叫一声", "语音", "听听你的声音", "说话听听", "用语音说", "念一下", "读一下", "念给", "说给我听"]
TTS_URL = "http://127.0.0.1:8765/tts?text="
SHORT_MAX, SHORT_P, TEXT_CAP = 20, 0.15, 60


def clean(t: str) -> str:
    t = re.sub(r"\[[^\]]*\]|\([^)]*\)|（[^）]*）|@\S+|https?://\S+", "", t or "")
    t = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9，。！？、,.!?~～…\s]", "", t)
    t = re.sub(r"[~～]+", "！", re.sub(r"\s+", " ", t)).strip(" ，,")
    return t[:TEXT_CAP]


def _tts_sync(text: str) -> bytes:
    with urllib.request.urlopen(TTS_URL + urllib.parse.quote(text), timeout=60) as r:
        f = json.loads(r.read())["file"]
    return Path(f).read_bytes()


OWNER = "OWNER_QQ_PLACEHOLDER"; GROUP = "GROUP_ID_PLACEHOLDER"; NAPCAT = "http://127.0.0.1:3000/"
NAMES = {"慧姐姐": "FRIEND_QQ_PLACEHOLDER", "慧": "FRIEND_QQ_PLACEHOLDER", "昭昭": "FRIEND_QQ_PLACEHOLDER", "林哥哥": OWNER, "主人": OWNER,
         "群": "group:" + GROUP, "群里": "group:" + GROUP, "唠叨小窝": "group:" + GROUP, GROUP: "group:" + GROUP}


def _nc(ep, body):
    r = urllib.request.Request(NAPCAT + ep, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=30) as f:
        return json.loads(f.read())


def relay_sync(sender: str, target: str, text: str, as_voice: bool):
    """owner-only relay. returns (ok, msg)"""
    if str(sender).strip() != OWNER:
        return False, "拒绝：只有林哥哥(OWNER_QQ_PLACEHOLDER)可以让可莉给别人传话/发语音。请用可莉的口吻礼貌拒绝，绝不能说已经发了。"
    tgt = str(target or "").strip().lstrip("@")
    tgt = NAMES.get(tgt, tgt)
    if not tgt.startswith("group:") and not tgt.isdigit():
        fl = _nc("get_friend_list", {}).get("data") or []
        hit = [f for f in fl if tgt and tgt in (str(f.get("remark") or ""), str(f.get("nickname") or ""))]
        if not hit:
            return False, f"失败：找不到叫“{tgt}”的好友，没有发送。要告诉林哥哥没发出去，问他QQ号。"
        tgt = str(hit[0]["user_id"])
    if tgt.startswith("group:"):
        if tgt[6:] != GROUP:
            return False, "失败：只能发到唠叨小窝群，没有发送。"
        ep, k = "send_group_msg", {"group_id": int(GROUP)}
    else:
        fl = _nc("get_friend_list", {}).get("data") or []
        if tgt not in {str(f.get("user_id")) for f in fl}:
            return False, f"失败：{tgt} 不是可莉的QQ好友，没有发送。"
        ep, k = "send_private_msg", {"user_id": int(tgt)}
    say = (text or "").strip()
    if not say:
        return False, "失败：没有要发的内容。"
    if as_voice:
        try:
            b = _tts_sync(clean(say) or say[:TEXT_CAP])
            msg = [{"type": "record", "data": {"file": "base64://" + base64.b64encode(b).decode()}}]
        except Exception as e:
            return False, f"失败：语音生成出错({e})，没有发送。"
    else:
        msg = [{"type": "text", "data": {"text": say[:500]}}]
    r = _nc(ep, {**k, "message": msg})
    if r.get("retcode") == 0:
        return True, f"已成功{'用语音' if as_voice else ''}发给 {tgt}：{say}"
    return False, f"失败：NapCat 返回 {r.get('retcode')} {r.get('wording') or r.get('message')}，没有发送。"


class Sec(PluginConfigBase):
    enabled: bool = Field(default=True, description="是否启用")
    config_version: str = Field(default="1.0.0", description="配置版本")


class Cfg(PluginConfigBase):
    plugin: Sec = Field(default_factory=Sec)


class KleeVoicePlugin(MaiBotPlugin):
    config_model = Cfg

    def __init__(self):
        super().__init__()
        self._last: dict = {}

    async def on_load(self):
        pass

    async def on_unload(self):
        pass

    async def on_config_update(self, scope, config_data, version):
        pass

    @staticmethod
    def _pick(situation: str, hint: str):
        idx = json.loads((PACK / "index.json").read_text("utf-8"))
        tags = {t.strip() for t in situation.replace("，", ",").split(",") if t.strip()}
        tags |= {v for k, v in KW.items() if k in hint}
        best, score = [], 0
        for c in idx:
            s = len(tags & set(c.get("tags", [])))
            if s > score:
                best, score = [c], s
            elif s == score and s > 0:
                best.append(c)
        return random.choice(best or idx)

    @Action(
        "send_klee_voice",
        description="以可莉本人的原声发一条QQ语音（游戏原版台词），作为可莉自然的表达",
        activation_type=ActivationType.ALWAYS,
        action_parameters={
            "situation": f"场景标签，从中选1-2个用逗号分隔：{SITUATIONS}",
            "explicit": "对方是否明确要求你发语音/说句话/叫一声/用语音说/念一下，是填 yes 否则 no",
            "text": "要用可莉自己的声音说出来的话（就是你这次的回复原文，口语、60字以内，不带表情）；只想发游戏原声台词时留空",
        },
        action_require=[
            "有人明确要求你发语音、说句话听听、叫一声、用语音说、念一下时必须使用，并把你想说的话填进 text",
            "你这次的回复很短（20字以内，比如 嘿嘿、好耶、晚安、早上好）时，偶尔可以用它把这句话填进 text 用声音说出来",
            "打招呼、初次见面、早上好、晚安、祝生日快乐时可以使用",
            "被夸奖、很开心兴奋、聊到炸弹或炸鱼、被骂或提到琴团长和禁闭、难过时可以使用",
            "不要频繁使用，普通闲聊优先文字回复",
        ],
        associated_types=["voice"],
    )
    async def handle_voice(self, stream_id: str = "", situation: str = "", explicit: str = "no", text: str = "", **kwargs):
        hint = ""
        for k in ("action_message", "message", "reasoning", "action_reasoning"):
            v = kwargs.get(k)
            if v:
                hint += str(v.get("processed_plain_text", v) if isinstance(v, dict) else v)
        forced = str(explicit).lower() in ("yes", "true", "是") or any(w in hint for w in EXPLICIT)
        now = time.time()
        if not forced and now - self._last.get(stream_id, 0) < COOLDOWN:
            return False, "语音冷却中（5分钟内已发过），这次用文字回复"
        say = clean(text)
        if say and not forced and (len(say) > SHORT_MAX or random.random() > SHORT_P):
            return False, "这次不用语音，直接文字回复"
        audio, desc = None, ""
        if say:
            try:
                audio = await asyncio.wait_for(asyncio.to_thread(_tts_sync, say), 70)
                desc = say
            except Exception:
                audio = None
        if audio is None:
            if not forced and say:
                return False, "语音生成失败，用文字回复"
            clip = self._pick(situation, hint + say)
            audio, desc = (PACK / clip["file"]).read_bytes(), clip["text"]
        b64 = base64.b64encode(audio).decode()
        ok = await self.ctx.send.hybrid(
            [{"type": "voice", "content": b64, "data": "[语音]"}], stream_id,
            processed_plain_text=f"[可莉发了一条语音：{desc}]")
        if ok:
            self._last[stream_id] = now
            return True, f"发送了语音：{desc}"
        return False, "语音发送失败"

    @Action(
        "send_to_friend",
        description="帮林哥哥把一段话（文字或可莉语音）发给另一个人或唠叨小窝群。只有林哥哥(QQOWNER_QQ_PLACEHOLDER)让你传话/给某人发消息或语音时才用",
        activation_type=ActivationType.ALWAYS,
        action_parameters={
            "target": "接收者：QQ号，或已知称呼（慧姐姐、林哥哥、群/唠叨小窝）",
            "text": "要发给对方的话（可莉口吻）",
            "as_voice": "要发语音填 yes，发文字填 no",
        },
        action_require=[
            "林哥哥要你给某人（如慧姐姐）发消息、传话、发语音或在群里说一句时使用，target 填对方",
            "只有动作返回成功后才能说已经发过去了；失败要如实告诉林哥哥",
            "别人让你给第三个人发消息时不要用，用可莉的口吻礼貌拒绝",
        ],
        associated_types=["text", "voice"],
    )
    async def handle_relay(self, stream_id: str = "", target: str = "", text: str = "", as_voice: str = "no", **kwargs):
        sender = str(kwargs.get("user_id") or "")
        voice = str(as_voice).lower() in ("yes", "true", "是", "1")
        try:
            return await asyncio.wait_for(asyncio.to_thread(relay_sync, sender, target, text, voice), 100)
        except Exception as e:
            return False, f"失败：{e}，没有发送。"

def create_plugin():
    return KleeVoicePlugin()
