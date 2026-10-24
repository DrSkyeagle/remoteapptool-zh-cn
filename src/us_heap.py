"""RemoteApp Tool 汉化 - .NET #US 字符串堆读写核心
纯 PE/CLI 元数据解析，无第三方依赖。原位替换，不重写 IL / token。
"""
import struct, sys, json

class PE:
    def __init__(self, path):
        self.data = bytearray(open(path, 'rb').read())
        d = self.data
        if d[:2] != b'MZ':
            raise ValueError('not PE')
        e_lfanew = struct.unpack_from('<I', d, 0x3C)[0]
        assert d[e_lfanew:e_lfanew+4] == b'PE\0\0'
        coff = e_lfanew + 4
        nsec = struct.unpack_from('<H', d, coff + 2)[0]
        optsz = struct.unpack_from('<H', d, coff + 16)[0]
        opt = coff + 20
        magic = struct.unpack_from('<H', d, opt)[0]
        pe32plus = (magic == 0x20b)
        ddir = opt + (112 if pe32plus else 96)
        self.cli_rva, self.cli_size = struct.unpack_from('<II', d, ddir + 14*8)
        self.sections = []
        so = opt + optsz
        for i in range(nsec):
            off = so + i*40
            name = d[off:off+8].rstrip(b'\0').decode('latin1')
            vsize, vaddr, rawsize, rawptr = struct.unpack_from('<IIII', d, off+8)
            self.sections.append((name, vaddr, max(vsize, rawsize), rawptr))
        self._parse_metadata()

    def rva2off(self, rva):
        for name, vaddr, vsize, rawptr in self.sections:
            if vaddr <= rva < vaddr + vsize:
                return rawptr + (rva - vaddr)
        raise ValueError('bad rva %x' % rva)

    def _parse_metadata(self):
        d = self.data
        cli = self.rva2off(self.cli_rva)
        md_rva, md_size = struct.unpack_from('<II', d, cli + 8)
        md = self.rva2off(md_rva)
        self.md = md
        assert struct.unpack_from('<I', d, md)[0] == 0x424A5342
        vlen = struct.unpack_from('<I', d, md + 12)[0]
        p = md + 16 + vlen
        nstreams = struct.unpack_from('<H', d, p + 2)[0]
        p += 4
        self.streams = {}
        for _ in range(nstreams):
            soff, ssize = struct.unpack_from('<II', d, p)
            p += 8
            end = d.index(b'\0', p)
            name = d[p:end].decode('latin1')
            p = end + 1
            p = (p + 3) & ~3
            self.streams[name] = (md + soff, ssize)

    # ---------- #US heap ----------
    def us_entries(self):
        """顺序遍历 #US 堆，返回 [(offset, total_bytes, text)]；offset 相对堆起点。"""
        base, size = self.streams['#US']
        d = self.data
        i = 1  # 第 0 字节固定为 0x00 空串
        out = []
        while i < size:
            start = i
            b = d[base + i]
            if b & 0x80 == 0:
                ln = b; i += 1
            elif b & 0xC0 == 0x80:
                ln = ((b & 0x3F) << 8) | d[base + i + 1]; i += 2
            else:
                ln = ((b & 0x1F) << 24) | (d[base+i+1] << 16) | (d[base+i+2] << 8) | d[base+i+3]
                i += 4
            if ln == 0 or i + ln > size:
                break
            body = bytes(d[base + i: base + i + ln - 1])
            # 末字节为标志位，不计入文本
            try:
                text = body.decode('utf-16-le', errors='replace')
            except Exception:
                text = ''
            total = (i - start) + ln
            out.append((start, total, text))
            i += ln
        return out

    def patch_us(self, offset, old_total, new_text):
        """原位写入。要求新条目总字节数 <= old_total，返回是否成功。"""
        base, _ = self.streams['#US']
        payload = new_text.encode('utf-16-le')
        flag = 1 if any(ord(c) > 0x7F for c in new_text) else 0
        body_len = len(payload) + 1  # 含标志字节
        # 先按长度决定所需前缀宽度，再校验是否塞得进原槽位
        if body_len < 0x80:
            needed_pfx = 1
        elif body_len < 0x4000:
            needed_pfx = 2
        else:
            needed_pfx = 4
        if needed_pfx + body_len > old_total:
            return False
        pfx = needed_pfx
        d = self.data
        buf = bytearray()
        if pfx == 1:
            buf.append(body_len)
        elif pfx == 2:
            buf += bytes([0x80 | (body_len >> 8), body_len & 0xFF])
        else:
            buf += bytes([0xC0 | (body_len >> 24), (body_len >> 16) & 0xFF,
                          (body_len >> 8) & 0xFF, body_len & 0xFF])
        buf += payload
        buf.append(flag)
        # 剩余空间补 0，保持后继条目偏移不变
        buf += b'\0' * (old_total - len(buf))
        d[base + offset: base + offset + old_total] = buf
        return True

    def save(self, path):
        open(path, 'wb').write(bytes(self.data))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'dump':
        pe = PE(sys.argv[2])
        ents = pe.us_entries()
        rows = [{'off': o, 'total': t, 's': s} for o, t, s in ents]
        json.dump(rows, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('%s: %d entries' % (sys.argv[2], len(ents)))
