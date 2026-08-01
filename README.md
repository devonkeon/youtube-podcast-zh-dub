# youtube-podcast-zh-dub

把 YouTube 英文播客变成**中文口播版**：默认播放即中文配音，可一键切回英文原声，附中英双语字幕。

```bash
zhdub run 'https://youtu.be/VIDEO_ID'
# → runs/<id>/output/dubbed.mp4   中文音轨(default) + 英文原声 + 中英字幕轨
```

## 现在的状态

**规划完成，代码未开始。** 本仓库当前是一份可直接交给 AI 编码 agent 执行的完整规格。

| 文件 | 作用 |
|---|---|
| [RESEARCH.md](RESEARCH.md) | 近 2 年现成方案调研、选型判断、本机环境实测、可用密钥清单 |
| [SPEC.md](SPEC.md) | 实现契约：CLI、目录结构、7 个阶段的算法与参数、QC 质量门 |
| [PLAN.md](PLAN.md) | PDCA 执行计划 + 7 份可独立验收的 Agent 任务书 + 风险预案 |
| [STATE.md](STATE.md) | 当前基线 / 下一步 / 已知问题（每个 Brief 完成后更新） |

## 设计要点（为什么不直接用现成工具）

现成工具（KrillinAI、VideoLingo、pyVideoTrans）都是"全语种 + GUI"的大而全方案，
在**英文播客 → 中文**这一条垂直路径上做了不必要的妥协：翻译不控字数，靠 1.5x 以上
变速硬压回原时长，听感发飘。

本项目的差异点是**把时长对齐提前到翻译阶段**：按每段原时长算出中文目标字数
（≈ 5.2 字/秒），让 LLM 在这个字数区间内写口播稿；只有仍然超长时才用变速（上限 1.30），
再超长就退回去让 LLM 压缩重写。同时砍掉播客场景用不上的唇形同步与画面重绘。

## 技术路线

```
yt-dlp 下载 → faster-whisper 词级时间戳 → 规则语义断句 →
LLM 两遍翻译(带上下文+字数约束) → edge-tts 中文合成 →
时长对齐(变速/补白/绝对时间轴贴入) → ffmpeg 双音轨双字幕封装 → QC + 人耳样片
```

Python 3.11 · ffmpeg · yt-dlp · faster-whisper / AssemblyAI · edge-tts（可选 MiMo 声音克隆）

## 交付标准

技术跑通不算完成。必须产出 3 段人耳验收片段（全片 25%/50%/75% 处各 15 秒），
中文自然、跟得上画面、不赶字，才算完成。详见 SPEC 第 4 节。

## 仓库

<https://github.com/devonkeon/youtube-podcast-zh-dub>

## 开始执行

```bash
cd /Users/lx/Downloads/soft/tts/youtube-podcast-zh-dub

```bash
kimi "读 SPEC.md 和 PLAN.md，执行 Brief 1，完成后写 EVIDENCE_1.md 并 git commit"
```

MIT License
