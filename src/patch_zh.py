"""对程序集原位应用中文映射，输出统计与被跳过的条目。

匹配策略（两级，保证换行风格不被改动）：
1. 精确匹配：原文与映射键完全一致，值原样写入。
2. 归一化匹配：仅当原文不含真换行（纯字面量 \\n 风格）时启用，
   写入时把值里的真换行转成字面量 \\n，与原文风格保持一致。
"""
import json, sys
from us_heap import PE

# VB.NET 后期绑定（LateCall / LateSet）的成员名以字符串字面量出现在 IL 里。
# 这些词一旦被翻译，运行时就会抛 MissingMemberException：
#   未找到类型“ImageCollection”的公共成员“添加”。
# 实测踩坑：Add（ImageList.Images.Add）。同类集合成员一律禁止入表。
HARD_DENY = {
    'Add', 'Remove', 'RemoveAt', 'Item', 'Count', 'Clear', 'Insert',
    'IndexOf', 'Contains', 'Sort', 'Clone', 'ToString', 'Equals',
    'GetType', 'Dispose', 'ToString',
}


def _canon(s):
    return s.replace('\\r\\n', '\x00').replace('\\n', '\x00') \
            .replace('\r\n', '\x00').replace('\n', '\x00')


def build_maps(mapping):
    exact = {}
    for k, v in mapping.items():
        if k in HARD_DENY:
            print('[警告] 拒绝翻译后期绑定成员名 %r（会导致 MissingMemberException）' % k)
            continue
        exact[k] = v
    loose = {}
    for k, v in exact.items():
        loose[_canon(k.replace('\r\n', '\x00').replace('\n', '\x00'))] = \
            _canon(v).replace('\x00', '\\n')
    return exact, loose


def apply(src, dst, mapping, dry=False):
    exact, loose = build_maps(mapping)
    pe = PE(src)
    hit = 0
    skip = []
    for off, total, text in pe.us_entries():
        if text in exact:
            zh = exact[text]
        elif '\r' not in text and '\n' not in text and _canon(text) in loose:
            zh = loose[_canon(text)]
        else:
            continue
        if zh == text:
            continue
        body = len(zh.encode('utf-16-le')) + 1
        pfx = 1 if body < 0x80 else (2 if body < 0x4000 else 4)
        if pfx + body > total:
            skip.append((total, text, zh))
            continue
        if not dry and not pe.patch_us(off, total, zh):
            skip.append((total, text, zh))
            continue
        hit += 1
    if not dry:
        pe.save(dst)
    return hit, skip


if __name__ == '__main__':
    mapping = json.load(open(sys.argv[1], encoding='utf-8'))
    dry = '--dry' in sys.argv
    for f in [a for a in sys.argv[2:] if a != '--dry']:
        dst = f if dry else f.replace('.exe', '.zh.exe').replace('.dll', '.zh.dll')
        hit, skip = apply(f, dst, mapping, dry)
        print('%s -> %s  命中 %d，超长跳过 %d' % (f, dst, hit, len(skip)))
        for total, text, zh in skip:
            print('   [超长 %dB] %r -> %r' % (total, text[:60], zh))
