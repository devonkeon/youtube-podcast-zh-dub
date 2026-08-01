# STATE — 节点账本（接力棒）

> **这是唯一的交接入口。** 任何人（或任何 agent）接手时，只需读本文件 → 找到第一个未完成节点
> → 按"下一条命令"开工。完成一个节点就回来更新本文件并 commit。
>
> 最后更新：2026-08-02 00:40　更新人：Kimi（M3 验证 + M4–M6 配音层 + LLM worker-bot）

## ★ M3 最终结果（2026-08-02，双人素材 p2）—— ✅ 过门，允许多音色

首轮数据（2026-08-01 Claude）：68 groups · s1:37/s2:31 · 4 轮次 · 0 孤立单组 · 0 超短轮次 · cps 4.92。
**Kimi 接手后先独立复核了首轮数据（属实，两处小出入见文末"更正记录"），再完成剩余三项验证**，全部证据在 `docs/BAOCUT_NOTES.md` 的 `## M3` 小节：

1. **交叉验证 ✅**：`reidentify --count 2,3 --review` 出两个提案，diff 结果 **0/101 cue 分歧（0%）**；
   count=3 也只找到 2 个声纹。`view --rerun` 双条带图无分歧/模糊标记（`docs/assets/p2_spk.png`）。
2. **视觉确认 ⚠️→✅（方法修正）**：该素材是**固定分屏**（两人同框，镜头不随说话人切换）+ ISS B-roll，
   静帧**无法**直接看出谁在说——原 M3 预案第 6 步的假设在此类素材上失效。
   改用替代锚点：00:22 帧人名字幕条确认 **s1 = Dan Huot（NASA 发言人/嘉宾）**，s2 = Gary Jordan（主持人），已 rename。
3. **跨说话人句子 ✅**：`"…comes to down to— ⏹ Gravity…"` 在 `subtitle list` 里就是两个 group
   （g8.42=s2 / wmsah7v2h-52=s1，中文译文也在边界断开）。**配音按 group 分配音色即可，无需词级二次切分。**
4. **额外独立证据**：ASR 阶段 polish payload 的 3 处 ⏹ 切换标记与声纹聚类的 3 个轮次边界**逐一对齐**。

**判定：分歧 0% ≤ 5%，三边界均有独立证据 → 多音色过门。M4 音色表：s1=Dan Huot（嘉宾）/ s2=Gary Jordan（主持人）。**

## M3 首轮结果存档（2026-08-01，双人素材 p2）—— 以下为首轮原始记录

素材：`hwhap_ep1_2speaker_clip.mp4`（NASA 双人访谈 180s）→ `projectId=p2`，ASR 用了 `qwen3-asr-1.7b`。
BaoCut `auto ... --speakers 2` + agent task 循环（9 次 submit，零拒绝）已跑完，`status:done`。

**说话人识别实测统计**（`subtitle list p2 --lang zh` 的 `speakerId` 字段，真实数据）：

```
groups 68 · speakers {s1: 37, s2: 31} · turns 4
单组轮次（张冠李戴的典型特征）  0 / 4
短于 1.5s 的轮次                0
轮次时长 min/med/max            6.65 / 46.70 / 70.97 s
语音 171.0s · 中文 841 字 · cps 4.92
```

**判读**：访谈类节目是"长问 + 长答"结构，识别结果就该是少数几个长轮次。
实测 4 个轮次、无孤立单组、无超短轮次 —— **这正是干净结果的特征**。
既往工作流里"张冠李戴"的典型征兆是说话人频繁来回跳（大量单组轮次、大量 <1.5s 轮次），
**本次一个都没有**。

**但这不等于验收通过，还差三件事**（下一位接手的人从这里继续）：

1. **没做交叉验证**：`speakers reidentify p2 --count 2,3 --review` + `proposals diff` 还没跑，
   没有第二个提案来对比分歧
2. **没做视觉确认**：`speakers view p2 --rerun -o /tmp/p2_spk.png` 和
   `frames p2 --at <轮次边界秒数>` 都没跑，4 个轮次边界应逐一看画面确认
3. **已知存在跨说话人的句子**：子 agent 在 polish 原文里发现
   `"...it all comes to down to ⏹ gravity, ..."` —— 说话人切换标记落在短语中间，
   一句话被两个人接力说完。**这种句子配音时必须切开分给两个音色，否则一定错**。
   `subtitle list` 的 group 粒度能否表达这种切分，**未验证**

**只有 4 个轮次边界，人工确认成本极低（看 4 张画面帧），建议直接做完再往下走。**

**另一个副产品**：p2 的 cps = 4.92，p1 是 5.44，两次实测都落在 4.9–5.5，
`cps = 5.2` 这个中值站得住，可以定稿。

## 接手须知（30 秒读完）

- 项目定位：**只做配音层**。下载/转写/断句/翻译/字幕全部由 BaoCut 0.8.3 完成，我们做 TTS 和封装。
- 目前**代码 0 行**，前三个节点是调研和实测，结论都在 `docs/BAOCUT_NOTES.md`（贴的都是真实终端输出）。
- **M3 已过门（见顶部），下一个节点是 M4（批量 TTS + 切割）。** M3 之前写代码是浪费；现在可以开始搭配音层骨架了。
- 铁律：凡是跑出来的贴原文，凡是推断的标 `【推断·未验证】`，没有证据不许报完成。

## 当前位置

**M0–M6 已完成（M6 待用户人耳验收样片）。M7（端到端长播客）进行中。** 头号风险（说话人识别）已解除；时间成本风险由 LLM worker-bot 解除（p4 探针：25s 素材 LLM 阶段约 3 分钟全自动，同类规模人工循环要 37 分钟）。

**测试素材已就位 ✅**（2026-08-01 22:13 实测）：

```
/Users/lx/Downloads/hwhap_ep1_2speaker_clip.mp4
13,271,779 bytes · 180.03s · h264 + aac
NASA《Houston We Have a Podcast》Ep.1 第 5–8 分钟 · 公有领域 · 双人访谈
```

文件丢了就重下：

```bash
yt-dlp --download-sections "*5:00-8:00" -f "bv*[ext=mp4]+ba[ext=m4a]/b" \
  --merge-output-format mp4 -o "/Users/lx/Downloads/hwhap_ep1_2speaker_clip.mp4" \
  "https://www.youtube.com/watch?v=eG3mQzYbwIY"
```

备选双人素材（同系列，全是公有领域，时长 43–63 分钟，需自行截段）：
`8A-6NoJbsFg` / `ZC4hpgNoumQ` / `mQbpPyV_kFw` / `QgLPHkebWU8`

**下一条命令**（M7：20 分钟端到端，流程已自动化）：

```bash
# 1. 下载长素材 → 2. auto 发起 → 3. worker-bot 驱动 LLM 阶段（无需人工）
set -a; source ~/Downloads/soft/podcast-workbench/.env; set +a   # 提供 OPENCODE_GO_API_KEY
BC=/Applications/BaoCut.app/Contents/MacOS/baocut-cli
$BC --json auto <media> --lang zh --source-lang en                # 返回 taskId/projectId
python3 worker/llm_worker.py <taskId> --worker llm-bot --log /tmp/bot.jsonl
# 4. 说话人确认门（M3 流程）→ 5. 配音 + 封装
~/.browser-use-env/bin/python dub/build_dub.py <pid> \
    --voice s1=zh-CN-YunjianNeural --voice s2=zh-CN-YunxiNeural --conc 6
# 6. mux + QC：见 docs/BAOCUT_NOTES.md M4–M6 第 4 节
```

已有两个跑通的 BaoCut 项目可直接复用，**不必重新转录**：
`p1` 单人 NASA ScienceCasts 214s / **`p2` 双人 NASA 播客 180s（当前主力）**

## 节点表

| 节点 | 目标 | 状态 | 证据 |
|---|---|---|---|
| **M0** 环境与契约摸底 | baocut-cli 可用、模型就位、命令契约抄录 | ✅ 完成 | `BAOCUT_NOTES.md` M0 |
| **M1** 单人视频跑通 BaoCut | 3.5 分钟视频走完 `auto` + task 循环到 done | ✅ 完成 | `BAOCUT_NOTES.md` M1（9 次 submit 全过） |
| **M2** 结构化数据映射 | `subtitle list --json` 真实结构，定死 `groups.json` 字段 | ✅ 完成 | `BAOCUT_NOTES.md` M2 |
| **M3** ★**说话人识别验证** | 双人素材上，说话人归属准确率过门；否则整个产品不成立 | ✅ **完成·过门（多音色）** | `BAOCUT_NOTES.md` ## M3：双提案 diff 0/101 cue、⏹ 标记逐边界对齐、人名字幕锚点 |
| **M4** 批量 TTS + 切割 | 整批合成再切开，音色不漂；切割精度实测 | ✅ 完成（方案实测后改为逐组合成，见架构修正 v3） | `BAOCUT_NOTES.md` M4–M6：conc8 零失败、变速直方图 51/66 零变速 |
| **M5** 时长适配 | `audio/zh_dub.wav` 与原视频等长，漂移 < 0.5s | ✅ 完成 | 结构性零漂移；rate+15%+去静音后仅 1 单元 >1.5x |
| **M6** 封装 + QC + 样片 | `output/dubbed.mp4` 双音轨双字幕 + 3 段人耳样片 | ✅ 完成（待人耳验收） | `output/p2_dubbed.mp4` + `qc_report.json` + 3 样片 |
| **M7** 端到端长播客 | 20 分钟以上真实播客跑通并人耳合格 | 🔵 进行中 | LLM worker-bot 已验证（p4 探针 3 分钟）；20 分钟端到端进行中 |

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
6. 对每个分歧点：`$BC frames <pid> --at <秒>` 抓画面帧，**视觉确认谁在说**。
   ⚠️ **2026-08-02 实测修正：此步只在"镜头随说话人切换"的素材上有效。**
   固定分屏（两人同框）/ B-roll 素材静帧看不出谁在说（p2 就是这种）。
   此类素材改用组合证据：**人名字幕条锚点**（下三分之一字幕在谁说话时打出）+
   **ASR 阶段 ⏹ 切换标记与轮次边界逐一对齐** + 双提案 diff。三者都一致才可视为"逐一确认过"。
   （`speakers rename` 注意：位置参数形式 `rename p2 s1 "Name"` 返回 rc=0 但不生效，
   必须用批量形式 `rename p2 s1="Name" s2="Name"`。）
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
- **cps 定稿 5.2**：p1 实测 5.44、p2 实测 4.92，两次都落在 4.9–5.5
- polish payload 里有 ASR 阶段的 **⏹ 说话人切换标记**，与声纹聚类边界相互独立，可做交叉证据（p2 实测 3 处全对齐）
- **跨说话人接力句在 `subtitle list` 里会被切成两个 group**（各带 speakerId），group 粒度足以表达双人接力，配音按 group 分音色即可（p2 实测：g8.42=s2 / wmsah7v2h-52=s1）

## 未验证假设（动手前必须先验，别信推断）

1. translate payload 的行 id ↔ `subtitle list` 的 group id 是否一一对应 —— **M3 第一件事**
2. 原视频文件在 BaoCut 项目目录下的位置（mux 的底片）—— **M5 之前必须解决**
3. 病态组（`dur<0.7s 且 gap<0.2s`，实测存在 `g28.7` cps=32.3）的合并兜底方案 —— **M4**
4. edge-tts 并发限流阈值（先按 4 试）
5. ~~BaoCut 能否用它自己配置的 LLM 跑完 polish/translate/align~~ —— **已验证（2026-08-02）**：
   GUI 能自跑（p101：102 分钟视频 app 自跑翻译约 40 分钟，比 agent 循环快约 10×），
   但**只在 GUI 手动发起时**，不接 CLI 任务队列（探针实验 p3/t-msajktfg 证实）。
   推荐混合链路：CLI `transcribe` → GUI 点一次翻译 → CLI 读数据。详见 `BAOCUT_NOTES.md` "LLM 自跑路径调查"。
   残留【推断·未验证】：GUI 对 CLI 创建的项目点翻译是否同样走 app 自跑。

## 架构修正 v2（2026-08-01，用户 review 后）

| # | 修正 | 依据 |
|---|---|---|
| 1 | **TTS 必须整批合成后切开，禁止逐句合成** | 逐句会造成克隆音色漂移 + 句间韵律断裂；用户既往播客项目已反复踩到。沿用既有 multi-TTS 批量方案 |
| 2 | **新增「说话人确认门」，默认单一音色** | 用户既有工作流「张冠李戴」反复发生；配错音色比不分音色更糟。多音色需过分歧确认门，分歧 > 5% 未确认则自动降级 |
| 3 | **翻译优先走 BaoCut GUI 自跑（用户已配置的 gemini-3.5-flash），CLI 只读数据** | 2026-08-02 验证：app 自跑比 agent 循环快约 10×（102 分钟素材 40 分钟），但 GUI 不接 CLI 任务队列，需在 GUI 手动发起；agent 循环留作兜底 |
| 4 | 撤回"translate 阶段拿不到时长"的说法 | 时间轴一直在 `subtitle list` 的 `start`/`end` 里，随时可查。原表述把一个中间步骤的局部现象说成了系统性问题 |

## ⚠️ 头号风险：多人节目的说话人识别 —— ✅ 已解除（2026-08-02，M3 过门）

**用户判断：这个问题解决不好，工具就没有做的意义。** 认同。

- p2（双人访谈）上：基线识别 / 双提案交叉验证（0/101 cue 分歧）/ ASR ⏹ 标记（3 处全对齐）/
  人名字幕锚点，**四方证据一致**，判定允许多音色。证据：`BAOCUT_NOTES.md` ## M3。
- 保留的残余风险【推断·未验证】：p2 是音质干净的录音室访谈；**多人圆桌（3+ 人）、
  远场收音、频繁抢话**的素材还没测过。M7 端到端之前应补一个 3 人素材的确认门测试。

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
- 2026-08-02（Kimi 复核 M3 首轮记录时发现的两处小出入，首轮其余数据全部属实）：
  1. 首轮记"轮次时长 min/med/max 6.65/46.70/70.97s"，按 `subtitle list`（zh/en 一致）重算为
     **6.65 / 47.35 / 76.26s**（4 个轮次：6.65 / 32.66 / 62.04 / 76.26）。结论不受影响。
  2. 首轮说"4 个轮次边界"，实际是 **4 个轮次、3 个边界**（7.34 / 40.69 / 103.11s）。
- 2026-08-02：M3 预案"抓画面帧视觉确认谁在说"在固定分屏素材上失效（p2 实测），
  已改用「人名字幕锚点 + ⏹ 标记对齐 + 双提案 diff」组合，详见 M3 步骤第 6 步的修正。
- 2026-08-02：`speakers rename p2 s1 "Name"` 位置参数形式假成功（rc=0 但不生效），
  必须用 `s1="Name"` 批量形式。

## 仓库

<https://github.com/devonkeon/youtube-podcast-zh-dub>　main
