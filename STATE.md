# STATE — 节点账本（接力棒）

> **这是唯一的交接入口。** 任何人（或任何 agent）接手时，只需读本文件 → 找到第一个未完成节点
> → 按"下一条命令"开工。完成一个节点就回来更新本文件并 commit。
>
> 最后更新：2026-08-01 21:40　更新人：Claude（主线程）

## 接手须知（30 秒读完）

- 项目定位：**只做配音层**。下载/转写/断句/翻译/字幕全部由 BaoCut 0.8.3 完成，我们做 TTS 和封装。
- 目前**代码 0 行**，前三个节点是调研和实测，结论都在 `docs/BAOCUT_NOTES.md`（贴的都是真实终端输出）。
- **别急着写代码。** 下一个节点 M3 是产品生死线，没过之前写代码是浪费。
- 铁律：凡是跑出来的贴原文，凡是推断的标 `【推断·未验证】`，没有证据不许报完成。

## 当前位置

**M0 / M1 / M2 已完成。下一个是 M3（说话人识别验证）——这是头号风险，优先级高于一切功能。**

**测试素材（我已开始下载，接手时先确认在不在）**：

```bash
ls -la /Users/lx/Downloads/hwhap_ep1_2speaker_clip.mp4
cat /tmp/ytdl.log        # 下载日志；没下完就重跑下面这条
```

没有的话重下（NASA 官方播客《Houston We Have a Podcast》第 1 集，**公有领域，双人访谈**，取第 5–8 分钟）：

```bash
yt-dlp --download-sections "*5:00-8:00" -f "bv*[ext=mp4]+ba[ext=m4a]/b" \
  --merge-output-format mp4 -o "/Users/lx/Downloads/hwhap_ep1_2speaker_clip.mp4" \
  "https://www.youtube.com/watch?v=eG3mQzYbwIY"
```

备选双人素材（同系列，全是公有领域，时长 43–63 分钟，需自行截段）：
`8A-6NoJbsFg` / `ZC4hpgNoumQ` / `mQbpPyV_kFw` / `QgLPHkebWU8`

**下一条命令**：

```bash
BC=/Applications/BaoCut.app/Contents/MacOS/baocut-cli
$BC --json auto /Users/lx/Downloads/hwhap_ep1_2speaker_clip.mp4 --lang zh --source-lang en --speakers 2
# 立即返回 {taskId, projectId}；然后用 task status 轮询（绝不要用 task wait，会阻塞超时）
```

## 节点表

| 节点 | 目标 | 状态 | 证据 |
|---|---|---|---|
| **M0** 环境与契约摸底 | baocut-cli 可用、模型就位、命令契约抄录 | ✅ 完成 | `BAOCUT_NOTES.md` M0 |
| **M1** 单人视频跑通 BaoCut | 3.5 分钟视频走完 `auto` + task 循环到 done | ✅ 完成 | `BAOCUT_NOTES.md` M1（9 次 submit 全过） |
| **M2** 结构化数据映射 | `subtitle list --json` 真实结构，定死 `groups.json` 字段 | ✅ 完成 | `BAOCUT_NOTES.md` M2 |
| **M3** ★**说话人识别验证** | 双人素材上，说话人归属准确率过门；否则整个产品不成立 | ⬜ **下一个** | 见下方"M3 怎么做" |
| **M4** 批量 TTS + 切割 | 整批合成再切开，音色不漂；切割精度实测 | ⬜ 未开始 | 词边界精度、音色一致性抽听 |
| **M5** 时长适配 | `audio/zh_dub.wav` 与原视频等长，漂移 < 0.5s | ⬜ 未开始 | 漂移值 + 变速直方图 |
| **M6** 封装 + QC + 样片 | `output/dubbed.mp4` 双音轨双字幕 + 3 段人耳样片 | ⬜ 未开始 | `ffprobe` + `qc_report.json` |
| **M7** 端到端长播客 | 20 分钟以上真实播客跑通并人耳合格 | ⬜ 未开始 | 耗时表 + 样片 |

> 节点顺序在 2026-08-01 用户 review 后**重排过**：原来的"配音字数约束"降级为 M5 的一部分，
> **说话人识别提到最前面**。理由：用户既有工作流里"张冠李戴"反复发生，
> 这一关过不了，工具就没有做的意义。功能做得再全也白搭。

## M3 怎么做（说话人识别验证）

**目标不是"跑出说话人"，是"知道哪些地方它可能错了"。**

1. 跑 `auto ... --speakers 2` 得到基线
2. `$BC speakers show <pid> --cues` 看逐句归属和文本证据
3. `$BC speakers reidentify <pid> --count 2,3 --review` —— 一次识别出多个提案，返回 proposalId
4. `$BC speakers proposals <pid> <a> <b>` —— 逐 cue 对比两个提案的**分歧**
5. `$BC speakers view <pid> --rerun -o /tmp/spk.png` —— 波形 + 双说话人条带 + **分歧/模糊标记 PNG**，用 Read 工具看图
6. 对每个分歧点：`$BC frames <pid> --at <秒>` 抓画面帧，**视觉确认谁在说**（视频播客能直接看出来）
7. `$BC speakers assign <pid> --speaker <sid> --cue <cueId>` 定点改正；确认无误的用 `--protect` 锁住
8. `$BC speakers propose-names <pid>` 从自我介绍推断人名（**不会自动应用，要人工核对**）

**过门标准（写进证据）**：

- 统计：总 cue 数 / 两提案分歧 cue 数 / 分歧占比
- **分歧占比 ≤ 5% 且全部逐一确认过 → 允许多音色**
- **> 5% 或未逐一确认 → 整片回落单一音色**，并在 QC 报告写明原因
- 宁可少用音色，不可张冠李戴

**证据要求**：分歧统计表、`view --rerun` 的 PNG、至少 3 个分歧点的 `frames` 视觉确认记录、
最终判定（多音色 or 降级）及理由。写进 `docs/BAOCUT_NOTES.md` 的 `## M3` 小节。

## 已验证事实（可直接依赖，不必复查）

- `baocut-cli` 在 `/Applications/BaoCut.app/Contents/MacOS/baocut-cli`，**不在 PATH**
- `baocut doctor` → 9 checks all healthy；本地 ASR = **qwen3-asr-0.6b (MLX 4bit)**；说话人模型已装
- yt-dlp 2026.06.09 / ffmpeg 8.1.2，BaoCut 直接调系统这两个
- BaoCut 项目数据在 `~/Library/Application Support/BaoCut/projects`，磁盘余量 22 GB
- `--json auto <url> --lang zh --source-lang en` 立即返回 `{projectId, taskId, state:"running"}`
- **`task wait` 会阻塞**（本地 ASR 慢），超过工具调用超时 → **agent 必须用 `task status` 轮询**
- `task status` 返回 `phase` / `progress` / `pendingCount` / `waitingOn` / `workerProcessAlive`
- 测试素材：NASA ScienceCasts（公有领域），`t8pNAuKnXEI` 214s / `1MDw2zrbAAs` 216s
- **task 循环协议**：`claim --worker <name>` → 读 `payloadFile` + `contractsDir/<contract>.md`
  → 写答案 JSON → `submit --call <id> --lease-id <id> --file <f> --next`（`--next` 直接带出下一个）
  → 被 rejected 时**用同一个 lease 改了重提**，不要重开
- **一条 3.5 分钟视频 = 9 次 submit**（polish×1 / repunct×1 / translate×1 / align×6），
  agent 驱动全程约 37 分钟。⚠️ **成本随时长线性增长，20 分钟播客要按小时估**
- `subtitle list --lang zh --json` 给出 `id/start/end/chars/text/source/speaker/speakerId/hidden/stale`，
  `start/end` 是**绝对秒**，`unit:"group"`
- **实测 cps = 5.44**（64 组，895 字 / 164.4s 语音），SPEC 的 5.2 估算成立
- **组间静音总计 41.9s**，允许溢出 60% 可把"需 >1.25 变速"的组从 28% 降到 12%
- translate payload **没有时长字段**，只有 `maxChars`（字幕显示速度预算，9 非空白字符/秒），
  **不可当配音字数预算**

## 未验证假设（动手前必须先验，别信推断）

1. translate payload 的行 id ↔ `subtitle list` 的 group id 是否一一对应 —— **M3 第一件事**
2. 原视频文件在 BaoCut 项目目录下的位置（mux 的底片）—— **M5 之前必须解决**
3. 病态组（`dur<0.7s 且 gap<0.2s`，实测存在 `g28.7` cps=32.3）的合并兜底方案 —— **M4**
4. edge-tts 并发限流阈值（先按 4 试）
5. BaoCut 能否用它自己配置的 LLM 跑完 polish/translate/align 而**不走 agent 循环**
   （`model list` 里有一行 `cline-pass/deepseek-v4-flash cloud · connected`）——
   若可以，M6 长播客的时间成本会大幅下降，**值得优先调查**

## 架构修正 v2（2026-08-01，用户 review 后）

| # | 修正 | 依据 |
|---|---|---|
| 1 | **TTS 必须整批合成后切开，禁止逐句合成** | 逐句会造成克隆音色漂移 + 句间韵律断裂；用户既往播客项目已反复踩到。沿用既有 multi-TTS 批量方案 |
| 2 | **新增「说话人确认门」，默认单一音色** | 用户既有工作流「张冠李戴」反复发生；配错音色比不分音色更糟。多音色需过分歧确认门，分歧 > 5% 未确认则自动降级 |
| 3 | **翻译改由 BaoCut GUI 用用户已配置的 API 自己跑**，CLI 只读数据 | `auto --help` 明确 CLI 自己不调 LLM，必须外部 agent 驱动；GUI 有用户配好的翻译 API。可省掉 agent 循环的巨大时间成本 |
| 4 | 撤回"translate 阶段拿不到时长"的说法 | 时间轴一直在 `subtitle list` 的 `start`/`end` 里，随时可查。原表述把一个中间步骤的局部现象说成了系统性问题 |

## ⚠️ 头号风险：多人节目的说话人识别

**用户判断：这个问题解决不好，工具就没有做的意义。** 认同。

- **当前测试素材 p1 是单人旁白（`speakers:1`），完全没有验证过这个问题**
- **下一个测试必须换成真实双人/多人播客**，先过说话人这一关，再谈其他
- BaoCut 的工具链比既有工作流强得多，可用来做置信度分级（详见 SPEC 阶段 A-bis）：
  `reidentify --count 2,3 --review` 出多提案 → `proposals diff` 找分歧 →
  `view --rerun` 出波形分歧标记 PNG → `frames --at <t>` 视觉确认 → `assign --cue` 定点改
- 思路：**一致的段落直接用，分歧的段落逐一确认，确认不了的退回单一音色** —— 不猜

## 已知质量问题

- **repunct 阶段会在紧凑词组中间插逗号**（实测："night, sky" / "closest, approach" /
  "one, another"），导致 align 阶段大量跨单元错位。M1 里的 align 修正大半都在收拾这个。
  影响：断句质量下降 → 配音断点不自然。缓解：align 阶段人工/agent 修正；
  或考虑 `terms fix` / 换更大的 ASR 模型（`qwen3-asr-1.7b`）减少源头错误。

## 决策记录

| 决策 | 理由 |
|---|---|
| **以 BaoCut 0.8.3 为前半链路，本项目只做配音层** | CLI 实测证明它有词级时间戳、语义分组、翻译、说话人、质检、双语导出，且 `--json` 可被 agent 驱动 |
| 不 fork KrillinAI/VideoLingo | 大而全 + GUI，播客垂直场景用不上多语种/唇形/画面重绘 |
| 字数约束落在"说得完"而非"看得下" | BaoCut 的 align 拟合字幕单行容量（CJK 16 字）；配音需要 `字数 ≈ 时长 × 5.2` |
| 默认 edge-tts | 免费无 key、中文播客音色好、原生支持 rate 调节 |
| 不复用同目录 `../youtube-zh-dub` | 其 STATE 自述从未真实运行过，链路选型（BaoCut+macOS say）不成立 |
| 输出 mp4 而非 mkv | QuickTime/IINA/VLC 都能切音轨；mov_text 字幕够用 |
| 骨架代码推迟到 M2 之后 | `groups.json` 字段全是推断，先跑真实数据再写，避免返工 |

## 更正记录

- 2026-08-01：初版曾断言"BaoCut 无词级时间戳、不能作主链路"。**该结论未经核实且错误**，
  被 `timing repair` / `subtitle retime` / `subtitle split --at wordId` 的 CLI 原始输出推翻。
  架构已改为以 BaoCut 为前半链路。教训：**下结论前先跑 `--help`。**

## 仓库

<https://github.com/devonkeon/youtube-podcast-zh-dub>　main　`7a54f1f`
