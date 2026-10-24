#!/usr/bin/env python3
"""校验打好的中文版：从成包里逐条回读 #US 条目，与语言映射表比对。

用法：
    python src/verify.py
    python src/verify.py --official <原版exe> --patched <汉化exe>
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from us_heap import PE                       # noqa: E402
from patch_zh import build_maps, _canon      # noqa: E402

TARGET = 'RemoteApp Tool.exe'


def read_at(pe, off):
    base, _ = pe.streams['#US']
    d = pe.data
    i = off
    b = d[base + i]
    if b & 0x80 == 0:
        ln = b
        i += 1
    elif b & 0xC0 == 0x80:
        ln = ((b & 0x3F) << 8) | d[base + i + 1]
        i += 2
    else:
        ln = ((b & 0x1F) << 24) | (d[base + i + 1] << 16) | (d[base + i + 2] << 8) | d[base + i + 3]
        i += 4
    return bytes(d[base + i: base + i + ln - 1]).decode('utf-16-le')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--official', default=os.path.join('dist', '原始英文备份', TARGET))
    ap.add_argument('--patched', default=os.path.join('dist', TARGET))
    ap.add_argument('--lang', default=os.path.join(HERE, 'lang', 'zh-CN.json'))
    args = ap.parse_args()

    mapping = json.load(open(args.lang, encoding='utf-8'))
    exact, loose = build_maps(mapping)
    off_pe = PE(args.official)
    zh_pe = PE(args.patched)

    ok = bad = 0
    problems = []
    for off, total, text in off_pe.us_entries():
        if text in exact:
            want = exact[text]
        elif '\r' not in text and '\n' not in text and _canon(text) in loose:
            want = loose[_canon(text)]
        else:
            continue
        got = read_at(zh_pe, off)
        if got == want:
            ok += 1
        else:
            bad += 1
            problems.append((text, want, got))

    print('回读校验: %d 正确, %d 异常' % (ok, bad))
    for t, w, g in problems[:10]:
        print('  不一致: %r -> 期望 %r / 实际 %r' % (t[:40], w[:40], g[:40]))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
