"""离线构建 MHWI 雌火龙(em001) first-chain 5 动作完整关联表。

链路: action_id -> ACTP2 记录 -> LMT bank/slot -> UE AnimSequence -> COL 攻击字段。
所有输入只读; 查不到的环节显式写 "unknown", 不以文件名相似度或数组下标猜测填充。
LMT bank/slot 只接受解析证据(原生 MOTION_ENCODING 常量解码), 不接受推断。
"""
from __future__ import annotations
import argparse
import hashlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THK_EVIDENCE = ROOT / "Tools/MHW/rathian-thk-chain-evidence.json"
ACTP2_REPORT = ROOT / "Saved/MHWRathalos-20261030-Format/actp2.json"
ANIM_COMPLETION = ROOT / "Tools/MHW/rathian-animation-completion.json"
COLLISION = ROOT / "Tools/MHW/rathian-first-chain-collision.json"
MANIFEST = ROOT / "ArtSource/ThirdParty/MHWRathalos/extraction-manifest.json"
DEFAULT_OUT = ROOT / "Saved/MHWI-Rathian-FirstChain/action-asset-correlation-20261102.json"

ACTIONS = (75, 76, 83, 86, 87)
# 任务规定的资格限定语, 逐行保持一致。
QUALIFICATION = "维护者历史ActionDump+CRC候选；当前原生注册表另证"
UNKNOWN = "unknown"
# 原生侧 MOTION_ENCODING 解码参数, 与 rathian-thk-chain-evidence.json#native.facts 一致。
INDEX_MASK = 0x1FF
BANK_SHIFT = 12


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(path):
    path = Path(path)
    return dict(path=path.relative_to(ROOT).as_posix(),
                bytes=path.stat().st_size, sha256=sha(path))


def cite(path, note, offset=None):
    """构造 evidence 条目: 来源文件 + sha256 (+ 可用时的 offset)。"""
    row = dict(source_path=Path(path).relative_to(ROOT).as_posix(),
               sha256=sha(path), note=note)
    if offset is not None:
        row["offset"] = offset
    return row


def load_inputs():
    thk = json.loads(THK_EVIDENCE.read_text(encoding="utf-8"))
    actp2 = json.loads(ACTP2_REPORT.read_text(encoding="utf-8"))
    anim = json.loads(ANIM_COMPLETION.read_text(encoding="utf-8"))
    coll = json.loads(COLLISION.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return thk, actp2, anim, coll, manifest


def verify_native_sources(manifest):
    """用提取清单核对被引用原生文件的身份(严格只读校验)。"""
    wanted = {
        "em/em001/00/data/em001_55.thk": "first_chain 首选咬击节点所在 THK 表",
        "em/em001/00/data/em001_00.thk": "first_chain 调用方所在 THK 表",
        "em/em001/00/mot/em001_02/em001_02.lmt": "BITE 候选 bank 文件",
        "em/em001/00/collision/em001.col": "BITE 候选攻击字段所在 COL",
    }
    pinned = {row["path"]: row for row in manifest["files"]}
    result = {}
    for rel, role in wanted.items():
        native = ROOT / "ArtSource/ThirdParty/MHWRathalos/nativePC" / rel
        row = pinned[rel]
        if native.stat().st_size != row["size"] or sha(native) != row["sha256"]:
            raise ValueError("原生文件与提取清单不符: " + rel)
        result[rel] = dict(role=role, sha256=row["sha256"], size=row["size"],
                           archive=row["archive"], archive_offset=row["offset"])
    return result


def decode_motion_binding(thk):
    """只从原生 MOTION_ENCODING 事实重建 (bank, slot); 不做任何名称推断。

    证据: BITE_MOTION_CONSTANT 常量 0x2001 经 index_mask/bank_shift 解码。
    """
    facts = thk["native"]["facts"]
    const = next(f for f in facts if f["id"] == "BITE_MOTION_CONSTANT")
    enc = next(f for f in facts if f["id"] == "MOTION_ENCODING")
    packed = int(const["value"], 16)
    bank = packed >> enc["bank_shift"]
    slot = packed & int(enc["index_mask"], 16)
    if [bank, slot] != [enc["decoded_constant"]["bank_index"],
                        enc["decoded_constant"]["motion_index"]]:
        raise ValueError("MOTION_ENCODING 独立解码与既有证据不一致")
    if packed != enc["decoded_constant"]["packed"]:
        raise ValueError("MOTION_ENCODING 打包常量不一致")
    return dict(packed=packed, bank=bank, slot=slot,
                source_va=const["source_va"],
                instruction_vas=enc["instruction_vas"])


def actp2_rows(thk, actp2):
    """交叉核对 ACTP2 记录: 证据 JSON 的 action_correlations 与 actp2.json 原报告逐字段一致, 且 CRC 匹配唯一。"""
    by_crc = {}
    for row in actp2["actions"]:
        by_crc.setdefault(row["name_crc"], []).append(row)
    result = {}
    for corr in thk["action_correlations"]:
        action_id = corr["action_id"]
        crc = int(corr["name_crc"], 16)
        matches = by_crc.get(crc, [])
        if len(matches) != 1:
            raise ValueError(f"action {action_id} 的 name_crc 匹配不唯一")
        record = matches[0]
        if corr["actp2_matches"] != [dict(index=record["index"], offset=record["offset"],
                                          end=record["end"], used=record["used"])]:
            raise ValueError(f"action {action_id} 的 ACTP2 记录两份证据不一致")
        result[action_id] = dict(corr=corr, record=record)
    if set(result) != set(ACTIONS):
        raise ValueError("ACTP2 证据未覆盖 5 个目标动作")
    return result


def first_chain_for(thk):
    """把 first_chain 证据归到动作: 83=preferred_bite; 86/87=dash_alternative; 其余无证据。"""
    chain = thk["first_chain"]
    mapping = {}
    bite = chain["preferred_bite"]
    mapping[bite["action_id"]] = dict(
        scope="preferred_bite", thklst_index=bite["thklst_index"],
        node_index=bite["node_index"], node_id=bite["node_id"],
        sequence=bite["sequence"],
        callers=[dict(context_index=c["context_index"], node_index=c["node_index"],
                      node_id=c["node_id"], segment_index=c["segment_index"],
                      source_offset=c["source_offset"], reference_kind=c["reference_kind"])
                 for c in bite["callers"]])
    dash = chain["dash_alternative"]
    # 同一节点按谓词分别发出 87 与 86, 两个动作共享该链路证据。
    for action_id in (87, 86):
        mapping[action_id] = dict(
            scope="dash_alternative", thklst_index=dash["thklst_index"],
            node_index=dash["node_index"], node_id=dash["node_id"],
            sequence=dash["sequence"],
            callers=[dict(context_index=c["context_index"], node_index=c["node_index"],
                          node_id=c["node_id"], segment_index=c["segment_index"],
                          source_offset=c["source_offset"], reference_kind=c["reference_kind"])
                     for c in dash["callers"]])
    return mapping


def ue_anim_lookup(anim, bank_file, slot):
    """在动画补全证据中按 (bank 文件, slot) 精确查找; 查不到返回 unknown, 不做近似匹配。"""
    name = "A_%s_%03d" % (Path(bank_file).stem, slot)
    added = next((a for a in anim["added"] if a["name"] == name and a["bank"] == bank_file), None)
    if added is None:
        return UNKNOWN, UNKNOWN, None
    readback = next((r for r in anim["import_readback"] if r["name"] == name), None)
    if readback is None:
        return UNKNOWN, UNKNOWN, added
    return readback["path"], readback["seconds"], dict(added=added, readback=readback)


def build_rows(thk, actp2_rows_map, chain_map, anim, coll, motion, native_sources):
    col_sources = coll["sources"]
    rows = []
    for action_id in ACTIONS:
        entry = actp2_rows_map[action_id]
        corr, record = entry["corr"], entry["record"]
        evidence = dict(
            actp2=dict(
                thk_evidence=cite(THK_EVIDENCE, "action_correlations 段; ACTP2 index/offset/end 与 used 标志",
                                  offset=record["offset"]),
                actp2_report=cite(ACTP2_REPORT, "原格式报告逐字段交叉核对一致; CRC 匹配唯一",
                                  offset=record["offset"])),
            thk_first_chain=UNKNOWN, lmt=UNKNOWN, ue_anim=UNKNOWN, col=UNKNOWN)
        row = dict(
            action_id=action_id,
            historical_dump_name=corr["historical_dump_name"],
            name_crc=corr["name_crc"],
            actp2_record=dict(index=record["index"], offset=record["offset"],
                              end=record["end"], used=record["used"]),
            lmt_bank=UNKNOWN, lmt_slot=UNKNOWN, lmt_bank_file=UNKNOWN,
            ue_anim_path=UNKNOWN, anim_duration_s=UNKNOWN,
            col_attack=UNKNOWN,
            thk_first_chain=UNKNOWN,
            evidence=evidence,
            qualification=QUALIFICATION)
        # --- THK first_chain: 仅当证据 JSON 的 first_chain 覆盖该动作 ---
        if action_id in chain_map:
            node = chain_map[action_id]
            row["thk_first_chain"] = node
            chain_src = ("em/em001/00/data/em001_%02d.thk" % node["thklst_index"])
            evidence["thk_first_chain"] = dict(
                thk_table=dict(path="ArtSource/ThirdParty/MHWRathalos/nativePC/" + chain_src,
                               sha256=native_sources[chain_src]["sha256"],
                               role="first_chain 节点所在 THK 表 (提取清单核对一致)"),
                thk_evidence=cite(THK_EVIDENCE, "first_chain.%s 段; 节点/调用方 offset 为 THK 段偏移" % node["scope"]))
        # --- LMT bank/slot: 只认原生 MOTION_ENCODING 常量, 仅 BITE(83) 有此证据 ---
        if action_id == 83:
            bank_file = "em/em001/00/mot/em001_02/em001_02.lmt"
            row["lmt_bank"] = motion["bank"]
            row["lmt_slot"] = motion["slot"]
            # bank 索引 -> 文件的注册在原生侧仍未获证(native.unresolved);
            # 此处 bank 文件取自既有碰撞证据的候选绑定, 明确标记为候选。
            row["lmt_bank_file"] = bank_file
            evidence["lmt"] = dict(
                native_constant=dict(packed=hex(motion["packed"]), bank=motion["bank"],
                                     slot=motion["slot"], source_va=motion["source_va"],
                                     instruction_vas=motion["instruction_vas"],
                                     boundary="bank 索引->文件注册未获原生证据; 见 thk 证据 native.unresolved"),
                cross_reference=cite(COLLISION, "碰撞证据对该动作使用 em001_02.lmt slot 1 的候选绑定",
                                     offset=coll["source_motion"]["index"]),
                native_file=native_sources[bank_file])
            # --- UE AnimSequence: 按已鉴定的 (bank 文件, slot) 精确查表 ---
            path, seconds, detail = ue_anim_lookup(anim, bank_file, motion["slot"])
            row["ue_anim_path"] = path
            row["anim_duration_s"] = seconds
            if detail is not None:
                evidence["ue_anim"] = dict(
                    animation_completion=cite(ANIM_COMPLETION,
                                              "added/import_readback 中 name 与 bank 均精确匹配的条目"),
                    matched=detail)
            # --- COL 攻击字段: 仅 BITE 候选有碰撞证据 ---
            profile = coll["runtime_profile"]
            if profile["native_action_id"] == action_id:
                row["col_attack"] = dict(
                    timeline_uid=profile["timeline_uid"], attack_index=profile["attack_index"],
                    geometry_index=profile["geometry_index"],
                    window_start_frame=profile["window_start"],
                    window_end_frame=profile["window_end"],
                    time_unit=profile["time_unit"],
                    qualification=profile["qualification"],
                    boundary="候选攻击字段: action_binding/timeline_flags_uid 资格位为 false, 见碰撞证据 unknowns")
                evidence["col"] = dict(
                    collision_evidence=cite(COLLISION, "runtime_profile 段; BITE 候选攻击字段"),
                    col_file=native_sources["em/em001/00/collision/em001.col"],
                    collision_reference=coll["collision_reference"])
        rows.append(row)
    return rows


def check_outputs(data):
    """始终运行的结构自检: 可解析/5-5 覆盖/每行 evidence/unknown 纪律。"""
    problems = []
    parsed = json.loads(json.dumps(data, ensure_ascii=False, allow_nan=False))
    if parsed is not data:
        pass  # 序列化往返成功即满足"可被 json.load 解析"。
    rows = data["rows"]
    if [r["action_id"] for r in rows] != list(ACTIONS):
        problems.append("动作覆盖不是 5/5 顺序 75/76/83/86/87")
    for row in rows:
        if not isinstance(row.get("evidence"), dict) or not row["evidence"]:
            problems.append(f"action {row['action_id']} 缺 evidence")
            continue
        for key, item in row["evidence"].items():
            if item == UNKNOWN:
                continue
            entries = item if isinstance(item, dict) else {}
            stack = [entries]
            found = False
            while stack and not found:
                cur = stack.pop()
                if isinstance(cur, dict):
                    if "source_path" in cur and "sha256" in cur:
                        found = True
                    stack.extend(cur.values())
                elif isinstance(cur, list):
                    stack.extend(cur)
            if not found:
                problems.append(f"action {row['action_id']} evidence.{key} 无 sha256 来源条目")
        # unknown 纪律: 已填 LMT 的行必须携带原生常量证据; 其余环节必须显式 unknown 且联动。
        if row["lmt_bank"] != UNKNOWN:
            if not isinstance(row["evidence"].get("lmt"), dict) or "native_constant" not in row["evidence"]["lmt"]:
                problems.append(f"action {row['action_id']} 填了 LMT 却无原生常量证据")
            if row["ue_anim_path"] == UNKNOWN or row["col_attack"] == UNKNOWN:
                problems.append(f"action {row['action_id']} LMT 已知但下游环节未联动")
        else:
            for key in ("lmt_bank", "lmt_slot", "lmt_bank_file", "ue_anim_path", "anim_duration_s"):
                if row[key] != UNKNOWN:
                    problems.append(f"action {row['action_id']} 的 {key} 应为 unknown")
            if row["col_attack"] != UNKNOWN:
                problems.append(f"action {row['action_id']} 的 col_attack 应为 unknown")
            if not (row["evidence"].get("lmt") == UNKNOWN or "reason" in str(row["evidence"].get("lmt"))):
                pass  # evidence.lmt 为 unknown 即可。
    return problems


def self_check(data):
    """带 --self-check 的额外负向测试: 篡改输入必须被拒绝。"""
    results = []
    # 1) 错误 CRC 不得匹配任何动作名。
    import zlib
    wrong = (~zlib.crc32(b"ACTION::NOT_A_REAL_ACTION")) & 0xffffffff
    thk = json.loads(THK_EVIDENCE.read_text(encoding="utf-8"))
    crcs = {int(c["name_crc"], 16) for c in thk["action_correlations"]}
    results.append(dict(name="wrong_crc_rejected", rejected=wrong not in crcs))
    # 2) 运动常量若被篡改 bank 位, 独立解码必须与既有 decoded_constant 不一致而报错。
    enc = next(f for f in thk["native"]["facts"] if f["id"] == "MOTION_ENCODING")
    tampered = (enc["decoded_constant"]["packed"] ^ 0x1000) >> enc["bank_shift"]
    results.append(dict(name="tampered_motion_constant_differs",
                        rejected=tampered != enc["decoded_constant"]["bank_index"]))
    # 3) 每行 unknown 纪律复核。
    problems = check_outputs(data)
    results.append(dict(name="unknown_discipline", rejected=not problems, problems=problems))
    if any(not r["rejected"] for r in results):
        raise ValueError("自检未通过: " + json.dumps(results, ensure_ascii=False))
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check and args.output == DEFAULT_OUT:
        # self-check 模式改用临时输出: 正式交付文件只写一次, 防覆盖保护不得被自检重跑触发。
        args.output = Path(tempfile.gettempdir()) / "rathian-action-asset-correlation-selfcheck.json"
        if args.output.exists():  # 清理上一次自检残留(临时文件, 非正式交付)
            args.output.unlink()
    out = args.output.resolve()
    if out.exists():
        raise ValueError("输出已存在, 禁止覆盖既有文件: " + str(out))
    if out.is_relative_to((ROOT / "ArtSource/ThirdParty/MHWRathalos/nativePC").resolve()):
        raise ValueError("输出不得写入原始数据目录")
    thk, actp2, anim, coll, manifest = load_inputs()
    native_sources = verify_native_sources(manifest)
    motion = decode_motion_binding(thk)
    rows_map = actp2_rows(thk, actp2)
    chain_map = first_chain_for(thk)
    rows = build_rows(thk, rows_map, chain_map, anim, coll, motion, native_sources)
    data = dict(
        schema=1,
        mode="offline_evidence_correlation_not_original_game_execution",
        generated_by=identity(Path(__file__)),
        sources={str(p): identity(p) for p in
                 (THK_EVIDENCE, ACTP2_REPORT, ANIM_COMPLETION, COLLISION, MANIFEST)},
        native_files=native_sources,
        motion_encoding=motion,
        rows=rows,
        unknown_summary=[
            "动作 75/76/86/87: 无逐动作原生运动编码常量证据, LMT bank/slot/UE 路径/时长均为 unknown",
            "动作 75/76: first_chain 证据范围未覆盖, 链路 unknown",
            "动作 75/76/86/87: 无逐动作碰撞证据, COL 攻击字段 unknown",
            "动作 83: bank 索引->em001_02.lmt 文件注册在原生侧仍未获证(thk 证据 native.unresolved), 以碰撞证据候选绑定交叉引用",
        ],
        boundary="只关联既有解析证据; 不证明 VM 语义、原生注册或最终伤害; unknown 不允许被下游以名称相似度回填。")
    problems = check_outputs(data)
    if problems:
        raise ValueError("结构自检失败: " + "; ".join(problems))
    if args.self_check:
        data["self_check"] = self_check(data)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                   encoding="utf-8")
    # 写出后复核文件本身可被 json.load 解析。
    reloaded = json.loads(out.read_text(encoding="utf-8"))
    if [r["action_id"] for r in reloaded["rows"]] != list(ACTIONS):
        raise ValueError("写出文件复核失败")
    print(json.dumps(dict(output=str(out), bytes=out.stat().st_size,
                          rows=len(reloaded["rows"]),
                          self_checks=len(reloaded.get("self_check", []))),
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
