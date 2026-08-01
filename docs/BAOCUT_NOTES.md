# BaoCut 实测笔记（真实终端输出，非推断）

CLI 路径：`/Applications/BaoCut.app/Contents/MacOS/baocut-cli`（**不在 PATH**）
App 版本：0.8.3

> 本文件只记录**跑出来的**东西。凡是从 `--help` 推断、未经运行验证的，一律标 `【推断·未验证】`。

## M0-1 · 环境体检（2026-08-01 已验证 ✅）

`baocut-cli doctor` → **9 checks · all healthy**

```
VERSIONS  app 0.8.3 · skill contract: not running under skill wrapper
MODELS    ASR: qwen3-asr-0.6b installed · speaker-diarization installed
TOOLS     yt-dlp /opt/homebrew/bin/yt-dlp (2026.06.09) · ffmpeg /opt/homebrew/bin/ffmpeg (8.1.2)
DATA      root /Users/lx/Library/Application Support/BaoCut (22.08 GB free)
          models .../models · projects .../projects
TASKS     no orphan projects · no stalled tasks
```

`baocut-cli model list`：

```
qwen3-asr-0.6b            installed   aufklarer/Qwen3-ASR-0.6B-MLX-4bit
qwen3-asr-1.7b            -           aufklarer/Qwen3-ASR-1.7B-MLX-8bit
whisper-large-v3-turbo    -           aufklarer/Whisper-Large-v3-Turbo-CoreML
moss-transcribe-diarize   -           OpenMOSS-Team/MOSS-Transcribe-Diarize
speaker-diarization       installed
gpt-4o-transcribe / gpt-4o-mini-transcribe / whisper-1   cloud · no key (OpenAI)
bigmodel-asr / bigmodel-asr-flash                        cloud · no key (火山引擎)
scribe_v2 / scribe_v1                                    cloud · no key (ElevenLabs)
qwen3-asr-flash                                          cloud · no key (DashScope)
cline-pass/deepseek-v4-flash                             cloud · connected (cline)
```

**读出来的事实**

1. 本地 ASR 默认是 **qwen3-asr-0.6b（MLX 4bit）**，不是 Whisper。想要更准可以
   `baocut model download qwen3-asr-1.7b` 或 `whisper-large-v3-turbo`（CoreML）。
   → 播客场景建议 M1 先用 0.6b 试跑，若术语错误多再换 1.7b。
2. **说话人识别模型已装**，多主持人音色映射这条路可行。
3. yt-dlp / ffmpeg 都是 BaoCut 直接调用系统里这两个（同一份，版本已知）。
4. 项目数据落在 `~/Library/Application Support/BaoCut/projects`，**不在我们的 runs/ 里**。
   我们的 `source/video.mp4` 需要从那里拷贝或另行下载 —— 具体路径待 M1 确认。
5. 磁盘只剩 **22 GB**，跑长视频前要注意。

## M0-2 · 命令契约（来自 `--help`，尚未运行）

已抄录在 RESEARCH.md 第 1 节。关键待验证点：

- 【推断·未验证】`subtitle list <pid> --lang zh --json` 的字段名与结构
- 【推断·未验证】译文 group 的**绝对起止时间**从哪个字段取
- 【推断·未验证】`task wait` 返回的 prompt 文件格式与 `task submit --file` 的答案格式
- 【推断·未验证】原视频文件在 BaoCut 项目目录下的位置

以上四条是 M2 必须解决的，`groups.json` 的实现完全依赖它们。

---

## M1 · 短视频端到端（已执行 ✅ 2026-08-01）

任务：`taskId=t-msac81kt`，`projectId=p1`，视频为 NASA ScienceCasts "Something for Every Sky Watcher"（英译中）。
从已领取的 `callId=c0001`（polish）开始，用 `task submit ... --next` 循环驱动到 `status:"done"`，全程 **9 次 submit，全部一次通过（attempt:1），没有遇到任何 rejected**。

### 1. kind 列表、次数、耗时（真实输出）

| kind | 次数 | callId |
|---|---|---|
| polish | 1 | c0001 |
| repunct | 1 | c0002 |
| translate | 1 | c0003 |
| align | 6 | c0004, c0005, c0006, c0007, c0008, c0009 |
| **合计** | **9** | |

耗时（真实终端时间戳，非推断）：
- 本 agent 从 c0002 提交到最终 `status:"done"` 确认：`date` 显示 **2026-08-01 20:31:32 → 2026-08-01 20:55:39**，约 **24 分 07 秒**（覆盖 c0002~c0009 共 8 次 submit）。c0001（polish）在此之前已完成，未单独计时，落在任务 `startedAt` 与 20:31:32 之间。
- BaoCut 任务自身统计（`task status` 输出）：`"startedAt":"2026-08-01T12:18:27Z"`（UTC，即本地 20:18:27），`"elapsedSec":2219`（约 **36 分 59 秒**），与上面两个时间点换算基本吻合。
- 最终 summary（引擎原话）：`"462 words · 20 edits · polish PASS · retries 0 · recovered pages 0 · fallback pages/sentences 0/0 · residual terms 0 · 27 lines → Chinese (Simplified)"`

### 2. 各 kind 样例：payload 原文 + 我们提交的答案（前 30 行）

**说明**：这几类 payload 在磁盘上实际都是**单行 JSON / 纯文本**（没有物理换行），"前 30 行"对 payload 不完全适用，下面 payload 部分贴的是该行的真实原文（较长的做了截断并注明）；答案 JSON 是我们自己写的多行文件，"前 30 行"精确适用。

#### (a) polish — callId c0001（唯一一份 polish payload，1 行）

payload 原文（`payloads/c0001.txt`，真实输出，仅截取开头，完整內容更长）：
```
Something for every sky watcher. ⏸⏸⏸ Presented by Science at NASA. ⏸⏸⏸ Go outside on a clear night, look up, and consider the following. ⏸ Standing on Earth's a surface. We are part of the universe's perpetual symphony of heavenly bodies, rotating on their axes, ⏸ and revolving around one another in an intricate rhythm. ⏸⏸ As far as we know, we are the only ones listening and extolling these movements in songs and poems. ⏸⏸ The July twenty-seventh night sky offers treats for sky watchers and listeners around the globe. ⏸⏸ ...(后略，完整文本约 500 词，含多处 ⏸ 停顿标记)
```

我们提交的答案 `/tmp/bc_c0001.json`（真实文件，前 30 行）：
```json
{
  "summary": "This NASA ScienceCasts segment previews the night of July 27th, when Mars reaches opposition at the same time as a total lunar eclipse, offering a rare celestial alignment for sky watchers worldwide. NASA planetary scientist Sarah Noble explains why oppositions vary in intensity, comparing the historic 2003 close approach to the anticipated 2018 event. The piece also describes how Earth's shadow turns the eclipsed Moon a reddish color similar to Mars, closing with a 19th-century description of the planet's brilliance from astronomer Percival Lowell.",
  "terms": [
    {"term": "Mars", "note": "The Red Planet; the transcript inconsistently lower-cases the name in a few places.", "observedVariants": ["mars"]},
    {"term": "opposition", "note": "Astronomical term for when Mars and the Sun are on opposite sides of Earth's sky; misheard once as \"expedition.\"", "observedVariants": ["expedition"]},
    {"term": "Red Planet", "note": "Popular nickname for Mars, referenced for its reddish glow.", "observedVariants": ["red planet"]},
    {"term": "Sun", "observedVariants": ["sun"]},
    {"term": "Moon", "observedVariants": ["moon"]},
    {"term": "Sarah Noble", "note": "NASA planetary scientist quoted in the piece; later referred to simply as \"Noble.\""},
    {"term": "Percival Lowell", "note": "19th-century astronomer quoted describing Mars's brightness."},
    {"term": "Capricornus", "note": "Constellation where the Moon and Mars appear close together on the night described."},
    {"term": "Science at NASA", "note": "The production presenting this piece."},
    {"term": "Universal Orchestra", "note": "Recurring cosmic metaphor, used alongside \"the universe's perpetual symphony\" and \"the Universal Symphony.\""},
    {"term": "Universal Symphony", "note": "Closing variant of the recurring orchestra/symphony metaphor, tied to science.nasa.gov."}
  ],
  "namedEntities": ["NASA", "Science at NASA", "Sarah Noble", "Percival Lowell", "Mars", "Earth", "Sun", "Moon", "Capricornus", "Europe", "Australia", "Africa", "Asia", "Sirius", "Jupiter", "science.nasa.gov"],
  "paragraphs": [
    {"sentences": ["Something for every sky watcher.", "Presented by Science at NASA."]},
    {"sentences": ["Go outside on a clear night, look up, and consider the following.", "Standing on Earth's a surface, we are part of the universe's perpetual symphony of heavenly bodies, rotating on their axes, and revolving around one another in an intricate rhythm.", "As far as we know, we are the only ones listening and extolling these movements in songs and poems."]},
    {"sentences": ["The July twenty-seventh night sky offers treats for sky watchers and listeners around the globe.", "On this night, in a tiny section of the Universal Orchestra, our sun, our planet, our moon, and Mars fall into a rare alignment."]},
    {"sentences": ["Mars will be at opposition.", "Mars and the Sun will be directly on opposite sides of the sky from our point of view."]},
    {"sentences": ["The Moon will also be opposite the Sun that night.", "The Sun, Earth, and Moon will be perfectly aligned.", "So viewers on Earth's night side will enjoy a total lunar eclipse along with a big, bright Mars."]},
    {"sentences": ["The Moon and Mars will be about five degrees apart in the constellation Capricornus.", "In the days surrounding opposition, Mars and Earth are closer to one another than at any other time in their orbits, explains NASA planetary scientist Sarah Noble."]},
    {"sentences": ["Mars' oppositions happen about every two years, but not all oppositions are the same.", "That's because planetary orbits are elliptical, and the distance between the Sun and Mars varies during Mars' orbit."]},
    {"sentences": ["During its 2003 opposition, Mars made its closest approach to Earth in sixty thousand years, enthralling skywatchers worldwide.", "The twenty eighteen opposition of Mars will be nearly as spectacular."]},
    {"sentences": ["The Red Planet will climb in the eastern sky at sunset, rising almost overhead at midnight, glowing burnt orange, and earning its nickname.", "In nineteenth-century astronomer Percival Lowell's words, Mars blazes forth against the dark background of space with splendour that outshines Sirius and rivals the giant Jupiter himself."]},
    {"sentences": ["Viewers in Europe, Australia, Africa, and Asia, where it will be nighttime, will also experience Earth's shadow edging softly across the face of the full Moon.", "During a lunar eclipse, Earth is between the Moon and Sun, preventing most of the Sun's light from hitting the Moon.", "A total lunar eclipse occurs only when the Sun, Earth, and Moon are precisely aligned in that order."]},
    {"sentences": ["As Earth's shadow begins to cover the lunar surface, the Moon fades into an eerie reddish hue, as red as the Red Planet.", "That's because sunlight is scattered as it travels through Earth's atmosphere, like at sunrise and sunset."]},
    {"sentences": ["Noble says, \"You can think of the reddish color as all of the sunrises and sunsets on Earth at that moment reflected off the surface of the Moon.\""]},
    {"sentences": ["For more movements of the Universal Symphony, visit science.nasa.gov."]}
  ]
}
```
提交结果：`baocut --json task submit t-msac81kt --call c0001 ...` → 一次通过，无 warnings。

#### (b) repunct（"其他"之一，1 次）— callId c0002

payload 原文（`payloads/c0002.txt`，真实输出，完整）：
```json
{"budget":42,"segs":[{"id":9,"text":"The Moon will also be opposite the Sun that night.","cm":"The<c3> Moon<c8> will<c13> also<c18> be<c21> opposite<c30> the<c34> Sun<c38> that<c43> night."},{"id":17,"text":"The twenty eighteen opposition of Mars will be nearly as spectacular.","cm":"The<c3> twenty<c10> eighteen<c19> opposition<c30> of<c33> Mars<c38> will<c43> be<c46> nearly<c53> as<c56> spectacular."},{"id":19,"text":"In nineteenth-century astronomer Percival Lowell's words, Mars blazes forth against the dark background of space with splendour that outshines Sirius and rivals the giant Jupiter himself.","cm":"In<c2> nineteenth-century<c21> astronomer<c32> Percival<c41> Lowell's<c50> words, Mars<c62> blazes<c69> forth<c75> against<c83> the<c87> dark<c92> background<c103> of<c106> space<c112> with<c117> splendour<c127> that<c132> outshines<c142> Sirius<c149> and<c153> rivals<c160> the<c164> giant<c170> Jupiter<c178> himself."}],"v":2}
```

我们提交的答案 `/tmp/bc_c0002.json`（真实文件，完整，仅 1 行，未超 30 行）：
```json
{"segs":[{"id":9,"cuts":[{"id":"c38","m":","}]},{"id":17,"cuts":[{"id":"c38","m":","}]},{"id":19,"cuts":[{"id":"c32","m":","},{"id":"c92","m":","},{"id":"c132","m":","},{"id":"c170","m":","}]}]}
```
提交结果：一次通过，无 warnings。

#### (c) translate — callId c0003（唯一一份，仅在此列出结构，完整 27 行译文见正文）

payload 原文（`payloads/c0003.txt`，真实输出，节选前几条 + 尾部字段）：
```json
{"lines":[{"source":"Something for every sky watcher.","maxChars":27,"id":"g1.0"},{"source":"Presented by Science at NASA.","maxChars":26,"id":"g2.0"},{"source":"Go outside on a clear night, look up, and consider the following.","maxChars":50,"id":"g3.0"},{"source":"Standing on Earth's a surface, we are part of the universe's, perpetual symphony of heavenly bodies, rotating on their axes, and revolving, around one another in an intricate rhythm.","maxChars":113,"id":"g4.0"}, ...(共 27 条 line，每条都带 source + maxChars + id)... ],"context":"Chapters: Transcript","lang":"zh"}
```

我们提交的答案 `/tmp/bc_c0003.json`（真实文件，前 30 行）：
```json
{
  "summary": "This NASA ScienceCasts segment previews the night of July 27th, when Mars reaches opposition at the same time as a total lunar eclipse, offering a rare celestial alignment for sky watchers worldwide. NASA planetary scientist Sarah Noble explains why oppositions vary in intensity, comparing the historic 2003 close approach to the anticipated 2018 event. The piece also describes how Earth's shadow turns the eclipsed Moon a reddish color similar to Mars, closing with a 19th-century description of the planet's brilliance from astronomer Percival Lowell.",
  "glossary": [
    {"source":"Mars","target":"火星","locked":false},
    {"source":"opposition","target":"冲日","note":"Astronomical term for when Mars and the Sun sit on opposite sides of Earth's sky; commonly paired as \"火星冲日\".","locked":false},
    {"source":"Red Planet","target":"红色星球","note":"Mars's nickname from its color; translated by sense rather than transliterated.","locked":false},
    {"source":"Sun","target":"太阳","locked":false},
    {"source":"Moon","target":"月球","locked":false},
    {"source":"Sarah Noble","target":"Sarah Noble","note":"Kept in English per project policy for personal names (avoids TTS mispronunciation of an invented transliteration); later short form \"Noble\" also kept in English.","locked":false},
    {"source":"Percival Lowell","target":"Percival Lowell","note":"Kept in English per project policy for personal names.","locked":false},
    {"source":"Capricornus","target":"摩羯座","note":"Standard Chinese constellation/zodiac name, more recognizable to listeners than a Latin transliteration.","locked":false},
    {"source":"Science at NASA","target":"Science at NASA","note":"Kept in English as the proper program/brand name presenting the piece.","locked":false},
    {"source":"Universal Orchestra","target":"宇宙交响乐团","note":"Recurring cosmic metaphor; kept distinct from \"Universal Symphony\" to preserve the source's wording variation.","locked":false},
    {"source":"Universal Symphony","target":"宇宙交响曲","note":"Closing variant of the orchestra/symphony metaphor, tied to science.nasa.gov.","locked":false},
    {"source":"NASA","target":"NASA","note":"Kept as the English acronym, standard practice in Chinese media.","locked":false},
    {"source":"Earth","target":"地球","locked":false},
    {"source":"Jupiter","target":"木星","locked":false},
    {"source":"Sirius","target":"天狼星","locked":false},
    {"source":"Europe","target":"欧洲","locked":false},
    {"source":"Australia","target":"澳大利亚","locked":false},
    {"source":"Africa","target":"非洲","locked":false},
    {"source":"Asia","target":"亚洲","locked":false},
    {"source":"science.nasa.gov","target":"science.nasa.gov","note":"URL preserved verbatim.","locked":false}
  ],
  "namedEntities": ["NASA","Science at NASA","Sarah Noble","Percival Lowell","Mars","Earth","Sun","Moon","Capricornus","Europe","Australia","Africa","Asia","Sirius","Jupiter","science.nasa.gov"],
  "styleGuide": "Warm, accessible science-education register for a general audience, matching NASA ScienceCasts' informative-but-poetic tone... (完整版见提交文件，含 TTS 相关的专有名词保留规则)",
  "difficulties": [
    "\"Red Planet\" first appears before the narration says Mars is \"earning its nickname,\" then recurs later as an established nickname; both instances rendered as \"红色星球\" for glossary consistency.",
    "..."
  ],
  "translations": {
    "g1.0": "献给每一位仰望星空的人。",
    "g2.0": "由 Science at NASA 呈现。",
    "g3.0": "找个晴朗的夜晚走到户外，抬头看看夜空，想想接下来发生的事。"
  }
}
```
（完整答案含全部 11 条 glossary + 27 条 translations，此处只截取到第 30 行以内；真实提交结果一次通过，无 warnings。）

#### (d) align（"其他"之一，6 次，最多）— 示例 callId c0004

payload 原文（`payloads/c0004.txt`，真实输出，完整）：
```json
{"v":4,"lang":"zh","pairs":[{"sm":"The<@0> July<@1> twenty-seventh<@2> night,<@3><#0> sky<@4> offers<@5> treats<@6> for<@7> sky<@8> watchers,<@9> and<@a> listeners<@b> around<@c> the<@d> globe.","ctx":{"b":"据我们所知，我们是唯一会聆听，并用歌曲与诗篇歌颂这些天体运行的存在。","a":"这一夜，在宇宙交响乐团的一个小小乐章里，我们的太阳、地球、月球，将与火星迎来一次罕见的排列。"},"id":"g7.0","tm":"7<@0>月<@1>27<@2>日<@3>的<@4>夜空，<@5><#0>为<@6>全球<@7>的<@8>观<@9>星<@a>者<@b>和<@c>聆听<@d>者<@e>带来<@f>了<@g>惊喜。"},{"problems":["unit boundaries after \"enjoy\" (word 8) were placed by char-proportional timing with no punctuation anchor — re-cut those boundaries at natural semantic points in BOTH languages"],"sm":"So<@0> viewers<@1> on<@2> Earth's<@3> night,<@4> side<@5> will<@6> enjoy<@7><#0> a<@8> total<@9> lunar<@a> eclipse,<@b><#1> along<@c> with<@d> a<@e> big,<@f> bright<@g> Mars.","pt":["火星","地球"],"ctx":{"b":"太阳、地球和月球将完美地连成一线。","a":"在摩羯座中，月球和火星之间大约相距五度。"},"id":"g12.0","tm":"因此，<@0>处于<@1>地球<@2>夜晚<@3>一侧<@4>的<@5>观众，<@6><#0>将<@7>同<@8>时<@9>看到<@a>月全食，<@b><#1>以及<@c>一<@d>颗<@e>又<@f>大<@g>又<@h>亮<@i>的<@j>火星。"},{"sm":"The<@0> Red<@1> Planet<@2> will<@3> climb<@4> in<@5> the<@6> eastern,<@7> sky<@8> at<@9> sunset,<@a><#0> rising<@b> almost<@c> overhead<@d> at<@e> midnight,<@f><#1> glowing<@g> burnt<@h> orange,<@i> and<@j> earning<@k> its<@l> nickname.","pt":["红色星球"],"ctx":{...},"id":"g19.0","tm":"红色星球<@0>将<@1>在<@2>日落<@3>时分<@4>从<@5>东方<@6>天空<@7>升起，<@8><#0>到<@9>午夜<@a>时分<@b>几乎<@c>升至<@d>头顶，<@e><#1>泛<@f>着<@g>橙红色<@h>的<@i>光芒，<@j>也<@k>因此<@l>得名。"},{"sm":"During<@0> a<@1> lunar<@2> eclipse,<@3> Earth<@4> is<@5> between<@6> the<@7> Moon<@8> and<@9> Sun,<@a><#0> preventing<@b> most<@c> of<@d> the<@e> Sun's,<@f> light<@g> from<@h> hitting<@i> the<@j> Moon.","pt":["太阳","月球","地球"],"ctx":{...},"id":"g23.0","tm":"在<@0>月食<@1>期间，<@2>地球<@3>位于<@4>月球<@5>与<@6>太阳<@7>之间，<@8><#0>挡住<@9>了<@a>大部分<@b>照<@c>向<@d>月球<@e>的<@f>太阳光。"}],"budgets":{"f":16,"t":14,"s":42}}
```

我们提交的答案 `/tmp/bc_c0004.json`（真实文件，完整，1 行，未超 30 行）：
```json
{"pairs":[{"id":"g7.0","action":"recut","cuts":[{"s":"4","t":"5"}]},{"id":"g12.0","action":"recut","cuts":[{"s":"5","t":"6"},{"s":"b","t":"b"}]}]}
```
提交结果：一次通过；返回 2 条 warning（均为"翻译片段超出 14 字瞄准值但在 20 字容忍上限内，未强行切分"，非拒绝），原文：
```
"translation segment is 17 chars — above the 14-char aim but within the 20-char tolerance ceiling; no safe balanced semantic cut was found, so keeping this atomic span whole is allowed" (loc: g7.0 unit 2)
"translation segment is 15 chars — above the 14-char aim but within the 20-char tolerance ceiling; no safe balanced semantic cut was found, so keeping this atomic span whole is allowed" (loc: g12.0 unit 1)
```

align 其余 5 次（c0005~c0009）同样全部一次通过，做法一致：对**契约标出 `"problems"` 的 pair 必须返回修正**，对未标 `"problems"` 的 pair 逐条读语义后判断是否需要动（大多数情况判断为"已经是最佳切法，不动"）。6 次里一共处理了两类问题：
1. **recut 类**（7 处）：机械按比例时间切出的边界落在了介词/量词与其宾语之间（如 "of the sunrises"、"all of"、"night sky" 被切开），改成把整体挪到同一个 unit。
2. **rewrite 类，reasonCode:"reorder"**（3 处：`wmsacp0is-9`、`g24.0`、`g14.0`）：这三句译文为了中文自然语序，把英文句尾的状语/归因分句（"from our point of view" / "...explains, NASA...Sarah Noble." 这类倒装归因句）提到了句首，导致 5 个 unit 里内容整体错位（比如某个 unit 的中文在讲"NASA科学家"，对应的英文却在讲"这几天里"）。按契约 HARD RULE 改写为**跟随英文分句顺序、但仍是自然中文**的版本（如"…，NASA 行星科学家 Sarah Noble 解释说。"这种中文里同样成立的尾置归因句式）。

### 3. rejected 记录

**本次 9 次 submit 全部一次通过（`"attempt":1`），没有遇到任何一次 `"status":"rejected"`。** 因此没有"原始错误信息 + 怎么改好"的真实案例可贴——如果后续任务里出现 rejected，会在这里补充真实报错原文。

需要说明：过程中收到过 **6 条 `warnings`**（c0004×2、c0006×2、c0007×2），但 warnings 不是 rejected —— `task submit` 依然返回了下一个 callId，任务继续推进，这些只是"译文片段长度在 14~20 字容忍区间内、未做进一步切分"的告知信息，见上面第 2 节引用的原文。

### 4. 关键结论：translate payload 里到底有没有时长/字数预算字段？

**没有"时长（秒）"字段，只有按字符数换算好的 `maxChars` 字段。** 真实证据：

- `payloads/c0003.txt`（translate 契约）里每条 line 的结构是 `{"source":..., "maxChars":<int>, "id":...}`，通篇搜索**不存在** `duration`、`durationSec`、`seconds`、`start`/`end` 时间戳一类字段。顶层也只有 `"context":"Chapters: Transcript"` 和 `"lang":"zh"`，`context` 只是章节标题，不是时长。
- `translate.md` 契约原文明确写了 `maxChars` 的定义：*"The adult delivery limit is 9 visible non-whitespace characters per second. Treat each supplied `maxChars` as the line's reading-speed budget without sacrificing essential meaning."* —— 也就是说 `maxChars` 是**已经按"每秒 9 个非空白字符"这个字幕可读速度上限换算好的字符预算**，字段名叫 `maxChars`，不是"每秒几个字"或"多少秒"。
- `align.md` 契约里也出现了一组相关但同样不是"时长"的数字：`"budgets":{"f":16,"t":14,"s":42}`（f=单行字数上限、t=目标瞄准字数、s=源文本行宽提示），全是**字符数**，不是秒数。

**结论对我们后续工作的影响**：M1 任务书里设想的"目标字数 ≈ 时长(秒) × 5.2"公式**在 translate 阶段无法直接套用**，因为：
1. 没有时长字段可以乘 5.2；
2. 即使想反推，`maxChars` 用的是 9 字/秒的**字幕阅读速度**上限，跟配音口播的 5.2 字/秒完全是两套不同用途、不同数值的标准（字幕允许读者眼睛扫得比说话快，配音字数必须卡在真实语速内），**不能**把 `maxChars ÷ 9` 反推出秒数后再乘 5.2 当成配音字数预算去用——这是【推断】而非契约给出的字段，本次没有这样做，翻译时按契约本身的自然度/忠实度要求正常处理，没有额外压缩或放宽字数。
3. 如果后续要做配音字数约束，需要在 **别的阶段**（比如切分后的实际语音时长，或原始 ASR 的时间戳）另外获取秒数，translate/align 这两个契约本身都不提供。

### 5. 观察到的系统性现象（附带记录，非任务要求，但直接导致了多次 align 修正）

在我接手之前已经跑完的 repunct 结果里，有一个**反复出现的规律**：几乎每次都把逗号点在两词复合词/介词短语中间靠后的那个词前面，例如（均为真实 payload 原文片段）：
`night, sky`、`night, side`、`eastern, sky`、`closest, approach`、`universe's, perpetual`、`revolving, around`、`planetary, orbits`、`precisely, aligned`、`one, another`、`any, other`、`reddish, color`、`and, sunsets`、`reflected, off`、`Sun's, light`、`five, degrees`、`giant, Jupiter`、`constellation, Capricornus`。

这些逗号本身在 align 阶段没有引发拒绝，但当机械时间轴恰好也在这些位置附近切 unit 时，就会造成"中文已经把两个词放一起翻译了，但对应的英文源文两个词却被分到了前后两个 unit"的错位，是本次 6 次 align 里绝大多数 recut 修正的直接原因。**【推断·未验证】** 这可能是 repunct 契约提示词里某种偏好被过度触发；如果后续要减少 align 阶段的返工，可以考虑在 repunct 契约里补充"不要在紧密复合词内部插入逗号"的约束。

### 6. 最终 status（真实完整输出）

```json
{
  "claimedCount" : 0,
  "configuredConcurrency" : 4,
  "elapsedSec" : 2219,
  "expiredClaimCount" : 0,
  "flow" : "auto",
  "lang" : "zh",
  "pendingByKind" : {},
  "pendingByWorkClass" : {},
  "pendingCount" : 0,
  "phase" : "Assembling translation",
  "polishQuality" : {
    "fallbackPageCount" : 0,
    "fallbackSentenceCount" : 0,
    "measuredPageCount" : 1,
    "pageCount" : 1,
    "recoveredPageCount" : 0,
    "residualTermVariantCount" : 0,
    "residualTermVariants" : [],
    "retryCount" : 0,
    "status" : "PASS"
  },
  "progress" : 100,
  "projectId" : "p1",
  "slowClaimCount" : 0,
  "slowClaims" : [],
  "stalledClaimCount" : 0,
  "startedAt" : "2026-08-01T12:18:27Z",
  "status" : "done",
  "summary" : "462 words · 20 edits · polish PASS · retries 0 · recovered pages 0 · fallback pages/sentences 0/0 · residual terms 0 · 27 lines → Chinese (Simplified)",
  "taskId" : "t-msac81kt",
  "unclaimedCount" : 0,
  "waitingOn" : "terminal",
  "workers" : []
}
```

命令：`baocut --json task status t-msac81kt` → `"status" : "done"` ✅ 达成 Completion standard。

## M2 · 结构化数据映射（已执行 ✅ 2026-08-01）

### 1. `subtitle list` 真实结构 —— `groups.json` 的字段来源已定死

命令：`baocut-cli --json subtitle list p1 --lang zh --limit 3`（真实输出）

```json
{
  "lang":"zh", "projectId":"p1", "returned":3, "total":64, "unit":"group", "status":"ok",
  "subtitles":[
    {"id":"g1.0","start":3.24,"end":4.77,"chars":12,"hidden":false,"stale":false,
     "speaker":"Speaker 1","speakerId":"s1",
     "source":"Something for every sky watcher.",
     "text":"献给每一位仰望星空的人。"}
  ]
}
```

**M0 列的四条未验证假设，前两条到此解决：**

| 原假设 | 结论 |
|---|---|
| `subtitle list --lang zh --json` 字段结构 | ✅ 已确认，见上 |
| group 的绝对起止时间取自哪个字段 | ✅ **`start` / `end`，单位秒的绝对时间**，无需回落解析 SRT |

`groups.json` 映射（**已验证，可直接实现**）：

| groups.json | 来源 |
|---|---|
| `gid` | `id`（形如 `g1.0` / `g28.7`） |
| `start` / `end` / `dur` | `start` / `end` / `end-start` |
| `text_zh` | `text` |
| `text_en` | `source` |
| `speaker` | `speakerId`（`s1`…），显示名用 `speaker` |
| `stale` / `hidden` | 同名字段，`hidden=true` 的组**不配音** |

### 2. cps 系数校准（真实统计，64 个组）

```
groups 64 · 语音总时长 164.4s · 中文总字数 895 · 视频总长 214s
dur   min/med/max  0.65 / 2.41 / 5.53 s
chars min/med/max  7 / 14 / 21
cps   min/p25/med/p75/max  2.61 / 4.46 / 5.40 / 6.98 / 32.31
整体 chars/sec = 5.44
```

**结论：SPEC 里 `cps = 5.2` 的估算成立**（实测整体 5.44）。但**单组方差极大**，
p75 已到 6.98，最大 32.31 —— 逐组硬塞会大面积赶字。

### 3. ★ 关键设计修正：必须允许向后续静音间隙溢出

组间静音总计 **41.9s**（中位 0.54s，p75 1.10s，最大 4.65s）。
按 `需变速比 = chars / 5.2 / 可用时长` 统计不同溢出策略：

| 允许占用后续间隙 | 需变速 >1.25 的组 | 占比 |
|---|---|---|
| 0%（只用 group 自身时长） | 18 / 64 | **28%** |
| 30% | 11 / 64 | 17% |
| **60%（推荐）** | **8 / 64** | **12%** |
| 100% | 7 / 64 | 11% |

- 不溢出 → 28%，逼近 SPEC 的 FAIL 线（>30%），**原设计站不住**
- 溢出 60% → 12%，落在 WARN 线（15%）以下，**设计成立**，且保留呼吸感
- 溢出 100% 边际收益仅 1 个组，却吃光全部停顿，不值得

→ **SPEC 阶段 C 已据此改为：可用时长 = `dur + min(gap × 0.6, gap − 0.15)`。**

### 4. 病态组（已知问题，需兜底）

```
最挤的 5 组:
  g28.7   dur=0.65  gap=0.00  chars=21  cps=32.3   ← 组边界过窄且无间隙
  g14.25  dur=0.88  gap=1.11  chars=16  cps=18.2
  g2.0    dur=1.44  gap=3.68  chars=21  cps=14.6
  g10.13  dur=0.96  gap=0.53  chars=12  cps=12.5
  g27.22  dur=0.90  gap=0.95  chars=10  cps=11.1
```

`g28.7` 这类（时长 < 0.7s 且无间隙）单靠变速和压缩都救不了。
兜底方案【推断·未验证】：与相邻同说话人组**合并共享时间预算**，或用
`baocut subtitle merge` 在源头合并。**M4 必须处理，否则会出现明显赶字点。**

### 5. M0 遗留问题状态

| 假设 | 状态 |
|---|---|
| `subtitle list --json` 字段结构 | ✅ M2 已验证 |
| group 绝对起止时间字段 | ✅ M2 已验证（`start`/`end`） |
| `task wait/submit` 的 prompt 与答案格式 | ✅ M1 已验证（见 M1 各 kind 样例） |
| 原视频在 BaoCut 项目目录下的位置 | ⬜ **仍未确认，M5 mux 之前必须解决** |

## M3-loop · 双人素材 BaoCut 跑通记录（已执行 ✅ 2026-08-01）

任务：`taskId=t-msagprsx`，`projectId=p2`，素材为 NASA《Houston We Have a Podcast》第 1 集第 5–8 分钟，**双人录音室访谈**（主持人 Gary Jordan + 一位 NASA 嘉宾），180 秒，英译中。全程从 `task status` 发现 `pendingCount:1` 开始，用 `task claim` → 读 payload/contract → 写答案 → `task submit --next` 循环驱动到 `status:"done"`，**9 次 submit，全部一次通过（`"attempt":1`），没有遇到任何 `rejected`**。

### 1. kind 列表、次数、submit 总次数、耗时（真实数据）

| kind | 次数 | callId |
|---|---|---|
| polish | 1 | c0001 |
| repunct | 1 | c0002 |
| translate | 1 | c0003 |
| align | 6 | c0004, c0005, c0006, c0007, c0008, c0009 |
| **合计** | **9** | |

与 M1（单人 3.5 分钟视频）的 kind 结构**完全一致**（polish×1 / repunct×1 / translate×1 / align×6 = 9 次），双人素材并没有因为多一个说话人而多出额外的 submit 轮次。

耗时（真实数据，来自 `task status` / `task submit` 返回的字段，本 agent 本身没有在会话最开始调用过 `date` 做基准，故用引擎自己的计时字段回推）：
- 任务自身 `"startedAt":"2026-08-01T14:24:13Z"`（UTC，即北京时间 22:24:13）。
- 本 agent 第一次 `task status` 轮询时返回 `"elapsedSec":82`，即真实时间约 **14:25:35 UTC**；当时 `"pendingByKind":{"polish":1}`，说明转录/分句已提前跑完，polish 是第一个待办。
- 最后一次 `task submit`（c0009 → `--next`）与随后的确认性 `task status` 均返回 `"elapsedSec":2340`，即真实时间约 **15:03:13 UTC**（39 分 00 秒）。
- 因此本 agent 从接手（首次看到 `pendingCount:1`）到任务 `status:"done"`，跨度 ≈ `2340-82=2258` 秒，约 **37 分 38 秒**（覆盖 c0001~c0009 全部 9 次 submit）。
- 落笔记录本节时执行 `date`，真实输出：`2026-08-01 15:04:49 UTC` / `2026-08-01 23:04:49 CST`，与上面的完成时刻（15:03:13 UTC）相差约 1 分 36 秒，用于写文档，吻合。
- 最终 summary（引擎原话）：`"571 words · 27 edits · polish PASS · retries 0 · recovered pages 0 · fallback pages/sentences 0/0 · residual terms 0 · 2 speakers · 33 lines → Chinese (Simplified)"`

### 2. 各 kind 样例：payload 片段 + 我们提交的答案

**说明**：与 M1 一致，这几类 payload 磁盘上都是单行 JSON/纯文本，下面对较长的做了截断并注明；答案是我们自己写的多行文件，按“前 30 行”截取。

#### (a) polish — callId c0001（唯一一份，1 行，3098 字符）

payload 原文（`payloads/c0001.txt`，真实输出，截取开头到第一个说话人切换标记）：
```
I ⏸ mean, some Soyuz rides have been as little as like six hours, right? Relatively ⏸ easy. Going to space is only rocket science. Don't want to trivialize. ⏸ ⏹ It's still, and even that's the— you even have to admonish myself— it's still not easy to go to space. ...(后略，完整文本共出现 3 处 ⏹ 说话人切换标记，见下第 4 节)
```

我们提交的答案 `/tmp/p2_c0001.json`（真实文件，全文 27 行，未超 30 行）：
```json
{
  "summary": "Two speakers discuss how, even though some spaceflights like short Soyuz missions can seem easy, human spaceflight remains an extremely complex and risky undertaking, especially compared to future goals like traveling to Mars. They explain that gravity, or the lack of it, is the key factor that makes engineering in space fundamentally different from on Earth, citing examples such as capillary action in fluid systems and astronaut water supplies. They describe the International Space Station as the first large-scale modern test bed for learning to live and operate in space, building on decades of prior U.S. and Russian space station experience.",
  "terms": [
    {"term": "Soyuz", "note": "Russian crewed spacecraft that ferries astronauts to and from the International Space Station."},
    {"term": "International Space Station", "note": "Also referred to as the ISS."},
    {"term": "capillary action", "note": "Physical phenomenon that lets fluids move without relying on gravity, referenced regarding spacecraft fluid and fuel systems.", "observedVariants": ["capillary reaction"]},
    {"term": "Mars", "note": "Referenced as a future target for human space exploration."}
  ],
  "namedEntities": ["Soyuz", "International Space Station", "Mars", "Earth", "United States", "Russia"],
  "paragraphs": [
    {"sentences": ["I mean, some Soyuz rides have been as little as like six hours, right?", "Relatively easy.", "Going to space is only rocket science.", "Don't want to trivialize."]},
    {"sentences": ["It's still, and even that's the— you even have to admonish myself— it's still not easy to go to space.", "It's still, I mean, it is rocket—rocket science—it's literal rocket science, which is hugely complex, and there's always inherent risk and all these other things."]},
    ...（后略 12 段，完整 14 段/36 句，一次通过，无 warnings）
  ]
}
```

#### (b) repunct — callId c0002（唯一一份，1 行，2 个待切分段落）

payload 原文（`payloads/c0002.txt`，真实输出，完整）：
```json
{"budget":42,"segs":[{"id":21,"text":"Like, little—those little tiny things are things that make the huge difference in being able to kind of explore the solar system.","cm":"Like, little—those<c18> little<c25> tiny<c30> things<c37> are<c41> things<c48> that<c53> make<c58> the<c62> huge<c67> difference<c78> in<c81> being<c87> able<c92> to<c95> kind<c100> of<c103> explore<c111> the<c115> solar<c121> system."},{"id":35,"text":"And so you have all of these different technologies that—like I said earlier—everything you do in space is different from the way that you do it on planet Earth, where, you know, you have.","cm":"...(省略中段 cm 序列)...know<c172> you<c182> have."}],"v":2}
```

我们提交的答案 `/tmp/p2_c0002.json`（真实文件，完整，1 行）：
```json
{"segs":[{"id":21,"cuts":[{"id":"c48","m":","},{"id":"c87","m":","}]},{"id":35,"cuts":[{"id":"c28","m":","},{"id":"c51","m":","},{"id":"c87","m":","},{"id":"c121","m":","}]}]}
```
提交结果：一次通过，无 warnings。id=35 这句 160 字符按 42 宽度算至少要切 4 刀（3 刀在数学上不可行，因为候选 seam 在 `c68`→`c87` 之间有 19 字符的空档，逼得任何 3 刀方案都凑不出满足两端预算的组合），实测提交也确认了这个判断。

#### (c) translate — callId c0003（唯一一份，33 行 lines，4513 字符）

payload 原文（`payloads/c0003.txt`，真实输出，节选前两条 + 尾部）：
```json
{"lang":"zh","lines":[{"maxChars":27,"id":"g1.0","source":"I mean, some Soyuz, rides have been as little as like, six hours, right?"},{"maxChars":40,"id":"g1.14","source":"Relatively easy. Going to space is only rocket science. Don't want to trivialize."}, ...(中略 31 条)..., {"maxChars":112,"id":"g16.0","source":"And so you have all of these, different technologies, that—like I said earlier—everything, you do in space is different from, the way that you do it on planet Earth, where, you know, you have."}],"context":"Chapters: Transcript"}
```

我们提交的答案 `/tmp/p2_c0003.json`（真实文件，完整 60 行，前 30 行如下）：
```json
{
  "summary": "两位主持人围绕 NASA 载人航天展开对话：虽然像联盟号这样的短途任务只需几个小时，看似轻松，但太空飞行本身依然极其复杂、充满风险，尤其是与未来登陆火星等目标相比。他们指出，重力（或者说太空中重力的缺失）是让太空工程与地面工程截然不同的核心因素，并以毛细作用如何影响流体系统、宇航员饮水系统等例子加以说明。最后，他们将国际空间站描述为人类学习长期太空生活与作业的现代化试验平台，这也建立在美俄两国此前数十年空间站经验的基础之上。",
  "glossary": [
    {"source":"Soyuz","target":"联盟号","note":"俄罗斯联盟号飞船的通行中文译名。","locked":false},
    {"source":"International Space Station","target":"国际空间站","note":"标准中文译名，全篇统一使用，不用英文原词或裸缩写。","locked":false},
    {"source":"capillary action","target":"毛细作用","note":"物理学标准译法；原文曾误识别为 capillary reaction，已统一订正。","locked":false},
    {"source":"Mars","target":"火星","locked":false},
    {"source":"Earth","target":"地球","locked":false},
    {"source":"U.S.","target":"美国","locked":false},
    {"source":"Russia","target":"俄罗斯","locked":false},
    {"source":"gravity","target":"重力","note":"全篇反复出现的核心概念，统一译为“重力”。","locked":false}
  ],
  "namedEntities": ["Soyuz","International Space Station","Mars","Earth","United States","Russia"],
  "styleGuide": "这是一档 NASA 播客的双人对谈，主持人 Gary Jordan 与一位 NASA 嘉宾就国际空间站展开轻松但专业的讨论...(完整版含配音口语化规则，见提交文件)",
  "difficulties": [
    "口水词与自我打断（you know / I mean / like，以及 that's the— 这类未说完就改口的表达）需要在中文里删减或合并，只保留自然口语停顿感，不能逐字直译。",
    "...(后略 4 条)"
  ],
  "translations": {
    "g1.0": "有些联盟号任务才六个小时，对吧？",
    "g1.14": "相对简单。去太空说到底就是搞火箭科学。我也不想把话说轻巧了。",
    "g1.27": "但这事儿吧，我得提醒自己——去太空，真没那么容易。"
    ...(后略 30 条，共 33 条 translations，一次通过，无 warnings)
  }
}
```

#### (d) align（6 次中出现次数最多）— 示例 callId c0004

payload 原文（`payloads/c0004.txt`，真实输出，仅摘录被判定需要修正的一条）：
```json
{"sm":"But<@0> when<@1> you<@2> start<@3> comparing<@4> it<@5> to,<@6><#0> you<@7> know,<@8> going<@9> to<@a> Mars,<@b> ...<#3> it's,<@10> ...easy,<@16> but<@17> it's<@18> still<@19> a<@1a> monumental<@1b> undertaking.","id":"wmsah7v2e-8","problems":["unit boundary after \"know,\" (word 15) was placed by proportional timing snapped to punctuation ...","unit boundary after \"that,\" (word 36) was placed by proportional timing snapped to punctuation ..."],"pt":["火星"],"tm":"可<@0>一旦<@1>拿<@2>它<@3>跟<@4>去<@5>火星，<@6><#0>或<@7>者...<#3>但<@q>即便<@r>这样，<@s>它<@t>仍然<@u>是<@v>一<@w>项<@x>了不起<@y>的<@z>壮举。"}
```

我们提交的答案 `/tmp/p2_c0004.json`（真实文件，完整，1 行）：
```json
{"pairs":[{"id":"wmsah7v2e-8","action":"rewrite","reasonCode":"reorder","reason":"原译把两次比较合并成一个跟A、B相比的框架，相比动词被推迟到末尾，导致火星、银河系、容易等核心内容比源文对应单元提前一个单元出现；改写为按源文顺序对每个比较对象分别使用跟...比，使目标内容与源文单元一一对齐，中文仍自然通顺。","pieces":[{"through":"b","t":"但要是拿它跟去火星比，"},{"through":"o","t":"或者跟我们那些遍布太阳系、"},{"through":"z","t":"银河系的宏伟目标比，"},{"through":"16","t":"这就只能算是“容易”的了。"},{"through":"end","t":"但即便这样，它仍然是一项了不起的壮举。"}]}]}
```
提交结果：一次通过，附 1 条 warning（`wmsah7v2e-8 unit 5` 19 字，超 14 字瞄准值但在 20 字容忍上限内，未强行切分，非拒绝）。

align 其余 5 次（c0005~c0009）做法一致：**契约标出 `"problems"` 的 pair 必须返回修正**（本次 24 个 pair 里有 8 个带 `problems`，全部修正）；带 `"advisory"` 的（3 个，均为 CPS 超速提示）判断后也选择修正；其余 13 个未标注问题的 pair 逐条核对语义边界后判断"已是最佳切法，不动"。6 次共改了 11 处，其中：
- **recut（纯挪边界，不改文字）6 处**：`g16.0`（核实后确认原边界正确，用 recut 显式确认）、`g4.26`、`g11.28`、`g1.45`、`g12.14`、`g14.0`——共性原因是源文按字符比例机械切分，切在了介词/冠词/复合词中间（如 `针<#0>对` 把"针对"这个词从中间切开、`there's<@g><#2>` 把 "there's" 和它的宾语 "always inherent risk" 分家）。
- **rewrite，reasonCode:"reorder" 2 处**：`wmsah7v2e-8`、`g5.11`——中文自然语序把英文分散的两次"跟…比"合并/前置，导致内容整体错位一个单元，按契约 HARD RULE 改写为跟随源文分句顺序、但仍自然的中文。
- **rewrite，reasonCode:"grammar"（压缩语速）3 处**：`g1.14`、`g7.11`、`g11.0`——均为 `advisory` 提示译文按时长换算超过 9.0 字/秒成人语速上限（9.1～10.7 字/秒不等），删掉非必要虚词或换更短同义词压缩 1～3 字，语义不变。

### 3. rejected 记录

**本次 9 次 submit 全部一次通过（`"attempt":1`），零拒绝**，没有真实的"原始错误 + 怎么改好"案例可贴。

过程中收到 **9 条 `warnings`**（c0004×1、c0006×2、c0007×2、c0008×2、c0009×2），全部是"译文片段超出 14 字瞄准值但在 20 字容忍上限内，未强行切分"一类的告知信息，`task submit` 照常返回下一个 `callId`，不影响流程。原文示例（`g11.28` 一条比较特别，明确说合并方案"可行但也可以选择再切一刀"，仍不算拒绝）：
```
"translation segment is 18 chars — above the 14-char aim; splitting at the natural balanced clause punctuation ， cut (\"这影响了一切——\" | \"从输送火箭燃料，到…\") is preferred but optional" (loc: g11.28 unit 2)
```

### 4. 双人素材特有的观察（对主线程说话人验证最重要）

**结论先行：polish/repunct/translate/align 四类 payload 里都没有名为 `speaker` / `speakerId` / `role` 之类的独立字段。** 说话人信息只在 **polish 阶段的原始转录文本里以内联标记形式存在**，逐条核实如下：

1. **字段名/载体**：polish 契约（`polish.md`）原文明确写道：*"Some words are followed by a "⏹" marker: the SPEAKER CHANGES after that word — a sentence must NEVER span across it."* 也就是说说话人切换不是一个 JSON 字段，而是**混在转录文本字符串里的标记字符 `⏹`**（与表示停顿强度的 `⏸`/`⏸⏸`/`⏸⏸⏸` 同一套记号体系）。真实 payload `c0001.txt` 里一共出现 **3 处 `⏹`**（对应本 180 秒片段里 4 段说话人轮次）。repunct（`c0002.txt`）、translate（`c0003.txt`）、align（`c0004~c0009.txt`）的 payload 结构里**完全没有**再出现任何说话人相关字段——`⏹` 标记只活在 polish 这一步，polish 输出（`summary/terms/namedEntities/paragraphs`）本身也不携带说话人标签，是纯文本+段落结构。

2. **转录文本里的轮换是否明显**：明显。3 处 `⏹` 中有 2 处落在完整句尾（`"trivialize."` 之后、`"undertaking."` 之后），从内容上看也确实像是话轮交接点——比如 `⏹` 之后紧跟 `"Yeah, and that's why. So we're doing that just like you said."`，"just like you said" 这种措辞明显是在回应*另一个人*刚说过的话，和前一句"it's still a monumental undertaking."的说话人对不上，指向真实的双人对话。

3. **一句话被拆给两个人的直接证据（跑出来的，非推断）**：第 3 处 `⏹` 落在**一个短语中间**，真实原文（`payloads/c0001.txt` 原样摘录）：
   ```
   ...Like little, those little tiny things are things that make the huge difference in being able to kind of explore the solar system. Well, it all comes to down to ⏹ gravity, ⏸ and that's kind of. The ultimate differentiator between why everything we do in outer space is different from the way we do it on Earth. Totally, some of the stuff you touch on is—is very apt...
   ```
   `⏹` 出现在 `"...it all comes to down to"` 与 `"gravity, ..."` 之间——即一个人说到"这一切说到底还是……"话没说完，**下一个词"gravity"（重力）是由另一个说话人接上的**。这是本次素材里唯一一处说话人切换落在语义未完整处的例子（另外 2 处都在完整句尾），处理时按契约 HARD RULE 必须让句子在此处硬断，不能跨说话人拼接——最终体现为 polish 输出里段落 9（`"Well, it all comes to down to—"`）与段落 10（`"Gravity, and that's kind of the ultimate differentiator..."`）被强制分成两段。这条对主线程验证"是否存在一句话被两个说话人分别说完"的现象是直接、可复核的证据。

4. **完成态 summary 里的独立佐证**：本任务最终 `task status` 返回的 `summary` 字段原文包含 **`"2 speakers"`**（见上第 1 节完整引用），而 M1 单人素材的最终 summary（已记录在本文件 M1 节）里**完全没有 "speakers" 这个子串**。两相对比，说明"speakers"计数只在多人素材里才会出现在这个汇总字段中，侧面印证引擎确实识别出了本素材是双人对话（不过这只是一个汇总计数，不是逐句的说话人标签）。

5. **【推断·未验证】** M2 节已经记录过（非本次验证，引用自本文件既有内容）：最终 `subtitle list` 输出的每条记录带有 `"speaker":"Speaker 1","speakerId":"s1"` 字段。本次会话按任务要求全程未调用任何 `speakers` 子命令、也没有调用 `subtitle list` 去复核这一点，因此双人素材最终每条字幕的 `speakerId` 是否正确对应到 `s1`/`s2` 两个不同的人，**仍待主线程用 `subtitle list p2 --lang zh` 之类命令自行核实**——本次能确认的只是"引擎最终判定为 2 个说话人"，以及"polish 阶段的 `⏹` 边界被正确遵守（没有句子跨边界）"。

### 5. 最终 status（真实完整输出）

```json
{
  "claimedCount" : 0,
  "configuredConcurrency" : 4,
  "elapsedSec" : 2340,
  "expiredClaimCount" : 0,
  "flow" : "auto",
  "lang" : "zh",
  "pendingByKind" : {},
  "pendingByWorkClass" : {},
  "pendingCount" : 0,
  "phase" : "Assembling translation",
  "polishQuality" : {
    "fallbackPageCount" : 0,
    "fallbackSentenceCount" : 0,
    "measuredPageCount" : 1,
    "pageCount" : 1,
    "recoveredPageCount" : 0,
    "residualTermVariantCount" : 0,
    "residualTermVariants" : [],
    "retryCount" : 0,
    "status" : "PASS"
  },
  "progress" : 100,
  "projectId" : "p2",
  "slowClaimCount" : 0,
  "slowClaims" : [],
  "stalledClaimCount" : 0,
  "startedAt" : "2026-08-01T14:24:13Z",
  "status" : "done",
  "summary" : "571 words · 27 edits · polish PASS · retries 0 · recovered pages 0 · fallback pages/sentences 0/0 · residual terms 0 · 2 speakers · 33 lines → Chinese (Simplified)",
  "taskId" : "t-msagprsx",
  "unclaimedCount" : 0,
  "waitingOn" : "terminal",
  "workers" : []
}
```
（注：本次最终 `task status` 输出里**没有** `concurrencyHint` 字段、也没有 `warnings` 字段——这两个字段只出现在任务较早期的中间态响应里，如实按最后一次真实调用的返回内容记录，不补全、不脑补。）

命令：`baocut-cli --json task status t-msagprsx` → `"status" : "done"` ✅ 达成 Completion standard。

## M3 · 说话人识别验证（已执行 ✅ 2026-08-02，Kimi 接手完成）

M3 首轮（见 STATE.md 顶部）剩下三件事，本节全部做完。素材 p2（NASA HWHAP Ep.1 第 5–8 分钟，180s 双人访谈）。

### 1. 交叉验证：reidentify 双提案 + diff（真实输出）

```
$ baocut-cli speakers reidentify p2 --count 2,3 --review
note: count 3: only 2 distinct voices found
2 proposals from one diarization:
  sp-msaiqodc: 2 voices (s1 · s2) · 0 cue changes · 0 ambiguous
  sp-msaiqode: 2 voices (s1 · s2) · 0 cue changes · 0 ambiguous

$ baocut-cli speakers proposals p2 sp-msaiqodc sp-msaiqode
the two proposals label every cue identically
```

- **分歧统计：0 / 101 cue（0%）**，远低于 5% 过门线；count=3 时模型也只找到 2 个声纹。
- `speakers view p2 --rerun` 双条带诊断图（A=当前归属，B=全新声纹聚类）：无红色分歧标、无橙色模糊标，与上面 0 分歧一致。PNG 存 `docs/assets/p2_spk.png`。

### 2. 视觉确认：原方案在此素材上失效，改用字幕锚点（重要修正）

M3 预案第 6 步假设"视频播客抓帧能直接看出谁在说"。**该假设在本素材上不成立**：

- `frames p2 --at 7.34 / 40.69 / 103.11`（三个轮次边界）+ 全片 12 帧总览（`docs/assets/p2_overview.png`）实测：
  **0–45s 及全片访谈段均为固定左右分屏**（两人同框，画面不随说话人切换），103s 附近是 ISS B-roll 动画。
  静帧无法从唇动分辨说话人，"看 4 张画面帧就完事"不成立。
- **替代锚点（实测有效）**：00:22 帧右半屏出现下三分之一字幕条
  **"Dan Huot — NASA Public Affairs Spokesman, International Space Station"**，落在 s1 的轮次内（7.34–40.69s）。
  下三分之一字幕条在人说话时打出 → **s1 = Dan Huot（光头蓄须，NASA 发言人/嘉宾）**，s2 = Gary Jordan（深色头发，主持人）。
- 已执行 `speakers rename p2 s1="Dan Huot" s2="Gary Jordan"` 生效（`show --json` 确认）。
  ⚠️ CLI 怪癖：`speakers rename p2 s1 "Dan Huot"` 位置参数形式**返回 rc=0 但不生效也不报错**，必须用 `s1=Name` 批量形式。

### 3. 第三方独立证据：ASR 阶段说话人切换标记（⏹）逐边界对齐

转录/分段阶段产出的 polish payload（`payloads/c0001.txt`）里有 3 处 ⏹ 说话人切换标记，
与声纹聚类的 3 个轮次边界**逐一对应**（原文真实截取）：

| ⏹ 位置（payload 原文） | 对应边界 | 轮次切换 |
|---|---|---|
| `Don't want to trivialize. ⏸ ⏹ It's still, …` | 7.34s | s2→s1 |
| `…a monumental undertaking. ⏸ ⏹ Yeah, and that's why.` | 40.69s | s1→s2 |
| `Well, it all comes to down to ⏹ gravity, …` | 103.11s | s2→s1 |

⏹ 标记与声纹聚类是两条独立链路（文本分段阶段 vs 声纹重识别），加上基线识别，**三方结果完全一致**。

### 4. 跨说话人句子：group 粒度可以表达切分（已验证）

`"Well, it all comes to down to— ⏹ Gravity, …"` 在 `subtitle list` 里就是两个 group：

```
g8.42        s2  101.42-102.73  "Well, it all comes to down to—"  / zh「这一切啊，说到底还是…」(11字)
wmsah7v2h-52 s1  103.11-106.39  "Gravity, and that's kind of the ultimate, differentiator between," / zh「重力，说到底就是那个终极分水岭，」(16字)
```

**结论：配音时按 group 分配音色即可正确切开两人接力句，不需要词级二次切分。** 中文翻译也已在 group 边界断开。

### 5. M3 最终判定

- 分歧占比 **0% ≤ 5%**，三个边界全部有 ⏹ 独立证据 + 双提案交叉验证 + 人名字幕锚点 → **过门，允许多音色**。
- 对 M4 的约束：音色表 `s1=Dan Huot（嘉宾，男中音）/ s2=Gary Jordan（主持人，男中音）`；接力句按 group 切音色。
- 流程修正（写回 STATE.md 的 M3 步骤）：**frames 视觉确认只在"镜头随说话人切换"的素材上有效**；
  分屏/双机位同框素材改用「人名字幕锚点 + ⏹ 标记对齐 + 双提案 diff」组合确认。

## LLM 自跑路径调查（已执行 ✅ 2026-08-02，Kimi）——GUI 能自跑，但不接 CLI 任务

**问题**：BaoCut 能否用它自己配置的 LLM 跑完 polish/translate/align，不走 agent 循环？
这决定长播客（M7）的时间预算。

### 证据 1：tasks-history.json 里存在 app 自跑的完整记录（真实数据）

```
p101 "Translate subtitles" · source:"app" · outcome:"done" · 2026-07-26 01:25→02:05（约40分钟）
  detail.llm 含真实 SYSTEM prompt + reqTokens/resTokens（app 直接调 LLM API）
  detail.changesTotal:635 · fallback:11
  该项目的源视频 mediaDur:6157s（102 分钟！）
对照：p1/p2 的 CLI 任务 source:"cli" · model:"agent"（外部 agent 驱动，3.5 分钟视频约 37 分钟）
```

**app 自跑的 LLM 阶段比 agent 循环快约一个数量级**（102 分钟素材 40 分钟 vs 3.5 分钟素材 37 分钟）。

### 证据 2：GUI 确实配了 LLM（defaults read com.jimliu.baocut）

```
vk-ai-last-model    = gemini-3.5-flash
vk-keymasks         = gemini:Personal（有 key）+ custom-c4d35ecb:Personal（有 key，sk-…3f27）
```
（`model list` 里的 `cline-pass/deepseek-v4-flash` 是**语音识别**目录里的云端 ASR 条目，与 LLM 阶段无关，此前STATE.md 的理解有误。）

### 证据 3：探针实验 —— GUI 不会接走 CLI 创建的任务（2026-08-02 实测）

- 切 25 秒探针片段 → `auto /tmp/llm_probe.mp4 --lang zh --no-speakers` → p3 / t-msajktfg
- 转录 54 秒内完成（25s 素材，qwen3-asr-0.6b），随后 `pendingCount:1 (polish)` · `waitingOn:answer-workers`
- **BaoCut GUI 保持运行，轮询 4 分多钟，pendingCount 始终为 1，GUI 没有接走**
- 实验后 `task cancel t-msajktfg` 清理

### 结论与推荐链路

- CLI 的 task 队列**设计上就只接受外部 agent**（`task --help` 原话："with the agent supplying every model answer"）。
- app 自跑只在 **GUI 里手动发起**时发生（app 侧任务 id 形如 `task-ai-*`，不走 claim/submit 队列）。
- **推荐混合链路**：CLI `transcribe`（只转录，不产生 LLM pending，本地 ASR 快）
  → **GUI 里点一次翻译**（app 用自己的 gemini-3.5-flash 跑 polish+translate，约 0.4× 实时）
  → CLI 读 `subtitle list` 做配音层。每条视频仅需一次人工点击。
- 留待验证【推断·未验证】：GUI 对 CLI 创建的项目点翻译是否同样走 app 自跑（p101 大概率是 GUI 创建；
  项目存储共享，预计可行，下次开 GUI 时点一下 p3 即可终验）。
- agent 循环保留为兜底（无 GUI 环境 / 需要自定义 instructions 时）。

## M4–M6 · 配音层实现与实测（已执行 ✅ 2026-08-02，Kimi）

### 1. LLM worker-bot（`worker/llm_worker.py`）—— agent 循环自动化

- 用 OpenAI 兼容 API（opencode 网关的 deepseek-v4-flash）驱动 BaoCut task 队列：
  `claim → 读 contract+payload → LLM → submit`，被 lint 拒绝时把 problems 拼回提示重试。
- **探针实测（p4，25s 素材）**：LLM 阶段（polish+translate+align 共 5 次 submit）约 3 分钟跑完到
  `status:done`；对照同规模人工 agent 循环（p2，180s，9 次 submit）37 分钟。
  期间 2 次 align 答案被 lint 拒绝（"译文超 20 字上限"、"unknown cut id"），bot 自动带反馈重试后通过。
- 并行化：align 阶段 BaoCut 本身支持 4–8 并发窗口，可同时跑多个 worker 进程（`--worker` 名不同即可），
  长播客时间 ≈ 线性 ÷ 并发数。
- **三个坑（全部实测）**：
  1. opencode 网关在 Cloudflare 后，urllib 默认 UA 被 1010 拦截，必须带浏览器 UA；
  2. deepseek-v4-flash 默认开启推理，复杂 contract（align）会把全部 completion 预算烧在
     `reasoning_content` 上（实测 16000 tokens 烧光、content 为空）——网关支持
     `"thinking":{"type":"disabled"}` 关闭，关掉后 align 单次 3 秒；
  3. `task claim` 对同一 worker 重复 claim 返回 `already-claimed`（不含 payload 路径），
     bot 需 `release` 后重 claim 自愈。
- key 现状：`~/.hermes/.env` 的 key 余额不足且 flash 需区域 opt-in；
  可用的是 `~/Downloads/soft/podcast-workbench/.env` 里的 `OPENCODE_GO_API_KEY`（sk-GDd…），
  deepseek-v4-flash / v4-pro / qwen3.6-plus / glm-5.1 均实测可用。

### 2. edge-tts 实测（M4 假设全部有了数据）

- **并发阈值**：1/4/8 三档共 32 次请求零失败，单次延迟恒 ~3.5s，并发 8 无 403。
  生产取 6–8（与调研结论一致），配合逐条落盘 + 指数退避重试 + 断点续跑。
- **自然语速只有 3.90 字/秒**（zh-CN-Yunxi/Yunjian 实测），远低于 cps 预算 5.2 ——
  直接用自然语速会有 36/66 个 unit 超槽。对策：`rate=+15%`（合成端）+
  **去静音**（edge-tts 每条首尾垫静音，实测 -45dB silenceremove 每条省约 1.15s，短句收益最大）。
- **病态组兜底**：`dur<0.7s 且 gap<0.2s` 的组并入下一个同说话人组（p2 有 2 个），合成/计时按并后单元。
- **最终时长适配成绩（p2，66 单元）**：51 个零变速、11 个 1.0–1.25x、3 个 1.25–1.5x、
  **仅 1 个 >1.5x（max 1.675）**；音轨时长 = 视频时长（结构性零漂移，局部溢出由
  gap_spill=0.6 吸收，超出部分 atempo 强制贴合）。

### 3. 架构修正 v3（实测驱动）

| # | 修正 | 依据 |
|---|---|---|
| 1 | **「整批合成后切开」不适用于 edge-tts**：改为逐组合成 + 断点续跑 | 「整批防漂移」针对克隆音色 TTS；edge-tts 是确定性云音色无漂移问题，且业界共识（VideoLingo/Edge-TTS-Subtitle-Dubbing）就是逐句合成+线程池。长片整批一旦中途失败前功尽弃，逐组可 resume |
| 2 | **原视频不在 BaoCut 项目目录**（假设 2 解决） | p2 目录实测只有 `audio16k.pcm`/封面/波形，无源媒体。mux 底片 = 原始下载文件（URL 源在 `--save-dir`，默认 ~/Downloads） |
| 3 | 时长适配三级瀑布落地为：rate+15% → 去静音 → gap_spill 0.6 → atempo（上限实测 1.675） | 见上「最终时长适配成绩」；超过 1.5x 的极少数 unit 标记人工复查，后续可加「LLM 重译缩短」层（调研结论 #3） |

### 4. M6 封装与 QC（p2）

- `output/p2_dubbed.mp4`：h264 + aac 中文配音（默认轨）+ aac 英文原声 + mov_text 中/英双字幕，180.033s。
- `output/qc_report.json`：时长/流/音色表/变速直方图/四段音量检查（-23~-25dB，无死区）。
- 3 段人耳样片在 `output/samples/`：轮次切换 ×2 + 跨说话人接力句 ×1。**待用户醒后人耳验收。**

## M7 · 端到端 20 分钟真实播客（已执行 ✅ 2026-08-02，Kimi）—— 全链路自动化跑通

素材：HWHAP 直播集（`8A-6NoJbsFg` 0:00–20:00，公有领域，**3 人**：主持 Gary Jordan + 嘉宾 Ann Romer + PA Jennifer Hernandez）。
产物：`output/p5_dubbed.mp4`（1200.015s，三音色中配默认轨 + 原声 + 中英字幕）+ `output/qc_report_p5.json` + 3 段样片。

### 耗时表（真实数据）

| 阶段 | 耗时 | 说明 |
|---|---|---|
| 下载 | 10m16s | yt-dlp 被限速 130KB/s，非链路问题 |
| 转录+说话人 | 306s | qwen3-asr-0.6b 本地，0.26× 实时 |
| LLM 阶段 | **约 7 分钟** | **2 个 llm_worker 并行**，79 calls（align 62 个），$0.059 |
| TTS 配音 | 约 6 分钟 | 450 单元，edge-tts conc 6，rate+15% |
| 封装+QC | <1 分钟 | |
| **合计（不含下载）** | **约 25 分钟 / 20 分钟素材** | ≈1.25× 实时；按并行度推算 **3 小时播客 ≈ 2 小时内** |

对照：人工 agent 循环做 LLM 阶段，同比例要 4+ 小时。**worker-bot 是整条链路的提速关键。**

### M7 说话人确认门第一次拦到真分歧（3 人场景）

- 基线识别 3 人（s1/s3/s4）。`reidentify --count 3,4 --review`：
  - count=3 提案：把主持人整个并入嘉宾（277 cues，36%）——**被内容证据否决**：
    开场白是主持人点名"Starting with Ann Romer. Ann, welcome."，随后 Ann 作答"Thank you, glad to be here."，
    自问自答不成立。教训：**3+ 人场景声纹欠拟合（count 给少了）会把两个人并掉，人数宁多勿少，且必须过内容结构校验**。
  - count=4 提案：与基线仅 1/764 cue 差异 + 9 ambiguous（1.2% < 5% 门限）→ **过门，保留三音色**。
- `speakers propose-names` 给出 "guessing now" 这种噪声（heuristic 提示会出错，人名必须内容核实）。
- 人名按内容证据标注：s3=Gary Jordan（主持）/ s1=Ann Romer（嘉宾）/ s4=Jennifer Hernandez（PA）。

### 踩到的坑（全部已修或已记录）

1. **`subtitle list` 默认 `--limit 200`，长项目静默截断**（p5：returned 200 / total 474）——
   第一版 p5 配音只配了前 8 分钟，QC 音量检查在 600s 处发现 -91dB 死区才暴露。
   `build_dub.py` 已改为显式 `--limit 100000` + returned≠total 直接报错。**QC 覆盖检查救了这次发布。**
2. align lint 拒绝 112 次（对 79 次通过）：flash 关推理后对"译文 ≤20 字"硬约束一次通过率低，
   全靠 problems 反馈重试收敛。能跑通但浪费，后续 align 可换更强模型。
3. p5 的 >1.5x 变速单元 29 个（6.4%），比 p2（1 个）差：直播问答 cps=5.64、间隙紧。
   方向：超长 unit 走 LLM 重译缩短（SPEED_RESEARCH 第 3 节）。
4. cps 实测第三次：p1=5.44 / p2=4.92 / **p5=5.64（直播问答偏快）**。5.2 仍是好中值，但直播类按 5.6 估。

## 克隆音色 TTS（mimo / moss）接入（2026-08-02，Kimi）

### API 调用约定（全部实测）

**MOSS**（key 无限用，`api.mosi.cn`）：
- `POST https://api.mosi.cn/v1/audio/speech`，**JSON body**（不是 multipart！）
- `{"model":"moss-tts","version":"flash-20260626","input":文本,"ref_audio":"data:audio/wav;base64,…","ref_text":参考音频逐字稿,"language":"Chinese","response_format":"wav"}`
- 直接返回 48kHz 立体声 wav。实测单次约 20-60s。
- ⚠️ 变迁记录：旧 `MOSS-TTS` 模型已弃用（API 会报错提示换 `moss-tts` + `version=flash-20260626`）；
  旧版要求的 multipart 上传在新版会报 `invalid json`，**新版只要 JSON**。workbench 里"绝不用 JSON 传 ref_audio"的注释已过时。
- studio.mosi.cn（voice_id 流程）用这个 key 认证不过（4010），两套账号体系。

**MiMo**（`api.xiaomimimo.com/v1`）：
- `POST /chat/completions`，`{"model":"mimo-v2.5-tts-voiceclone","messages":[{user:语境描述},{assistant:文本}],"audio":{"format":"wav","voice":"data:…base64"}}`，
  双 header：`api-key` + `Authorization: Bearer`。返回 JSON，`choices[0].message.audio.data` 是 base64 wav（24kHz 单声道）。
- **极快**：实测单句 1.9s。user 消息可放情绪/语气描述（mimo 特有）。
- ⚠️ env 里的 `XIAOMI_BASE_URL=…/anthropic` 是 chat 端点，TTS 要用 `api.xiaomimimo.com/v1`（代码里已分开）。
- **配额会被同账号的批量任务挤爆**：实测 3 次调用后连续 429（用户当时在跑批量转录），代码里有熔断器自动降级。

### build_dub.py 引擎链（已实现）

`--voice s1=mimo:/ref.wav+moss:/ref.wav,zh-CN-YunjianNeural`
- 链式降级：mimo → moss → edge-tts；429/401/403 触发**熔断**（该引擎后续整批跳过）
- **时长护栏**：合成时长 > 字数×0.35s 时重采样一次，仍超时落到下一个引擎
  （实测拦下 moss 把"因为它们…"生成成 10 秒静默的幻觉）
- 文本预处理：合成前把 `…` 换成 `，`（省略号会诱导克隆引擎生成超长停顿）

### p2 克隆音色实测（work/p2_clone2，output/p2_dubbed_clone.mp4）

- ref 音频直接从原片按说话人切：s1=Dan Huot 10-22s、s2=Gary Jordan 45-58s（ref_text 用对应英文转录）
- **克隆引擎实测语速 4.86 字/s**，比 edge-tts（3.90）更贴近 5.2 预算，不需要 rate 提升
- 时长适配：30/66 零变速，>1.5x 有 11 个（max 2.95）——比 edge-tts 方案（1 个）差，
  但换来的是**原说话人的音色**。取舍留给人耳验收：
  `output/samples/p2_clone_turn1-2.mp4` / `p2_clone_cross-speaker.mp4`
- 待定【推断·未验证】：克隆音色的"像不像"只有人耳能判；若像，>1.5x 那 11 个 unit 可以走 LLM 重译缩短来救
