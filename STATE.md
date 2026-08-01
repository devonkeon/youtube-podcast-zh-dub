# STATE — 节点账本（接力棒）

> **这是唯一的交接入口。** 任何人（或任何 agent）接手时，只需读本文件 → 找到第一个未完成节点
> → 按"下一条命令"开工。完成一个节点就回来更新本文件并 commit。
>
> 最后更新：2026-08-01 21:05　更新人：Claude（主线程）

## 当前位置

**M0 / M1 / M2 已完成。下一个是 M3。**

已有一个跑通的 BaoCut 项目可直接复用，**不必重新转录**：
`projectId=p1`（NASA ScienceCasts，214s，64 个中文 group，已 done）

**下一条命令**：

```bash
BC=/Applications/BaoCut.app/Contents/MacOS/baocut-cli
# M3 第一步：验证 translate payload 的行 id 与 subtitle list 的 group id 是否对得上
$BC --json subtitle list p1 --lang zh --limit 500 > /tmp/p1_zh.json
head -c 2000 "/Users/lx/Library/Application Support/BaoCut/projects/p1/agent/t-msac81kt/payloads/c0003.txt"
```

## 节点表

| 节点 | 目标 | 状态 | 证据 |
|---|---|---|---|
| **M0** 环境与契约摸底 | 确认 baocut-cli 可用、模型就位、命令契约抄录 | ✅ 完成 | `docs/BAOCUT_NOTES.md` M0 |
| **M1** 短视频跑通 BaoCut | 一条 3.5 分钟公开视频走完 `auto` + task 循环到 done | ✅ 完成 | `BAOCUT_NOTES.md` M1（9 次 submit 全过） |
| **M2** 结构化数据映射 | 拿到 `subtitle list --json` 真实结构，定死 `groups.json` 字段来源 | ✅ 完成 | `BAOCUT_NOTES.md` M2 |
| **M3** 配音字数约束 | 验证 id 映射；注入配音 prompt；超界比例 < 10% | ⬜ 下一个 | 对照表 + 前后统计 |
| **M4** TTS + 时长适配 | `audio/zh_dub.wav` 与原视频等长，漂移 < 0.5s | ⬜ 未开始 | 漂移值 + 变速直方图 |
| **M5** 封装 + QC + 样片 | `output/dubbed.mp4` 双音轨双字幕 + 3 段人耳样片 | ⬜ 未开始 | `ffprobe` + `qc_report.json` |
| **M6** 端到端长播客 | 20 分钟以上真实播客一条命令跑通并人耳合格 | ⬜ 未开始 | 耗时表 + 样片 |

节点与 PLAN.md 的 Brief 对应：M0+M1+M2 = Brief 0，M3 = Brief 2，M4 = Brief 3，M5 = Brief 4，M6 = Brief 5。
（Brief 1 骨架代码在 M2 定死字段后再写，避免返工。）

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
