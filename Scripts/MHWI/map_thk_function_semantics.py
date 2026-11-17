"""将 Leviathon default.fexty 条件函数命名映射到本项目 60 种 THK functionType（BEH-01/BEH-03 复用）。

输入(只读):
- Saved/MHWI-Rathian-FirstChain/Leviathon/.../common/default.fexty  (社区条件映射, 145 行)
- Saved/MHWI-Rathian-FirstChain/thk-condition-semantics-20261102.json (我们全量统计)

输出: Tools/MHW/rathian-thk-fexty-coverage-20261103.json
边界: 社区命名 = 优先验证的候选映射, 不自动证明运行语义; 需与本机字节/运行观测核对后才可升证据级。
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FEXTY = (ROOT / "Saved/MHWI-Rathian-FirstChain/Leviathon/"
         "Leviathon-1e647f08ed4356e9feac037ccec7c08149fa2ef5/common/default.fexty")
STATS = ROOT / "Saved/MHWI-Rathian-FirstChain/thk-condition-semantics-20261102.json"
DEFAULT_OUT = ROOT / "Tools/MHW/rathian-thk-fexty-coverage-20261103.json"

SIMPLE = re.compile(r"^([0-9A-F]+)\s*:\s*(.+)$")
BLOCK_OPEN = re.compile(r"^([0-9A-F]+)\s*\{\s*$")
BLOCK_ROW = re.compile(r"^\s*(?:parameter1\s*==\s*([0-9A-F]+)\s*:\s*)?(.+?)\s*$")


def parse_fexty(path: Path):
    mapping = {}
    block = None
    selector = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("Use Hex"):
            continue
        m = SIMPLE.match(line)
        if m:
            mapping[int(m.group(1), 16)] = dict(kind="expr", expr=m.group(2).strip(), cases=[])
            continue
        m = BLOCK_OPEN.match(line)
        if m:
            block = int(m.group(1), 16)
            mapping[block] = dict(kind="block", expr="", cases=[], selector=None)
            continue
        if block is not None:
            if line == "}":
                block = None
                selector = None
                continue
            if line.startswith(">"):
                mapping[block]["selector"] = line[1:].strip()
                continue
            m = BLOCK_ROW.match(line)
            if m:
                p1 = m.group(1)
                expr = m.group(2).strip()
                if p1 is not None:
                    mapping[block]["cases"].append([p1, expr])
                elif expr.lower().startswith("otherwise"):
                    mapping[block]["cases"].append(["otherwise", expr.split(":", 1)[-1].strip()])
                elif mapping[block]["expr"] == "":
                    mapping[block]["expr"] = expr
    return mapping


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    if not FEXTY.exists() or not STATS.exists():
        raise SystemExit("缺少输入: fexty 或统计 JSON")
    fexty = parse_fexty(FEXTY)
    stats = json.load(open(STATS, encoding="utf-8"))
    per_ft = stats["function_type_usage"]["per_function_type"]

    rows, covered, uncovered = [], 0, 0
    total_uses = 0
    covered_uses = 0
    for ft_hex, info in per_ft.items():
        ft = int(ft_hex, 16)
        count = info["count"]
        total_uses += count
        entry = fexty.get(ft)
        if entry:
            covered += 1
            covered_uses += count
            name = entry["expr"] or ("switch(" + (entry.get("selector") or "param1") + ")")
            row = dict(function_type=ft_hex, uses=count, fexty=name,
                       selector=entry.get("selector"),
                       param_cases=entry["cases"][:8],
                       top_params=info.get("top_param_pairs", [])[:4],
                       status="community-mapped-pending-verification")
        else:
            uncovered += 1
            row = dict(function_type=ft_hex, uses=count, fexty=None,
                       top_params=info.get("top_param_pairs", [])[:4],
                       status="unmapped")
        rows.append(row)

    rows.sort(key=lambda r: -r["uses"])
    # 结构段（非条件）：thk.py 注释 "ifs can't have a 00 on checkType" —— ft 0x0 为基础动作段，
    # 0x2 为流程段；二者不参与条件语义分母（各自语义由 actionID/流程处理）。
    STRUCTURAL = {0x0, 0x2}
    cond_rows = [r for r in rows if int(r["function_type"], 16) not in STRUCTURAL]
    cond_uses = sum(r["uses"] for r in cond_rows)
    cond_covered = sum(r["uses"] for r in cond_rows if r["fexty"])
    cond_types = len(cond_rows)
    cond_types_covered = sum(1 for r in cond_rows if r["fexty"])
    out = dict(
        schema=1, date="2026-11-03",
        mode="community_mapping_cross_reference_read_only",
        sources=dict(
            fexty=dict(path=str(FEXTY.relative_to(ROOT)),
                       note="Leviathon commit 1e647f08; community mapping, candidate semantics only"),
            stats=dict(path=str(STATS.relative_to(ROOT)),
                       note="本机 13015 段 functionType 全量统计")),
        coverage=dict(
            distinct_function_types=len(per_ft),
            mapped_by_fexty=covered,
            unmapped=uncovered,
            mapped_ratio=round(covered / max(1, len(per_ft)), 3),
            total_segment_uses=total_uses,
            uses_covered=covered_uses,
            uses_covered_ratio=round(covered_uses / max(1, total_uses), 3),
            structural_types=["0x0", "0x2"],
            structural_uses=total_uses - cond_uses,
            condition_types=cond_types,
            condition_types_covered=cond_types_covered,
            condition_types_ratio=round(cond_types_covered / max(1, cond_types), 3),
            condition_uses=cond_uses,
            condition_uses_covered=cond_covered,
            condition_uses_ratio=round(cond_covered / max(1, cond_uses), 3)),
        rows=rows,
        boundary=[
            "社区命名=fexty 中的候选映射, 不自动等于运行语义; 需逐项与本机字节/参数形态/运行观测核对",
            "0x0/0x2 为结构段(动作/流程), 不参与条件语义分母",
            "升级为 [已证] 前必须完成: 参数形态一致性(本表 top_params 可先做)+ 受控运行观测",
        ])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    cov = out["coverage"]
    print(json.dumps(cov, ensure_ascii=False))
    print("--- top rows ---")
    for r in rows[:14]:
        name = r["fexty"] or "(unmapped)"
        print("0x%-4s uses=%-5d %s %s" % (r["function_type"][2:], r["uses"], name,
                                          r["top_params"] if r["top_params"] else ""))


if __name__ == "__main__":
    main()
