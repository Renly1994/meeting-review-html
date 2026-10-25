// 会议复盘页交互：时间戳 → 原文抽屉、原文搜索、速览/完整、顶栏进度条与当前章节。内容不需要改这里。
(() => {
const RAW = JSON.parse(document.getElementById('raw-data').textContent);
const KEYS = Object.keys(RAW);
const sec = t => t ? t.split(':').map(Number).reduce((a, b) => a * 60 + b, 0) : -1;
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const TIME = /\d{1,2}:\d{2}(?::\d{2})?/;
const body = document.body, db = document.getElementById('db'), dq = document.getElementById('dq');
KEYS.forEach(k => RAW[k].forEach(e => e.s = sec(e.t)));
// 段落：每个 details.raw 是一段（来源、起止、主讲人、所属场次）
const SEGS = [...document.querySelectorAll('details.raw')].map((d, i) => {
  const part = d.closest('.part');
  const no = part && part.querySelector('.part-no');
  const h2 = part && part.querySelector('h2');
  const k = getComputedStyle(part || body).getPropertyValue('--k').trim() || 'var(--p0)';
  return {i, src: d.dataset.src, f: sec(d.dataset.from), to: sec(d.dataset.to), main: (d.dataset.main || '').split('|'),
    name: (no ? no.textContent.trim() + ' ' : '') + (h2 ? h2.textContent.split(/[：:]/)[0].trim() : ''), c: k, part, d};
});
const segOf = (src, s) => SEGS.find(g => g.src === src && s >= g.f && s <= g.to);
// 渲染全文（按来源 → 段）
let html = '';
KEYS.forEach(k => {
  html += `<div class="dsrc" data-src="${k}">`;
  let cur = null;
  RAW[k].forEach((e, i) => {
    const g = e.s >= 0 ? segOf(k, e.s) : null;
    if (g !== cur || i === 0) {
      cur = g;
      const lab = (KEYS.length > 1 ? `来源 ${k} · ` : '') + (g ? g.name : '段外');
      html += `<div class="dsg" ${g ? `id="dsg${g.i}"` : ''} style="color:${g ? g.c : 'var(--muted)'}">${esc(lab)}</div>`;
    }
    const main = g && g.main.includes(e.sp) ? ' main' : '';
    html += `<div class="de${main}" id="de-${k}-${i}"><div class="eh">${e.t ? `<time>${e.t}</time>` : ''}<span class="sp">${esc(e.sp)}</span></div><p>${esc(e.x)}</p></div>`;
  });
  html += '</div>';
});
db.innerHTML = html;
const total = KEYS.reduce((n, k) => n + RAW[k].length, 0);
const cnt = document.getElementById('dcount');
cnt.textContent = `共${total}轮`;
document.getElementById('dsegs').innerHTML = SEGS.map(g => `<button type="button" data-seg="${g.i}"><i style="background:${g.c}"></i>${esc(g.name || '第' + (g.i + 1) + '段')}</button>`).join('');
// 抽屉开关
let last = null;
const dr = document.getElementById('drawer');
const openD = () => { body.classList.add('dr'); dr.setAttribute('aria-hidden', 'false'); };
const closeD = () => { body.classList.remove('dr'); dr.setAttribute('aria-hidden', 'true'); if (last) last.focus(); };
const scrollTo = el => requestAnimationFrame(() => { db.scrollTop = el.offsetTop - 52; });
function clearQ() { if (dq.value) { dq.value = ''; filt(''); } }
function goT(src, t) {
  clearQ(); openD();
  const s = sec(t), rows = RAW[src] || [];
  let idx = 0; rows.forEach((e, i) => { if (e.s >= 0 && e.s <= s) idx = i; });
  db.querySelectorAll('.hit').forEach(x => x.classList.remove('hit'));
  const el = document.getElementById(`de-${src}-${idx}`);
  if (el) { el.classList.add('hit'); scrollTo(el); }
}
function goSeg(i) { clearQ(); openD(); const el = document.getElementById('dsg' + i); if (el) requestAnimationFrame(() => { db.scrollTop = el.offsetTop; }); }
function filt(q) {
  let n = 0;
  KEYS.forEach(k => RAW[k].forEach((e, i) => {
    const el = document.getElementById(`de-${k}-${i}`), p = el.querySelector('p');
    const ok = !q || e.x.includes(q) || e.sp.includes(q);
    el.classList.toggle('hide', !ok); if (ok) n++;
    p.innerHTML = q && ok && e.x.includes(q) ? esc(e.x).split(esc(q)).join(`<mark>${esc(q)}</mark>`) : esc(e.x);
  }));
  db.querySelectorAll('.dsg').forEach(g => g.style.display = q ? 'none' : '');
  db.scrollTop = 0;
  cnt.textContent = q ? `匹配${n}轮` : `共${total}轮`;
}
let tm; dq.addEventListener('input', () => { clearTimeout(tm); tm = setTimeout(() => filt(dq.value.trim()), 120); });
// 时间戳 → 按钮。来源：.ts 自己的 data-src > 所在场次的 details.raw > 第一个来源
const timed = KEYS.filter(k => RAW[k].some(e => e.t));
document.querySelectorAll('.ts').forEach(ts => {
  const part = ts.closest('.part');
  const src = ts.dataset.src || (part && part.querySelector('details.raw') || {dataset: {}}).dataset.src || timed[0];
  if (!src || !timed.includes(src)) return;
  const pieces = ts.textContent.split(/(\s*(?:\/|、|，|,)\s*)/);
  ts.innerHTML = pieces.map(p => TIME.test(p) ? `<button type="button" class="tsb" data-src="${src}" data-t="${p.match(TIME)[0]}">${esc(p.trim())}</button>` : esc(p)).join('');
});
// details.raw → 打开抽屉的按钮（保留 data-* 给检查脚本）
SEGS.forEach(g => {
  const sum = g.d.querySelector('summary');
  const b = document.createElement('button');
  b.type = 'button'; b.className = 'rawbtn'; b.dataset.seg = g.i;
  const small = sum && sum.querySelector('small');
  const label = sum ? [...sum.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim().replace(/^展开/, '查看') : '查看这一段原话';
  b.innerHTML = `<b>${esc(label || '查看这一段原话')}</b>${small ? `<small>${esc(small.textContent)}</small>` : ''}<i>→</i>`;
  g.d.replaceWith(b); g.d = b;
});
// 页脚加一个全文入口
const ft = document.querySelector('footer');
if (ft && total) { const p = document.createElement('p'); p.innerHTML = `<button type="button" class="tsb" data-all="1">打开全文原话（${total}轮）</button>`; ft.appendChild(p); }
document.addEventListener('click', ev => {
  const t = ev.target.closest('.tsb');
  if (t) { last = t; if (t.dataset.all) { clearQ(); openD(); db.scrollTop = 0; } else goT(t.dataset.src, t.dataset.t); return; }
  const r = ev.target.closest('.rawbtn, .dsegs button');
  if (r) { if (r.classList.contains('rawbtn')) last = r; goSeg(+r.dataset.seg); }
});
document.getElementById('dclose').onclick = closeD;
document.getElementById('scrim').onclick = closeD;
document.addEventListener('keydown', e => { if (e.key === 'Escape' && body.classList.contains('dr')) closeD(); });
// 速览 / 完整
const modeBtns = document.querySelectorAll('.mode button');
modeBtns.forEach(b => b.onclick = () => {
  const q = b.dataset.mode === 'quick';
  body.classList.toggle('quick', q);
  modeBtns.forEach(x => x.setAttribute('aria-pressed', String(x === b)));
});
// 顶栏进度条：复制全场流程条的比例；没有流程条时按场次平分
const strip = document.querySelector('.strip');
const bars = [...document.querySelectorAll('.flow-bar a')];
const src = bars.length ? bars.map(a => ({href: a.getAttribute('href'), flex: a.style.flex || '1', bg: a.classList.contains('brk') ? 'var(--line2)' : a.style.background}))
  : [...document.querySelectorAll('.part')].map(p => ({href: '#' + p.id, flex: '1', bg: getComputedStyle(p).getPropertyValue('--k')}));
strip.innerHTML = src.map(s => `<a ${s.href ? `href="${s.href}"` : ''} style="flex:${s.flex};background:${s.bg}"></a>`).join('');
// 当前章节高亮
const links = [...document.querySelectorAll('.topbar .nav a, .strip a')];
const io = new IntersectionObserver(es => es.forEach(e => {
  if (e.isIntersecting) links.forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#' + e.target.id));
}), {rootMargin: '-40% 0px -55% 0px'});
document.querySelectorAll('section[id]').forEach(s => io.observe(s));
})();
