# SPEC：YouTube 播客中文口播版

> 本文件是实现契约。执行 agent（kimi / grok / hermes）只需读本文件 + PLAN.md 即可开工，**不需要读其他目录**。

## 0. 产品定义（验收的最终标准）

一条命令，把一个 YouTube 播客视频变成：

- **默认播放即中文口播**（中文配音是第 0 条音轨且标记 default）
- **可一键切回英文原声**（原声保留为第 1 条音轨）
- **中英双语字幕**（软字幕轨 + 独立 .srt 文件 + 可选硬烧录版本）
- 口播**跟得上画面**：任意时刻中文说的内容与画面/原声在同一件事上，偏差 < 0.5s

**产品失败的定义**（技术上跑通但产品不合格，一律算失败）：
中文听起来像机器人念稿、语速忽快忽慢、明显赶字、段落之间抢话或大段空白、
字幕与语音对不上、翻译是书面语而不是口语。

## 1. 命令行契约

```bash
zhdub run <YouTube URL | 本地视频路径> [options]

  --out DIR              输出目录，默认 ./runs/<video_id>
  --asr {whisper,assemblyai}      默认 whisper（本地 faster-whisper large-v3）
  --tts {edge,mimo}               默认 edge
  --voice NAME           默认 zh-CN-YunxiNeural
  --burn-subs            额外产出硬烧录双语字幕的 mp4
  --max-speed FLOAT      单段最大变速比，默认 1.30
  --resume               从已有 run 目录的最后成功阶段继续
  --stage STAGE          只跑到某阶段（ingest|asr|segment|translate|tts|fit|mux）
  --dry-run              只跑到 translate，产出字幕不产出音频（用于快速校对翻译）

zhdub qc <run目录>        重跑质检并产出对照片段
zhdub doctor             检查 ffmpeg/yt-dlp/网络/密钥是否就绪
```

## 2. 运行目录结构（每个阶段的产物都要落盘，用于 --resume 和取证）

```
runs/<video_id>/
  meta.json                 # 视频标题/时长/URL/分辨率/采样率/各阶段耗时
  source/video.mp4          # 原视频
  source/audio.wav          # 16kHz 单声道，供 ASR
  work/transcript.json      # 阶段2 产物：词级时间戳
  work/units.json           # 阶段3 产物：配音单元
  work/translated.json      # 阶段4 产物：含中文译文与目标字数
  work/tts/unit_0001.wav …  # 阶段5 产物：每段原始中文音频
  work/fitted/unit_0001.wav # 阶段6 产物：变速/补白后的音频
  audio/zh_dub.wav          # 拼接后的完整中文音轨（与原视频等长）
  subtitles/en.srt
  subtitles/zh.srt
  subtitles/bilingual.srt   # 中文在上、英文在下
  output/dubbed.mp4         # ★ 主交付物
  output/dubbed_burned.mp4  # 可选
  quality/qc_report.json
  quality/samples/sample_1.mp4 … sample_3.mp4   # ★ 人耳验收片段
  logs/<stage>.log
```

## 3. 各阶段实现细则

### 阶段 1 · ingest
- `yt-dlp -f "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]" --merge-output-format mp4`
- 同时 `ffmpeg -i video.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le source/audio.wav`
- 失败重试 3 次；yt-dlp 报 403/限流时提示更新 yt-dlp，不要静默降级
- 本地文件输入时跳过下载，直接抽音轨

### 阶段 2 · asr（必须有词级时间戳）
- 默认 `faster-whisper`，模型 `large-v3`，`word_timestamps=True`，`vad_filter=True`，
  `compute_type="int8"`（Apple Silicon CPU 可跑；有 MPS 则用 float16）
- 备用 `assemblyai`：`speaker_labels=True`, `punctuate=True`, `format_text=True`
- 统一输出 `transcript.json`：
  ```json
  {"language":"en","words":[{"start":1.23,"end":1.45,"text":"hello","speaker":"A"}]}
  ```
- **验收**：词数 > 0，最后一个词的 end 与音频时长差 < 5s（否则说明转录截断）

### 阶段 3 · segment（质量命门，不要偷懒）
把词序列切成"配音单元"，规则按优先级：
1. 句末标点（`. ? !`）**必切**
2. 单元时长上限 **12s**，下限 **1.2s**（过短的与相邻同说话人单元合并）
3. 词间静音 ≥ **0.5s** 视为可切点
4. 说话人变化**必切**
5. 超长句在 `, ; and but so because that which` 等连接处切，且切点两侧各 ≥ 1.5s
- 输出 `units.json`：`[{"id":1,"start":..,"end":..,"dur":..,"speaker":"A","text_en":".."}]`
- **验收**：无单元 > 12.5s；无单元 < 1.0s；相邻单元不重叠；覆盖率 > 95% 音频时长

### 阶段 4 · translate（本项目的差异点）
- 逐单元翻译，但每次请求带 **前 2 句 + 后 2 句原文**作为上下文（不翻译上下文）
- **两遍法**：第一遍直译 → 第二遍以"中文播客主播口语"改写（去掉 uh/you know/I mean，
  长句拆短，被动改主动，术语保留英文原词）
- **字数约束（关键）**：对每个单元计算目标字数
  `target_chars = dur × 5.2`（中文播客舒适语速 ≈ 5.2 字/秒），
  在 prompt 中明确要求 `target_chars × 0.85 ~ × 1.15`；
  返回后校验字数，超界的单元**自动重试一次并把区间写进 prompt**（最多 2 次）
- 全局术语表 `config/glossary.json`（人名/公司名/专有名词固定译法），每次请求注入
- 输出 `translated.json`：`[{"id":1,...,"text_zh":"..","target_chars":62,"actual_chars":58}]`
- **验收**：100% 单元有译文；字数超界单元占比 < 10%；无残留英文整句

### 阶段 5 · tts
- `edge-tts`：`Communicate(text, voice, rate="+0%")`，输出 mp3 → 统一转 24kHz 单声道 wav
- 说话人映射：`config/voices.json` 把 speaker A/B 映射到不同音色（播客常有主持+嘉宾）
- 并发 4，失败重试 2 次；空音频（< 0.1s）判为失败
- 可选 `mimo` 声音克隆：参考 `../audiobook/engine/audiobook/voice/mimo_client.py` 的调用方式**照抄重写**（不 import），需要一段干净参考音频
- **验收**：每个单元都有 wav 且 > 0.2s

### 阶段 6 · fit（时长对齐）
对每个单元，令 `src_dur` = 原单元时长，`tts_dur` = 合成音频时长：

| 情况 | 处理 |
|---|---|
| `tts_dur ≤ src_dur` | 原速播放，尾部补静音至 `src_dur` |
| `src_dur < tts_dur ≤ src_dur × max_speed` | `ffmpeg atempo=tts_dur/src_dur` 压到 `src_dur` |
| `tts_dur > src_dur × max_speed` | **回到阶段 4**，要求 LLM 把该句压缩到 `target_chars × 0.8` 重译重合成（最多 2 轮）；仍超则 `atempo=max_speed` 并在 QC 报警 |

- `atempo` 超过 2.0 需串联多个 atempo；本项目上限 1.30，单个即可
- 段间保持原始静音间隔；**以原始时间轴绝对定位**每个单元（不要顺序拼接，避免误差累积）
- 拼接方式：生成与原视频等长的静音底轨，用 `ffmpeg adelay` / `sox` 或 numpy 按 `start` 精确贴入
- **验收**：`|len(zh_dub.wav) - len(source video)| < 0.5s`；每单元起始偏差 < 100ms

### 阶段 7 · mux
```
ffmpeg -i source/video.mp4 -i audio/zh_dub.wav \
  -map 0:v -map 1:a -map 0:a \
  -c:v copy -c:a aac -b:a 192k \
  -metadata:s:a:0 language=chi -metadata:s:a:0 title="中文配音" -disposition:s:a:0 default \
  -metadata:s:a:1 language=eng -metadata:s:a:1 title="原声"    -disposition:s:a:1 0 \
  -map 2:s -map 3:s -c:s mov_text \
  -movflags +faststart output/dubbed.mp4
```
（字幕轨用 `-i subtitles/zh.srt -i subtitles/en.srt` 一并输入；mp4 用 `mov_text`，
若要保留样式则输出 mkv 用 `srt`。**默认出 mp4**，因为 QuickTime/IINA/VLC 都能切轨。）
- 硬烧录版本：`-vf "subtitles=bilingual.srt:force_style='FontName=PingFang SC,FontSize=18'"`
- **验收**：`ffprobe` 显示 2 条音轨 + 2 条字幕轨，音轨 0 的 disposition 含 default

## 4. QC 质量门（`quality/qc_report.json`，任一 FAIL 则整个 run 失败）

| 检查项 | 阈值 | 级别 |
|---|---|---|
| 单元覆盖率 | > 95% | FAIL |
| 缺失 TTS 单元 | 0 | FAIL |
| 全片时长漂移 | < 0.5s | FAIL |
| 单元起始偏差 | < 100ms | FAIL |
| 变速 > 1.25 的单元占比 | < 15% | WARN，> 30% FAIL |
| 中文语速 | 3.5–6.5 字/秒 | 越界 WARN |
| 连续静音 | > 3s 且原声非静音 | WARN |
| 输出视频可解码、双音轨、双字幕轨 | ffprobe 验证 | FAIL |

**人耳验收（不可省）**：从全片 25% / 50% / 75% 处各截 15 秒，导出
`quality/samples/sample_N.mp4`（中文音轨 + 双语字幕）。**没有这三个片段，不许报"完成"。**

## 5. 配置文件

- `.env`（不进 git）：`ASSEMBLYAI_API_KEY` / `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` / `MIMO_API_KEY`
- `config/default.yaml`：语速常数、上限、并发、模型名、音色
- `config/glossary.json`：术语表
- `config/voices.json`：说话人→音色映射

## 6. 技术栈与约束

- Python **3.11**（`uv venv --python 3.11`；不要用系统 3.9，也避开 3.13 的轮子缺失问题）
- 依赖：`yt-dlp faster-whisper edge-tts httpx pydantic typer rich pyyaml numpy soundfile assemblyai`
- 外部：`ffmpeg` / `ffprobe`（homebrew，已装）
- **禁止**：引用 `../podcast-tool-local`、`../audiobook`、`../youtube-zh-dub` 的任何代码/venv/密钥文件；
  需要的东西复制进本目录
- **禁止**：上传/发布到 YouTube；只产出本地文件
