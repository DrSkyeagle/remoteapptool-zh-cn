#!/usr/bin/env python3
"""一键生成 RemoteApp Tool 简体中文版（不修改 IL，只原地重写 #US 字符串堆）。

用法：
    python build.py --src RemoteApp.Tool.6100.zip --out ./dist
    python build.py --src ./unpacked_official --out ./dist

--src 可以是官方 release 的 zip，也可以是已解压的官方目录。
官方下载：https://github.com/kimmknight/remoteapptool/releases
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'src'))

from us_heap import PE            # noqa: E402
from patch_zh import apply       # noqa: E402

TARGET = 'RemoteApp Tool.exe'
LANG = os.path.join(HERE, 'src', 'lang', 'zh-CN.json')


def unpack(src, workdir):
    """把官方 zip 解到 workdir，返回程序所在目录。"""
    if os.path.isdir(src):
        return src
    if zipfile.is_zipfile(src):
        with zipfile.ZipFile(src) as z:
            z.extractall(workdir)
        for base, dirs, files in os.walk(workdir):
            if TARGET in files:
                return base
        raise SystemExit('压缩包里找不到 %s' % TARGET)
    raise SystemExit('--src 只支持 zip 或目录')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, help='官方 zip 或解压后的目录')
    ap.add_argument('--out', default='dist', help='输出目录')
    args = ap.parse_args()

    mapping = json.load(open(LANG, encoding='utf-8'))
    tmp = tempfile.mkdtemp(prefix='rat_zh_')
    try:
        srcdir = unpack(args.src, tmp)
        os.makedirs(args.out, exist_ok=True)

        # 1. 复制官方全部文件
        for name in os.listdir(srcdir):
            p = os.path.join(srcdir, name)
            if os.path.isfile(p):
                shutil.copy2(p, os.path.join(args.out, name))

        # 2. 备份原版并打中文补丁
        exe = os.path.join(args.out, TARGET)
        backup = os.path.join(args.out, '原始英文备份')
        os.makedirs(backup, exist_ok=True)
        shutil.copy2(exe, os.path.join(backup, TARGET))

        hit, skip = apply(exe, exe, mapping)
        print('已替换 %d 条界面字符串' % hit)
        for total, en, zh in skip:
            print('  [跳过·槽位不足 %dB] %r' % (total, en[:60]))
        print('输出目录:', os.path.abspath(args.out))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
