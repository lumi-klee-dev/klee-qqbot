# 自己下载素材（仓库不包含）

可莉的语音、立绘、表情包和音色模型都属于米哈游（miHoYo）或原作者，本仓库不分发。请自行下载，仅限个人学习使用。

## 1. 原声语音包（klee_voice 插件的预录台词）
- 来源：哔哩哔哩原神 WIKI（bwiki）可莉语音页：https://wiki.biligame.com/ys/可莉语音
- 页面里每条中文台词都有 `.ogg` 链接。把需要的台词下载到 `klee/voice_pack/`，文件名对应 `scripts/voice_lines.md` 里的台词 key。
- QQ 发语音需要转成 silk/amr，或交给 NapCat 自动转码（需要 ffmpeg）。

## 2. 克隆音色（GPT-SoVITS 可莉模型）
- 模型：Hugging Face Space `baicai1145/Genshin_A-L`：https://huggingface.co/spaces/baicai1145/Genshin_A-L
- 下载其中「可莉」的 GPT（`.ckpt`）和 SoVITS（`.pth`）权重，以及参考音频，放到 `tts/model/`、`tts/refs/`。
- 安装 GPT-SoVITS 依赖后运行 `tts/start_tts.sh`，`tts/server.py` 会在本机提供合成接口，CPU 也能跑短句。

## 3. 表情包、头像、立绘
- 原神官方表情可以从 bwiki 表情页或米游社下载；其他可莉表情图请自己挑选，并注意来源授权。
- 放到 MaiBot 的表情目录后，按情绪（开心、委屈、生气、炸弹等）打标签。
- QQ 头像和资料卡图片请自己准备。
