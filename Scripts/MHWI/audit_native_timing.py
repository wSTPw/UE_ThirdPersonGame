"""Read-only source-fidelity audit of native LMT95 TIML and XFS19 FSM.

Preserves raw hashes, track order, interpolation and condition trees. A named
property is not a decoded flag bit or evidence of the game's native evaluator.
Does not launch UE, rewrite authoring metadata, or modify original game assets.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

from read_source_fsm import XfsReader

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "ArtSource/ThirdParty/MHWLongSword/nativePC"
DEFAULT_OUT = ROOT / "Saved/MHWIImport/SourceFidelity-20261024"
COMMON = 1221988687
INPUT = 1875693838
SPEED = 717816547
INTERPOLATION = ["CONSTANT", "LINEAR", "QUAD", "CUBIC", "QUART", "EXPO", "SINE"]


def listify(value):
    return value if isinstance(value, list) else ([] if value is None else [value])


def names(path, datatypes=False):
    if not path.exists():
        return {}
    result = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        key, tail = line.split(",", 1)
        result[int(key)] = tail.rsplit(",", 1)[0] if datatypes else tail
    return result


def parse_lmt(path, group_names, field_names):
    data = path.read_bytes()
    def read(fmt, pos):
        if pos < 0 or pos + struct.calcsize("<" + fmt) > len(data):
            raise ValueError((path, "out_of_bounds", pos, fmt))
        return struct.unpack_from("<" + fmt, data, pos)
    if data[:4] != b"LMT\0" or read("H", 4)[0] != 95:
        raise ValueError((path, "requires_LMT95"))
    entries = []
    for index in range(read("H", 6)[0]):
        offset = read("Q", 16 + index * 8)[0]
        if not offset:
            continue
        timl = read("Q", offset + 88)[0]
        entry = dict(index=index, source_frame_count=read("I", offset + 12)[0],
                     source_loop_frame=read("i", offset + 16)[0], groups=[])
        if timl:
            go, gc, ix0, ix1, length, loop, control, label = read("QQiiffiI", timl)
            entry["timl"] = dict(length=length, loop_start=loop, loop_control=control,
                                  data_ix0=ix0, data_ix1=ix1, label_hash=label)
            for gi in range(gc):
                to, tc, gh, unknown = read("QQIi", go + gi * 24)
                group = dict(order=gi, hash=gh, name=group_names.get(gh), unknown=unknown, tracks=[])
                for ti in range(tc):
                    fo, fc, fh, kind = read("QQIi", to + ti * 24)
                    track = dict(order=ti, hash=fh, name=field_names.get(fh), kind=kind, keys=[])
                    for ki in range(fc):
                        pos = fo + ki * 20
                        if kind == 3:
                            values = [list(read("4B", pos)), *read("ff", pos + 4)]
                        else:
                            fmt = {0: "iii", 1: "III", 2: "fff", 4: "III"}[kind]
                            values = read(fmt, pos)
                        frame, transition, key_kind = read("fhh", pos + 12)
                        track["keys"].append(dict(frame=frame, value=values[0], control_l=values[1],
                                                  control_r=values[2], transition=transition, key_kind=key_kind))
                    group["tracks"].append(track)
                entry["groups"].append(group)
        entries.append(entry)
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(data).hexdigest(),
                size=len(data), entries=entries)


def raw_bit_intervals(track, end):
    """Candidate spans under previous-key hold, NOT native evaluator windows.

    Input tracks in this source use transition 5. Bit-field runtime evaluation is
    unknown; assuming previous-key hold is useful for inspection only.
    """
    result = {}
    keys = track["keys"]
    for bit in range(32):
        spans = []
        for index, key in enumerate(keys):
            if int(key["value"]) & (1 << bit):
                stop = keys[index + 1]["frame"] if index + 1 < len(keys) else end
                if stop > key["frame"]:
                    if spans and spans[-1][1] == key["frame"]:
                        spans[-1][1] = stop
                    else:
                        spans.append([key["frame"], stop])
        if spans:
            result[str(bit)] = spans
    return result


def condition_summary(value):
    if not isinstance(value, dict):
        return value
    if "mVariable" in value:
        return dict(property=value["mVariable"].get("mPropertyName"),
                    owner=value["mVariable"].get("mOwnerName"),
                    is_bit_no=value.get("mIsBitNo"), index=value.get("mIndex"))
    if "mOperator" in value:
        return dict(operator_raw=value["mOperator"],
                    children=[condition_summary(v) for v in listify(value.get("mpChildList"))])
    return value


def audit(out):
    out.mkdir(parents=True, exist_ok=True)
    label_root = ROOT / "Saved/MHWI"
    if not (label_root / "TIMLDatatypes.txt").exists():
        label_root = out / "timing-FreeHK-upstream/MHW-Free-HyperKinetics-main/struct"
    gn = names(label_root / "TIMLTimelineParam.txt")
    fn = names(label_root / "TIMLDatatypes.txt", True)
    lmt = parse_lmt(NATIVE / "hm/wp/wp03/mot/w03_00/w03_00.lmt", gn, fn)
    fsm_path = NATIVE / "hm/wp/wp03/wp03_action.fsm"
    fsm_data = fsm_path.read_bytes()
    fsm = XfsReader(fsm_data).parse()["root"]
    nodes = fsm["mpRootCluster"]["mpNodeList"]
    conditions = {c["mName"]["mId"]: c["mpRootNode"] for c in fsm["mpConditionTree"]["mpTreeList"]}
    node_report, connectors = [], []
    for node in nodes:
        process = node["mpProcessList"]
        links = [dict(**link, condition_tree=conditions.get(link["mConditionId"]),
                      condition_summary=condition_summary(conditions.get(link["mConditionId"])))
                 for link in listify(node["mpLinkList"])]
        item = dict(node_id=node["mId"], name=node["mName"], process=process, links=links)
        node_report.append(item)
        if process["mContainerName"].startswith("LinkMotion"):
            connectors.append(item)
    focus, speeds, input_bits = [], [], []
    group_count, transitions = Counter(), Counter()
    relevant = ("turn", "adjust", "blend", "interpolation", "startframe", "motionphase", "speed", "weaponmotion", "actionphase")
    for entry in lmt["entries"]:
        for group in entry["groups"]:
            group_count[group["name"] or str(group["hash"])] += 1
            for track in group["tracks"]:
                for key in track["keys"]:
                    transitions[str(key["transition"])] += 1
                item = dict(motion=entry["index"], group=group["name"], group_hash=group["hash"],
                            group_order=group["order"], group_unknown=group["unknown"], track=track)
                if group["hash"] == COMMON and track["hash"] == SPEED:
                    speeds.append(item)
                if any(word in (track["name"] or "").lower() for word in relevant):
                    focus.append(item)
                if group["hash"] == INPUT and track["kind"] in (0, 1, 4):
                    input_bits.append(dict(**item, raw_bit_intervals=raw_bit_intervals(track, entry["timl"]["length"]),
                                           interval_assumption="previous_key_hold_not_native_evaluator",
                                           semantics="unknown: candidate bit spans only, not mapped input/cancel windows"))
    report = dict(status="read_only_native_static_audit_not_runtime_validation", source=lmt,
                  label_dictionary_sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (label_root / "TIMLDatatypes.txt", label_root / "TIMLTimelineParam.txt") if p.exists()},
                  interpolation_reference="https://github.com/AsteriskAmpersand/MHW-Free-HyperKinetics/blob/main/blender/timl_importer.py",
                  interpolation_labels=INTERPOLATION,
                  limitations=["Property names from public format research do not prove per-bit runtime meanings.",
                    "Source frame units are not wall-clock duration; rate tracks and native modifiers apply.",
                    "Source interpolation codes/control values are retained, not silently coerced to linear.",
                    "FSM does not embed ActionNo native implementation; route existence does not prove its cancel time."],
                  fsm_sha256=hashlib.sha256(fsm_data).hexdigest(), fsm_nodes=node_report,
                  all_conditions=conditions, connectors=connectors, motion_speed=speeds,
                  focus_tracks=focus, input_bit_intervals=input_bits,
                  counts=dict(motions=len(lmt["entries"]), fsm_nodes=len(nodes), conditions=len(conditions),
                              links=sum(len(n["links"]) for n in node_report), connectors=len(connectors),
                              groups=group_count, key_interpolation_codes=transitions))
    path = out / "timing-native-full.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = dict(counts=report["counts"], motion_speed_interpolation=Counter(str(k["transition"]) for s in speeds for k in s["track"]["keys"]),
                   focus_field_names=sorted({f["track"]["name"] for f in focus}),
                   connectors=[dict(node=n["node_id"], parameters=n["process"]["mpParameter"],
                                    destinations=[l["mDestinationNodeId"] for l in n["links"]]) for n in connectors])
    (out / "timing-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    audit(parser.parse_args().output)
