"""全 .text 扫描动作构造器的 motion encoding 写入并提取注册名（B1 招式表数据源）。

依据(2026-11-02 实证):
- 消费端解码指令: slot = packed & 0x1FF; bank = (packed >> 12) & 0xF (0x141c0158a/0x141c0159c/0x141c015a7)
- 动作构造器形态(0x1413ec13d 附近, BITE): push rbx; mov rbx,rcx; lea rax,[rip+desc];
  mov qword [rbx+0x1E0], packed; mov [rbx],rax; mov dword [rbx+0x1B0], imm; mov dword [rbx+0x1B4], float
- 本脚本只读 analysis-text.bin(.text 镜像, hash 内建校验), 不执行原生字节。

输出: 每个构造器一行(ctor VA / packed / bank / slot / 名称候选 / 附加属性), JSON 落盘。
名称候选来自 desc 指针解引用或 desc 原位字符串; 解析不到显式标 unknown, 不猜测。
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
DEFAULT_OUT = ROOT / "Saved/MHWI-Rathian-FirstChain/action-ctor-motion-scan-20261102.json"

# mov qword ptr [r64+0x1E0], imm32: 48 C7 /0(=reg000) mod10 disp32
# modrm = 0x80 | rm (rm=0..7, rsp/rbp 形态罕见也扫)
CTORENC = b"\x48\xc7"
OFFSET_DISP = 0x1E0


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 22), b""):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if sha256_file(TEXT_BIN) != PINNED_TEXT_SHA256:
        raise SystemExit("text.bin 指纹不匹配")
    data = TEXT_BIN.read_bytes()
    exe = EXE.read_bytes()
    pe = pefile.PE(data=exe, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    secs = [(base + s.VirtualAddress, s.VirtualAddress + s.Misc_VirtualSize,
             s.PointerToRawData, s.SizeOfRawData, bytes(s.Name).split(b"\x00")[0].decode())
            for s in pe.sections]

    def in_text(va):
        return TEXT_BASE <= va < TEXT_BASE + len(data)

    def va2off(va):
        for v, ve, raw, rsz, _ in secs:
            if v <= va < ve and va - v < rsz:
                r = va - v
                return ("text", TEXT_BASE + r) if _ == ".text" else ("exe", raw + r)
        return None

    def read_cstr(va, maxlen=80):
        m = va2off(va)
        if not m:
            return None
        src, off = m
        buf = data if src == "text" else exe
        chunk = buf[off:off + maxlen]
        cut = chunk.find(b"\x00")
        if cut <= 0:
            return None
        c = chunk[:cut]
        if len(c) >= 3 and all(0x20 <= x < 0x7F for x in c):
            return c.decode("ascii")
        return None

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True

    # 1) 扫描 mov qword [reg+0x1E0], imm32
    hits = []
    n = len(data)
    for i in range(n - 12):
        if data[i] != 0x48 or data[i + 1] != 0xC7:
            continue
        modrm = data[i + 2]
        if (modrm & 0xC0) != 0x80 or ((modrm >> 3) & 7) != 0 or (modrm & 7) == 4:
            continue
        disp = struct.unpack_from("<I", data, i + 3)[0]
        if disp != OFFSET_DISP:
            continue
        imm = struct.unpack_from("<i", data, i + 7)[0] & 0xFFFFFFFF
        hits.append((TEXT_BASE + i, modrm & 7, imm))
    print("motion-encoding write sites:", len(hits))

    # 2) 每个命中: 回溯函数头, 收集 lea reg,[rip+d] 描述符与同函数属性写
    rows = []
    for site, rm, packed in hits:
        slot = packed & 0x1FF
        bank = (packed >> 12) & 0xF
        lo = max(TEXT_BASE, site - 160)
        ins = list(md.disasm(data[lo - TEXT_BASE:site - TEXT_BASE + 8], lo))
        func_start = None
        for k, ins_i in enumerate(ins):
            if ins_i.mnemonic == "push" and "rbx" in ins_i.op_str:
                func_start = ins_i.address
        desc_vas, props = [], {}
        for ins_i in ins:
            if ins_i.mnemonic == "lea" and len(ins_i.operands) == 2:
                d, s2 = ins_i.operands
                if s2.type == capstone.x86.X86_OP_MEM and s2.mem.base == capstone.x86.X86_REG_RIP:
                    desc_vas.append(ins_i.address + ins_i.size + s2.mem.disp)
            if ins_i.mnemonic == "mov" and len(ins_i.operands) == 2:
                d, s2 = ins_i.operands
                if (d.type == capstone.x86.X86_OP_MEM and (d.mem.disp in (0x1B0, 0x1B4))
                        and s2.type == capstone.x86.X86_OP_IMM):
                    props[hex(d.mem.disp)] = s2.imm & 0xFFFFFFFF
        name = None
        for dv in reversed(desc_vas):  # 离 mov 最近(通常最后一个 lea)的描述符优先
            st = read_cstr(dv)
            if not st:
                m = va2off(dv)
                if m:
                    src, off = m
                    buf = data if src == "text" else exe
                    if off + 8 <= len(buf):
                        ptr = struct.unpack_from("<Q", buf, off)[0]
                        st = read_cstr(ptr) if ptr else None
            if st:
                name = st
                break
        rows.append(dict(ctor_write_va=hex(site), packed=hex(packed), bank=bank, slot=slot,
                         name=name, desc_va=[hex(x) for x in desc_vas[-2:]],
                         props=props, func_start=hex(func_start) if func_start else None))
    named = [r for r in rows if r["name"]]
    out = dict(schema=1, date="2026-11-02",
               mode="offline_static_scan_read_only_no_execution",
               source=dict(path=str(TEXT_BIN), sha256=PINNED_TEXT_SHA256,
                           decode_evidence="0x141c0158a(and 0x1FF)/0x141c0159c(shr 0xC)/0x141c015a7(and 0xF)"),
               counts=dict(write_sites=len(rows), named=len(named)),
               rows=rows,
               boundary=["构造器写入偏移 0x1E0 为扫描启发式; 名称来自 desc 解引用, 解析不到标 unknown",
                         "不证明动作 ID 与构造器的运行时注册顺序; ID 关联需经名字对 ActionDumps 或注册表证据",
                         "不执行原生字节; 不修改游戏安装; bank/slot 语义为位域事实, 是否等效 UE 播放需运行验证"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(dict(output=str(args.output), sites=len(rows), named=len(named),
                          banks=sorted({r["bank"] for r in rows})), ensure_ascii=False))
    for r in rows[:24]:
        print("  site=%s packed=%s bank=%d slot=%3d name=%s" %
              (r["ctor_write_va"], r["packed"], r["bank"], r["slot"], r["name"]))


if __name__ == "__main__":
    main()
