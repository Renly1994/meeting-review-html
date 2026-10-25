# /// script
# requires-python = ">=3.10,<3.13"
# dependencies = [
#   "funasr==1.4.16",
#   "modelscope==1.40.1",
#   "torch==2.11.0",
#   "torchaudio==2.11.0",
#   "imageio-ffmpeg==0.6.0",
#   "transformers==4.57.6",  # funasr 默认会解析到需要编译的老版本，这里锁一个有预编译包的
# ]
# [[tool.uv.index]]
# name = "pytorch-cpu"
# url = "https://download.pytorch.org/whl/cpu"
# explicit = true
# [tool.uv.sources]
# torch = { index = "pytorch-cpu" }
# torchaudio = { index = "pytorch-cpu" }
# ///
"""把录音转成 review_tool.py 能读的转写稿（带说话人和时间戳）。

用法：
  uv run --script transcribe.py "录音.m4a" --out "录音_转写.md" [--start "2026-09-19 16:20"] [--speakers 5]

本地运行，不上传。用 FunASR：paraformer-zh 识别 + fsmn-vad 断句 + ct-punc 标点 + cam++ 说话人分离。
模型第一次运行时下载，缓存在 MODELSCOPE_CACHE（默认 ~/asr-models，可用环境变量改）。
同时写一个 <out>.meta.json：时长、说话人数、长静音（≥60 秒，常是茶歇、换场、转移到饭局）。
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import time

GAP = 60  # 秒，超过这个长度的静音记为“可能换场”
MERGE_GAP = 2.0  # 秒，同一说话人相邻句子间隔小于此值就并成一轮
MERGE_MAX = 400  # 字，一轮最多这么长，超过就另起一轮，方便按时间回查


def fmt(sec):
    sec = int(sec)
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f'{h:02d}:{m:02d}:{s:02d}' if h else f'{m:02d}:{s:02d}'


PUNC = set('，。？！、；：,.?!;:')
END = set('。？！?!')


def tokens_of(text):
    """把带标点的文本切成和 paraformer 逐字时间戳一一对应的 token，标点挂在前一个 token 后面。"""
    toks = []
    for m in re.finditer(r"[A-Za-z0-9']+|\S", text):
        t = m.group()
        if t in PUNC:
            if toks:
                toks[-1][1] += t
        else:
            toks.append([t, ''])
    return toks


def rebuild(res):
    """按逐字时间戳重新组装句子。

    FunASR 的 sentence_info 跨 VAD 段时文字会整体错一位（“哎”被算到上一个人末尾，后面每句都错一个字），
    但它给出的 (起止时间, 说话人) 是对的。所以只借用它的说话人区间，每个字按自己的时间点归属说话人。
    返回 [(start_s, end_s, spk, text)]；时间戳和文字对不上时退回 sentence_info。
    """
    sents, ts = res.get('sentence_info') or [], res.get('timestamp') or []
    toks = tokens_of(res.get('text', ''))
    if not sents or len(toks) != len(ts):
        return [(s['start'] / 1000, s['end'] / 1000, s.get('spk', 0), s['text']) for s in sents], False
    spans = [(s['start'], s['end'], s.get('spk', 0)) for s in sents]

    def spk_at(t):
        best = min(spans, key=lambda sp: 0 if sp[0] <= t <= sp[1] else min(abs(t - sp[0]), abs(t - sp[1])))
        return best[2]

    out, cur = [], None
    for (word, punc), (st, en) in zip(toks, ts):
        sp = spk_at((st + en) / 2)
        if cur and cur[2] == sp and not (cur[3] and cur[3][-1] in END):
            cur[1], cur[3] = en, cur[3] + word + punc
        else:
            if cur:
                out.append(cur)
            cur = [st, en, sp, word + punc]
    out.append(cur)
    return [(a / 1000, b / 1000, sp, x) for a, b, sp, x in out], True


def to_wav(src, dst):
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    r = subprocess.run([ff, '-y', '-i', src, '-ac', '1', '-ar', '16000', '-vn', dst],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        sys.exit('ffmpeg 转换失败：\n' + r.stderr[-1500:])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('audio')
    ap.add_argument('--out', required=True)
    ap.add_argument('--title', help='默认用录音文件名')
    ap.add_argument('--start', help='录音开始的现场时间，如 "2026-09-19 16:20"；不填就用文件修改时间减时长估算')
    ap.add_argument('--speakers', type=int, help='已知说话人数时填，分离会更准')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    if os.path.exists(a.out) and not a.force:
        sys.exit(f'{a.out} 已存在。换一个文件名，或者确认后加 --force。')
    os.environ.setdefault('MODELSCOPE_CACHE', os.path.join(os.path.expanduser('~'), 'asr-models'))

    t0 = time.time()
    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, 'a.wav')
        to_wav(a.audio, wav)
        from funasr import AutoModel
        model = AutoModel(model='paraformer-zh', vad_model='fsmn-vad', punc_model='ct-punc',
                          spk_model='cam++', disable_update=True, disable_pbar=True, log_level='ERROR')
        kw = {'batch_size_s': 300}
        if a.speakers:
            kw['preset_spk_num'] = a.speakers
        res = model.generate(input=wav, **kw)
    sents, aligned = rebuild(res[0])
    if not sents:
        sys.exit('没有识别出带说话人的句子。录音可能太短、太安静，或者不是中文。')

    # 说话人按第一次出现的顺序编号；相邻同一说话人的句子合并成一轮
    order = {}
    turns, gaps = [], []
    for i, (st, en, sp, tx) in enumerate(sents):
        sp = order.setdefault(sp, len(order))
        tx = tx.strip().lstrip('，。？！、；：,.?!;:')
        if i and st - sents[i - 1][1] >= GAP:
            gaps.append({'from': fmt(sents[i - 1][1]), 'to': fmt(st), 'sec': round(st - sents[i - 1][1])})
        if not tx:
            continue
        last = turns[-1] if turns else None
        if last and last['sp'] == sp and st - last['end'] < MERGE_GAP and len(last['x']) + len(tx) <= MERGE_MAX:
            last['x'] += tx
            last['end'] = en
        else:
            turns.append({'sp': sp, 'st': st, 'end': en, 'x': tx})
    dur = sents[-1][1]

    if a.start:
        start = dt.datetime.strptime(a.start, '%Y-%m-%d %H:%M')
        est = ''
    else:
        start = dt.datetime.fromtimestamp(os.path.getmtime(a.audio)) - dt.timedelta(seconds=dur)
        est = '（按文件修改时间估算）'
    title = a.title or os.path.splitext(os.path.basename(a.audio))[0]
    lines = [f'> # **{title}**', f'> **{start:%Y-%m-%d | %H:%M}**{est}', '']
    for t in turns:
        lines += [f'**说话人{t["sp"] + 1}  {fmt(t["st"])}**', '', t['x'], '', '']
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or '.', exist_ok=True)
    open(a.out, 'w', encoding='utf-8').write('\n'.join(lines))
    meta = {'source': os.path.abspath(a.audio), 'duration': fmt(dur), 'speakers': len({t['sp'] for t in turns}),
            'turns': len(turns), 'start': f'{start:%Y-%m-%d %H:%M}', 'start_estimated': not a.start,
            'long_silences': gaps, 'asr': 'FunASR paraformer-zh + fsmn-vad + ct-punc + cam++',
            'char_aligned': aligned,
            'elapsed_sec': round(time.time() - t0)}
    json.dump(meta, open(a.out + '.meta.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'已写 {a.out}：时长 {meta["duration"]}，{meta["speakers"]} 个说话人，{len(turns)} 轮，用时 {meta["elapsed_sec"]} 秒')
    if gaps:
        print('长静音（可能是换场）：' + '，'.join(f'{g["from"]}–{g["to"]}' for g in gaps))
    print('说话人编号是聚类得来的：同一个人可能被拆成两个编号，声音相近的两个人也可能被合成一个。切场次时以内容为准。')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    main()
