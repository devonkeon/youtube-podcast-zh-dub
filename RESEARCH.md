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
| **BaoCut 0.8.3** (`baocut.app` / `JimLiu/baocut`，本机已安装) | macOS 应用 + `baocut-cli` | yt-dlp 收 URL → MLX 本地 ASR（**词级时间戳**）→ 语义分组 → polish → LLM 翻译 → 说话人识别 → audit/finish-check → 导出双语 SRT/视频/剪辑工程 | **缺的只有音轨**。前半条链路是成熟产品，质量高于我们自研 |

### BaoCut 能力实测（2026-08-01，`baocut-cli --help` 及各子命令 `--help` 原始输出）

```
timing repair    repair zero/negative-duration words          → 每个词有独立时长
subtitle retime  linearly remap the cue's word times          → 词级时间可重映射
subtitle split   --at <t|wordId>, splits AFTER that word      → 词有稳定 id
caption          native word-level motion                     → 词级动画
align list --fit  列出超出单行容量的翻译组，给出 cpsChars/splittable/overHard
task start align  不重译、只重新切分对齐（Phase 2）
export --srt --bilingual --lang zh   原文+译文，按 source-cue 时间轴
--json (全局)     每个结果带 status，动作结果带 projectId
auto <file|URL> --lang zh            transcribe → polish → translate 一个任务搞定
audit / finish-check                 覆盖率、行宽、时序、闪烁、验收门
```

关键结构：`subtitle list` 返回原文 cue id（`q-…`）与译文 group id；译文与源 cue 是**多对一分组**模型。CLI 自己不调 LLM，`task wait` 把待办 prompt 以文件引用交给外部 agent，`task submit` 同步 lint——**翻译由我们驱动的 agent 写，风格与字数完全可控**。

商业方案（HeyGen / Rask / ElevenLabs Dubbing / VMEG）：质量高、含唇形同步，但闭源、按分钟计费、不可控。仅作质量标尺。

## 2. 判断（基于以上事实）

1. **以 BaoCut 为前半条链路，本项目只做"配音层"**。这正是最初的设想：*在其上增加中文翻译的音轨*。
   BaoCut 已覆盖 ingest / 词级 ASR / 语义分组 / polish / 翻译 / 说话人 / 字幕导出 / 质检，
   且有 `--json` CLI 供 agent 驱动。自研这半条只会更差更慢。
2. **本项目自研且只自研**：TTS 合成 → 时长适配 → 绝对时间轴拼接 → ffmpeg 双音轨双字幕封装 → 人耳样片验收。
3. **产品差异点仍然成立，但落点变了**。BaoCut 的 `align` 把译文拟合到**字幕单行容量**（`--fit`，CJK 默认 16 字），
   这是"看得下"的约束；配音要的是"**说得完**"的约束 —— 目标是 `字数 ≈ 时长 × 5.2`。两者不是一回事。
   我们在 BaoCut 的 `task` 循环里注入配音字数区间，把时长对齐提前到翻译阶段；
   剩余超长组再用 `subtitle set --lang zh` 定点压缩重写并重合成。
4. **KrillinAI / VideoLingo / pyVideoTrans 不 fork，只借鉴一点**：pyVideoTrans 的
   「变速 + 补静音 + 保持段间隔」是我们 fit 阶段的参考实现。
5. 首版**不做唇形同步、不做人声分离**。播客场景收益低、成本高。

> **更正记录**：本文件初版曾断言"BaoCut 无词级时间戳、不能作主链路"。该结论**未经核实且错误**，
> 已被上表的 CLI 原始输出推翻，架构随之改为以 BaoCut 为前半链路。

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
