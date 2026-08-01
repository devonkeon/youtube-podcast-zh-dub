# STATE

更新时间：2026-08-01　更新人：Claude（主线程，规划阶段）

## 当前基线

- 规格与计划已固定：RESEARCH.md（调研+选型）、SPEC.md（实现契约）、PLAN.md（7 份 Brief）
- 环境已实测：macOS 26.5.2、python3.11/3.13、uv、ffmpeg、yt-dlp、gh(devonkeon 已登录)、
  本地 agent grok/kimi/hermes/codex 均可用
- **代码量为 0**。没有跑过任何真实视频。

## 下一步（严格按顺序）

1. 复制密钥到本目录 `.env`（来源见 RESEARCH.md 第 3 节表格）
2. 执行 **Brief 1**（骨架 + doctor + ingest），产出 `EVIDENCE_1.md`
3. 依次 Brief 2 → 7，每个 Brief 完成后回来更新本文件

## 已知问题 / 待验证假设

- `target_chars = dur × 5.2` 是估算值，需在 Brief 4 用真实数据校准（可能落在 4.8–5.5）
- faster-whisper large-v3 在这台 Mac 上的转录速度未实测，可能需要切 AssemblyAI
- edge-tts 的并发限流阈值未实测，先按并发 4 试
- 说话人分离（多主持人音色映射）质量未验证，必要时首版退化为单音色
- BaoCut.app 已装但**不在主链路**，仅作可选字幕输入，暂不实现

## 决策记录

| 决策 | 理由 |
|---|---|
| 不 fork KrillinAI/VideoLingo，自建垂直管线 | 播客场景可砍掉唇形/画面重绘/多语种，自建更简单可控 |
| 翻译阶段就约束中文字数 | 现成工具靠高倍变速硬压，听感差；这是本项目产品差异点 |
| 默认 edge-tts | 免费无 key、中文播客音色好、原生支持 rate 调节 |
| 不以 BaoCut 为依赖 | 它无法提供词级时间戳，会拖垮断句质量 |
| 不复用同目录 `../youtube-zh-dub` | 其 STATE 自述从未真实运行过，链路选型（BaoCut + macOS say）不成立 |
| 输出 mp4 而非 mkv | QuickTime/IINA/VLC 都能切音轨；mov_text 字幕够用 |
