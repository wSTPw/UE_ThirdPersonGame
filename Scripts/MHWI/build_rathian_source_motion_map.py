# -*- coding: utf-8 -*-
"""
build_rathian_source_motion_map.py
==================================
雌火龙（Rathian, em001）"源动作 → UE 资产" 语义映射表生成脚本（首版）。

对应工作包：
  - Docs/Plans/PLAN-20261102-001-rathian-completeness-parallel.md 的 P4 工作包
  - 上游要求：Docs/Plans/PLAN-20261031-005-rathian-animation-assets.md 的 A0/A1

输入（严格只读，绝不修改）：
  1. Tools/MHW/rathian-animation-completion.json
     - verification.banks[]: 19 个 LMT bank 的 path/sha256/slots/valid/frames
       frames 为 {slot_name: 帧数}，848 个有效 slot 全部在此枚举。
     - added[] (824): 单条含 name/bank/source_frames/expected_seconds/fbx_sha256。
     - existing[] (24): 仅资产名（历史保留资产，无单条 SHA）。
     - import_readback[] (824): UE 导入回读 name/path/seconds/skeleton。
  2. Tools/MHW/rathian-thk-chain-evidence.json
     - action_correlations / tables / first_chain: 5 个动作
       (75/76/83/86/87) 的 THK 注册与调用链证据。
       注意：该文件不含任何 bank+slot ↔ 动作 的显式映射字段，
       故本脚本仅做"显式字段存在性"检测，找不到即留空，
       绝不凭 bank 名 / slot 序号猜测。

输出：
  Tools/MHW/rathian-source-motion-map-20261102.json（可用 --out 覆盖）

硬性边界：
  - qualification 一律 "unknown"：即使 848 条资产身份已验证，
    "战斗招式资格"语义仍未闭合（待 A0/A1），不得写 "verified"。
  - 本表为工程索引，不提升任何原作语义状态。

用法：
  python Scripts/MHWI/build_rathian_source_motion_map.py [--out PATH] [--self-check]
"""

import argparse
import hashlib
import json
import sys
from collections import OrderedDict
from pathlib import Path

# ---------------------------------------------------------------------------
# 路径常量（相对项目根 e:\Unreal Projects\IntorCpp）
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPLETION_JSON = PROJECT_ROOT / "Tools" / "MHW" / "rathian-animation-completion.json"
CHAIN_EVIDENCE_JSON = PROJECT_ROOT / "Tools" / "MHW" / "rathian-thk-chain-evidence.json"
DEFAULT_OUT = PROJECT_ROOT / "Tools" / "MHW" / "rathian-source-motion-map-20261102.json"

# UE 侧常量
ANIM_ROOT = "/Game/MHWI/Rathalos/Animations"
SKELETON = "/Game/MHWI/Rathalos/Mesh/SK_EM001_Body_Skeleton"

# 关联的 5 个原作动作 id（来自 THK 链路证据）
LINKED_ACTION_IDS = [75, 76, 83, 86, 87]

GENERATED_DATE = "2026-11-02"
SCHEMA_VERSION = 1


def sha256_of_file(path: Path) -> str:
    """计算文件级 SHA256（只读）。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    """只读加载 JSON 证据文件。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 1) 从 completion 证据枚举 848 条有效 slot
# ---------------------------------------------------------------------------
def build_rows_from_completion(completion: dict) -> list:
    """
    以 verification.banks[].frames 为唯一权威来源枚举全部 848 条。

    每行字段：
      source_sha256        added 条目 → fbx_sha256（单条级，FBX 中间产物哈希）；
                           existing 条目 → 所在 bank 的 LMT 文件级 sha256（注明）；
                           两者都没有 → "unknown"。
      bank                 LMT bank 源路径（如 em/em001/00/mot/em001_00/em001_00.lmt）
      slot                 从 slot_name 尾段解析出的整数 slot 号
      ue_asset_path        import_readback 有则用回读值，否则按既有命名规则构造
      skeleton             固定 SK_EM001_Body_Skeleton
      duration_s           import_readback 的 UE 实测秒数；existing 24 条无回读
                           且 expected→帧数存在两种口径（(n-1)/60 与 n/60），
                           不得猜测 → 置 None (null)
      qualification        一律 "unknown"
      linked_native_actions 仅当 chain 证据中有显式 bank+slot → 动作映射才填，
                           否则空数组（本版证据中不存在该映射，故全空）
    """
    # 三个辅助索引：资产名 → added 条目 / readback 条目
    added_by_name = {a["name"]: a for a in completion.get("added", [])}
    readback_by_name = {r["name"]: r for r in completion.get("import_readback", [])}

    rows = []
    for bank in completion["verification"]["banks"]:
        bank_path = bank["path"]
        bank_sha = bank.get("sha256", "unknown")
        for slot_name, frame_count in bank["frames"].items():
            asset_name = "A_" + slot_name
            # slot 号 = slot_name 尾段数字（如 em001_00_026 → 26）
            slot_no = int(slot_name.rsplit("_", 1)[1])

            added = added_by_name.get(asset_name)
            rb = readback_by_name.get(asset_name)

            # 单条 SHA：added 有 fbx_sha256；existing 用 bank 文件级 SHA
            if added is not None and added.get("fbx_sha256"):
                source_sha = added["fbx_sha256"]
            else:
                source_sha = bank_sha  # existing：bank 级哈希，已在顶层 note 注明

            # UE 资产路径：优先 readback 回读值，否则按 readback 统一模式构造
            if rb is not None:
                ue_path = rb["path"]
            else:
                ue_path = f"{ANIM_ROOT}/{asset_name}.{asset_name}"

            # duration：仅 UE 实测回读值；无回读不猜测
            duration_s = rb["seconds"] if rb is not None else None

            rows.append({
                "source_sha256": source_sha,
                "bank": bank_path,
                "slot": slot_no,
                "ue_asset_path": ue_path,
                "skeleton": SKELETON,
                "duration_s": duration_s,
                "qualification": "unknown",
                "linked_native_actions": [],
                # 内部排序/对账用字段，输出前剔除
                "_asset_name": asset_name,
                "_slot_name": slot_name,
                "_frames": frame_count,
            })

    # 排序：bank 路径 → slot 号
    rows.sort(key=lambda r: (r["bank"], r["slot"]))
    return rows


# ---------------------------------------------------------------------------
# 2) 从 chain 证据中提取显式 bank+slot → 动作 映射（存在才填，绝不猜测）
# ---------------------------------------------------------------------------
def extract_bank_slot_action_links(chain: dict) -> dict:
    """
    扫描 action_correlations / tables / first_chain，
    仅当某个动作条目带有明确指向 LMT bank + slot 的字段
    （键名含 lmt/bank/slot/motion 且值可直接对应 completion 中的
    bank 路径或 slot 号）时，才登记该映射。

    本版证据（schema 1）的 action_correlations 只含
    action_id / historical_dump_name / name_crc / actp2_matches（动作注册表
    字节偏移），tables/first_chain 只含 THK 节点调用链——均不含
    bank+slot 信息，因此预期返回空映射，所有行 linked_native_actions=[]。
    """
    links = {}  # {(bank_path, slot_no): [action_id, ...]}
    keywords = ("lmt", "bank", "slot", "motion")

    def scan_entry(entry: dict, action_id):
        """在单个动作证据条目里查找显式 bank/slot 字段。"""
        found = []
        for k, v in entry.items():
            kl = k.lower()
            if any(kw in kl for kw in keywords):
                # 键名命中只是候选，还要求值是可直接对账的：
                #   bank → 字符串路径；slot → 整数
                if isinstance(v, str) and (v.endswith(".lmt") or "mot/" in v):
                    found.append(("bank", v))
                elif isinstance(v, int) and ("slot" in kl):
                    found.append(("slot", v))
        # 只有 bank 和 slot 同时显式出现，才算"明确对应"
        banks = [v for t, v in found if t == "bank"]
        slots = [v for t, v in found if t == "slot"]
        for b in banks:
            for s in slots:
                links.setdefault((b, s), [])
                if action_id not in links[(b, s)]:
                    links[(b, s)].append(action_id)

    # action_correlations：每个条目对应一个动作
    for entry in chain.get("action_correlations", []):
        if isinstance(entry, dict) and "action_id" in entry:
            scan_entry(entry, entry["action_id"])

    # first_chain / tables：不含 action_id 顶层的结构，只递归查字典字段，
    # 若未来证据版本加入 motion slot 引用，可在此被捕获
    for chain_key in ("first_chain",):
        sub = chain.get(chain_key, {})
        if isinstance(sub, dict):
            for sub_entry in sub.values():
                if isinstance(sub_entry, dict) and "action_id" in sub_entry:
                    scan_entry(sub_entry, sub_entry["action_id"])

    return links


def apply_links(rows: list, links: dict) -> int:
    """把显式映射写入行；返回命中的行数。"""
    hit = 0
    for r in rows:
        key = (r["bank"], r["slot"])
        if key in links:
            r["linked_native_actions"] = sorted(links[key])
            hit += 1
    return hit


# ---------------------------------------------------------------------------
# 3) 组装顶层文档
# ---------------------------------------------------------------------------
def build_document(rows: list, completion_path: Path, chain_path: Path,
                   linked_hit_rows: int, expected_total: int) -> dict:
    # per_bank 计数（按 bank 源路径统计）
    per_bank = OrderedDict()
    for r in rows:
        per_bank[r["bank"]] = per_bank.get(r["bank"], 0) + 1

    null_duration = sum(1 for r in rows if r["duration_s"] is None)
    linked_actions_with_rows = sorted({
        a for r in rows for a in r["linked_native_actions"]
    })

    note = (
        "qualification 全部 unknown，待 A0/A1 语义闭合；本表为工程索引，"
        "不提升任何原作语义状态。"
        "source_sha256 语义：added 824 条为单条 fbx_sha256（导入用 FBX 中间产物哈希，"
        "非原作 LMT 单条哈希，原作侧仅有 bank 文件级 sha256）；"
        "existing 24 条（历史保留资产）无单条 SHA，如实填所在 bank 的 LMT 文件级 sha256。"
        f"duration_s：{len(rows) - null_duration} 条来自 UE 导入回读实测秒数；"
        f"{null_duration} 条（existing 历史资产，无回读）为 null——expected_seconds 与帧数"
        "存在 (n-1)/60 与 n/60 两种口径，不得猜测。"
        f"linked_native_actions：chain 证据（action_correlations/tables/first_chain）"
        f"不含 bank+slot ↔ 动作的显式映射字段，故全部留空（命中 {linked_hit_rows} 行；"
        f"5 个候选动作 {LINKED_ACTION_IDS} 中有证据行级关联的为 {linked_actions_with_rows}），"
        "不得凭 bank 名/slot 序号猜测。"
    )

    return {
        "schema": SCHEMA_VERSION,
        "generated": GENERATED_DATE,
        "generated_by": "Scripts/MHWI/build_rathian_source_motion_map.py",
        "sources": [
            {
                "path": str(completion_path).replace("\\", "/"),
                "sha256": sha256_of_file(completion_path),
                "role": "848 条 bank/slot→UE 资产映射证据（只读）",
            },
            {
                "path": str(chain_path).replace("\\", "/"),
                "sha256": sha256_of_file(chain_path),
                "role": "5 个动作 THK 链路证据（只读；不含 bank+slot 映射）",
            },
        ],
        "counts": {
            "total": len(rows),
            "expected_total": expected_total,
            "per_bank": per_bank,
        },
        "note": note,
        "rows": [
            {k: v for k, v in r.items() if not k.startswith("_")}
            for r in rows
        ],
    }


# ---------------------------------------------------------------------------
# 4) 自检
# ---------------------------------------------------------------------------
def self_check(doc: dict, completion: dict) -> list:
    """返回错误列表；空列表即通过。"""
    errors = []
    rows = doc["rows"]

    # (a) 行数 == 848（与 completion 证据 verification.total / frames 枚举数一致）
    expected = completion["verification"]["total"]
    if len(rows) != expected:
        errors.append(f"行数不符：got {len(rows)}, expected {expected}")
    frames_total = sum(
        len(b["frames"]) for b in completion["verification"]["banks"]
    )
    if frames_total != expected:
        errors.append(f"completion frames 枚举数 {frames_total} != verification.total {expected}")

    # (b) 每行字段完整
    required = ["source_sha256", "bank", "slot", "ue_asset_path", "skeleton",
                "duration_s", "qualification", "linked_native_actions"]
    for i, r in enumerate(rows):
        missing = [k for k in required if k not in r]
        if missing:
            errors.append(f"行 {i} 缺字段：{missing}")
        if r.get("qualification") != "unknown":
            errors.append(f"行 {i} qualification 非 unknown：{r.get('qualification')!r}")

    # (c) ue_asset_path 前缀
    for i, r in enumerate(rows):
        if not str(r.get("ue_asset_path", "")).startswith(ANIM_ROOT + "/"):
            errors.append(f"行 {i} ue_asset_path 前缀不符：{r.get('ue_asset_path')}")

    # (d) 无重复 (bank, slot)
    seen = set()
    for i, r in enumerate(rows):
        key = (r["bank"], r["slot"])
        if key in seen:
            errors.append(f"行 {i} 重复 (bank,slot)：{key}")
        seen.add(key)

    return errors


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="生成雌火龙源动作→UE资产语义映射表（qualification 一律 unknown）")
    parser.add_argument("--out", type=str, default=str(DEFAULT_OUT),
                        help="输出 JSON 路径（默认 Tools/MHW/rathian-source-motion-map-20261102.json）")
    parser.add_argument("--self-check", action="store_true",
                        help="生成后执行自检（行数/字段/前缀/去重）")
    args = parser.parse_args()

    # 输入严格只读：仅 open('r')，绝不写入
    completion = load_json(COMPLETION_JSON)
    chain = load_json(CHAIN_EVIDENCE_JSON)

    # 1) 枚举 848 行
    rows = build_rows_from_completion(completion)

    # 2) 关联 5 个动作（仅显式映射）
    links = extract_bank_slot_action_links(chain)
    linked_hit_rows = apply_links(rows, links)

    # 3) 顶层文档
    doc = build_document(
        rows, COMPLETION_JSON, CHAIN_EVIDENCE_JSON,
        linked_hit_rows, expected_total=completion["verification"]["total"],
    )

    # 4) 自检
    if args.self_check:
        errors = self_check(doc, completion)
        if errors:
            print("[self-check] 失败：")
            for e in errors[:50]:
                print("  -", e)
            if len(errors) > 50:
                print(f"  ... 共 {len(errors)} 条错误")
            sys.exit(1)
        n_null = sum(1 for r in doc["rows"] if r["duration_s"] is None)
        print("[self-check] 通过：")
        print(f"  行数 = {len(doc['rows'])} == verification.total = {completion['verification']['total']}")
        print(f"  全部行字段完整，qualification 全为 unknown")
        print(f"  ue_asset_path 全部以 {ANIM_ROOT}/ 开头")
        print(f"  无重复 (bank,slot)")
        print(f"  duration_s 为 null 的行（existing 无回读，不猜测）= {n_null}")
        print(f"  linked_native_actions 非空行 = {linked_hit_rows}")

    # 5) 写出
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")

    size = out_path.stat().st_size
    print(f"[out] {out_path} ({size} bytes, rows={len(doc['rows'])})")


if __name__ == "__main__":
    main()
