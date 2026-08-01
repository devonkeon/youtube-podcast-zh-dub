# ONBOARDING — youtube-podcast-zh-dub 项目全解（写给第一次接触的人）

> 一句话：**把英文 YouTube 播客变成中文配音视频**。前半链路（下载/转写/断句/翻译/字幕/说话人）全部交给本
> 地应用 BaoCut，本仓库只做**配音层**（TTS 合成、时长适配、封装 QC）和**自动化**（LLM worker-bot）。
> 当前状态：62 分钟 4 人播客端到端 52 分钟跑完，已出 3 条成片。接手先读 `STATE.md`。

## 1. 为什么是这个架构

- BaoCut（macOS GUI 应用，带 CLI）实测具备：词级时间戳、语义分组、声纹说话人、agent 可驱动的任务队列、
  双语字幕导出。重复造这些没有意义，所以项目定位是"BaoCut 之上的配音层"。
- **产品的生死线是"张冠李戴"**：多人节目说话人归属错了，配音就配错人。所以有一条铁规矩——
  **说话人确认门**：每个新项目必须过 `reidentify` 交叉验证，分歧 >5% 且未逐一确认就**整片降级单音色**，
  宁可不分音色也不配错。2/3/4 人场景实测均过门（证据见 BAOCUT_NOTES.md 的 M3/M7 小节）。

## 2. 流水线全貌（一条命令）

```bash
cd ~/Downloads/soft/tts/youtube-podcast-zh-dub
set -a; source ~/Downloads/soft/podcast-workbench/.env; set +a   # 提供各家 API key
./run_dub.sh "https://youtu.be/VIDEO_ID" --title "标题"
# 产物：output/<pid>_dubbed.mp4（中配默认轨 + 原声 + 中英双字幕）
```

`run_dub.sh` 内部六步（也可分步手动执行，命令在 STATE.md"下一条命令"）：

| 步 | 做什么 | 62 分钟素材实测耗时 |
|---|---|---|
| 1 | `baocut auto <url>`：yt-dlp 下载 → 本地 ASR 转录（qwen3-asr-0.6b）→ 声纹说话人 | 11 min |
| 2 | 等转录完成（轮询 `task status`） | — |
| 3 | `worker/llm_worker.py` 驱动 polish/repunct/translate/align | ~25 min，~$0.06/20min |
| 4 | 说话人确认门（多提案 diff；>5% 降级单音色） | ~5 min |
| 5 | `dub/build_dub.py` 逐组合成 → 时长适配 → 拼装音轨 | ~13 min（edge-tts） |
| 6 | ffmpeg 封装 + QC 报告 + 样片 | <1 min |

## 3. 环境依赖（缺一不可）

- **BaoCut.app**（CLI 在 `/Applications/BaoCut.app/Contents/MacOS/baocut-cli`，不在 PATH）
- **ffmpeg + yt-dlp**（BaoCut 和我们共用）
- **LLM key**：`~/Downloads/soft/podcast-workbench/.env` 里的 `OPENCODE_GO_API_KEY`
  （opencode 网关的 deepseek-v4-flash；注意 `~/.hermes/.env` 里那把已欠费）
- **TTS key（按需）**：同文件的 `MOSS_API_KEY`（无限用）/ `XIAOMI_API_KEY`（mimo，配额共享会 429）
- **edge-tts**：`~/.browser-use-env/bin/python`（跑 `dub/build_dub.py` 必须用这个解释器）
- **EdgeSpeak.app**（可选，本地 TTS 兜底；gateway key 问 lx 要）

## 4. 配音层设计（dub/build_dub.py）

**TTS 引擎链**（`--voice` 规格，按序降级，429/401/403 熔断）：

```
s1=mimo:/ref.wav+moss:/ref.wav+es:user:<uuid>,zh-CN-YunjianNeural
 └ mimo 克隆(1.9s/句,有配额) → moss 克隆(~40s/句,无限用) → EdgeSpeak 本地克隆(离线,慢) → edge-tts 通用音色
```

- **克隆 ref 音频**：直接从原片按说话人切 10-15s 干净独白 + 对应逐字稿（`.txt` 同名）。
- **时长适配**：`rate+15%（仅 edge-tts）→ 首尾去静音（-45dB，每条省 ~1.15s）→ 槽位 = 句长 + 0.6×后间隙
  → 超出部分 atempo 强制贴合`。每个单元锚定绝对时间轴，**全局零漂移**。
- **病态组**：`dur<0.7s 且 gap<0.2s` 并入下一个同说话人组。
- **断点续跑**：每条产物按 `uid.引擎.扩展名` 缓存，重跑只补缺的。
- 音色经验值：edge-tts 自然语速 3.9 字/s（要 +15%）；克隆引擎 4.86 字/s；中文预算 cps=5.2
  （访谈 4.9-5.5，直播问答 5.6，财经对谈 4.4）。

## 5. 坑的全集（每一条都是实测踩出来的）

### BaoCut 侧
1. `subtitle list` **默认 `--limit 200`，长项目静默截断**（p5 后半没配音的事故）→ 永远显式传大 limit。
2. `task claim` 对同 worker 重复 claim 返回 `already-claimed`（无 payload 路径）→ release 后重 claim。
3. `speakers rename <pid> <sid> "名字"` 位置参数形式**假成功（rc=0 不生效）**→ 用 `s1="名字"` 批量形式。
4. `speakers propose-names` 会给出 "guessing now" 这种噪声 → 人名必须内容核实。
5. 说话人确认门的视觉确认：**固定分屏/双人同框素材抓静帧看不出谁在说** → 用人名字幕锚点 +
   ASR ⏹ 标记对齐 + 双提案 diff。3+ 人场景 count 给少了会把两个人并掉（p5 实测 277 cue 大合并，
   被内容结构否决）→ **人数宁多勿少 + 内容校验**。
6. BaoCut 项目目录**不存源视频**（只有 audio16k.pcm）→ mux 底片用原始下载文件。
7. `task wait` 会阻塞 → 一律 `task status` 轮询。

### LLM worker-bot 侧
8. opencode 网关在 Cloudflare 后，**urllib 默认 UA 被 1010 拦截** → 带浏览器 UA。
9. deepseek-v4-flash 默认开推理，复杂 contract 会把全部 token 烧在 `reasoning_content`（content 为空）
   → 请求带 `"thinking":{"type":"disabled"}`。
10. align 的 lint 拒绝率高（20 字硬上限、cut id 安全集）→ bot 的 problems 反馈重试会收敛，
    但长任务要 `--max-rounds 400+`（align 队列会随批次落地补充新 call）。

### TTS 侧
11. moss 新旧 API 完全不同：旧 `MOSS-TTS` multipart 已弃用；新 `moss-tts` + `version=flash-20260626`
    是 **JSON body**（ref_audio 传 data-uri base64）。`studio.mosi.cn` 是另一套账号。
12. mimo 的 TTS 端点是 `api.xiaomimimo.com/v1`，**不是** env 里常见的 `…/anthropic`（那是 chat 用的）。
    同账号批量任务会把配额挤到 429 → 熔断器自动降级。
13. 克隆引擎会把 `…` 幻生成超长停顿（4 字文本出 10 秒静默）→ 合成前 `…→，`，
    外加时长护栏 `chars×0.35s`（**只对克隆引擎**，edge-tts 短句天然 1.8s 会误杀）。
14. EdgeSpeak gateway：`response_format:"wav"` 必须带，`language` 字段会 400。本地推理 RTF≈3.5，
    只适合做兜底，别做长片主引擎。
15. ffmpeg 千路输入超 macOS 256 fd 软限制 → 分块 50 路预混再总混。

### Git 侧
16. GitHub 单文件 100MB 上限 → 大成片（p6 917MB）只留本地，仓库放小样片。

## 6. 仓库地图

```
STATE.md            ← 节点账本/接手入口（先读这个）
PLAN.md             ← 原始计划（部分编号已过时，以 STATE.md 为准）
SPEC.md / RESEARCH.md
HANDOFF_CLAUDE.md   ← 给 Claude Code 的交接（它做的 M0-M3 首轮）
run_dub.sh          ← 一键端到端
worker/llm_worker.py  ← LLM 自动答卷 bot
dub/build_dub.py      ← 配音层（引擎链/时长适配/拼装）
docs/BAOCUT_NOTES.md  ← 全部实测原始输出（M0→M7+，证据库）
docs/SPEED_RESEARCH.md ← 业界提速方案调研
output/             ← 成片、qc_report.json、样片（大文件只留本地）
work/               ← TTS 中间产物（gitignore，本地缓存可断点续跑）
```

## 7. 下一步（团队 backlog）

1. 人耳验收 `output/samples/`（唯一未闭环项）；
2. >1.5x 变速句治本：LLM 重译缩短（SPEED_RESEARCH 第 3 节）；
3. align 换更强模型减少 retry 浪费；
4. EdgeSpeak 本地 LLM 加载后可做 worker-bot 的全离线兜底（现在 chat provider 未配置）；
5. 3 小时以上播客的压力测试（目前最大 62 分钟）。
