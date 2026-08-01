# 调研报告（Plan 阶段第 1 步）

日期：2026-08-01　方法：先检索既有方案 → 罗列事实 → 基于事实判断

## 1. 现成开源方案（近 2 年，事实清单）

| 项目 | 形态 | 技术路线 | 与我们场景的差距 |
|---|---|---|---|
| **KrillinAI / KlicStudio** (`github.com/krillinai/KrillinAI`) | Go 桌面/服务，活跃 | 下载→ASR→LLM 翻译→TTS 配音→字幕烧录，一体化；已内置面向 AI Agent 的 Skills | 最接近成品。中文配音质量依赖所选 TTS 供应商；断句/时长对齐策略不可控 |
| **VideoLingo** (`Huanshere/VideoLingo`) | Python + Streamlit | WhisperX 词级时间戳 → NLP 断句 → 三步翻译（直译/反思/意译）→ 字幕 → 配音 | 断句与翻译质量最好，值得抄的是「词级时间戳 + 语义断句」和「三步翻译」 |
| **pyVideoTrans** (`pyvideotrans.com`) | Python 桌面 | faster-whisper → 翻译 → TTS → `videotrans/task/rate.py` 做**配音/字幕/视频三方对齐** | 时长对齐模块是本项目最该借鉴的部分（变速 + 补静音 + 片段合并） |
| **SmartSub / 妙幕** (`buxuku/smartsub`) | Electron 桌面 | 转字幕→翻译→润色→TTS 配音→烧录 | 产品形态参考（桌面一条龙），非管线参考 |
| **voice-pro** (`abus-aikorea/voice-pro`) | Gradio | YouTube 下载→人声分离→Whisper→翻译→TTS | 多了 UVR 人声分离，播客场景可选（保留背景音乐） |
| **BaoCut** (`baocut.app`, 本机 `/Applications/BaoCut.app` 已安装) | macOS 应用 | 英文视频→中文字幕 | **只做字幕，没有音轨**。定位为可选的字幕来源，不作为主链路依赖 |

商业方案（HeyGen / Rask / ElevenLabs Dubbing / VMEG）：质量高、含唇形同步，但闭源、按分钟计费、不可控。仅作质量标尺。

## 2. 判断（基于以上事实）

1. **不从零造轮子，也不 fork 任何一个**。KrillinAI/VideoLingo 都是"大而全 + GUI"，把 YouTube 播客这一垂直场景做深反而更简单：播客是**单机位、说话人少、背景音乐轻、无需唇形同步**，可以砍掉视频重绘、唇形、人声分离等重模块。
2. **必抄的三件事**：
   - VideoLingo 的「词级时间戳 → 语义断句」（断句错，后面全错）
   - VideoLingo 的「翻译要带上下文 + 二次反思」
   - pyVideoTrans 的「时长对齐 = 变速 + 补静音 + 段间隔保持」
3. **必须自研的一件事**：**让 LLM 在翻译时就控制中文字数**，把时长对齐从"事后补救"提前到"源头约束"。这是现有开源工具做得最差的一环（它们普遍靠 1.5x 以上变速硬压，听感明显发飘）。这是本项目的产品差异点。
4. **BaoCut 只作可选字幕输入**，不作依赖——它无法提供词级时间戳，会拖垮断句质量。
5. 首版**不做唇形同步**。播客场景收益极低、成本极高。

## 3. 本机环境实测（2026-08-01，用户 Mac）

```
macOS 26.5.2
python3.13 (/opt/homebrew/bin) · python3.11 (~/.local/bin) · uv 已装
ffmpeg / ffprobe / yt-dlp  已装（homebrew）
gh 已登录：devonkeon（keyring，https）
本地 agent：grok · kimi · hermes · codex · claude 均在 PATH
BaoCut.app 已安装
```

可用密钥（存在于同级其他项目，**本项目需自己复制一份到自己的 .env，不跨目录引用**）：

| 用途 | 来源文件 | 变量 |
|---|---|---|
| 云端 ASR（带说话人分离） | `../podcast-tool-local/pipeline/.env` | `ASSEMBLYAI_API_KEY`、`ASSEMBLYAI_BACKUP_API_KEY` |
| 翻译 LLM | `../podcast-radar/.env` | `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`(deepseek) |
| 翻译 LLM 备用 | `../audiobook/.env` | `MIMO_API_KEY`、`MOSS_API_KEY`、`OPENCODE_GO_API_KEY` |
| 中文声音克隆（可选） | `../audiobook/.env` | `MIMO_API_KEY`（audiobook 项目已有可跑通的调用代码，见 `engine/audiobook/voice/mimo_client.py`，可**照抄实现**但不要 import） |

**默认 TTS 选 edge-tts**：免费、无需 key、`zh-CN-YunxiNeural`（男声，适合播客）/ `zh-CN-XiaoxiaoNeural`（女声），原生支持 `rate=±N%`，是当前中文配音性价比最高的方案。MiMo 声音克隆作为 `--tts mimo` 可选项。

## 4. 前次尝试的处理

同目录 `../youtube-zh-dub/` 是 2026-08-01 18:xx 的一次尝试，其 `STATE.md` 自述"**尚未运行真实 URL、BaoCut、TTS 或成品视频测试**"，且以 BaoCut + macOS `say` 为主链路——链路选型不成立。

**结论：不作为基线。** 仅 `src/zhdub/srt.py`、`mux.py`、`qc.py` 可作为代码片段参考，需重新验证。本项目独立建仓、独立目录。
