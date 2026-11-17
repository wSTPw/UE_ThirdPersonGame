"""全 .text 精确扫描 switch 间接跳转(所有 modrm/SIB 变体), 解析分发表并按条目数过滤。

覆盖:
- jmp/call r/m64 (FF /2,/4): mod=00/01/10 + SIB(scale=8) + disp
- movsxd (48 63 /r): mod=00/01/10 + SIB(scale=4) + disp
基址解析: 绝对(base=101&&mod=00) 或 回溯 lea/mov base,[rip+disp] / mov base, imm。
只读; 不执行原生字节。
"""
from __future__ import annotations
import struct
from pathlib import Path

import capstone

ROOT = Path(__file__).resolve().parents[2]
EXE = Path(r"F:/PCprogram/Steam/steamapps/common/Monster Hunter World/MonsterHunterWorld.exe")
TEXT_BIN = ROOT / "Saved/MHWIRestoration/B05-20261024/analysis-text.bin"
TEXT_BASE = 0x140001000

REGS = {v: k for k, v in vars(capstone.x86).items() if k.startswith("X86_REG_R") and isinstance(v, int)}


def regname(r):
    return REGS.get(r, "r?%d" % r).replace("X86_REG_", "")


def main():
    data = TEXT_BIN.read_bytes()
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True

    def in_text(va):
        return TEXT_BASE <= va < TEXT_BASE + len(data)

    sites = []
    n = len(data)
    for i in range(n - 7):
        if data[i] != 0xFF and data[i] != 0x48:
            continue
        if data[i] == 0xFF and data[i + 1] in (0x24, 0x64, 0xA4, 0x14, 0x54, 0x94):
            sites.append((i, "indirect"))
        elif data[i] == 0x48 and data[i + 1] == 0x63 and (data[i + 2] & 7) == 4 and (data[i + 2] >> 6) in (0, 1, 2):
            sites.append((i, "movsxd"))
    print("candidate sites:", len(sites))

    tables = {}
    for i, kind in sites:
        try:
            insns = list(md.disasm(data[i:i + 16], TEXT_BASE + i, count=1))
        except Exception:
            continue
        if not insns:
            continue
        insn = insns[0]
        op = insn.operands[0] if insn.operands else None
        mem = None
        if op is not None and op.type == capstone.x86.X86_OP_MEM:
            mem = op.mem
        elif insn.mnemonic == "mov" and len(insn.operands) == 2 and \
                insn.operands[1].type == capstone.x86.X86_OP_MEM:
            mem = insn.operands[1].mem
        if mem is None or not mem.index or (mem.scale not in (4, 8)):
            continue
        scale, index, base = mem.scale, mem.index, mem.base
        if base == 0:
            table_va = mem.disp & 0xFFFFFFFFFFFFFFFF
        else:
            lo = max(TEXT_BASE, insn.address - 80)
            back = list(md.disasm(data[lo - TEXT_BASE:insn.address - TEXT_BASE], lo))
            baseva = None
            for b in reversed(back):
                if b.mnemonic in ("lea", "mov") and len(b.operands) == 2:
                    d, s2 = b.operands
                    if d.type == capstone.x86.X86_OP_REG and d.reg == base:
                        if s2.type == capstone.x86.X86_OP_MEM and s2.mem.base == capstone.x86.X86_REG_RIP \
                                and s2.mem.index == 0:
                            baseva = b.address + b.size + s2.mem.disp
                        elif s2.type == capstone.x86.X86_OP_IMM:
                            baseva = s2.imm & 0xFFFFFFFFFFFFFFFF
                        if baseva:
                            break
            if not baseva or not in_text(baseva):
                continue
            table_va = baseva
        if not in_text(table_va):
            continue
        off = table_va - TEXT_BASE
        if scale == 4:
            offs = struct.unpack_from("<1024i", data, off)
            cnt = 0
            for o in offs:
                if in_text(table_va + o):
                    cnt += 1
                else:
                    break
            entries = [(table_va + o) & 0xFFFFFFFFFFFFFFFF for o in offs[:cnt]]
        else:
            vals = struct.unpack_from("<1024Q", data, off)
            cnt = 0
            for v in vals:
                if in_text(v):
                    cnt += 1
                else:
                    break
            entries = list(vals[:cnt])
        if cnt >= 32:
            key = (table_va, scale)
            old = tables.get(key)
            if old is None or cnt > old[0]:
                tables[key] = (cnt, insn.address, hex(base) if base else "abs")

    ranked = sorted(tables.items(), key=lambda kv: -kv[1][0])
    print("resolved tables:", len(ranked))
    big = 0
    for (tva, scale), (cnt, site, basetxt) in ranked[:40]:
        mark = " <== >202" if cnt > 202 else ""
        if cnt > 202:
            big += 1
        print("  table=%s scale=%d entries=%d site=%s base=%s%s" % (hex(tva), scale, cnt, hex(site), basetxt, mark))
    print("tables with >202 entries:", big)


if __name__ == "__main__":
    main()
