## 文档导航

- **新人接手**：`ONBOARDING.md`（项目全解 + 执行细节 + 坑的全集）
- **节点账本**：`STATE.md`（当前进度、下一条命令）
- **Claude Code 交接**：`HANDOFF_CLAUDE.md`
- **实测证据库**：`docs/BAOCUT_NOTES.md` · **提速调研**：`docs/SPEED_RESEARCH.md`

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

## 设计要点

**本项目只做配音层。** BaoCut 0.8.3 已经把前半条链路做成了成熟产品——内置 yt-dlp 收 URL、
MLX 本地 ASR（词级时间戳）、语义分组、polish、LLM 翻译、说话人识别、质检验收门、双语字幕导出，
并且有 `baocut-cli --json` 供 agent 驱动。重写这半条只会更差更慢。

差异点在**字数约束的落点**：BaoCut 的 `align` 把译文拟合到*字幕单行容量*（CJK 默认 16 字），
那是"看得下"；配音要的是"**说得完**"——目标 `字数 ≈ 时长 × 5.2`。我们在 BaoCut 的 task 循环里
注入配音字数区间，把时长对齐提前到翻译阶段；剩余超长组再定点压缩重写并重合成。
只有仍超长才动变速（上限 1.30）。

首版不做唇形同步、不做人声分离——播客场景收益低、成本高。

## 技术路线

```
BaoCut：URL → 词级 ASR → 语义分组 → polish → 翻译(注入配音字数约束) → 双语 SRT + audit
  ↓ baocut --json subtitle list / export
本项目：edge-tts 合成 → 时长适配(变速/补白/回退重写) → 绝对时间轴拼接
        → ffmpeg 双音轨双字幕封装 → QC + 3 段人耳样片
```

Python 3.11 · BaoCut ≥ 0.8.3 · ffmpeg · edge-tts（可选 MiMo 声音克隆）

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
