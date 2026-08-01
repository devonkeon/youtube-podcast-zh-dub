# STATE

更新时间：2026-08-01　更新人：Claude（主线程，规划阶段）

## 当前基线

- 规格与计划已固定：RESEARCH.md（调研+选型）、SPEC.md（实现契约）、PLAN.md（7 份 Brief）
- 环境已实测：macOS 26.5.2、python3.11/3.13、uv、ffmpeg、yt-dlp、gh(devonkeon 已登录)、
  本地 agent grok/kimi/hermes/codex 均可用
- **代码量为 0**。没有跑过任何真实视频。

- 仓库已建并推送：<https://github.com/devonkeon/youtube-podcast-zh-dub>（main，首个 commit `bcb5a7c`）

## 下一步（严格按顺序）

1. 复制密钥到本目录 `.env`（来源见 RESEARCH.md 第 3 节表格）
2. 执行 **Brief 1**（骨架 + doctor + ingest），产出 `EVIDENCE_1.md`
3. 依次 Brief 2 → 7，每个 Brief 完成后回来更新本文件

## 已知问题 / 待验证假设

- **SPEC 里 `groups.json` 的字段是按 CLI `--help` 推断的**，必须用 Brief 0 的真实 JSON 校正
- BaoCut `task wait / submit` 的 prompt 契约未实操过，Brief 0 必须走完一遍完整循环
- group 的绝对起止时间从哪个字段取，未确认（回落方案：解析导出的 SRT cue 时间）
- `target_chars = dur × 5.2` 是估算值，需在 Brief 2 用真实数据校准（可能落在 4.8–5.5）
- BaoCut 本地 MLX ASR 在这台 Mac 上的速度未实测
- edge-tts 的并发限流阈值未实测，先按并发 4 试
- 说话人识别质量未验证，必要时首版退化为单音色

## 决策记录

| 决策 | 理由 |
|---|---|
| **以 BaoCut 0.8.3 为前半链路，本项目只做配音层** | CLI 实测证明它有词级时间戳、语义分组、翻译、说话人、质检、双语导出，且 `--json` 可被 agent 驱动；重写只会更差更慢 |
| 不 fork KrillinAI/VideoLingo | 大而全 + GUI，播客垂直场景用不上多语种/唇形/画面重绘 |
| 字数约束落在"说得完"而非"看得下" | BaoCut 的 align 拟合的是字幕单行容量（CJK 16 字），配音需要 `字数 ≈ 时长 × 5.2` |
| 默认 edge-tts | 免费无 key、中文播客音色好、原生支持 rate 调节 |
| 不复用同目录 `../youtube-zh-dub` | 其 STATE 自述从未真实运行过，链路选型（BaoCut + macOS say）不成立 |
| 输出 mp4 而非 mkv | QuickTime/IINA/VLC 都能切音轨；mov_text 字幕够用 |
