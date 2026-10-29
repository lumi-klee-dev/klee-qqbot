# 可莉 QQ 机器人（klee-qqbot）

一个以《原神》可莉为人设的 QQ 聊天机器人，基于 [MaiBot（麦麦）](https://github.com/Mai-with-u/MaiBot) 和 [NapCat](https://github.com/NapNeko/NapCatQQ)（OneBot 11）。本仓库**只包含我们自己写的脚本、插件、补丁和脱敏后的配置模板**，不包含上游源码、任何密钥、聊天记录或米哈游素材。

## 架构
```
QQ 客户端(NapCat, xvfb) --OneBot11 WS:3001/HTTP:3000--> napcat_adapter 插件 --> MaiBot(人设/记忆/回复决策)
                                                                         |--> 模型路由（SenseNova 等 OpenAI 兼容接口，多模型自动降级）
                                                                         |--> klee_voice 插件 --> 原声台词 / 本地 GPT-SoVITS TTS(tts/server.py)
watchdog.sh（cron 每分钟） / proactive.py（主动发言） / inbox_ws.py（消息记录）
```

## 目录
- `persona.toml`：可莉人设（别名、语气、绝对不出戏、儿童安全规则）
- `config/bot_config.template.toml`、`config/model_config.template.toml`：脱敏配置模板（所有 key、QQ 号已替换为占位符）
- `keys.env.example`：环境变量模板
- `plugins/klee_voice/`：发语音插件（场景触发原声台词 + 克隆音色合成）
- `patches/`：对上游的补丁（MaiBot `utils.py` 的强制回复判定、NapCat `napcat.mjs` 补丁）
- `scripts/`：启动/停止/重启大脑/看门狗/主动发言/消息记录/配置脚本；`fetch_assets.md` 说明素材下载
- `tts/`：本地 GPT-SoVITS 合成服务
- `使用说明.md`：日常操作手册

## 部署
1. 安装 NapCat（Linux 版 QQ + NapCat.Core），开启 OneBot 11 HTTP 3000、WebSocket 3001，扫码登录一次，之后用 `-q <BOT_QQ>` 快速登录。
2. 克隆 MaiBot 到 `MaiBot/`，启用 napcat_adapter 插件；把 `plugins/klee_voice` 复制到 `MaiBot/plugins/`。
3. 应用补丁：`cd MaiBot && patch -p1 < ../patches/maibot-utils-force-reply.patch`；NapCat 补丁按需应用到 `napcat.mjs`。
4. `cp keys.env.example keys.env` 并填入你的 key、`BOT_QQ`、`OWNER_QQ`、`GROUP_ID`；把两个配置模板复制到 `MaiBot/config/`，替换 `YOUR_API_KEY` 和 `*_PLACEHOLDER`（也可以跑 `scripts/configure.py`）。
5. 按 `scripts/fetch_assets.md` 自行下载语音、表情包和 TTS 模型。
6. `scripts/start.sh` 启动；改完配置用 `scripts/restart-brain.sh`（只重启 MaiBot，不掉 QQ 登录）。脚本里的路径默认是 `/workspace/dafeiyu`，请按需修改。

## 功能
- **人设**：活泼的火花骑士可莉，永不承认自己是 AI；拒绝恋爱/色情内容，不鼓励现实中玩火。
- **群聊规则**：主人的消息必回；@她、回复她、喊她名字必回；正在和她聊的人会一直接话直到话题自然结束；其他消息按兴趣选择性插话，插几次后会安静一阵。会记住群里每个人并形成印象。
- **私聊**：所有私聊都回。
- **语音**：打招呼、早安晚安、生日、被夸、聊炸鱼等场景发原声台词（同一聊天 5 分钟最多 1 条）；有人要求发语音或回复很短时，用克隆音色合成；合成失败回落到原声。
- **表情包**：按回复情绪挑选可莉表情（需自行下载，见 fetch_assets.md）。
- **主动性**（`proactive.py`）：白天群里冷场 1.5 小时以上时可能主动开话题（每天最多 4 次、间隔 ≥2 小时）；偶尔私聊主人（每天最多 2 条），深夜不打扰。
- **看门狗**（`watchdog.sh`）：每分钟检查 QQ/MaiBot/TTS，挂了自动拉起；30 分钟内最多重启 3 次；需要重新扫码时只记录不清登录。
- **模型路由**：主聊天优先 DeepSeek V4.1 Flash（SenseNova），限流时依次降级到 glm-5.2、kimi-k3 等；判断/杂活/表情/看图用 sensenova-6.8-flash-lite；联网搜索用 Tavily；记忆向量和语音识别可接 SiliconFlow（bge-m3 / SenseVoiceSmall）。

## 声明
非商业的爱好者项目。可莉及《原神》相关形象、语音、图片版权归米哈游所有，本仓库不包含任何此类素材。请遵守 QQ 用户协议，自行承担使用风险。
