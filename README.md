# meeting-review-html · 会议复盘 HTML + Markdown

把交流会、分享、沙龙、访谈、饭局、工作会的**录音或转写稿**，同时整理成一份单文件 HTML 复盘页和一份纯文字 Markdown 归档稿：

- 按真实时间一场一块，每场一句金句、一张结构图、讲述顺序、问答、可信度
- 右上角“速览 / 完整”：30 秒看结论，3 分钟看逻辑
- 页面上每个时间戳都能点开，右侧弹出原文并定位到那一句，还能搜索
- 每场都有“对你 / 我的判断”（分享版是“可借鉴 / 复盘者判断”）
- 手机、深色模式可用；单个 HTML 文件，离线能打开、能直接发人
- 默认同时交付同目录、同名的 `.html` 和 `.md`；Markdown 可直接导入个人知识库，保留完整复盘内容和来源时间，结构图转成文字逻辑链

## 安装

### 直接发给你的 AI Agent

复制下面这段，发给支持 Skill 的 AI Agent：

```text
请帮我安装这个录音复盘 Skill：https://github.com/Renly1994/meeting-review-html
先阅读仓库里的 README.md 和 SKILL.md，下载完整仓库，并按照当前 AI Agent 的规范安装到全局 Skills 目录。
请按说明检查运行依赖。我会优先提供录音 App 导出的转写稿；直接使用转写稿时，无需安装本地语音转写模型。
```

### 手动安装

把整个 `meeting-review-html` 文件夹放进你的 agent 的 skills 目录，例如：

- Claude Code：`~/.claude/skills/meeting-review-html/`
- Codex：`~/.codex/skills/meeting-review-html/`
- 其他支持 SKILL.md 的 agent：放进它的 skills 目录

依赖：
- Python 3.10+（必需，脚本只用标准库）
- `pip install playwright && playwright install chromium`（可选，用来自动截图和自测交互；有 Edge / Chrome 也能用）
- [uv](https://docs.astral.sh/uv/)（可选，只有给录音、需要本地转写时才用；首次会下载约 2GB 模型到 `~/asr-models`）

## 第一次用之前（推荐）

复制 `profile.example.md` 为 `profile.md`，填上你是谁、在做什么。“对你”这部分会写得具体得多。不填也行，skill 会在需要时问你三个问题。

## 怎么用

对 agent 说：

- “把这份转写稿做成复盘 HTML：D:\会议\沙龙_转写.md”
- “这是昨天交流会的录音，帮我复盘一下”
- “做一版能发给团队的复盘页”（分享版：不写“对你”，按角色写“可借鉴”，并去掉私聊段原文）

支持的转写格式：飞书妙记、通义听悟、腾讯会议、钉钉导出，`[时间] 说话人：正文`，srt/vtt 字幕，纯文本，以及录音（m4a/mp3/wav，本地转写，不上传）。

例如，一次复盘会同时得到 `佛山AI沙龙回顾_20261022.html` 和 `佛山AI沙龙回顾_20261022.md`。Markdown 不依赖网页、图片或折叠控件，包含完整层的事实、问答、原话、可信度和复盘判断；默认不附整份转写原文。改版时两份使用相同版本号，分享版的删减范围也保持一致。

## 分享前注意

页面默认嵌入了转写原文。外发前确认：私聊、饭局段已用 `--redact` 去掉（或 `--no-raw` 整页不放），讲者同意公开，自述数字已标存疑。

## 文件

```
SKILL.md                 agent 读的主说明
profile.example.md       读者画像模板
references/
  components.md          所有组件的 HTML 片段
  forms.md               分享/访谈/散聊/饭局/工作会各怎么写
  audience.md            个人版 vs 分享版，“对你”怎么写
  markdown.md            纯文字归档稿的内容、结构和核对规则
assets/                  样式、骨架、交互脚本（不用改）
scripts/review_tool.py   inspect / init / check
scripts/transcribe.py    录音 → 转写稿（本地 FunASR）
```
