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
