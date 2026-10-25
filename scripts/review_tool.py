"""会议复盘 HTML 的辅助脚本。

子命令：
  inspect  读转写稿，打印标题、开始时间、发言人统计和发言轮次，用来切分场次
  init     用骨架 + 样式 + 交互脚本 + 转写原文生成一个待填充的 HTML
  check    静态检查 + 时间戳越界 + 交互自测（点时间戳开原文、搜索、速览）+ 宽窄屏截图 + 挤压文字检测

支持的转写稿（自动识别，取识别出轮次最多的一种）：
  A  **发言人2  00:01**        飞书妙记、通义听悟导出的 md；transcribe.py 的输出也是这种
  B  发言人2  00:01           同上但没有加粗；腾讯会议、钉钉等“说话人 + 时间”单独一行
  C  00:01  发言人2           时间在前
  D  [00:01] 发言人2：正文     时间、说话人、正文在同一行
  E  发言人2：正文             没有时间戳（微信转文字、手工整理）
  F  .srt / .vtt 字幕          有时间，没有说话人
  G  纯文本                    按段落切，没有时间也没有说话人
录音文件（m4a/mp3/wav…）先用 transcribe.py 转成 A 格式。
"""
import argparse
import html.parser
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, '..', 'assets')
NOISE = re.compile(r'^.*(文档部分内容由\s*AI\s*生成|内容由AI生成).*$', re.M)
AUDIO = ('.m4a', '.mp3', '.wav', '.aac', '.amr', '.flac', '.ogg', '.opus', '.wma', '.mp4', '.mov', '.webm')
TS = r'(\d{1,2}:\d{2}(?::\d{2})?)(?:[.,]\d{1,3})?'
SP = r'([^\s:：\[\]()（）|*#>][^:：\[\]|*#>]{0,23}?)'
# (名字, 正则, 每行的分组含义)；h = 这一行只是轮次头，正文在下面几行
HEADS = [
    ('A', re.compile(rf'^\*\*{SP}\s+{TS}\*\*\s*$'), 'sp t h'),
    ('B', re.compile(rf'^{SP}\s{{1,}}{TS}\s*$'), 'sp t h'),
    ('C', re.compile(rf'^{TS}\s+{SP}\s*$'), 't sp h'),
    ('D', re.compile(rf'^[\[(（]?{TS}[\])）]?\s*{SP}\s*[:：]\s*(.+)$'), 't sp x'),
    ('E', re.compile(rf'^{SP}\s*[:：]\s*(.+)$'), 'sp x'),
]


def sec(t):
    if not t:
        return -1
    s = 0
    for p in t.split(':'):
        s = s * 60 + int(p)
    return s


def norm_t(t):
    """统一成 MM:SS / HH:MM:SS，去掉 00: 开头的小时位"""
    p = t.split(':')
    if len(p) == 3 and p[0] in ('0', '00'):
        p = p[1:]
    return ':'.join(x.zfill(2) for x in p)


def clean(x):
    x = NOISE.sub('', x)
    x = re.sub(r'\*+', '', x).strip()
    return re.sub(r'\n{2,}', '\n', x)


def parse_lines(lines, name, rx, fields):
    turns, cur = [], None
    for line in lines:
        m = rx.match(line.strip())
        if m:
            g = dict(zip(fields.split(), m.groups()))
            cur = {'t': norm_t(g['t']) if g.get('t') else '', 'sp': g['sp'].strip(), 'x': g.get('x', '')}
            turns.append(cur)
        elif cur is not None and line.strip():
            cur['x'] += ('\n' if cur['x'] else '') + line.strip()
    return turns


def parse_srt(text):
    turns = []
    for blk in re.split(r'\n\s*\n', text.replace('\r', '')):
        m = re.search(rf'{TS}\s*-->\s*{TS}', blk)
        if not m:
            continue
        x = ' '.join(l.strip() for l in blk[m.end():].splitlines() if l.strip())
        sp = '未标注'
        mm = re.match(r'^<v\s+([^>]+)>(.*)$', x) or re.match(rf'^{SP}\s*[:：]\s*(.+)$', x)
        if mm:
            sp, x = mm.group(1).strip(), mm.group(2).strip()
        if x:
            turns.append({'t': norm_t(m.group(1)), 'sp': sp, 'x': x})
    return turns


def parse(path, alias=None):
    if path.lower().endswith(AUDIO):
        sys.exit(f'{path} 是录音文件。先转写：uv run --script scripts/transcribe.py "{path}" --out "xxx_转写.md"')
    text = open(path, encoding='utf-8-sig', errors='replace').read().replace('\r\n', '\n')
    head = text[:600]
    title = (re.search(r'^>?\s*#+\s*\**(.+?)\**\s*$', head, re.M) or re.search(r'^\s*(\S.{0,40})$', head, re.M))
    start = re.search(r'(\d{4}[-/.年]\d{1,2}[-/.月]\d{1,2})日?\D{0,6}?(\d{1,2}:\d{2})', head)
    lines = text.split('\n')
    body = [l for l in lines if not l.lstrip().startswith('>')]
    nonempty = max(1, sum(1 for l in body if l.strip()))
    if path.lower().endswith(('.srt', '.vtt')):
        fmt_name, turns = 'F', parse_srt(text)
    else:
        best = ('G', [])
        for name, rx, fields in HEADS:
            ts = parse_lines(body, name, rx, fields)
            # E（说话人：正文）容易误判普通的“原因：xxx”，要求说话人重复出现、且覆盖大部分行
            if name == 'E':
                names = {}
                for e in ts:
                    names[e['sp']] = names.get(e['sp'], 0) + 1
                if len(ts) < 0.4 * nonempty or sum(1 for v in names.values() if v >= 2) < 2:
                    continue
            if len(ts) >= 3 and len(ts) > len(best[1]):
                best = (name, ts)
        fmt_name, turns = best
        if not turns:
            paras = [p.strip() for p in re.split(r'\n\s*\n', '\n'.join(body)) if p.strip()]
            turns = [{'t': '', 'sp': '未标注', 'x': p} for p in paras[1:] or paras]
    out = []
    for e in turns:
        x = clean(e['x'])
        if x:
            out.append({'t': e['t'], 'sp': (alias or {}).get(e['sp'], e['sp']), 'x': x})
    if not out:
        sys.exit(f'没有读出任何内容：{path}')
    meta = {}
    if os.path.exists(path + '.meta.json'):
        meta = json.load(open(path + '.meta.json', encoding='utf-8'))
    return {
        'title': title.group(1).strip('* ') if title else os.path.basename(path),
        'date': re.sub(r'[/.年月]', '-', start.group(1)) if start else '',
        'start': start.group(2) if start else '',
        'format': fmt_name,
        'timed': any(e['t'] for e in out),
        'turns': out,
        'meta': meta,
    }


def parse_alias(items, keys):
    """'原名=显示名' 对所有文件生效；'b:原名=显示名' 只对 key 为 b 的文件生效（同一编号在不同文件里是不同的人时用）。"""
    g, per = {}, {k: {} for k in keys}
    for a in items or []:
        k, _, v = a.partition('=')
        k = k.strip()
        src, sep, name = k.partition(':')
        if sep and src in per:
            per[src][name] = v.strip()
        else:
            g[k] = v.strip()
    return {k: {**g, **per[k]} for k in keys}


def windows(ts, size):
    """按时间窗统计：每窗谁说得最多、字数。散聊、饭局的窗口通常是多人平均、字数低；分享是一人独大。"""
    wins = {}
    for e in ts:
        w = sec(e['t']) // size
        d = wins.setdefault(w, {})
        d[e['sp']] = d.get(e['sp'], 0) + len(e['x'])
    print(f'时间窗（每 {size // 60} 分钟：总字数 / 前三个说话人占比）：')
    for w in sorted(wins):
        d = wins[w]
        tot = sum(d.values())
        top = sorted(d.items(), key=lambda kv: -kv[1])[:3]
        a = w * size
        lab = f'{a // 3600:02d}:{a % 3600 // 60:02d}'
        print(f'  {lab}  {tot:>5} 字  ' + '  '.join(f'{sp} {v * 100 // tot}%' for sp, v in top))


def cmd_inspect(a):
    for path in a.files:
        d = parse(path)
        ts = d['turns']
        timed = d['timed']
        print(f'\n=== {d["title"]} | {d["date"]} {d["start"]} | 格式 {d["format"]} | {len(ts)} 轮 | '
              + (f'末尾 {ts[-1]["t"]}' if timed else '没有时间戳'))
        if not timed:
            print('提醒：没有时间戳。页面里不放原文折叠，要点也不标时间；按内容切段。')
        if d['meta']:
            m = d['meta']
            print(f'录音转写：时长 {m.get("duration")}，{m.get("speakers")} 个说话人，开始时间 {m.get("start")}'
                  + ('（估算）' if m.get('start_estimated') else ''))
            for g in m.get('long_silences', []):
                print(f'  长静音 {g["from"]}–{g["to"]}（{g["sec"]} 秒）：常是茶歇、换场、转去饭局')
        stat = {}
        for e in ts:
            s = stat.setdefault(e['sp'], [0, 0, e['t'], e['t']])
            s[0] += 1
            s[1] += len(e['x'])
            s[3] = e['t']
        print('发言人统计（轮数 / 字数 / 首次 / 最后）：')
        for sp, (n, c, f, l) in sorted(stat.items(), key=lambda kv: -kv[1][1]):
            print(f'  {sp:<16} {n:>4} 轮 {c:>7} 字  {f} – {l}')
        # 连续同一发言人合并成一段，便于找场次边界
        print(f'发言段（合并连续同一发言人，只列 ≥{a.min_chars} 字的段）：')
        run = None
        for e in ts + [None]:
            if run and (e is None or e['sp'] != run['sp']):
                if run['n'] >= a.min_chars:
                    print(f'  {run["t"]:>8}  {run["sp"]:<14} {run["n"]:>5} 字  {run["head"]}')
                run = None
            if e is None:
                break
            if run is None:
                run = {'t': e['t'], 'sp': e['sp'], 'n': 0, 'head': e['x'][:40].replace('\n', ' ')}
            run['n'] += len(e['x'])
        if timed:
            windows(ts, a.window * 60)


def cmd_init(a):
    if os.path.exists(a.out) and not a.force:
        sys.exit(f'{a.out} 已存在。换一个文件名（比如加 _v2），或者确认后加 --force。')
    srcs = [item.partition('=')[::2] for item in a.src]
    alias = parse_alias(a.alias, [k for k, _ in srcs])
    raw, untimed = {}, []
    cuts = {}
    for item in a.redact or []:
        k, _, rng = item.partition(':')
        f, _, t = rng.partition('-')
        if not (k and f and t):
            sys.exit(f'--redact 写法是 key:起-止，例如 a:01:30:00-02:10:00，现在是 {item}')
        cuts.setdefault(k, []).append((sec(f), sec(t)))
    for key, path in srcs:
        d = parse(path, alias[key])
        turns = d['turns']
        if key in cuts:
            n0 = len(turns)
            turns = [e for e in turns if not (e['t'] and any(f <= sec(e['t']) <= t for f, t in cuts[key]))]
            print(f'{key}：按 --redact 去掉 {n0 - len(turns)} 轮原文（这些时间段不要再写 details.raw）')
        raw[key] = [] if a.no_raw else turns
        if not d['timed']:
            untimed.append(key)
    sk = open(os.path.join(ASSETS, 'skeleton.html'), encoding='utf-8').read()
    share = a.audience == 'share'
    sk = sk.replace('{{ME_LABEL}}', '怎么用' if share else '对你')
    if share:
        sk = sk.replace('<body>', '<body data-audience="share">', 1)
    if a.no_raw or all(not any(e['t'] for e in v) for v in raw.values()):
        sk = re.sub(r'<span class="if-raw">.*?</span>', '', sk)
    if a.no_raw:
        sk = sk.replace('<body', '<body data-raw="none"', 1)
    if a.light:
        # 轻量版：没有全场流程和串起来看
        sk = (sk.replace('<body>', '<body data-mode="light">').replace('<a href="#flow">全场</a>', '')
              .replace('<a href="#cross">串起来看</a>', '').replace('<!--FLOW-->' + chr(10), '').replace('<!--CROSS-->' + chr(10), ''))
    css = open(os.path.join(ASSETS, 'base.css'), encoding='utf-8').read()
    js = open(os.path.join(ASSETS, 'app.js'), encoding='utf-8').read()
    # 原文放进 <script>，必须转义 </ 防止提前闭合
    data = json.dumps(raw, ensure_ascii=False).replace('</', '<\\/')
    s = (sk.replace('/*BASE_CSS*/', css).replace('/*APP_JS*/', js).replace('/*RAW*/', data)
         .replace('{{TITLE}}', a.title).replace('{{SHORT_TITLE}}', a.short_title or a.title))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, 'w', encoding='utf-8').write(s)
    print(f'已生成 {a.out}，原文：' + '，'.join(f'{k}={len(v)} 轮' for k, v in raw.items()))
    left = re.findall(r'<!--[A-Z_]+-->', s)
    print('下一步：把 ' + ' '.join(dict.fromkeys(left)) + ' 逐个替换成内容。')
    if a.no_raw:
        print('--no-raw：页面不含原文。不要写 details.raw；时间戳照写，显示为普通文字。')
    if share:
        print('分享版：场内两栏写“可借鉴 / 复盘者判断”，总节写“怎么用”，不要写“对你”。见 references/audience.md')
    if untimed:
        print(f'{"、".join(untimed)} 没有时间戳：这些来源的场次不放原文折叠，要点也不标时间。')


class Balance(html.parser.HTMLParser):
    TRACK = {'div', 'section', 'ul', 'ol', 'li', 'details', 'summary', 'table', 'tr', 'p', 'header', 'a', 'span', 'b'}

    def __init__(self):
        super().__init__()
        self.stack, self.errors, self.ids, self.hrefs = [], [], set(), set()

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if 'id' in d:
            self.ids.add(d['id'])
        if tag == 'a' and (d.get('href') or '').startswith('#'):
            self.hrefs.add(d['href'][1:])
        if tag in self.TRACK:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag not in self.TRACK:
            return
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
        else:
            top = self.stack[-1] if self.stack else None
            self.errors.append(f'第 {self.getpos()[0]} 行 </{tag}> 对不上，当前打开的是 {top}')
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    break


# 展开所有折叠后，找出“长文字被挤进很窄的盒子”和横向溢出。
# 这正是“只记三句”那次的 bug：<li> 是两列 grid，却有三个子元素，正文掉进了 40px 的序号列。
SQUEEZE_JS = r"""() => {
  document.querySelectorAll('details').forEach(d => d.open = true);
  const bad = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode, t = n.textContent.trim();
    if (t.length < 8) continue;
    const el = n.parentElement;
    if (el.closest('script,style,.raw-body,.drawer')) continue;
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.width < 72 && r.height > 64) bad.push(`${el.tagName.toLowerCase()}.${el.className} 宽 ${Math.round(r.width)}px：${t.slice(0, 24)}`);
  }
  document.querySelectorAll('.flow-bar a, .flow-axis span, .chips span').forEach(el => {
    if (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1 && getComputedStyle(el).overflow === 'hidden')
      bad.push(`${el.className || el.tagName.toLowerCase()} 文字被截断：${el.textContent.trim().slice(0, 16)}（缩短文字，或给这块 min-width）`);
  });
  const over = document.documentElement.scrollWidth - window.innerWidth;
  return {bad: [...new Set(bad)].slice(0, 20), over};
}"""


def static_check(s):
    errs, warns = [], []
    for ph in re.findall(r'<!--[A-Z_]+-->|\{\{[A-Z_]+\}\}|/\*(?:RAW|BASE_CSS|APP_JS)\*/', s):
        errs.append(f'占位符没替换：{ph}')
    b = Balance()
    b.feed(re.sub(r'<script.*?</script>|<style.*?</style>', '', s, flags=re.S))
    errs += b.errors[:10]
    for tag, line in b.stack:
        if tag not in ('p', 'li'):  # p/li 允许隐式闭合
            errs.append(f'第 {line} 行 <{tag}> 没有闭合')
    for h in sorted(b.hrefs - b.ids):
        errs.append(f'锚点 #{h} 找不到对应 id')
    m = re.search(r'<script id="raw-data" type="application/json">(.*?)</script>', s, re.S)
    raw = {}
    try:
        raw = json.loads(m.group(1)) if m else {}
    except ValueError as e:
        errs.append(f'raw-data 不是合法 JSON：{e}')
    for d in re.finditer(r'<details class="raw"([^>]*)>', s):
        at = dict(re.findall(r'data-(\w+)="([^"]*)"', d.group(1)))
        miss = [k for k in ('src', 'from', 'to', 'main') if k not in at]
        if miss:
            errs.append(f'原文折叠缺少 data-{"/".join(miss)}：{d.group(0)[:80]}')
            continue
        rows = [e for e in raw.get(at['src'], []) if sec(at['from']) <= sec(e['t']) <= sec(at['to'])]
        if not rows:
            errs.append(f'原文折叠 {at["src"]} {at["from"]}–{at["to"]} 取不到任何发言')
        elif not any(e['sp'] in at['main'].split('|') for e in rows):
            errs.append(f'原文折叠 {at["from"]}–{at["to"]} 里没有主讲人“{at["main"]}”，检查 data-main 是否和别名一致')
    if re.search(r'type="checkbox"|localStorage', s):
        errs.append('出现了勾选框或本地存储：复盘页不做待办')
    if re.search(r'这周(就)?做|待办|To-?do', s, re.I):
        warns.append('出现“这周做 / 待办 / Todo”字样：确认不是行动清单')
    light = 'data-mode="light"' in s
    parts = re.findall(r'<section id="([^"]+)" class="part[^"]*"(?: data-type="([^"]*)")?>(.*?)</section>', s, re.S)
    if not parts:
        errs.append('没有 class="part" 的场次区块')
    need = {'访谈': ('class="qa"', '访谈段应该用一问一答（.qa）'),
            '散聊': ('class="topic"', '散聊段应该按话题切（.topic）'),
            '饭局': ('class="topic"', '饭局段应该按话题切（.topic）'),
            '工作会': ('class="decisions"', '工作会议段应该有“会上定下的事”（.decisions）')}
    for pid, typ, body in parts:
        if typ in need and need[typ][0] not in body:
            warns.append(f'#{pid}（{typ}）：{need[typ][1]}')
        if 'class="part-head"' not in body:
            errs.append(f'#{pid} 缺少 part-head')
        if 'class="take"' not in body:
            errs.append(f'#{pid} 缺少 take 两栏（对你 / 我的判断，分享版是可借鉴 / 复盘者判断）')
        if 'class="ts"' not in body and 'details class="raw"' in body:
            warns.append(f'#{pid} 一个时间戳都没有')
        mine = re.search(r'<div class="mine">(.*?)</ul>', body, re.S)
        if mine:
            for li in re.findall(r'<li>(.*?)</li>', mine.group(1), re.S):
                if 't-inf' not in li:
                    warns.append(f'#{pid} “我的判断”有一条没标“推论”：{re.sub("<[^>]+>", "", li)[:30]}')
    # 时间戳越界：每个时间点都要能在对应来源里定位到原话（来源取法与 app.js 一致）
    last_t = {k: max([sec(e['t']) for e in v if e['t']] or [-1]) for k, v in raw.items()}
    timed = [k for k, v in last_t.items() if v >= 0]
    def ts_check(chunk, default, where):
        for m in re.finditer(r'<span class="ts"(?: data-src="([^"]*)")?>(.*?)</span>', chunk, re.S):
            src = m.group(1) or default
            if src not in last_t or last_t[src] < 0:
                continue
            for t in re.findall(r'\d{1,2}:\d{2}(?::\d{2})?', m.group(2)):
                if sec(t) > last_t[src] + 30:
                    errs.append(f'{where} 时间戳 {t} 超出来源 {src} 的最后一条（{last_t[src] // 60} 分），点了会定位错：检查是不是写错了来源或时间')
    outside = re.sub(r'<section id="[^"]+" class="part.*?</section>', '', s, flags=re.S)
    ts_check(outside, timed[0] if timed else '', '场次外')
    for pid, typ, body in parts:
        d = re.search(r'<details class="raw"[^>]*data-src="([^"]+)"', body)
        ts_check(body, d.group(1) if d else (timed[0] if timed else ''), f'#{pid}')
        if typ in ('分享', '路演', '圆桌', '访谈', '') and 'class="quote"' not in body:
            warns.append(f'#{pid} 没有原话（.quote）：每场放 1 句记忆点在头部下面')
    subst = [p for p in parts if p[1] not in ('茶歇',)]
    if not light and len(subst) >= 3 and 'class="cmp"' not in s:
        warns.append('3 场以上却没有横向对比表（#cross 里的 table.cmp）：讲法可比时应该加')
    # 完整版：2 场以上要有全场流程，3 场以上要有串起来看；轻量版都可省
    required = ['me']
    if not light and len(parts) >= 2:
        required.append('flow')
    if not light and len(parts) >= 3:
        required.append('cross')
    for sid in required:
        if f'id="{sid}"' not in s:
            errs.append(f'缺少 #{sid} 区块')
    mem = re.search(r'<div class="memory">.*?<ol>(.*?)</ol>', s, re.S)
    n = len(re.findall(r'<li>', mem.group(1))) if mem else 0
    lo, hi = (2, 3) if light else (3, 5)
    if not lo <= n <= hi:
        errs.append(f'“如果只记”应有 {lo}–{hi} 条，现在 {n} 条')
    elif re.search(r'<li>(?!<div>)', mem.group(1)):
        errs.append('“如果只记”的 <li> 里要用 <div> 包住 <b> 和 <span>，否则文字会掉进 40px 的序号列')
    if 'data-audience="share"' in s:
        vis = re.sub(r'<script.*?</script>|<style.*?</style>|<[^>]+>', '', s, flags=re.S)
        for w in ('对你', '放到你身上'):
            if w in vis:
                warns.append(f'分享版里出现“{w}”：分享版写给一群读者，改成“可借鉴 / 怎么用”或具体角色')
    if 'data-raw="none"' in s and '<details class="raw"' in s:
        errs.append('--no-raw 页面里写了 details.raw：没有原文可展开，删掉')
    if 'class="fig"' not in s:
        warns.append('整页没有一张图（.fig）：检查是否有阶段、对比、流程类内容被写成了列表')
    return errs, warns


def raw_has_t(s):
    m = re.search(r'<script id="raw-data" type="application/json">(.*?)</script>', s, re.S)
    try:
        return [any(e.get('t') for e in v) for v in json.loads(m.group(1)).values()] if m else []
    except ValueError:
        return []


def cmd_check(a):
    s = open(a.file, encoding='utf-8').read()
    errs, warns = static_check(s)
    shots = a.shots or os.path.join(os.path.dirname(os.path.abspath(a.file)), '_check')
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sync_playwright = None
        warns.append('没装 playwright，跳过截图：请用其他方式在宽屏和手机宽度各看一遍')
    if sync_playwright and not a.no_shots:
        os.makedirs(shots, exist_ok=True)
        url = 'file:///' + os.path.abspath(a.file).replace('\\', '/')
        with sync_playwright() as p:
            br = None
            for opt in ({'channel': 'msedge'}, {'channel': 'chrome'}, {}):
                try:
                    br = p.chromium.launch(**opt)
                    break
                except Exception:
                    pass
            if br is None:  # 都没有时找系统里的 chromium
                import shutil
                exe = shutil.which('chromium') or shutil.which('chromium-browser') or shutil.which('google-chrome')
                br = p.chromium.launch(executable_path=os.path.realpath(exe))
            for w, tag in ((1100, 'wide'), (390, 'narrow')):
                pg = br.new_page(viewport={'width': w, 'height': 900})
                js_err = []
                pg.on('pageerror', lambda e: js_err.append(str(e)))
                pg.goto(url)
                pg.add_style_tag(content='.topbar{position:static!important}')  # 截图时别让吸顶栏盖住内容
                pg.wait_for_timeout(300)
                r = pg.evaluate(SQUEEZE_JS)
                errs += [f'[{tag}] JS 报错：{e}' for e in js_err]
                errs += [f'[{tag}] 文字被挤进窄列：{x}' for x in r['bad']]
                if r['over'] > 2:
                    errs.append(f'[{tag}] 页面横向溢出 {r["over"]}px（宽表格要包在 overflow-x:auto 里）')
                # 交互自测：点第一个时间戳要打开抽屉并高亮一轮；搜索要能过滤
                if tag == 'wide':
                    n_ts = pg.evaluate("document.querySelectorAll('.tsb:not([data-all])').length")
                    n_span = pg.evaluate("document.querySelectorAll('.ts').length")
                    if n_span and not n_ts and 'data-raw="none"' not in s and any(raw_has_t(s)):
                        errs.append('时间戳没有变成可点按钮：检查 raw-data 是否有时间、app.js 是否报错')
                    if n_ts:
                        pg.click('.tsb:not([data-all])')
                        pg.wait_for_timeout(500)
                        ok = pg.evaluate("document.body.classList.contains('dr') && !!document.querySelector('.de.hit')")
                        if not ok:
                            errs.append('点时间戳后没有打开原文并定位')
                        pg.screenshot(path=os.path.join(shots, 'wide_drawer.png'))
                        word = pg.evaluate("(document.querySelector('.de p')||{textContent:''}).textContent.slice(0,2)")
                        if word:
                            pg.fill('#dq', word)
                            pg.wait_for_timeout(300)
                            if pg.evaluate("document.querySelectorAll('.de:not(.hide)').length") == 0:
                                errs.append('原文搜索没有结果：检查 app.js 的 filt')
                        pg.keyboard.press('Escape')
                        pg.wait_for_timeout(300)
                    # 速览模式整页切片
                    pg.click('.mode button[data-mode="quick"]')
                    pg.wait_for_timeout(200)
                    H = pg.evaluate('document.documentElement.scrollHeight')
                    for j, top in enumerate(range(0, H, 1600)):
                        pg.screenshot(path=os.path.join(shots, f'quick_{j:02d}.png'), full_page=True,
                                      clip={'x': 0, 'y': top, 'width': w, 'height': min(1600, H - top)})
                    pg.click('.mode button[data-mode="full"]')
                    pg.wait_for_timeout(200)
                # 每个区块截一张；太长的按 1600px 切片，方便逐张看清
                for i, el in enumerate(pg.query_selector_all('header.hero, body > .wrap > section')):
                    sid = el.get_attribute('id') or 'hero'
                    box = pg.evaluate('e => { const r = e.getBoundingClientRect(); return [r.left + scrollX, r.top + scrollY, r.width, r.height]; }', el)
                    x, y, bw, bh = box
                    for j, top in enumerate(range(0, int(bh) + 1, 1600)):
                        h = min(1600, bh - top)
                        if h < 20:
                            break
                        pg.screenshot(path=os.path.join(shots, f'{tag}_{i:02d}_{sid}_{j}.png'), full_page=True,
                                      clip={'x': x, 'y': y + top, 'width': bw, 'height': h})
                pg.close()
            br.close()
        print(f'截图在 {shots}（每个区块一组，长区块按 1600px 切片；宽屏 1100 / 手机 390；另有 quick_* 速览模式和 wide_drawer 原文抽屉）。逐张看过再交付，看完删掉这个目录。')
    for e in errs:
        print('错误：' + e)
    for w in warns:
        print('提醒：' + w)
    print('通过' if not errs else f'共 {len(errs)} 个错误')
    sys.exit(1 if errs else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('inspect')
    p.add_argument('files', nargs='+')
    p.add_argument('--min-chars', type=int, default=300, help='发言段字数下限，调小能看到更多插话')
    p.add_argument('--window', type=int, default=10, help='时间窗分钟数，用来看哪里换了形式')
    p = sub.add_parser('init')
    p.add_argument('--src', action='append', required=True, help='key=转写稿路径，可多次；key 用 a、b……')
    p.add_argument('--alias', action='append', help='原名=显示名，对所有文件生效；b:原名=显示名 只对文件 b 生效')
    p.add_argument('--title', required=True)
    p.add_argument('--short-title')
    p.add_argument('--out', required=True)
    p.add_argument('--light', action='store_true', help='轻量版：短对话、单一话题，不要全场流程和串起来看')
    p.add_argument('--audience', choices=['self', 'share'], default='self', help='self=写给读者本人（对你）；share=写给没到场的一群人（可借鉴）')
    p.add_argument('--redact', action='append', help='key:起-止，从嵌入的原文里去掉这段（饭局、私聊），可多次')
    p.add_argument('--no-raw', action='store_true', help='不嵌入任何原文（页面要外发且原文敏感时）')
    p.add_argument('--force', action='store_true')
    p = sub.add_parser('check')
    p.add_argument('file')
    p.add_argument('--shots', help='截图目录，默认是输出文件旁边的 _check/')
    p.add_argument('--no-shots', action='store_true')
    a = ap.parse_args()
    {'inspect': cmd_inspect, 'init': cmd_init, 'check': cmd_check}[a.cmd](a)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    main()
