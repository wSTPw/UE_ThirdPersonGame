"""转储 exe 内动作注册表(name↔id↔vtable)并串联构造器 motion 编码(B1 招式表数据源)。

依据(2026-11-02 实证):
- 注册表条目 32B: {qword name_ptr, qword runtime_id, qword vtable, qword 0}
  样本: 0x142e639d8 -> ("ACTION::BITE", 0x54, 0x144f391c8, 0)
- 动作构造器: mov qword [reg+0x1E0], packed; mov [reg], vtable(lea rip)
- 解码: slot = packed & 0x1FF; bank = (packed>>12) & 0xF (消费端 0x141c0158a 等实证)

只读; 不执行原生字节; hash 校验内建。
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path

import capstone
import pefile

ROOT = Path(__file__).resolve().parents[2]
EXE = Path(r"F:/PCprogram/Steam/steamapps/common/Monster Hunter World/MonsterHunterWorld.exe")
TEXT_BIN = ROOT / "Saved/MHWIRestoration/B05-20261024/analysis-text.bin"
PINNED_TEXT_SHA256 = "9b48a8490df702ba9dc1cb95ffd387358ae2a639aa9675ad90719bd997124ebe"
TEXT_BASE = 0x140001000
DEFAULT_OUT = ROOT / "Saved/MHWI-Rathian-FirstChain/action-registry-dump-20261102.json"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    if sha256_file(TEXT_BIN) != PINNED_TEXT_SHA256:
        raise SystemExit("text.bin 指纹不匹配")
    data = TEXT_BIN.read_bytes()
    exe = EXE.read_bytes()
    pe = pefile.PE(data=exe, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    secs = [(base + s.VirtualAddress, base + s.VirtualAddress + s.Misc_VirtualSize,
             s.PointerToRawData, s.SizeOfRawData, bytes(s.Name).split(b"\x00")[0].decode())
            for s in pe.sections]

    def va2off(va):
        for v, ve, raw, rsz, name in secs:
            if v <= va < ve and va - v < rsz:
                r = va - v
                return ("text", TEXT_BASE + r) if name == ".text" else ("exe", raw + r)
        return None

    def read_cstr(va):
        m = va2off(va)
        if not m:
            return None
        src, off = m
        buf = data if src == "text" else exe
        chunk = buf[off:off + 64]
        cut = chunk.find(b"\x00")
        if cut <= 0:
            return None
        c = chunk[:cut]
        if len(c) >= 3 and all(0x20 <= x < 0x7F for x in c):
            return c.decode("ascii")
        return None

    def read_q(va):
        m = va2off(va)
        if not m:
            return None
        src, off = m
        buf = data if src == "text" else exe
        if off + 8 > len(buf):
            return None
        return struct.unpack_from("<Q", buf, off)[0]

    # 1) 定位种子: 已实证的 BITE 名字指针
    seed_str = None
    seed_hits = []
    for v, ve, raw, rsz, name in secs:
        if name not in (".rdata", ".data"):
            continue
        blob = exe[raw:raw + rsz]
        k = blob.find(b"ACTION::BITE\x00")
        while k >= 0:
            seed_hits.append((name, v + k))
            k = blob.find(b"ACTION::BITE\x00", k + 1)
    print("ACTION::BITE 字符串:", [(n, hex(v)) for n, v in seed_hits])

    # 2) 从每个指针命中处对齐条目并向两侧走表
    entries = {}
    for _, str_va in seed_hits:
        # 找 .rdata 中存该指针的 qword
        for v, ve, raw, rsz, name in secs:
            if name not in (".rdata", ".data"):
                continue
            blob = exe[raw:raw + rsz]
            pat = struct.pack("<Q", str_va)
            j = 0
            while True:
                k = blob.find(pat, j)
                if k < 0:
                    break
                hit_va = v + k
                j = k + 1
                # 对齐到条目起点: 条目 = {name,id,vtable,0}, name 在 +0
                for off in (0, -8, 8, -16, 16, -24, 24):
                    start = hit_va + off
                    if read_q(start) == str_va:
                        break
                else:
                    continue
                # 向前走
                p = start
                while True:
                    np_, idv, vt, z = (read_q(p), read_q(p + 8), read_q(p + 16), read_q(p + 24))
                    nm = read_cstr(np_) if np_ else None
                    if nm is None or not nm.startswith("ACTION::") or vt is None or z != 0:
                        break
                    key = nm
                    if key not in entries:
                        entries[key] = dict(name=nm, id=idv, vtable=hex(vt), table_entry=hex(p))
                    p += 32
                # 向后走
                p = start - 32
                while True:
                    np_, idv, vt, z = (read_q(p), read_q(p + 8), read_q(p + 16), read_q(p + 24))
                    nm = read_cstr(np_) if np_ else None
                    if nm is None or not nm.startswith("ACTION::") or vt is None or z != 0:
                        break
                    if nm not in entries:
                        entries[nm] = dict(name=nm, id=idv, vtable=hex(vt), table_entry=hex(p))
                    p -= 32
    print("registry entries:", len(entries))

    # 3) vtable -> 构造器 -> packed: 扫描 'lea reg,[rip+vt]; mov [reg2],reg' + 'mov qword [reg2+0x1E0],imm'
    #    直接扫 mov qword [reg+0x1E0],imm 全站点, 回溯其 lea 的 desc 与写入目标寄存器, 匹配 vtable
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    vt2packed = {}
    n = len(data)
    for i in range(n - 12):
        if data[i] != 0x48 or data[i + 1] != 0xC7:
            continue
        modrm = data[i + 2]
        if (modrm & 0xC0) != 0x80 or ((modrm >> 3) & 7) != 0 or (modrm & 7) == 4:
            continue
        if struct.unpack_from("<I", data, i + 3)[0] != 0x1E0:
            continue
        imm = struct.unpack_from("<i", data, i + 7)[0] & 0xFFFFFFFF
        site = TEXT_BASE + i
        ins = list(md.disasm(data[max(0, i - 100):i + 8], site - (i - max(0, i - 100))))
        dvt = None
        for x in reversed(ins):
            if x.mnemonic == "lea" and len(x.operands) == 2:
                d, s2 = x.operands
                if d.type == capstone.x86.X86_OP_REG and s2.type == capstone.x86.X86_OP_MEM \
                        and s2.mem.base == capstone.x86.X86_REG_RIP and s2.mem.index == 0:
                    dvt = x.address + x.size + s2.mem.disp
                    break
        if dvt:
            vt2packed.setdefault(dvt, []).append((hex(site), hex(imm)))

    rows = []
    joined = 0
    for nm, e in sorted(entries.items(), key=lambda kv: kv[1]["id"] if kv[1]["id"] is not None else -1):
        vt = int(e["vtable"], 16)
        mo = vt2packed.get(vt) or vt2packed.get(vt + 0) or []
        packed = mo[0][1] if mo else None
        row = dict(name=nm, id=e["id"], vtable=e["vtable"])
        if packed:
            p = int(packed, 16)
            row.update(motion_packed=packed, bank=(p >> 12) & 0xF, slot=p & 0x1FF)
            joined += 1
        else:
            row.update(motion_packed=None, bank=None, slot=None)
        rows.append(row)
    print("joined motion:", joined, "/", len(rows))
    banks = {}
    for r in rows:
        if r["bank"] is not None:
            banks[r["bank"]] = banks.get(r["bank"], 0) + 1
    print("bank 分布:", banks)
    sample = [r for r in rows if r["slot"] is not None][:12]
    for r in sample:
        print("  id=%-4s %-40s bank=%s slot=%s" % (r["id"], r["name"], r["bank"], r["slot"]))

    out = dict(schema=1, date="2026-11-02",
               mode="offline_static_read_only_no_execution",
               source=dict(exe="c2ebbbd2c49f216d484e31a5219bed419eb1e5e7d206d02cba040a3ab79d90ea",
                           text_bin=PINNED_TEXT_SHA256),
               registry_entry_layout="32B {name_ptr, runtime_id, vtable, 0}",
               decode="slot=packed&0x1FF; bank=(packed>>12)&0xF",
               counts=dict(entries=len(rows), motion_joined=joined, banks=banks),
               rows=rows,
               boundary=["registry id 与 ActionDumps 历史编号存在偏移(如 BITE: 注册表0x54 vs dump 83), "
                         "以本表为准并保留差异列; THK emit id 与 registry id 的映射需在 THK 侧抽验",
                         "bank/slot 是否等效 UE AnimSequence 播放需导入验证; 不执行原生字节"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("saved:", args.output)


if __name__ == "__main__":
    main()
