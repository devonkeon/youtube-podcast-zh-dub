# SPEC：YouTube 播客中文口播版（配音层）

> 实现契约。执行 agent（kimi / grok / hermes）读本文件 + PLAN.md 即可开工，**不需要读本目录以外的文件**。
>
> **架构前提**：BaoCut 0.8.3 负责下载/转录/分组/翻译/字幕；**本项目只做配音层**。
> 能力实测证据见 RESEARCH.md 第 1 节。

## 0. 产品定义（最终验收标准）

一条命令，把一个 YouTube 播客变成：

- **默认播放即中文口播**（中文音轨为第 0 轨且 `disposition=default`）
- **可一键切回英文原声**（原声保留为第 1 轨）
- **中英双语字幕**（软字幕轨 + 独立 `.srt` + 可选硬烧录版）
- 口播**跟得上画面**：任意时刻中文所讲与画面/原声在同一件事上，偏差 < 0.5s

**产品失败的定义**（技术跑通但产品不合格，一律算失败）：
中文像机器人念稿 · 语速忽快忽慢 · 明显赶字 · 段落抢话或大段空白 · 字幕与语音对不上 · 书面语而非口语。

## 1. 职责边界

| 阶段 | 由谁做 | 接口 |
|---|---|---|
| 下载 URL / 本地文件 | **BaoCut**（内置 yt-dlp） | `baocut --json auto <url\|file> --lang zh` |
| ASR（词级时间戳，MLX 本地） | **BaoCut** | 同上 |
| 语义分组 / polish / 说话人 | **BaoCut** | 同上 |
| 翻译 | **BaoCut 的 task 循环 + 我们注入的配音 prompt** | `task wait` → 写答案 → `task submit` |
| 字幕导出 | **BaoCut** | `export --srt --bilingual --lang zh` |
| 字幕质检 | **BaoCut** | `audit` / `finish-check` |
| **TTS 合成** | ★ 本项目 | — |
| **时长适配** | ★ 本项目 | — |
| **绝对时间轴拼接** | ★ 本项目 | — |
| **双音轨双字幕封装** | ★ 本项目 | — |
| **配音质检 + 人耳样片** | ★ 本项目 | — |

`baocut-cli` 路径：`/Applications/BaoCut.app/Contents/MacOS/baocut-cli`（不在 PATH，需在 config 里配）。

## 2. 命令行契约

```bash
zhdub run <YouTube URL | 本地视频路径> [options]
  --out DIR          默认 ./runs/<projectId>
  --project ID       跳过 BaoCut 阶段，直接对已有 BaoCut 项目配音
  --tts {edge,mimo}  默认 edge
  --voice NAME       默认 zh-CN-YunxiNeural
  --max-speed FLOAT  单段最大变速比，默认 1.30
  --cps FLOAT        中文舒适语速（字/秒），默认 5.2
  --burn-subs        额外产出硬烧录双语字幕 mp4
  --resume           从最后成功阶段继续
  --stage STAGE      只跑到某阶段（baocut|tts|fit|mux|qc）

zhdub qc <run目录>    重跑质检并导出人耳样片
zhdub doctor         检查 baocut-cli / ffmpeg / 密钥 / 模型
```

## 3. 运行目录

```
runs/<projectId>/
  meta.json                 # BaoCut projectId、URL、时长、各阶段耗时
  source/video.mp4          # 从 BaoCut 项目取得或本地拷入的原视频
  work/groups.json          # ★ 配音单元（由 baocut subtitle list 转换而来）
  work/tts/g_<id>.wav       # 每单元原始中文音频
  work/fitted/g_<id>.wav    # 变速/补白后
  audio/zh_dub.wav          # 完整中文音轨，与原视频等长
  subtitles/{zh,en,bilingual}.srt
  output/dubbed.mp4         # ★ 主交付物
  output/dubbed_burned.mp4  # 可选
  quality/qc_report.json
  quality/samples/sample_{1,2,3}.mp4   # ★ 人耳验收片段
  logs/<stage>.log
```

## 4. 阶段实现细则

### 阶段 A · baocut（驱动，不重写）

1. `baocut --json auto <input> --lang zh` → `{taskId, projectId}`
2. 循环：`baocut --json task wait <taskId>` → 返回待办 prompt 的**文件引用**；
   按 `skills/baocut/SKILL.md` 与 `contracts/<kind>.md` 写答案 → `baocut --json task submit <taskId> --call <id> --file <答案文件>`
   直到 `{"status":"done"}`
3. **翻译 prompt 注入（本项目的差异点）**：在 translate 类 prompt 的答案里，
   除 BaoCut 原有要求外，额外遵守：
   - 中文播客主播口语：去掉 uh / you know / I mean，长句拆短，被动改主动，术语保留英文原词
   - **字数区间**：目标 `avail × cps`（cps 默认 5.2），允许 `×0.85 ~ ×1.15`
   - 术语表 `config/glossary.json` 全量注入

   ⚠️ **M1 实测：translate payload 里没有任何时长字段**，只有 `maxChars`——那是**字幕单行
   阅读速度预算**（9 个非空白字符/秒的显示上限），与配音语速无关，**不可直接当字数预算用**。
   所以时长必须由我们自己算：claim 到 translate 待办后，先跑
   `subtitle list <pid> --lang zh --limit 500` 拿到各组 `start/end`，算出 `avail` 与
   `target_chars`，再写译文。【推断·未验证】translate payload 的行 id 与 `subtitle list`
   的 group id 是否一一对应 —— **M3 第一件事就是验证这个映射**，对不上则退化为
   "先照常翻译，再用 `subtitle set` 定点压缩重写"。
4. `baocut --json subtitle list <pid> --lang zh --limit 500` → 转成 `work/groups.json`。
   **字段映射已由 M2 实测定死**（`docs/BAOCUT_NOTES.md` M2-1）：
   `id→gid` · `start/end→start/end`（绝对秒）· `text→text_zh` · `source→text_en` ·
   `speakerId→speaker` · `hidden=true` 的组**不配音**。
   ```json
   [{"gid":"g1.0","start":3.24,"end":4.77,"dur":1.53,"gap":4.65,"avail":2.03,
     "speaker":"s1","text_en":"Something for every sky watcher.",
     "text_zh":"献给每一位仰望星空的人。","target_chars":10,"actual_chars":12}]
   ```
5. `baocut export <pid> --srt --bilingual --lang zh -o subtitles/bilingual.srt`（同理导出 zh / en）
6. `baocut audit <pid>` 与 `finish-check` 有 blocker → **中止**，不进入配音

**验收**：`groups.json` 每条都有 `text_zh`、`dur > 0`、无重叠；覆盖率 > 95% 视频时长。

### 阶段 B · tts（★ 必须批量合成后再切，禁止逐句合成）

**为什么**：逐句单独调 TTS 会导致
① **音色漂移**——克隆类模型每次调用都重新采样说话人特征，同一角色几句话之后就变了人；
② **韵律断裂**——即使用固定预设音色（edge-tts 不会漂移音色），每句都是"冷启动"，
句间没有语调承接，听起来像念列表而不是讲话。
用户在既往播客项目中已反复踩到 ①，这不是理论风险。

**做法（沿用既有 multi-TTS 批量方案）**：

1. **分批**：按「同一 speakerId 的连续组」切成批，单批上限约 60 秒或 12 组，
   遇到说话人切换 / 章节边界必断
2. **一次合成整批**：把批内各组文本按顺序拼成一段（组间用自然停顿标点分隔），**一次调用**
3. **按时间标记切开**：用 TTS 返回的 word/sentence boundary 偏移量定位每组的起止，切成 `work/tts/g_<id>.wav`
   - edge-tts 返回 `WordBoundary` 事件（词在合成音频中的偏移），即切割的尺子
     —— 【推断·未验证】**M4 第一件事就是验证 edge-tts WordBoundary 的实际精度**；
     若不可用，回落方案：批内用静音检测切分，或改用能返回时间戳的 TTS
4. **批内时间再分配**：切开后，批内各组可以互相借时间（前一组说快一点让后一组宽松），
   比逐组独立压缩更自然

**音色**：
- 说话人映射 `config/voices.json`；**未确认的说话人一律回落默认音色，不猜**（见阶段 A-bis）
- 默认 edge-tts 预设音色（不漂移）；`--tts mimo` 等克隆音色属于高漂移风险路径，
  必须整批合成，且开启时 QC 增加音色一致性抽检

**验收**：每个 group 都有 wav 且 > 0.2s；同一 speakerId 的相邻批之间人耳听不出换人。

### 阶段 A-bis · 说话人确认门（★ 多人节目的生死线）

用户既有工作流中「张冠李戴」反复发生，**配错音色比不分音色更糟**。因此：

1. **默认单一音色**。多音色是 opt-in（`--multi-voice`），且必须过下面这道门
2. 过门流程（BaoCut 已提供全部工具）：
   - `speakers reidentify <pid> --count 2,3 --review` → 一次 diarization 出多个提案
   - `speakers proposals <pid> <a> <b>` → 逐 cue 对比分歧
   - `speakers view <pid> --rerun` → 波形 + 双说话人条带 + **分歧/模糊标记** PNG
   - 对分歧点：`frames --at <t>` 取画面帧做视觉确认（视频播客能直接看出谁在说）
   - `speakers assign --cue <id>` 定点改正；`--protect` 锁住已确认的说话人
   - `speakers propose-names` 从自我介绍（"我是X"/"I'm X"）推断人名，**不自动应用**
3. **判定规则**：分歧 cue 占比 > 5% 且未逐一确认 → **拒绝多音色，整片回落单一音色**，
   并在 QC 报告里写明原因。宁可少用音色，不可张冠李戴。

**验收**：多音色模式下，分歧 cue 全部经过视觉或文本证据确认；否则自动降级并记录。

### 阶段 C · fit（时长适配）

**★ 可用时长不等于 group 时长。** M2 实测（见 `docs/BAOCUT_NOTES.md`）：只用 group 自身时长时，
28% 的组需要 >1.25 变速，逼近 FAIL 线；允许向后续静音间隙溢出 60% 后降到 12%。

```
gap      = next_group.start − this_group.end      # 组间静音
avail    = dur + max(0, min(gap × 0.6, gap − 0.15))   # ★ 可用时长，至少留 0.15s 呼吸
```

令 `tts_dur = len(wav)`：

| 情况 | 处理 |
|---|---|
| `tts_dur ≤ avail` | 原速，尾部补静音至 `avail` |
| `avail < tts_dur ≤ avail × max_speed` | `ffmpeg atempo=tts_dur/avail` 压到 `avail` |
| `tts_dur > avail × max_speed` | **回退重写**：`baocut subtitle set <pid> <gid> --lang zh --text "<压缩到 avail×cps×0.8 字的新译文>"`，重合成（最多 2 轮）；仍超则 `atempo=max_speed` 并在 QC 记 WARN |

- `target_chars` 一律按 **`avail × cps`** 算，不是 `dur × cps`
- `atempo` 单个上限 2.0，本项目封顶 1.30，单个足够
- 拼接：生成与原视频等长的静音底轨，**按 `start` 绝对定位贴入**（禁止顺序拼接，会累积误差）
- **病态组兜底**：`dur < 0.7s 且 gap < 0.2s` 的组（M2 实测存在，如 `g28.7` cps=32.3）
  变速和压缩都救不了 → 与相邻**同 speakerId** 组合并共享时间预算后再分配；
  合并后仍超标则记 FAIL，不许静默放过

**验收**：`|len(zh_dub.wav) − 视频时长| < 0.5s`；每单元起始偏差 < 100ms。

### 阶段 D · mux

```
ffmpeg -i source/video.mp4 -i audio/zh_dub.wav -i subtitles/zh.srt -i subtitles/en.srt \
  -map 0:v -map 1:a -map 0:a -map 2 -map 3 \
  -c:v copy -c:a aac -b:a 192k -c:s mov_text \
  -metadata:s:a:0 language=chi -metadata:s:a:0 title="中文配音" -disposition:s:a:0 default \
  -metadata:s:a:1 language=eng -metadata:s:a:1 title="原声"    -disposition:s:a:1 0 \
  -movflags +faststart output/dubbed.mp4
```

硬烧录版：`-vf "subtitles=subtitles/bilingual.srt:force_style='FontName=PingFang SC,FontSize=18'"`
（或直接用 `baocut export --video --lang zh` 烧录，样式更好）

**验收**：`ffprobe` 显示 2 音轨 + 2 字幕轨，音轨 0 带 `DISPOSITION:default=1`。

### 阶段 E · qc

| 检查项 | 阈值 | 级别 |
|---|---|---|
| BaoCut `finish-check` blocker | 0 | FAIL |
| 单元覆盖率 | > 95% | FAIL |
| 缺失 TTS 单元 | 0 | FAIL |
| 全片时长漂移 | < 0.5s | FAIL |
| 单元起始偏差 | < 100ms | FAIL |
| 变速 > 1.25 的单元占比 | < 15% WARN，> 30% FAIL | — |
| 中文语速 | 3.5–6.5 字/秒，越界 WARN | — |
| 连续静音 > 3s 且原声非静音 | WARN | — |
| 输出可解码 + 双音轨 + 双字幕轨 | ffprobe 验证 | FAIL |

**人耳验收（不可省）**：全片 25% / 50% / 75% 处各截 15 秒，导出
`quality/samples/sample_N.mp4`（中文音轨 + 双语字幕）。**没有这三个片段，不许报"完成"。**

## 5. 配置

- `.env`（不进 git）：`LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` / `MIMO_API_KEY`
  （ASR 用 BaoCut 本地 MLX，不再需要 AssemblyAI；保留 key 仅作备用）
- `config/default.yaml`：`baocut_cli` 路径、`cps`、`max_speed`、并发、音色
- `config/glossary.json`：术语表（注入 BaoCut 翻译 prompt）
- `config/voices.json`：说话人 → 音色映射

## 6. 技术栈与约束

- Python **3.11**（`uv venv --python 3.11`）
- 依赖：`edge-tts httpx pydantic typer rich pyyaml numpy soundfile`
  （不再需要 `yt-dlp` / `faster-whisper` / `assemblyai` —— BaoCut 已覆盖）
- 外部：`baocut-cli`（BaoCut ≥ 0.8.3）、`ffmpeg` / `ffprobe`
- **禁止**：引用 `../podcast-tool-local`、`../audiobook`、`../youtube-zh-dub` 的代码/venv/密钥文件（需要就复制进本目录）
- **禁止**：重写 BaoCut 已有能力（下载 / ASR / 分组 / 翻译 / 字幕导出）
- **禁止**：上传或发布到 YouTube；只产出本地文件
