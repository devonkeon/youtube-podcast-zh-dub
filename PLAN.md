# 执行计划（PDCA）与 Agent 任务书

> ⚠️ **2026-08-01 起，节点顺序以 `STATE.md` 的节点表为准**（用户 review 后重排：
> 说话人识别提到最前，字数约束降级并入时长适配）。本文件的 Brief 保留作为
> **每个节点的执行模板**（Goal / Scope / Forbidden / Done / Evidence 的写法），
> 但**编号与顺序已不作数**。冲突时听 `STATE.md` 的。
>
> 交接给 kimi / grok / hermes。**一次只做一个节点，做完写证据并 commit，再做下一个。**

## 交接现状

- ✅ 调研与 BaoCut 能力实测（RESEARCH.md）、实现契约（SPEC.md）、仓库已建并推送
- ⬜ 代码 0 行
- **架构**：BaoCut 0.8.3 做前半链路，本项目只做配音层（TTS / 时长适配 / 拼接 / 封装 / 质检）
- 不需要读本目录以外的文件（例外：按 SPEC 5 节复制密钥到本目录 `.env`）

## 启动命令

```bash
cd /Users/lx/Downloads/soft/tts/youtube-podcast-zh-dub
kimi "读 SPEC.md 和 PLAN.md，执行 Brief 0，完成后写 EVIDENCE_0.md 并 git commit"
```

## PDCA 循环

- **P**：开工前确认本 Brief 的 Goal / Scope / Forbidden / Done / Evidence
- **D**：只改 Allowed scope 内的文件
- **C**：跑 Brief 规定的验证命令，把**真实终端输出**贴进 `EVIDENCE_N.md`（禁止写"应该可以"）
- **A**：更新 `STATE.md`，`git commit`，进入下一个 Brief

**硬规则**：没有可复现命令 + 真实输出 = 没完成。

---

## Brief 0 · 摸清 BaoCut 真实行为（先探路，别急着写代码）

- **Goal**：用一条 **3 分钟以内**的公开 YouTube 视频，**纯手工跑通** BaoCut 全流程，把每一步的真实输入输出记录下来
- **Allowed scope**：只新建 `docs/BAOCUT_NOTES.md` 与 `_probe/`，不写 `src/`
- **Forbidden**：写任何封装代码；跳过 task 循环直接猜 JSON 结构
- **Done**：
  - 装好 skill：`npx skills add JimLiu/baocut -g -a claude-code -y`，读 `skills/baocut/SKILL.md`
  - `baocut --json auto <url> --lang zh` → 拿到 `{taskId, projectId}`
  - 完整跑一遍 `task wait` → 写答案 → `task submit` 循环直到 `done`
  - `subtitle list <pid> --lang zh --json`、`export --srt --bilingual`、`audit`、`finish-check` 各跑一次
- **Evidence**：`docs/BAOCUT_NOTES.md` 里贴出
  ① `auto` 的 JSON ② 至少一个 `task wait` 的 prompt 文件原文与我们提交的答案
  ③ `subtitle list --lang zh --json` 的前 5 条**原样 JSON**（这是 groups.json 的映射依据）
  ④ `audit` / `finish-check` 输出 ⑤ 每个 group 如何拿到 start/end（写清字段来源）
- **为什么先做这个**：SPEC 里 `groups.json` 的字段是按 CLI help 推断的，**必须用真实 JSON 校正**。
  这一步的产出直接决定 Brief 2 能不能一次做对。

## Brief 1 · 骨架 + doctor + baocut 驱动层

- **Goal**：`zhdub doctor` 体检；`zhdub run <url> --stage baocut` 跑完 BaoCut 阶段并产出 `work/groups.json` + 三份 srt
- **Allowed scope**：`pyproject.toml`、`src/zhdub/{__init__,cli,config,paths,baocut}.py`、`config/default.yaml`、`.env.example`、`tests/test_baocut.py`
- **Forbidden**：写 TTS / fit / mux；重写 BaoCut 已有能力
- **Done**：`uv venv --python 3.11 && uv pip install -e .` 成功；`zhdub doctor` 报出 baocut-cli 版本、ffmpeg、密钥就位；对 Brief 0 那条视频跑通并通过 SPEC 4-A 验收
- **Evidence**：两条命令完整输出 + `groups.json` 前 5 条 + `wc -l` 三份 srt

## Brief 2 · 翻译 prompt 注入（配音字数约束）

- **Goal**：在 `task submit` 的答案里注入配音口语风格 + `dur × cps` 字数区间 + 术语表
- **Allowed scope**：`src/zhdub/translate_prompt.py`、`config/glossary.json`、`tests/`
- **Forbidden**：绕过 BaoCut 自己另起一套翻译；事后截断译文充数
- **Done**：同一条视频，注入前 / 注入后两版 `groups.json`，字数超界比例明显下降且 < 10%
- **Evidence**：随机 10 个 group 的 `原文 / 注入前译文 / 注入后译文 / target_chars / actual_chars` 对照表 + 两版超界比例统计

## Brief 3 · TTS + 时长适配

- **Goal**：`audio/zh_dub.wav`，与原视频等长
- **Allowed scope**：`src/zhdub/tts/`、`src/zhdub/fit.py`、`config/voices.json`、`tests/`
- **Forbidden**：变速 > 1.30；顺序拼接（必须按绝对时间轴贴入）；跳过"回退重写"回路
- **Done**：SPEC 4-B、4-C 全部验收项通过，含 `subtitle set` 压缩重写回路
- **Evidence**：时长漂移数值、变速比直方图、起始偏差最大值、`ffprobe` 输出

## Brief 4 · 封装 + QC + 人耳样片

- **Goal**：`output/dubbed.mp4` + `quality/qc_report.json` + 3 个样片
- **Allowed scope**：`src/zhdub/mux.py`、`src/zhdub/qc.py`、`tests/`
- **Forbidden**：QC 有 FAIL 却报成功；跳过样片导出
- **Done**：SPEC 4-D、4-E 验收项通过
- **Evidence**：`ffprobe -show_streams` 完整输出（须见 2 音轨 2 字幕轨、音轨 0 `default=1`）、`qc_report.json` 全文、3 个样片路径与大小

## Brief 5 · 端到端 + 文档（**由主线程验收，子 agent 不得自行宣布完成**）

- **Goal**：一条真实 **20 分钟以上**英文播客全流程跑通
- **Done**：`zhdub run <url>` 一条命令无人工干预；QC 全绿；3 个样片人耳合格（中文自然、跟得上画面、不赶字）；README 步骤在干净 venv 重跑验证
- **Evidence**：各阶段耗时表、QC 报告、3 个样片、`ffprobe` 输出、README 复现记录

---

## 风险与预案

| 风险 | 触发信号 | 预案 |
|---|---|---|
| BaoCut task 循环的 prompt 契约理解错 | `task submit` 报 rejected | 读 `contracts/<kind>.md` 原文；submit 会同步 lint 并给出 named problem，按提示改 |
| BaoCut 版本契约不符 | skill 运行退出码 3 | 按提示升级 App 或 skill；`baocut doctor` 自检 |
| `subtitle list` 拿不到 group 的绝对起止时间 | Brief 0 发现字段缺失 | 回落解析 `export --srt --lang zh` 的 cue 时间；Brief 0 必须验证清楚 |
| 中文译文普遍过长 | 变速 > 1.25 占比 > 30% | `cps` 调到 4.8；强化 prompt 压缩指令；实在不行提高 `max_speed` 到 1.35 并记 WARN |
| edge-tts 限流 | 429 或空音频 | 并发降到 2；退避重试；备用 `--tts mimo` |
| BaoCut 本地 MLX ASR 慢 | 20 分钟视频转录 > 15 分钟 | 接受（一次性成本）；或用 BaoCut 自带的模型选择 `baocut model list` 换更小模型 |
| 说话人识别不准 | 样片音色乱跳 | `baocut speakers reidentify/merge` 修正；不行则全映射到单一音色，不阻塞交付 |
| 背景音乐被中文盖住 | 人耳样片听感差 | 首版接受；后续版本再引入人声分离保留 BGM |

## 明确的非目标（首版不做）

唇形同步 · 画面重绘 · 人声分离保留 BGM · 网页 UI · 批量队列 · 上传发布 · 非中文目标语言 · 重写 BaoCut 已有能力
