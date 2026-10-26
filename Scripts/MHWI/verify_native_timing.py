"""Independently check the native timing audit against supplied LMT95/XFS19.

This is a static file audit. It neither runs MHW/UE nor writes gameplay assets.
Key offsets/types are checked without calling audit_native_timing.parse_lmt.
FSM comparison reuses the project's XFS reader (not an independent XFS decoder).
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct

from read_source_fsm import XfsReader

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUDIT = ROOT / "Saved/MHWIImport/SourceFidelity-20261024/timing-native-full.json"
DEFAULT_OUTPUT = ROOT / "Saved/MHWIImport/SourceFidelity-20261024/timing-verification.json"
DEFAULT_READBACK = ROOT / "Saved/MHWIImport/SourceFidelity-20261024/editor-readback.json"
COMMON, INPUT, COLLISION = 1221988687, 1875693838, 956269290


def seq(value):
    return value if isinstance(value, list) else ([] if value is None else [value])


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def properties(value):
    if isinstance(value, dict):
        if value.get("mPropertyName"):
            yield value["mPropertyName"]
        for child in value.values():
            yield from properties(child)
    elif isinstance(value, list):
        for child in value:
            yield from properties(child)


class Verification:
    def __init__(self):
        self.assertion_count, self.errors = 0, []

    def check(self, actual, expected, where):
        self.assertion_count += 1
        if actual != expected:
            self.errors.append({"where": where, "actual": actual, "expected": expected})

    def lmt(self, path, report):
        data = path.read_bytes()

        def at(fmt, offset):
            size = struct.calcsize("<" + fmt)
            if not 0 <= offset <= len(data) - size:
                raise ValueError(("out_of_bounds", offset, fmt, len(data)))
            return struct.unpack_from("<" + fmt, data, offset)

        self.check(data[:4], b"LMT\0", "lmt.signature")
        self.check(at("H", 4)[0], 95, "lmt.version")
        self.check(digest(path), report["sha256"], "lmt.sha256")
        self.check(len(data), report["size"], "lmt.size")
        offsets = at(str(at("H", 6)[0]) + "Q", 16)
        expected_ids = [i for i, off in enumerate(offsets) if off]
        self.check([e["index"] for e in report["entries"]], expected_ids, "lmt.entry_order")
        entry_offsets, counts = [], Counter()
        for entry in report["entries"]:
            index = entry["index"]
            off = offsets[index]
            where = f"motion[{index}]"
            # LMTActionHeader: fcurveOffset Q, fcurveCount I, frameCount I,
            # loopFrame i, then remaining 68 bytes, then timlOffset Q.
            self.check(entry["source_frame_count"], at("I", off + 12)[0], where + ".frame_count")
            self.check(entry["source_loop_frame"], at("i", off + 16)[0], where + ".loop_frame")
            timl = at("Q", off + 88)[0]
            entry_offsets.append({"motion": index, "header_offset": off, "timl_offset": timl})
            if not timl:
                self.check(entry["groups"], [], where + ".no_timl")
                continue
            group_ptr, group_count, ix0, ix1, end, loop, control, label = at("QQiiffiI", timl)
            self.check(entry["timl"], {"length": end, "loop_start": loop, "loop_control": control,
                                      "data_ix0": ix0, "data_ix1": ix1, "label_hash": label}, where + ".timl")
            self.check(len(entry["groups"]), group_count, where + ".group_count")
            for gi, group in enumerate(entry["groups"]):
                track_ptr, track_count, group_hash, unknown = at("QQIi", group_ptr + gi * 24)
                gw = where + f".group[{gi}]"
                self.check([group["order"], group["hash"], group["unknown"], len(group["tracks"])],
                           [gi, group_hash, unknown, track_count], gw + ".header")
                counts["groups"] += 1
                for ti, track in enumerate(group["tracks"]):
                    key_ptr, key_count, field_hash, kind = at("QQIi", track_ptr + ti * 24)
                    tw = gw + f".track[{ti}]"
                    self.check([track["order"], track["hash"], track["kind"], len(track["keys"])],
                               [ti, field_hash, kind, key_count], tw + ".header")
                    counts["tracks"] += 1
                    for ki, key in enumerate(track["keys"]):
                        pos = key_ptr + ki * 20
                        if kind == 3:
                            raw = [list(at("4B", pos)), *at("ff", pos + 4)]
                        else:
                            raw = at({0: "3i", 1: "3I", 2: "3f", 4: "3I"}[kind], pos)
                        frame, transition, key_kind = at("fhh", pos + 12)
                        expected = {"frame": frame, "value": raw[0], "control_l": raw[1],
                                    "control_r": raw[2], "transition": transition, "key_kind": key_kind}
                        self.check(key, expected, tw + f".key[{ki}]")
                        counts["keys"] += 1
        return {"slot_count": len(offsets), "null_slots": len(offsets) - len(expected_ids),
                "motions": len(expected_ids), **counts, "offsets": entry_offsets}

    def fsm(self, path, report):
        data = path.read_bytes()
        reader = XfsReader(data)
        root = reader.parse()["root"]
        nodes = seq(root["mpRootCluster"]["mpNodeList"])
        conditions = {str(c["mName"]["mId"]): c["mpRootNode"]
                      for c in seq(root["mpConditionTree"]["mpTreeList"])}
        self.check(digest(path), report["fsm_sha256"], "fsm.sha256")
        self.check(reader.pos, len(data), "fsm.consumed_entire_file")
        self.check(conditions, report["all_conditions"], "fsm.complete_conditions")
        self.check([n["mId"] for n in nodes], [n["node_id"] for n in report["fsm_nodes"]], "fsm.node_order")
        node_table, omitted, unsorted = [], [], []
        for order, (native, audited) in enumerate(zip(nodes, report["fsm_nodes"])):
            where = f"fsm.node[{order}]"
            self.check(native["mName"], audited["name"], where + ".name")
            self.check(native["mpProcessList"], audited["process"], where + ".process")
            links = seq(native["mpLinkList"])
            stripped = [{k: v for k, v in link.items() if k not in ("condition_tree", "condition_summary")}
                        for link in audited["links"]]
            self.check(links, stripped, where + ".ordered_raw_links")
            for link in audited["links"]:
                self.check(link["condition_tree"], conditions.get(str(link["mConditionId"])), where + ".link_condition")
            raw_names = [l["mName"] for l in links]
            if raw_names != sorted(raw_names):
                unsorted.append(native["mId"])
            metadata = {k: v for k, v in native.items() if k not in ("mId", "mName", "mpProcessList", "mpLinkList")}
            omitted.append({"node": native["mId"], "metadata": metadata})
            node_table.append({"serialized_order": order, "node": native["mId"], "name": native["mName"],
                               "process": native["mpProcessList"],
                               "links_in_serialized_order": [self.route(l, report) for l in audited["links"]]})
        return root, {"nodes": len(nodes), "links": sum(len(n["links"]) for n in report["fsm_nodes"]),
                      "conditions": len(conditions), "node_table": node_table, "omitted_metadata": omitted,
                      "nodes_whose_link_order_differs_from_name_order": unsorted,
                      "order_semantics": "Serialization order preserved. Native evaluator priority is not decoded; do not sort by link name or claim array order proves runtime precedence.",
                      "root_metadata": {k: v for k, v in root.items() if k not in ("mpRootCluster", "mpConditionTree")},
                      "cluster_metadata": {k: v for k, v in root["mpRootCluster"].items() if k != "mpNodeList"}}

    @staticmethod
    def route(link, report):
        destination = next(n for n in report["fsm_nodes"] if n["node_id"] == link["mDestinationNodeId"])
        return {"link_name": link["mName"], "destination": link["mDestinationNodeId"],
                "destination_name": destination["name"], "destination_process": destination["process"],
                "condition_id": link["mConditionId"], "condition_tree": link["condition_tree"],
                "condition_properties": list(properties(link["condition_tree"]))}


def action_table(report, mapping, history, formal):
    entries = {e["index"]: e for e in report["source"]["entries"]}
    nodes = {n["node_id"]: n for n in report["fsm_nodes"]}
    result = []
    for move, definition in mapping["moves"].items():
        motion = int(definition["clip"].rsplit("_", 1)[1])
        entry, node = entries[motion], nodes[definition["fsm_node_id"]]
        tracks = [{"group_order": g["order"], "group_hash": g["hash"], "group": g["name"], **t}
                  for g in entry["groups"] for t in g["tracks"]]
        inputs = [t for t in tracks if t["group_hash"] == INPUT]
        collisions = [t for t in tracks if t["group_hash"] == COLLISION]
        focus = [t for t in tracks if t["name"] in ("mMotionSpeed", "mActionPhase", "mActionPhaseSub",
                 "mLinkMotionPhase", "mAttackAdjustAngleIndex", "mTurnSpeed", "mWeaponMotionNo", "mPosInterpolationProgress")]
        routes = []
        for order, link in enumerate(node["links"]):
            route = Verification.route(link, report)
            route["serialized_order"] = order
            destination = nodes[link["mDestinationNodeId"]]
            if destination["process"]["mContainerName"].startswith("LinkMotion"):
                route["connector_exit_links"] = [Verification.route(l, report) for l in destination["links"]]
            routes.append(route)
        result.append({"move": move, "motion": motion, "fsm_node": node["node_id"], "fsm_action": node["process"]["mpParameter"],
                       "mapping_status": definition["mapping_status"],
                       "source_frame_count": entry["source_frame_count"], "source_loop_frame": entry["source_loop_frame"],
                       "timl": entry.get("timl"), "input_key_tracks": inputs, "collision_tracks": collisions,
                       "source_focus_tracks": focus, "native_routes": routes,
                       "formal_editor_readback": formal.get("moves", {}).get(move),
                       "formal_editor_readback_status": formal.get("status"),
                       "historical_ue_data_snapshot": history.get("data", {}).get("moves", {}).get(move),
                       "historical_snapshot_status": "2026-10-23 prior PIE report, not newly inspected current UE asset",
                       "timing_decoding_status": {"input_cancel_accept_buffer_per_button": "unknown raw bit semantics; no native timestamps inferred",
                         "hit_windows": "literal source collision keys, node IDs and banks retained; gameplay evaluator/sweep semantics unverified",
                         "rate_interpolation": "all raw transitions and controls retained; no claim code 2 equals x^2",
                         "turn": "mAttackAdjustAngleIndex is an index, not degrees; external parameter resolution needed"}})
    return result


def formal_review(check, formal, report, mapping):
    """Compare declared saved-asset properties, retaining semantic gaps separately."""
    moves = formal["moves"]
    check.check(len(moves), formal["move_count"], "editor_readback.move_count")
    check.check(formal["move_count"], 32, "editor_readback.expected_move_count")
    disk_hashes = []
    for rel, expected in formal.get("disk_asset_sha256", {}).items():
        path = ROOT / Path(rel)
        actual = digest(path) if path.exists() else None
        check.check(actual, expected, "editor_readback.disk_hash." + rel)
        disk_hashes.append({"path": rel, "recorded_sha256": expected, "current_sha256": actual})
    for name, move in moves.items():
        for route in move["routes"]:
            check.check(route["next_move"] in moves, True, f"editor_readback.{name}.route_destination")
    segment_comparisons = []
    rate_comparisons = []
    scheduled = set()
    for name, move in moves.items():
        for segment in move.get("segments", []):
            stem = segment["sequence"].rsplit("/", 1)[1].split(".")[0]
            if stem.startswith("A_w03_00_"):
                scheduled.add(int(stem.rsplit("_", 1)[1]))
    for name, source in mapping["moves"].items():
        move = moves.get(name)
        if not move:
            continue
        expected_stem = "A_" + source["clip"]
        segments = move.get("segments", [])
        match = len(segments) == 1 and segments[0]["sequence"].rsplit("/", 1)[1].split(".")[0] == expected_stem
        check.check(match, True, "editor_readback." + name + ".source_clip")
        duration_match = (match and abs(float(segments[0]["anim_start_time"])) < 1e-5
                          and abs(float(segments[0]["anim_end_time"]) - source["source_frames"] / 60) < 1e-5)
        check.check(duration_match, True, "editor_readback." + name + ".source_segment_duration")
        segment_comparisons.append({"move": name, "source": source["clip"], "full_single_segment_matches": duration_match})
        rates = ast.literal_eval(move["source_play_rates"])
        expected = {float(frame) / 60: float(value) for frame, value in (source.get("source_motion_speed") or [[]])[0]}
        endpoint_match = len(rates) == len(expected) and all(
            any(abs(t - et) < 1e-5 and abs(v - ev) < 1e-5 for t, v in rates.items()) for et, ev in expected.items())
        check.check(endpoint_match, True, "editor_readback." + name + ".rate_endpoints")
        rate_comparisons.append({"move": name, "source": source["clip"], "key_endpoint_values_match": endpoint_match,
                                 "curve_semantics_match": "not_proven_current_runtime_linear"})
    connectors = []
    for node in report["connectors"]:
        param = node["process"]["mpParameter"]
        for key in ("MotionNo", "MotionNo_Phase1"):
            motion = param.get(key, -1)
            if motion >= 0:
                connectors.append({"node": node["node_id"], "parameter": key, "motion": motion,
                                   "appears_in_any_formal_montage_segment": motion in scheduled})
    return {"status": formal["status"], "generated_utc": formal["generated_utc"],
            "data_asset": formal["data_asset"], "move_count": formal["move_count"],
            "input_buffer_seconds": formal["input_buffer_seconds"],
            "disk_hash_checks": disk_hashes, "source_segment_comparisons": segment_comparisons,
            "source_rate_endpoint_comparisons": rate_comparisons,
            "scheduled_longsword_motions": sorted(scheduled), "connector_motion_coverage": connectors,
            "components": formal.get("components"), "attachment_defaults": formal.get("attachment_defaults"),
            "current_cancel_windows_seconds": {name: [float(m["cancel_start"]), float(m["cancel_end"])] for name, m in moves.items()},
            "gaps_confirmed_from_formal_readback": [
                {"move": "ForesightSlash", "current_routes": moves["ForesightSlash"]["routes"],
                 "source_node": 28, "gap": "Native triangle -> node11 StepSlash, circle -> node4 Thrust, R+triangle -> node45 SpiritThrust; formal Light instead goes OverheadSlash and Thrust/HelmBreaker routes are absent."},
                {"move": "HelmLand", "current_routes": moves["HelmLand"]["routes"],
                 "current_cancel": [moves["HelmLand"]["cancel_start"], moves["HelmLand"]["cancel_end"]],
                 "source_node": 57, "gap": "Native R+circle -> ForesightSlash exists; formal empty routes and cancel9999 prevent this exit under current runtime rules."},
                {"move": "IaiSpiritSlash", "current_routes": moves["IaiSpiritSlash"]["routes"],
                 "source_node": 65, "gap": "Native node65 has R+triangle -> connector357/367 -> SpiritThrust. Formal HelmBreaker skips connector, and Spirit -> SpiritIII is additional local behavior."},
                {"move": "SpiritComboThrust", "current_segments": moves["SpiritComboThrust"]["segments"],
                 "gap": "Formal reuses full105; native entry118 and continuation121 are unscheduled."},
                {"move": "SpiritComboRisingSlash", "current_segments": moves["SpiritComboRisingSlash"]["segments"],
                 "gap": "Formal reuses full107; native continuation124 is unscheduled."},
                {"move": "WeaponMesh/ScabbardMesh", "gap": "Both components use AnimationBlueprint mode with AnimClass=None. Native weapon tracks are not driven by a component AnimBP; current attachment-only behavior must not be called native weapon animation playback."},
            ],
            "limits": ["Readback is editor saved-asset inspection, not PIE/native-game behavior validation.",
                       "No input flag bits, condition runtime priority or native cancel time was inferred.",
                       "Connector absence is tested against Montage segment references only; separate runtime playback must be checked in C++.",
                       "Rate endpoints match within exporter string precision1e-5; interpolation/control behavior is not thereby proved."]}


def verify(audit_path=DEFAULT_AUDIT, output=DEFAULT_OUTPUT, readback=DEFAULT_READBACK):
    audit_path, output, readback = audit_path.resolve(), output.resolve(), readback.resolve()
    report = json.loads(audit_path.read_text(encoding="utf8"))
    lmt_path = ROOT / report["source"]["path"]
    fsm_path = ROOT / "ArtSource/ThirdParty/MHWLongSword/nativePC/hm/wp/wp03/wp03_action.fsm"
    check = Verification()
    lmt = check.lmt(lmt_path, report["source"])
    _, fsm = check.fsm(fsm_path, report)
    old_extractor = ROOT / "Scripts/MHWI/extract_moveset_mapping.py"
    module = ast.parse(old_extractor.read_text(encoding="utf8"))
    old_groups = next(ast.literal_eval(n.value) for n in module.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "GROUPS" for t in n.targets))
    all_groups = [g for e in report["source"]["entries"] for g in e["groups"]]
    old_kept = [g for g in all_groups if g["hash"] in old_groups]
    computed_counts = {
        "motions": lmt["motions"], "fsm_nodes": fsm["nodes"],
        "conditions": fsm["conditions"], "links": fsm["links"],
        "connectors": len(report["connectors"]),
        "groups": dict(Counter(g["name"] or str(g["hash"]) for g in all_groups)),
        "key_interpolation_codes": dict(Counter(str(k["transition"]) for g in all_groups for t in g["tracks"] for k in t["keys"])),
    }
    check.check(report["counts"], computed_counts, "report.computed_counts")
    summary_path = audit_path.with_name("timing-summary.json")
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf8"))
        check.check(summary["counts"], computed_counts, "summary.counts")
        check.check(summary["motion_speed_interpolation"],
                    dict(Counter(str(k["transition"]) for s in report["motion_speed"] for k in s["track"]["keys"])),
                    "summary.motion_speed_interpolation")
        check.check(summary["focus_field_names"],
                    sorted({f["track"]["name"] for f in report["focus_tracks"]}), "summary.focus_fields")
        check.check(summary["connectors"],
                    [{"node": n["node_id"], "parameters": n["process"]["mpParameter"],
                      "destinations": [l["mDestinationNodeId"] for l in n["links"]]} for n in report["connectors"]],
                    "summary.connectors")
    input_transitions = Counter(k["transition"] for x in report["input_bit_intervals"] for k in x["track"]["keys"])
    variable_rates = [x["motion"] for x in report["motion_speed"] if len({k["value"] for k in x["track"]["keys"]}) > 1]
    mapping_path = ROOT / "Scripts/MHWI/moveset_mapping.json"
    mapping = json.loads(mapping_path.read_text(encoding="utf8"))
    prior_pie = ROOT / "Saved/MHWIImport/PIE-behavior-all.json"
    history = json.loads(prior_pie.read_text(encoding="utf8")) if prior_pie.exists() else {}
    formal = json.loads(readback.read_text(encoding="utf8")) if readback.exists() else {}
    formal_result = formal_review(check, formal, report, mapping) if formal else None
    connector_table = []
    for node in report["connectors"]:
        incoming = [{"source_node": n["node_id"], "source_name": n["name"], "serialized_order": order,
                     **Verification.route(link, report)}
                    for n in report["fsm_nodes"] for order, link in enumerate(n["links"])
                    if link["mDestinationNodeId"] == node["node_id"]]
        connector_table.append({"node": node["node_id"], "name": node["name"],
                                "process": node["process"], "incoming_routes": incoming,
                                "outgoing_routes": [Verification.route(l, report) for l in node["links"]],
                                "runtime_gap": "Current local ground routes mostly blend directly between main move montages; native connector clips/phase variants are not generally scheduled. RollStepSlash alone composites 129 -> trimmed101 with project-selected entry48."})
    warnings = [
        "Static native-file verification only; no original-game runtime input, cancel, blend or timing measurements were performed.",
        "Audit raw_bit_intervals uses previous-value hold (previous_key_hold_not_native_evaluator in corrected report). All 961 input keys use transition 5; these spans are only held-key candidates, not proven active input/cancel intervals.",
        "Public interpolation labels are format-tool mappings, not a native gameplay evaluator. Do not infer code2 QUAD equals normalized x*x or assume flags use the same numeric evaluator as floats.",
        "mAttackAdjustAngleIndex stores an index; converting 0/6/8 directly to degrees is unsupported.",
        "Native FSM ActionNo process implementation, input bit-to-property mapping, native blend/start-frame rules and external angle tables are not embedded in this FSM/LMT audit.",
        "Current C++ has one CancelStart/CancelEnd per move, one pending input and shared InputBufferSeconds0.3. It does not evaluate 307 native condition trees or per-button native acceptance windows.",
        "Current C++ EvaluateSourcePlayRate linearly interpolates endpoints and discards source key controls/transition; mismatch potential exists on variable-speed motions173/308/309/310/311.",
        "Original audit omits node/cluster metadata. This verification retains omitted metadata; current file has no subclusters/from-all transitions and uniform mSetting1/UserAttribute0.",
        "Saved prior UE snapshots are historical observations, not verification of any modifications made after their timestamps.",
    ]
    result = {"status": "static_native_structure_verified_with_semantic_limitations" if not check.errors else "failed",
              "generated_utc": datetime.now(timezone.utc).isoformat(),
              "input_files": {str(p.relative_to(ROOT)): digest(p) for p in (audit_path, summary_path, readback, lmt_path, fsm_path, old_extractor, mapping_path, prior_pie) if p.exists()},
              "independence": "LMT offset/type/key checks do not call original audit parser. FSM comparison reuses XfsReader; not independent decoder proof.",
              "assertions": check.assertion_count, "errors": check.errors,
              "lmt_structure": lmt, "fsm_structure": fsm,
              "legacy_filter_review": {"retained_group_hashes": old_groups, "all_group_instances": len(all_groups),
                "retained_group_instances": len(old_kept), "dropped_group_instances": len(all_groups) - len(old_kept),
                "all_unique_group_hashes": len({g["hash"] for g in all_groups}),
                "dropped_group_names": sorted({g["name"] for g in all_groups if g["hash"] not in old_groups}),
                "loss": "Old extraction filters to five allowed hashes, drops transition/control/type fields and flattens conditions to property names. It is not a lossless source-fidelity record."},
              "input_track_key_transition_counts": dict(input_transitions), "variable_motion_speed_clips": variable_rates,
              "per_action_timing_audit": action_table(report, mapping, history, formal),
              "formal_editor_readback_comparison": formal_result,
              "connector_audit": connector_table, "warnings": warnings,
              "next_evidence_required": ["Resolve PlMotionInput bit semantics against cFSMPl_W03 native property evaluators.",
                "Resolve ActionNo -> motion variants/phase/blend/start-frame dispatch and native connector scheduling.",
                "Resolve external attack-angle index parameter table and native motion-speed curve evaluator.",
                "Measure original-game input-held/pressed/released and branch/cancel results at boundary frames; compare UE traces."]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"status": result["status"], "assertions": check.assertion_count,
                      "errors": len(check.errors), "motion_count": lmt["motions"], "key_count": lmt["keys"],
                      "per_action_rows": len(result["per_action_timing_audit"]), "connector_rows": len(connector_table),
                      "output": str(output)}, ensure_ascii=True))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--readback", type=Path, default=DEFAULT_READBACK)
    args = parser.parse_args()
    raise SystemExit(0 if not verify(args.audit, args.output, args.readback)["errors"] else 1)
