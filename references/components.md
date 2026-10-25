# 组件片段（v4）

所有 class 都在 `assets/base.css` 里。复制片段、换内容；不要另起样式体系，不引外部字体或 CDN。拿不准时，打开输出目录里最近一份用本 skill 做的 `*回顾*.html` 对照。

## 目录

0. 三条全局规则：时间戳、速览分层、颜色
1. 开场 hero
2. 全场流程条 flow
3. 场次区块 part：头部 / 金句 / 讲述顺序 / 问答 / 可信度 / 对你·我的判断 / 原文
4. 各形式专用：访谈 qblock / 散聊 topic / 工作会 decisions
5. 图：loop stairs matrix levers lights island eras trust
6. 串起来看：cmp 横向对比 + cross + reflect
7. 对你：map-me / ideas / memory
8. 页脚、标签

---

## 0. 三条全局规则

**时间戳 `.ts` 会被脚本变成可点按钮**，点了右侧抽屉打开原文并高亮那一轮。

```html
<span class="ts">01:19:13</span>                 <!-- 单个 -->
<span class="ts">14:41–15:20</span>              <!-- 区间：定位到起点 -->
<span class="ts">46:33 / 01:06:34</span>         <!-- 多个：用 / 、 ， 分隔，每个都单独可点 -->
<span class="ts" data-src="b">12:40</span>       <!-- 跨文件引用时指定来源 key -->
```

来源规则：`.ts` 自己的 `data-src` > 所在场次 `details.raw` 的 `data-src` > 第一个有时间的来源。“串起来看”“对你”里引用别的转写时必须写 `data-src`。时间写转写时间，不写现场时间（现场时间放在 `.when` 里当文字）。check 会报超出转写结尾的时间戳。

**速览/完整两层**。顶栏切到“速览”时自动隐藏：场次里的普通 `.card`（讲述顺序、问答、可信度）、“我的判断”、原文按钮、分歧、对照表、话题里的对话、访谈的回答。保留：hero、流程、头部、金句、图、“对你”、cross、ideas、memory。

- 某张卡在速览里也该留着：加 `key`，如 `<div class="card key">`。每场最多一张。
- 任何元素只想在完整版出现：加 `deep`。
- 写的时候自测一句：只看速览，30 秒能说出这场讲了什么吗？说不出就是金句或图题没写好。

**颜色**：场次用 `k1`–`k8`（`section.part` 上），对应变量 `--p1`–`--p8`、色标 `pc1`–`pc8`；散聊/茶歇不加 k，用 `--p0` / `pc0`（灰）。超过 8 场循环，并在流程条下写“颜色重复，以编号为准”。

## 1. 开场 hero

`h1` 是贯穿全场的问题，不是会议名。`lines` 挑最值钱的 3 场（轻量版 1–2 格），每格：场次 + 一句主张 + 可选一句原话 `<q>`（不用自己加引号）。`--c` 给顶部色条。

```html
<header class="hero">
  <div class="meta">2026.10.22 · 佛山 · 14:17–约16:59 · 转写约2小时42分 · 3位嘉宾 · 502轮原话</div>
  <h1>AI能做出来，怎样才能有人买、有人用？</h1>
  <p class="lead">邹总从销售管理切入，苏博从企业现场切入，思行从内容获客切入。三种做法都在回答：技术之外，客户为什么付钱。</p>
  <div class="lines">
    <div style="--c:var(--p2)"><small>② 邹总 · 场景与陪跑</small>软件接通之后，还要把业务流程教给AI和使用者。<q>我们把真正的业务语言变成AI能够理解的语言。</q></div>
    <div style="--c:var(--p3)"><small>③ 苏博 · 企业交付</small>复用底座，从一个能验证的经营问题开始。<q>你标准化的是方法论。</q></div>
  </div>
</header>
```

骨架在 hero 后面固定放了“怎么读”图例 `.howto`。转写没有时间戳时，删掉其中“点任意时间”那一项。

## 2. 全场流程条

`flex` = 分钟数（宽度成比例；顶栏进度条自动照抄这组比例）。图例的 `--c` 是左边色条。很短的场次（<6%）色块只写编号。

```html
<section id="flow">
  <div class="eyebrow">全场流程</div>
  <h2>先认人，再看三种生意怎么做</h2>
  <p class="sub">色块宽度按时长比例画，点任一块跳到对应场次。</p>
  <div class="flow">
    <div class="flow-bar">
      <a href="#p1" style="flex:12;background:var(--p0)">①</a>
      <a href="#p2" style="flex:81;background:var(--p2)"><small>12:11</small>② 邹总</a>
      <a class="brk" style="flex:10"><small>15:50</small>茶歇</a>   <!-- 没录音的空档：不带 href，不建区块 -->
    </div>
    <div class="flow-axis"><span>00:00</span><span>01:32:41</span><span>02:41:41</span></div>
    <div class="flow-legend">
      <a href="#p1" style="--c:var(--p0)"><b>① 自我介绍 · 散聊</b><span>00:00–12:11 · 约12分 · 适合回查人脉</span></a>
      <a href="#p2" style="--c:var(--p2)"><b>② 邹总 · 分享</b><span>12:11–01:32:41 · 约81分 · 后半示例更具体</span></a>
    </div>
  </div>
</section>
```

图例最后一句必须是判断：“全场密度最高”“转写质量差”“可以跳过”“后半是问答”。手机上 axis 只显示首尾。

## 3. 场次区块

### 3.1 头部（必有）

```html
<section id="p2" class="part k2" data-type="分享">
  <div class="part-head"><div class="part-no">2</div><div>
    <div class="when"><span class="kind">分享</span>12:11–01:32:41 · 现场约14:29–15:50 · 约81分</div>
    <h2>邹总：先抓销售场景，再把软件、流程和陪跑一起卖</h2>
    <div class="who"><span><b>背景：</b>自述做过阿里渠道管理</span><span><b>商业关系：</b>自称WorkBuddy佛山代理</span></div>
    <p class="gist">主线从“工具要能进入企业”走向“销售数据如何变成下一步行动”。</p>
  </div></div>
  <!-- 顺序：金句 → 统领图 → 讲述顺序 → 局部图 → 问答 → 可信度 → take → 原文 -->
</section>
```

`data-type`：`分享 路演 圆桌 访谈 散聊 饭局 工作会 茶歇`。`h2` = “谁：核心主张”。

### 3.2 金句（分享/路演/圆桌/访谈必有 1 句，紧跟头部）

这是这场的记忆点，速览里最显眼的东西。挑能独立成立、半年后还想引用的那句。

```html
<div class="quote">“我们把真正的业务语言变成AI能够理解的语言。”<cite>邹总 <span class="ts">01:19:13</span> · 顺句，保留原意</cite></div>
```

转写错字可以顺，不改意思；改动大就在 cite 写“转述”。第二句原话放进讲述顺序里，不再单独放 quote。

### 3.3 讲述顺序（竖向时间线，速览隐藏）

```html
<div class="card"><h4>邹总按这个顺序讲</h4><ol class="story">
  <li><p><b>客户要生意结果。</b>产品、流量、销售转化是整条链路。<span class="ts">14:41–15:20</span></p></li>
  <li><p><b>回到销售问题。</b>客户没跟、不会聊、异常难发现。<span class="ts">46:33</span></p></li>
</ol></div>
```

`<b>` 短标题（4–10 字带句号）会单独成一行，后面是数字、例子、原因。5–10 条。

### 3.4 现场问答（左右对照）

```html
<div class="card"><h4>现场追问</h4><div class="qa">
  <div class="m host"><b>发言人7</b><p>这是私人微信的数据吗？<span class="ts">01:10:34</span></p></div>
  <div class="m"><b>邹总</b><p>工作手机后台能看到微信和电话数据。<span class="ts">01:10:40</span></p></div>
</div>
<p class="qa-note">授权边界没有被正面回答。</p></div>
```

提问方用 `m host`（靠左），回答方靠右。没答上、绕开的，用 `.qa-note` 点出来。

### 3.5 可信度

```html
<div class="card"><h4>可信度</h4><ul class="cred">
  <li><span class="tag t-doubt">存疑</span><span>电话数先说46、后台又说43。<span class="ts">01:08:46</span></span></li>
  <li><span class="tag t-fact">较可信</span><span>公开可查的融资信息。</span></li>
  <li><span class="tag t-view">观点</span><span>“模型差距至少一年”不作为事实。<span class="ts">19:40</span></span></li>
</ul></div>
```

每条两个子元素：标签 + 一个 span（时间戳放在 span 里）。

### 3.6 对你 / 我的判断（每场必有，原文之前）

```html
<div class="take">
  <div class="you"><div class="lb">对你<small>结合你的小企业服务</small></div><ul>
    <li><b>轻量软件也可能带出重服务。</b>软件便宜，不代表培训和售后也轻。</li></ul></div>
  <div class="mine"><div class="lb">我的判断<small>不是现场原意</small></div><ul>
    <li>演示的价值在链路，不在“替掉销售”的承诺。<span class="tag t-inf">推论</span></li></ul></div>
</div>
```

各 2–3 条；“我的判断”每条以 `推论` 结尾。速览只留“对你”。

### 3.7 原文（每场一个，放最后，照旧写 details）

```html
<details class="raw" data-src="a" data-from="12:11" data-to="01:32:40" data-main="邹总（AI培训讲师）">
  <summary>展开邹总分享的转写原文<small>12:11–01:32:40</small></summary><div class="raw-body"></div></details>
```

脚本会把它换成“查看这一段原文”按钮，点开是右侧抽屉（含全场原文、搜索、按段跳转）；页脚自动加“打开全文原话”。**不要手写按钮或抽屉**。`data-main` 必须和 raw-data 里的名字一致（用了 alias 就写别名），多人用 `|`。段名取 `part-no` + h2 冒号前的部分，所以 h2 冒号前要短。

## 4. 各形式专用

### 4.1 访谈 qblock（代替讲述顺序；速览只留问题）

```html
<div class="card"><h4>按提问顺序</h4>
  <div class="qblock">
    <div class="q"><span class="no">Q1</span>你们第一批客户是怎么来的？<span class="ts">03:12</span></div>
    <div class="a"><p>回答要点……</p><ul><li>细节、例子、数字</li></ul></div>
  </div>
</div>
```

### 4.2 散聊 / 饭局 topic（速览只留标题和参与人）

```html
<div class="topic"><h3>物业客服的具体需求</h3>
  <div class="meta">10:06–11:28、13:40–14:02 · <span class="spk">苏博</span><span class="spk">小林</span></div>
  <div class="qa"><div class="m"><b>苏博</b><p>群消息多，客服听不过来……<span class="ts">10:51</span></p></div></div>
</div>
```

### 4.3 工作会 decisions

```html
<div class="fig"><div class="fig-title">会上定下的事<small>照会上原话记录，不是建议</small></div>
  <div style="overflow-x:auto"><table class="decisions">
    <tr><th>定了什么</th><th>谁跟进</th><th>时间</th><th>出处</th></tr>
    <tr><td>下一版先砍掉报表模块</td><td>阿杰</td><td>周五前</td><td><span class="ts">12:40</span></td></tr>
    <tr><td>定价</td><td colspan="2" class="open">还没定：两种方案，下次再议</td><td><span class="ts">31:05</span></td></tr>
  </table></div></div>
```

## 5. 图

外壳统一，编号“图 场次-序号”，small 写出处时间（可点）和“按讲述整理 / 点数是我的估计”。

```html
<div class="fig"><div class="fig-title">图 2-1 · 一句话说清图在讲什么<small><span class="ts">46:33 / 01:06:34</span> 根据讲述整理</small></div>
  <!-- 图本体 -->
</div>
```

| 内容结构 | 组件 |
|---|---|
| 流程、闭环 | `loop` |
| 阶段、等级、一关关往上 | `stairs`（3–5 级自动分列） |
| 选项 × 维度比较 | `matrix` |
| 3–4 个并列要素 | `levers`（固定 4 列） |
| 2–3 类分类 | `lights`（固定 3 列）+ 可选 `cost` 三格 |
| 现状 → 做法 → 结果 | `island` |
| 时间演进 | `eras` |
| 问—问—结论 | `trust`（2–4 格） |
| 需求/判断被推翻、改了几次 | `eras`（每格写“以为是… → 其实是…”，最后一格 `now`） |

**loop**（`.c.hi` 高亮讲者自己的位置或关键一步；`loop-back` 的 `data-l` 是左侧小标签，默认“循环”）：

```html
<div class="loop"><div class="c"><b>过程数据</b><span>工作手机／CRM</span></div><div class="ar">→</div>
  <div class="c hi"><b>AI输出</b><span>重点名单、话术</span></div><div class="ar">→</div>
  <div class="c"><b>管理者验收</b><span>判断、分派</span></div></div>
<div class="loop-back" data-l="前提">效果取决于数据与管理口径</div>
```

**stairs**：

```html
<div class="stairs">
  <div class="step"><span class="g">第 1 关</span><h4>卖什么、卖给谁</h4><p class="pain">做了什么</p><p class="fix"><b>撞墙：</b>遇到什么<span class="ts">09:54</span></p></div>
</div>
<div class="stairs-axis"><span>卖时间</span><span>→</span><span>卖产品</span></div>
<div class="selfq"><div><b>自检题 ①</b>……</div></div>   <!-- 可选 -->
```

**matrix**（`td.hi` 标重点格；外层 overflow 不能省）：

```html
<div style="overflow-x:auto"><table class="matrix">
  <tr><th>案例</th><th>原来的问题</th><th>正在做的</th><th>验证</th></tr>
  <tr><td>物业</td><td>投标定价难统一</td><td class="hi">成本／定价测算</td><td class="note">无原始数据 <span class="tag t-doubt">存疑</span></td></tr>
</table></div>
```

点数格：`<span class="dots"><i class="on"></i><i></i><i></i></span> 低`。

**levers**：

```html
<div class="levers"><div class="lev"><span class="ic">质量</span><h4>能验收</h4><p>有客资意向。</p><div class="eq">不只看播放</div></div></div>
```

**lights**：

```html
<div class="lights"><div class="light" style="--c:var(--p3)"><div class="lb">A 类 · 教练</div><h4>个人主播</h4><p>说明</p></div></div>
<div class="cost"><div><b>原理</b>…</div><div><b>收费</b>…</div><div><b>现状</b>…</div></div>
```

**island**（中间列 96px，≤10 字）：

```html
<div class="island">
  <div class="isl-col"><div class="s">CRM / ERP / OA<small>系统都有</small></div></div>
  <div class="isl-mid"><div class="bot">Agent</div>一句话</div>
  <div class="isl-col out"><div class="s">数据自动汇总</div></div>
</div>
```

**eras**：

```html
<div class="eras">
  <div class="era"><span class="y">第一次</span><h4>以为要接系统</h4><p>客户说……<span class="ts">01:35:02</span></p></div>
  <div class="era now"><span class="y">最后</span><h4>其实要解释亏损</h4><p>……</p></div>
</div>
```

**trust**：

```html
<div class="trust">
  <div class="tq"><b>问 1</b>问题<br><span class="sub">现场：回答</span></div>
  <div class="ta"><b>结论</b>① …<br>② …</div>
</div>
```

都不合适时在成品 `<style>` 末尾追加少量样式，复用 `--p* --line --paper` 变量和 `.fig` 外框，补 `@media (max-width:640px)` 单列写法。

## 6. 串起来看

≥3 场有可比的讲者时，先放 `cmp` 横向对比表（表头色点 = 场次色），再放 2–3 张 cross 卡，最后是分歧。

```html
<section id="cross">
  <div class="eyebrow">串起来看</div>
  <h2>三种做法，同一张表上对比</h2>
  <p class="sub">维度是复盘者归纳的，格内内容取自各场。</p>
  <div class="fig"><div style="overflow-x:auto"><table class="cmp">
    <tr><th>维度</th><th><span style="background:var(--p2)"></span>② 邹总</th><th><span style="background:var(--p3)"></span>③ 苏博</th></tr>
    <tr><td>切入场景</td><td>销售管理</td><td>企业现场</td></tr>
    <tr><td>证据强度</td><td>口述 <span class="tag t-doubt">存疑</span></td><td>缺上线数据</td></tr>
  </table></div></div>
  <div class="cross">
    <div class="card"><h3>工具之后，还缺业务语言</h3>
      <div class="chips"><a href="#p2"><span class="pc2">② 经验变技能</span></a><a href="#p3"><span class="pc3">③ 经营问题</span></a></div>
      <p class="sub">②怎么说；③怎么说。</p></div>
  </div>
  <div class="reflect"><h3>现场没有结论的分歧</h3>
    <ul><li><b>提效要落到哪里？</b>邹总偏老板人效；苏博偏员工减负。</li></ul></div>
</section>
```

对比表维度 3–6 行，最后一行建议是“证据强度”。只有一场时整节省略（init --light 已删）。

## 7. 对你

```html
<section id="me">
  <div class="eyebrow">回到你</div>
  <h2>把“会做AI”变成能说明白的价值</h2>
  <p class="sub">右侧都是推论 <span class="tag t-inf">推论</span></p>
  <div class="map-me"><div class="row h"><div>主题</div><div>现场说了什么</div><div></div><div>放到你身上</div></div>
    <div class="row"><div class="th">案例怎么讲<div class="chips"><span class="pc3">③</span><span class="pc4">④</span></div></div>
      <div class="said">技术问题要翻成经营损耗。</div><div class="ar">→</div><div class="me">你手上的案例按“原来怎么做、改后怎么用”讲。</div></div></div>
  <h3 style="margin-top:28px">你可以试的事</h3>
  <div class="ideas"><div class="idea"><div class="k">表达实验</div><h4>同一个案例，换一个开头</h4><p>怎么试、观察什么</p><div class="from">来自 ③、④</div></div></div>
  <div class="memory"><h3>如果只记三句</h3><ol>
    <li><div><b>“你标准化的是方法论。”</b><span>苏博 01:41:16。为什么对你有用。</span></div></li>
  </ol></div>
</section>
```

**分享版**（`init --audience share`）：eyebrow 写“带走什么”，h2 写给一群读者；map-me 表头改成 `<div>适合谁</div><div>现场说了什么</div><div></div><div>可以怎么用</div>`，每行第一列写角色（创业者 / 做销售的 / 做内容的），不写“你”；场内 take 的两个 `.lb` 改成“可借鉴”“复盘者判断”。详见 audience.md。

`memory` 的 `<li>` 里必须有那层 `<div>`，否则正文掉进 40px 序号列（真实 bug）。

## 8. 页脚、标签

```html
来源：22号佛山ai沙龙嘉宾分享_实时转写(1).md（2026-10-22 14:17，“a”）。现场时间按转写开始时间加时间戳推算。转写由 AI 生成，人名和数字可能有误。
```

只填文字替换 `<!--FOOTER-->`；“打开全文原话”链接由脚本追加。

| class | 文字 | 用在 |
|---|---|---|
| `tag t-fact` | 较可信 / 可查 | 多处印证或公开可查 |
| `tag t-view` | 观点 / 愿景 / 经验 | 讲者个人判断、目标、经验 |
| `tag t-doubt` | 存疑 | 口径不清、前后矛盾、听不清的数字人名 |
| `tag t-inf` | 推论 | 复盘者的判断，只用在“我的判断 / 复盘者判断”和“对你 / 怎么用” |
| `kind` | 分享 / 访谈 … | `.when` 开头的形式标签 |
