# 执行计划（PDCA）与 Agent 任务书

> 交接给 kimi / grok / hermes 用。**一次只做一个 Brief，做完提交并写 EVIDENCE，再做下一个。**

## 交接现状（Handoff）

- ✅ 已完成：调研（RESEARCH.md）、产品与技术规格（SPEC.md）、本机环境实测、目录与仓库建立
- ⬜ 未开始：全部代码
- 起点：本目录，`git` 已初始化，GitHub 仓库见 README
- **不需要读本目录以外的任何文件**（唯一例外：按 SPEC 6 节复制密钥到本目录 `.env`）

## 启动命令（给执行 agent 的第一条指令）

```bash
cd /Users/lx/Downloads/soft/tts/youtube-podcast-zh-dub
# 用本地 agent 执行，例如：
kimi   "读 SPEC.md 和 PLAN.md，执行 Brief 1，完成后写 EVIDENCE_1.md 并 git commit"
# 或
grok   "读 SPEC.md 和 PLAN.md，执行 Brief 1，完成后写 EVIDENCE_1.md 并 git commit"
```

## PDCA 循环定义

- **P**：每个 Brief 开工前，在 `_briefs/` 下确认 Goal / Scope / Forbidden / Done / Evidence
- **D**：只在 Allowed scope 内改文件
- **C**：跑 Brief 规定的验证命令，把**真实输出**贴进 `EVIDENCE_N.md`（不许写"应该可以"）
- **A**：更新 `STATE.md`（当前基线 / 下一步 / 已知问题），`git commit`，再进入下一个 Brief

**硬规则**：任何 Brief 的"完成"必须有可复现的命令 + 真实输出。没有证据 = 没完成。

---

## Brief 1 · 骨架 + doctor + ingest

- **Goal**：`zhdub doctor` 能体检环境；`zhdub run <url> --stage ingest` 能下载视频并抽 16k 音频
- **Allowed scope**：`pyproject.toml`、`src/zhdub/{__init__,cli,config,paths,ingest}.py`、`config/default.yaml`、`.env.example`
- **Forbidden**：写 ASR/翻译/TTS 逻辑；引用本目录外的代码
- **Done**：
  - `uv venv --python 3.11 && uv pip install -e .` 成功
  - `zhdub doctor` 输出 ffmpeg/yt-dlp/python 版本与密钥就位情况
  - 对一条 **3 分钟以内**的公开 YouTube 视频跑通 ingest，`meta.json` 有真实时长
- **Evidence**：两条命令的完整终端输出 + `ls -la runs/<id>/source/` + `ffprobe` 输出

## Brief 2 · ASR（词级时间戳）

- **Goal**：产出 `work/transcript.json`，词级时间戳
- **Allowed scope**：`src/zhdub/asr/`（`whisper_backend.py`、`assemblyai_backend.py`、`base.py`）、`tests/test_asr.py`
- **Forbidden**：改 ingest；把两个后端的输出格式做成不一致
- **Done**：两个后端都跑通同一条音频，输出**同一 schema**；SPEC 2 节验收项通过
- **Evidence**：`transcript.json` 前 20 个词、词数、最后一个词 end 与音频时长对比

## Brief 3 · 语义断句（segment）

- **Goal**：`work/units.json`
- **Allowed scope**：`src/zhdub/segment.py`、`tests/test_segment.py`
- **Forbidden**：调用 LLM（这一步是纯规则，必须可离线复现）
- **Done**：SPEC 3 节全部验收项通过；单测覆盖"超长句切分""短句合并""说话人切换"三种情况
- **Evidence**：单元总数、时长分布（min/median/max）、覆盖率百分比、`pytest` 输出

## Brief 4 · 翻译（带字数约束的两遍法）

- **Goal**：`work/translated.json` + `subtitles/{en,zh,bilingual}.srt`
- **Allowed scope**：`src/zhdub/translate.py`、`src/zhdub/srt.py`、`config/glossary.json`、`tests/`
- **Forbidden**：为了省 token 去掉上下文窗口或第二遍改写；把字数约束改成事后截断
- **Done**：SPEC 4 节验收项通过；`--dry-run` 能只出字幕
- **Evidence**：随机 10 个单元的 `原文 / 直译 / 口播改写 / target_chars / actual_chars` 对照表；
  超界比例统计；`bilingual.srt` 前 10 条

## Brief 5 · TTS + 时长对齐（fit）

- **Goal**：`audio/zh_dub.wav`，与原视频等长
- **Allowed scope**：`src/zhdub/tts/`、`src/zhdub/fit.py`、`config/voices.json`、`tests/`
- **Forbidden**：用 >1.30 的变速硬压；顺序拼接（必须按绝对时间轴贴入）
- **Done**：SPEC 5、6 节验收项通过；含"超长句回退重译"这条回路
- **Evidence**：时长漂移数值、变速比直方图、起始偏差最大值、`soxi`/`ffprobe` 输出

## Brief 6 · 封装 + QC + 人耳样片

- **Goal**：`output/dubbed.mp4` + `quality/qc_report.json` + 3 个样片
- **Allowed scope**：`src/zhdub/mux.py`、`src/zhdub/qc.py`、`tests/`
- **Forbidden**：QC 任一 FAIL 却仍报成功；跳过样片导出
- **Done**：SPEC 7、4 节验收项通过；`ffprobe` 证明双音轨双字幕轨且中文轨 default
- **Evidence**：`ffprobe -show_streams` 完整输出、`qc_report.json` 全文、3 个样片路径与大小

## Brief 7 · 端到端 + 文档（由主线程验收，不由子 agent 宣布完成）

- **Goal**：一条 **真实 20 分钟以上英文播客**全流程跑通
- **Done**：
  - 全程 `zhdub run <url>` 一条命令，无人工干预
  - QC 全绿
  - 3 个样片人耳听感合格（中文自然、跟得上画面、不赶字）
  - README 的安装/运行步骤在**干净 venv** 里被重跑验证过
- **Evidence**：总耗时与各阶段耗时表、QC 报告、样片、`ffprobe` 输出、README 复现记录

---

## 风险与预案（已知边界）

| 风险 | 触发信号 | 预案 |
|---|---|---|
| yt-dlp 被 YouTube 限流/403 | ingest 阶段报 403 | `yt-dlp -U`；改用 cookies-from-browser；或先手工下载走本地文件输入 |
| faster-whisper 在 Mac 上慢 | 20 分钟音频 > 15 分钟转录 | 切 `--asr assemblyai`（key 已有，云端分钟级） |
| 中文译文普遍过长 | 变速 > 1.25 的段落占比 > 30% | 调低 `target_chars` 系数至 4.8；加强 prompt 的"压缩"指令 |
| edge-tts 限流/断流 | 429 或空音频 | 降并发到 2；重试退避；备用 `--tts mimo` |
| 说话人分离不准 | 多人抢话段落音色乱跳 | 首版可退化为单一音色（`config/voices.json` 全映射到同一音色），不阻塞交付 |
| 背景音乐被中文盖住 | 人耳样片听感差 | 后续版本引入人声分离（UVR/Demucs）保留伴奏；首版接受 |

## 明确的非目标（首版不做）

唇形同步 · 视频画面重绘 · 人声分离保留 BGM · 网页 UI · 批量队列 · 上传发布 · 非中文目标语言
