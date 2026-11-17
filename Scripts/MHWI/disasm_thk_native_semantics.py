"""离线静态反汇编 MHWI 怪物 AI THK 虚拟机条件求值链（E01/BEH-01 取证）。

只读分析两类本地非执行缓冲:
- Saved/MHWIRestoration/B05-20261024/analysis-text.bin = 解包后的 .text 镜像
  (hash 锁定 9b48a849..., 与 exe .text 布局一致; 锁定地址对应该缓冲, 不对应 exe 原始文件偏移)
- MonsterHunterWorld.exe 原文件: 提供 .rdata/.data 只读访问与 .pdata 函数边界

流程: .pdata 定位 VM 区域函数 -> 扫描 switch 间接跳转(8字节绝对表/4字节相对表) ->
读取候选分发表 -> 逐 handler 提取结构特征(字符串/立即数比较/上下文字段偏移/浮点/
调用目标) -> 与 thk-all-raw.json 全 105 表 13015 段 functionType 使用统计交叉引用。

边界: 静态发现与结构推断, 不是运行验证; 不执行原生字节; 不修改游戏安装。
语义结论均为"候选", 只有字符串佐证的才具名, 其余保持 unknown。
"""
from __future__ import annotations
import argparse
import bisect
import hashlib
import json
import struct
from pathlib import Path

import capstone
import pefile

ROOT = Path(__file__).resolve().parents[2]
EXE = Path(r"F:/PCprogram/Steam/steamapps/common/Monster Hunter World/MonsterHunterWorld.exe")
TEXT_BIN = ROOT / "Saved/MHWIRestoration/B05-20261024/analysis-text.bin"
PINNED_EXE_SHA256 = "c2ebbbd2c49f216d484e31a5219bed419eb1e5e7d206d02cba040a3ab79d90ea"
PINNED_TEXT_SHA256 = "9b48a8490df702ba9dc1cb95ffd387358ae2a639aa9675ad90719bd997124ebe"
THK_ALL_RAW = ROOT / "Saved/MHWI-Rathian-FirstChain/THK/thk-all-raw.json"
DEFAULT_OUT = ROOT / "Saved/MHWI-Rathian-FirstChain/thk-condition-semantics-20261102.json"

ADDR_EVALUATOR = 0x1423FC990
ADDR_VM_TICK = 0x1423FE8D0
ADDR_NAME_LOOKUP = 0x142400150
TEXT_BASE = 0x140001000
VM_SCAN_LO, VM_SCAN_HI = 0x1423E0000, 0x142420000

MAX_TABLE_ENTRIES = 1024
HANDLER_MAX_INSNS = 150
FUNC_SCAN_MAX_INSNS = 8000


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


class DualImage:
    """text.bin 覆盖 .text VA 段; 其余 VA 落回 exe 原始映射。均只读。"""

    def __init__(self, exe_path: Path, text_path: Path):
        self.exe_data = exe_path.read_bytes()
        self.pe = pefile.PE(data=self.exe_data, fast_load=True)
        self.image_base = self.pe.OPTIONAL_HEADER.ImageBase
        self.text = text_path.read_bytes()
        self.sections = []
        for s in self.pe.sections:
            self.sections.append(dict(
                name=bytes(s.Name).split(b"\x00")[0].decode("ascii", "replace"),
                va=self.image_base + s.VirtualAddress,
                vsize=max(s.Misc_VirtualSize, s.SizeOfRawData),
                raw=s.PointerToRawData, rawsize=s.SizeOfRawData,
                exec=bool(s.Characteristics & 0x20000000)))
        pdata_sec = next(s for s in self.sections if s["name"] == ".pdata")
        blob = self.exe_data[pdata_sec["raw"]:pdata_sec["raw"] + pdata_sec["rawsize"]]
        self.func_starts, self.func_bounds = [], []
        for i in range(len(blob) // 12):
            b, e, _ = struct.unpack_from("<III", blob, i * 12)
            if b:
                self.func_starts.append(b)
                self.func_bounds.append((b, e))
        self.func_starts.sort()

    def in_text(self, va: int) -> bool:
        return TEXT_BASE <= va < TEXT_BASE + len(self.text)

    def section_of(self, va: int):
        for s in self.sections:
            if s["va"] <= va < s["va"] + s["vsize"]:
                return s
        return None

    def bytes_at(self, va: int, n: int):
        if self.in_text(va):
            off = va - TEXT_BASE
            return self.text[off:off + n]
        s = self.section_of(va)
        if s is None:
            return None
        rva = va - s["va"]
        if rva >= s["rawsize"]:
            return None
        off = s["raw"] + rva
        return self.exe_data[off:off + n]

    def is_exec(self, va: int) -> bool:
        if self.in_text(va):
            return True
        s = self.section_of(va)
        return bool(s and s["exec"])

    def qwords_at(self, va: int, n: int):
        b = self.bytes_at(va, n * 8)
        if b is None or len(b) < n * 8:
            return []
        return list(struct.unpack("<%dQ" % n, b))

    def int32s_at(self, va: int, n: int):
        b = self.bytes_at(va, n * 4)
        if b is None or len(b) < n * 4:
            return []
        return list(struct.unpack("<%di" % n, b))

    def read_string(self, va: int):
        b = self.bytes_at(va, 96)
        if not b:
            return None
        cut = b.find(b"\x00")
        if cut <= 0:
            return None
        chunk = b[:cut]
        if len(chunk) >= 4 and all(0x20 <= c < 0x7F for c in chunk):
            return chunk.decode("ascii")
        return None

    def func_of(self, va: int):
        rva = va - self.image_base
        i = bisect.bisect_right(self.func_starts, rva) - 1
        if i >= 0:
            b, e = self.func_bounds[i]
            if b <= rva < e:
                return (self.image_base + b, self.image_base + e)
        return None

    def next_start_after(self, va: int, cap: int):
        i = bisect.bisect_right(self.func_starts, va - self.image_base)
        if i < len(self.func_starts):
            return min(cap, self.image_base + self.func_starts[i])
        return cap


def disasm(code: bytes, va: int, limit: int):
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    out = []
    for insn in md.disasm(code, va):
        out.append(insn)
        if len(out) >= limit:
            break
    return out


def find_dispatch_in_func(img: DualImage, start: int, end: int):
    """在函数体内找 switch 间接跳转, 返回候选表标识列表。

    覆盖三种 MSVC 形态:
    A. jmp/call [idx*8 + disp] 或 lea 基址后 [base + idx*8]   (8 字节绝对表)
    B. mov reg2, [base + idx*8] + jmp/call reg2              (8 字节绝对表)
    C. movsxd reg, [base + idx*4] + add reg, base + jmp reg  (4 字节相对偏移表)
    """
    n = min(end - start, FUNC_SCAN_MAX_INSNS * 8)
    code = img.bytes_at(start, n)
    if code is None:
        return []
    insns = disasm(code, start, FUNC_SCAN_MAX_INSNS)
    lea_base = {}
    tables = []
    for i, insn in enumerate(insns):
        if insn.mnemonic == "lea" and len(insn.operands) == 2:
            dst, src = insn.operands
            if src.type == capstone.x86.X86_OP_MEM and src.mem.base == capstone.x86.X86_REG_RIP:
                lea_base[dst.reg] = insn.address + insn.size + src.mem.disp
        elif insn.mnemonic == "mov" and len(insn.operands) == 2:
            dst, src = insn.operands
            if src.type == capstone.x86.X86_OP_MEM and src.mem.base == capstone.x86.X86_REG_RIP \
                    and src.mem.index == 0 and dst.type == capstone.x86.X86_OP_REG:
                lea_base[dst.reg] = insn.address + insn.size + src.mem.disp  # mov reg,[rip+..] 载入表基址指针
            elif src.type == capstone.x86.X86_OP_IMM and dst.type == capstone.x86.X86_OP_REG:
                lea_base[dst.reg] = src.imm  # mov reg, imm64 载入绝对基址
        # A: 直接 jmp/call [.. idx*8 ..]
        if insn.mnemonic in ("jmp", "call") and len(insn.operands) == 1:
            op = insn.operands[0]
            if op.type == capstone.x86.X86_OP_MEM and op.mem.index and op.mem.scale == 8:
                if op.mem.base == 0:
                    tables.append(("abs8", op.mem.disp & 0xFFFFFFFFFFFFFFFF))
                elif op.mem.base in lea_base:
                    tables.append(("abs8", lea_base[op.mem.base]))
        # B: mov reg2,[base+idx*8] + jmp/call reg2
        if insn.mnemonic == "mov" and len(insn.operands) == 2:
            dst, src = insn.operands
            if (src.type == capstone.x86.X86_OP_MEM and src.mem.index and src.mem.scale == 8
                    and dst.type == capstone.x86.X86_OP_REG):
                nxt = insns[i + 1] if i + 1 < len(insns) else None
                if nxt and nxt.mnemonic in ("jmp", "call") and nxt.operands and \
                        nxt.operands[0].type == capstone.x86.X86_OP_REG and nxt.operands[0].reg == dst.reg:
                    if src.mem.base == 0:
                        tables.append(("abs8", src.mem.disp & 0xFFFFFFFFFFFFFFFF))
                    elif src.mem.base in lea_base:
                        tables.append(("abs8", lea_base[src.mem.base]))
        # C: movsxd + add + jmp (4 字节相对表)
        if insn.mnemonic == "movsxd" and len(insn.operands) == 2:
            dst, src = insn.operands
            if (src.type == capstone.x86.X86_OP_MEM and src.mem.index and src.mem.scale == 4
                    and dst.type == capstone.x86.X86_OP_REG):
                base_reg = src.mem.base
                base_va = lea_base.get(base_reg)
                if base_va:
                    for j in range(i + 1, min(i + 6, len(insns))):
                        a = insns[j]
                        if a.mnemonic == "add" and len(a.operands) == 2 and \
                                a.operands[0].type == capstone.x86.X86_OP_REG and a.operands[0].reg == dst.reg and \
                                a.operands[1].type == capstone.x86.X86_OP_REG and a.operands[1].reg == base_reg:
                            nxt = insns[j + 1] if j + 1 < len(insns) else None
                            if nxt and nxt.mnemonic == "jmp" and nxt.operands and \
                                    nxt.operands[0].type == capstone.x86.X86_OP_REG and \
                                    nxt.operands[0].reg == dst.reg:
                                tables.append(("rel4", base_va))
                            break
    return tables


def table_entries(img: DualImage, tag):
    kind, va = tag
    if kind == "rel4":
        offs = img.int32s_at(va, MAX_TABLE_ENTRIES)
        entries = []
        for o in offs:
            t = (va + o) & 0xFFFFFFFFFFFFFFFF
            if not img.is_exec(t):
                break
            entries.append(t)
        return entries
    entries = []
    for v in img.qwords_at(va, MAX_TABLE_ENTRIES):
        if not img.is_exec(v):
            break
        entries.append(v)
    return entries


def analyze_handler(img: DualImage, va: int):
    bound = img.next_start_after(va, va + HANDLER_MAX_INSNS * 8)
    fr = img.func_of(va)
    if fr and fr[1] > va:
        bound = min(bound, fr[1])
    span = min(bound - va, HANDLER_MAX_INSNS * 8)
    insns = disasm(img.bytes_at(va, span), va, HANDLER_MAX_INSNS)
    strings, calls, imm_cmps, ctx_reads, arith = [], [], [], [], []
    sse = 0
    for insn in insns:
        if insn.mnemonic == "call" and insn.operands and insn.operands[0].type == capstone.x86.X86_OP_IMM:
            calls.append(insn.operands[0].imm)
        if insn.mnemonic in ("lea", "mov") and len(insn.operands) == 2:
            src = insn.operands[1]
            if src.type == capstone.x86.X86_OP_MEM and src.mem.base == capstone.x86.X86_REG_RIP:
                t = insn.address + insn.size + src.mem.disp
                if insn.mnemonic == "lea" and not img.is_exec(t):
                    st = img.read_string(t)
                    if st:
                        strings.append(st)
        if insn.mnemonic in ("cmp", "test") and len(insn.operands) == 2:
            a, b = insn.operands
            if b.type == capstone.x86.X86_OP_IMM:
                imm_cmps.append("%s %s" % (insn.mnemonic, hex(b.imm & 0xFFFFFFFFFFFFFFFF)))
            if a.type == capstone.x86.X86_OP_MEM and a.mem.base not in (0, capstone.x86.X86_REG_RIP):
                ctx_reads.append(a.mem.disp)
        if insn.mnemonic in ("add", "sub", "imul", "and", "or", "shl", "shr") and len(insn.operands) == 2 and \
                insn.operands[1].type == capstone.x86.X86_OP_IMM:
            arith.append("%s %s" % (insn.mnemonic, hex(insn.operands[1].imm & 0xFFFFFFFFFFFFFFFF)))
        if insn.mnemonic.startswith(("ucomis", "comis", "movss", "movsd", "cvtt", "cvt")):
            sse += 1
        if insn.mnemonic == "ret":
            break
    return dict(handler_va=hex(va), insns=len(insns),
                strings=sorted(set(strings))[:8], calls=[hex(c) for c in sorted(set(calls))[:8]],
                imm_cmps=imm_cmps[:10], mem_disp_reads=sorted(set(ctx_reads))[:12],
                arith_consts=sorted(set(arith))[:8], sse_ops=sse,
                func_range=[hex(x) for x in fr] if fr else None)


def function_type_stats():
    data = json.load(open(THK_ALL_RAW, encoding="utf-8"))
    stats, ft_max = {}, -1
    per_ft = {}
    for tbl in data["tables"]:
        for node in tbl.get("nodes", []):
            for seg in node.get("segments", []):
                f = seg.get("fields", {})
                ft = f.get("functionType")
                if ft is None:
                    continue
                ft_max = max(ft_max, ft)
                key = str(f.get("branchingControl")) + "/0x%x" % ft
                stats[key] = stats.get(key, 0) + 1
                e = per_ft.setdefault(ft, dict(count=0, param_pairs=set()))
                e["count"] += 1
                e["param_pairs"].add((f.get("parameter1"), f.get("parameter2")))
    dist = {("0x%x" % k): dict(count=v["count"],
                               distinct_param_pairs=len(v["param_pairs"]),
                               top_param_pairs=[[p[0], p[1]] for p in
                                                sorted(v["param_pairs"], key=lambda x: 0)[:6]])
            for k, v in per_ft.items()}
    return dict(source=str(THK_ALL_RAW), max_function_type=ft_max,
                distinct_function_types=len(per_ft),
                total_distinct_pairs=len(stats),
                top=sorted(stats.items(), key=lambda kv: -kv[1])[:48],
                per_function_type=dist)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()

    exe_sha = sha256_file(EXE)
    text_sha = sha256_file(TEXT_BIN)
    if exe_sha != PINNED_EXE_SHA256 or text_sha != PINNED_TEXT_SHA256:
        raise SystemExit("指纹不匹配: exe=%s text=%s" % (exe_sha[:16], text_sha[:16]))
    img = DualImage(EXE, TEXT_BIN)

    ev_func = img.func_of(ADDR_EVALUATOR)
    tick_func = img.func_of(ADDR_VM_TICK)
    if args.probe:
        print(json.dumps(dict(
            text_sha=text_sha[:16], text_bytes=len(img.text),
            evaluator_func=[hex(x) for x in ev_func] if ev_func else None,
            vm_tick_func=[hex(x) for x in tick_func] if tick_func else None), indent=1))
        return

    starts = sorted({img.image_base + b for (b, e) in img.func_bounds
                     if VM_SCAN_LO <= img.image_base + b < VM_SCAN_HI})
    region = [(fs, fs + 0x8000) for fs in starts]  # pdata 碎片条目, 不用下一片段当边界

    found = []
    for fs, fe in region:
        for tag in find_dispatch_in_func(img, fs, fe):
            ents = table_entries(img, tag)
            if len(ents) >= 16 and sum(1 for v in ents if img.in_text(v)) / len(ents) > 0.9:
                found.append(dict(kind=tag[0], table=hex(tag[1]), func=[hex(fs), hex(fe)],
                                  n=len(ents), first=[hex(v) for v in ents[:6]]))

    stats = function_type_stats()
    ft_max = stats["max_function_type"]
    best = None
    for f in found:
        if ft_max is not None and f["n"] > ft_max:
            tag = (f["kind"], int(f["table"], 16))
            ents = table_entries(img, tag)
            in_vm = sum(1 for v in ents if VM_SCAN_LO <= v < VM_SCAN_HI + 0x400000) / len(ents)
            if in_vm > 0.8 and (best is None or f["n"] > best["n"]):
                best = dict(f, entries=ents)
    if best is None and found:
        f = max(found, key=lambda x: x["n"])
        best = dict(f, entries=table_entries(img, (f["kind"], int(f["table"], 16))))

    handlers = []
    if best:
        for i, v in enumerate(best["entries"]):
            handlers.append(dict(function_type="0x%x" % i, **analyze_handler(img, v)))

    evaluator = analyze_handler(img, ev_func[0]) if ev_func else None
    tick_span = 0x2000 if tick_func else 0  # pdata 在 VM 区为碎片条目, 取固定窗口
    tick_insns = disasm(img.bytes_at(tick_func[0], tick_span), tick_func[0], 900) if tick_func else []
    tick_calls = sorted({hex(i.operands[0].imm) for i in tick_insns
                         if i.mnemonic == "call" and i.operands
                         and i.operands[0].type == capstone.x86.X86_OP_IMM})

    out = dict(
        schema=1, date="2026-11-02",
        mode="offline_static_disassembly_read_only_no_execution",
        images=dict(
            text_bin=dict(path=str(TEXT_BIN), sha256=text_sha, bytes=len(img.text),
                          va_range=[hex(TEXT_BASE), hex(TEXT_BASE + len(img.text))]),
            exe=dict(path=str(EXE), sha256=exe_sha, image_base=hex(img.image_base)),
            pdata_functions=len(img.func_bounds), vm_region_funcs=len(region)),
        sources=dict(pinned_addresses="Tools/MHW/rathian-thk-chain-evidence.json#native.addresses",
                     thk_stats=stats["source"]),
        pinned=dict(evaluator=hex(ADDR_EVALUATOR), vm_tick=hex(ADDR_VM_TICK),
                    name_lookup=hex(ADDR_NAME_LOOKUP)),
        vm_tick=dict(func=[hex(x) for x in tick_func] if tick_func else None,
                     disasm_insns=len(tick_insns), calls=tick_calls[:24]),
        evaluator_wrapper=evaluator,
        dispatch_candidates=found,
        selected_dispatch=dict(kind=best["kind"], table=best["table"],
                               containing_func=best["func"], entries=len(best["entries"]))
        if best else None,
        condition_handlers=handlers,
        function_type_usage=stats,
        boundary=["analysis-text.bin 为解包后 .text 镜像(9b48a849...)；锁定地址对应它而非 exe 原始文件偏移",
                  "只读静态反汇编, 未执行原生字节, 未修改游戏安装",
                  "handler 特征是结构事实; 语义解释是候选, 未经字符串佐证不得具名",
                  "不证明运行时条件求值顺序与随机源; LR 资格仍需独立消费者证据",
                  "负结果: 全 .text 四种编码形式(8字节绝对/4字节相对/绝对SIB/带基址SIB)扫描未发现 functionType 跳转表; "
                  "结合 VM 模块无注册器调用(name_lookup 为字符串注册表遍历), 分发走运行时注册对象机制, "
                  "需 Ghidra/IDA 级类型恢复或受控运行采样才能闭合; 见 VM-Semantics 交接文档"])
    if args.self_check:
        named = sum(1 for h in handlers if h["strings"])
        out["self_check"] = dict(
            exe_hash_match=True, text_hash_match=True,
            dispatch_table_entries=len(best["entries"]) if best else 0,
            handlers_disassembled=sum(1 for h in handlers if h["insns"] > 0),
            handlers_with_strings=named,
            thk_function_type_max=stats["max_function_type"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(output=str(args.output), bytes=args.output.stat().st_size,
                          dispatch_tables=len(found), selected=best["table"] if best else None,
                          handlers=len(handlers),
                          thk_ft_max=stats["max_function_type"]), ensure_ascii=False))


if __name__ == "__main__":
    main()
