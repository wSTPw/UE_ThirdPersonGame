"""Extract em001 source motion identity, TIML keys and root candidates offline.

Run with the bundled Blender Python for --decode-roots (NumPy is bundled there).
No UE assets or game-install files are modified. A selected root export is an
explicit engineering adapter until native action/clock/coordinate/root consumers
and the original-game comparison are qualified independently.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Scripts/MHWI"))
from audit_native_timing import names, parse_lmt

BASE = ROOT / "ArtSource/ThirdParty/MHWRathalos"
NATIVE = BASE / "nativePC"
DEFAULT_OUT = ROOT / "Saved/MHWI-Rathian-FirstChain-20261031"
ADDON = ROOT / "Tools/MHW/BlenderAddons/blender-mhworld-tools-suite-main"


def identity(path):
    raw = path.read_bytes()
    return dict(path=path.relative_to(ROOT).as_posix(), bytes=len(raw),
                sha256=hashlib.sha256(raw).hexdigest())


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf8")


def read_model_bones(path):
    raw = path.read_bytes()
    if raw[:4] != b"MOD\0" or struct.unpack_from("<H", raw, 4)[0] != 237:
        raise ValueError("Requires the pinned MOD3 v237")
    count = struct.unpack_from("<H", raw, 6)[0]
    offset = struct.unpack_from("<Q", raw, 48)[0]
    remap_offset = offset + count * (24 + 64 + 64)
    inverse = {}
    for function in range(512):
        index = raw[remap_offset + function]
        if index != 255:
            if index >= count:
                raise ValueError(("remap outside skeleton", function, index, count))
            inverse.setdefault(index, []).append(function)
    rows = []
    for index in range(count):
        function, parent, child = struct.unpack_from("<HBB", raw, offset + index * 24)
        remaps = inverse.get(index, [])
        if len(remaps) != 1:
            raise ValueError(("ambiguous or missing imported bone name", index, remaps))
        local_matrix = list(struct.unpack_from("<16f", raw, offset + count * 24 + index * 64))
        rows.append(dict(source_index=index, source_bone_function=function,
                         source_parent_index=parent, source_child_index=child,
                         remap_function=remaps[0], ue_imported_name=f"bone_{remaps[0]:03}",
                         source_local_matrix_row_major=local_matrix))
    return dict(source=identity(path), native_bone_count=count, source_bone_offset=offset,
                remap_offset=remap_offset, bones=rows,
                generated_roots=[
                    dict(name="bone_root", origin="converter-generated; LMT bone -1 maps here"),
                    dict(name="Armature", origin="FBX import-generated UE root; not a MOD3 bone")],
                imported_bone_count=count + 2,
                qualification="static MOD3 layout and pinned converter naming, not native COL node binding")


def load_lmt_decoder():
    path = ADDON / "lmt/lmt_parser.py"
    spec = importlib.util.spec_from_file_location("rathian_pinned_lmt_parser", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.LmtParser


def root_track_headers(raw, slot):
    offset = struct.unpack_from("<Q", raw, 16 + slot * 8)[0]
    bone_offset, count = struct.unpack_from("<QI", raw, offset)
    result = []
    for index in range(count):
        position = bone_offset + index * 48
        encoding, kind, flags0, flags1, bone = struct.unpack_from("<BBBBi", raw, position)
        if bone not in (-1, 0):
            continue
        weight, size, pointer = struct.unpack_from("<fIQ", raw, position + 8)
        result.append(dict(descriptor_offset=position, encoding=encoding, kind=kind,
                           flags_raw=[flags0, flags1], bone_id=bone, weight=weight,
                           key_array_bytes=size, key_array_offset=pointer,
                           key_array_sha256=hashlib.sha256(raw[pointer:pointer + size]).hexdigest(),
                           constant_xyzw=list(struct.unpack_from("<4f", raw, position + 24)),
                           coefficient_offset=struct.unpack_from("<Q", raw, position + 40)[0]))
    return result


def normalized_quat(value):
    magnitude = math.sqrt(sum(float(v) ** 2 for v in value))
    if not math.isfinite(magnitude) or magnitude < 1.e-9:
        raise ValueError("Invalid source quaternion")
    return [float(v) / magnitude for v in value]


def interpolate(keys, time, quaternion=False):
    points = sorted((float(k), value) for k, value in keys.items())
    times = [point[0] for point in points]
    if not points:
        raise ValueError("Empty decoded channel")
    right = bisect_right(times, time)
    if right == 0:
        return normalized_quat(points[0][1]) if quaternion else points[0][1][:3]
    if right == len(points):
        return normalized_quat(points[-1][1]) if quaternion else points[-1][1][:3]
    left_time, a = points[right - 1]
    right_time, b = points[right]
    alpha = (time - left_time) / (right_time - left_time)
    if not quaternion:
        return [float(a[i]) * (1.0 - alpha) + float(b[i]) * alpha for i in range(3)]
    a, b = normalized_quat(a), normalized_quat(b)
    dot = sum(x * y for x, y in zip(a, b))
    if dot < 0.0:
        b, dot = [-v for v in b], -dot
    if dot > .9995:
        return normalized_quat([x * (1 - alpha) + y * alpha for x, y in zip(a, b)])
    angle = math.acos(max(-1.0, min(1.0, dot)))
    denominator = math.sin(angle)
    return normalized_quat([(x * math.sin((1 - alpha) * angle)
                             + y * math.sin(alpha * angle)) / denominator for x, y in zip(a, b)])


def build_engineering_track(entry, source, native_action_id, units_per_second):
    root = entry.get("decoded_root_channels", {}).get("-1")
    if not root or "pos" not in root or "rot" not in root:
        raise ValueError("Selected slot has no complete explicit bone -1 position/rotation channels")
    end = entry["source_frame_count"] - 1
    if end < 1:
        raise ValueError("Selected slot has no positive source duration")
    # Explicit source-frame sampling. The interpolation is labelled as an
    # engineering adapter, not assumed to match the original native evaluator.
    times = sorted({0.0, float(end), *(float(t) for channel in ("pos", "rot")
                    for t in root[channel] if 0.0 <= float(t) <= end),
                    *(float(t) for t in range(end + 1))})
    samples = []
    for time in times:
        position = interpolate(root["pos"], time)
        x, y, z, w = interpolate(root["rot"], time, quaternion=True)
        samples.append(dict(source_time=time, local_translation_cm=[position[0], position[2], position[1]],
                            local_rotation_xyzw=[-x, -z, -y, w], local_scale=[1.0, 1.0, 1.0]))
    return dict(schema=1, source_sha256=source["sha256"], motion_bank=Path(source["path"]).stem,
                motion_slot=entry["index"], native_action_id=native_action_id,
                evidence_path="Saved/MHWI-Rathian-FirstChain-20261031/motion-source-inventory.json",
                time_unit="NativeFrames", units_per_second=units_per_second,
                time_basis="Raw LMT frame domain; explicit caller rate is an adapter unless native qualified",
                coordinate_basis="C=(x,z,y), source unit->UE cm follows same converter pipeline; monster UE comparison pending",
                qualifications=dict(motion_binding="EngineeringAdapter", time_basis="EngineeringAdapter",
                                    coordinate_basis="EngineeringAdapter", root_track="StaticSourceVerified"),
                source_semantics_qualified=False, original_game_executed=False,
                interpolation="translation linear; quaternion slerp; native interpolation consumer not qualified",
                source_root_bone_id=-1, source_root_channels=root, samples=samples)



def update_selected_from_native(bank_name, slot, native_action_id, output, units_per_second=0.0):
    """Use the existing pinned native v95 sampler, never legacy decoder values."""
    import native_animation_source as native
    reader, pose = native.native_modules()
    path = NATIVE / f"em/em001/00/mot/{bank_name}/{bank_name}.lmt"
    bank = reader.read_lmt_file(path)
    action = next(action for action in bank.actions if action.id == slot)
    if action.header.flags2 & 1:
        raise ValueError("NeedsParent root candidate requires an independently qualified base")
    roots = {}
    root_records = []
    for index, track in enumerate(action.tracks):
        if track.header.usage not in (3, 4):
            continue
        if track.header.usage in roots:
            raise ValueError("Multiple root/action records need explicit binding, not last-wins guessing")
        curve = pose.compile_pose_curve(track)
        roots[track.header.usage] = curve
        root_records.append(dict(index=index, usage=track.header.usage, bone=track.header.bone_id,
                                 codec=track.header.buffer_type, buffer_offset=track.header.buffer_offset,
                                 buffer_size=track.header.buffer_size, frames=list(curve.frames),
                                 decoded_values=[list(value) for value in curve.values]))
    if set(roots) != {3, 4} or action.header.frame_count < 2:
        raise ValueError("No complete positive-duration source root/action track")
    group_names = names(ROOT / "Saved/MHWI/TIMLTimelineParam.txt")
    field_names = names(ROOT / "Saved/MHWI/TIMLDatatypes.txt", True)
    field_names.update({2996226662: "NodeID[0]", 3213885619: "Bank[0]", 150806694: "mFlag"})
    group_names[956269290] = "CollisionTimelineObject"
    timeline = parse_lmt(path, group_names, field_names)
    entry = next(entry for entry in timeline["entries"] if entry["index"] == slot)
    samples = []
    for time in range(action.header.frame_count):
        x, y, z = roots[4].sample(time)
        w, qx, qy, qz = roots[3].sample(time)
        samples.append(dict(source_time=float(time), local_translation_cm=[x, z, y],
                            local_rotation_xyzw=[-qx, -qz, -qy, w], local_scale=[1.0, 1.0, 1.0]))
    report = dict(schema=2, source_sha256=identity(path)["sha256"], motion_bank=bank_name,
                  motion_slot=slot, native_action_id=native_action_id,
                  evidence_path=(output / "selected-source-track.json").relative_to(ROOT).as_posix(),
                  time_unit="NativeFrames", units_per_second=units_per_second,
                  time_basis="Raw LMT frame domain; seconds conversion requires qualified native clock consumer",
                  coordinate_basis="C=(x,z,y), source unit->UE cm; monster asset readback qualification separate",
                  qualifications=dict(motion_binding="EngineeringAdapter", time_basis="EngineeringAdapter",
                                      coordinate_basis="EngineeringAdapter", root_track="StaticSourceVerified"),
                  source_semantics_qualified=False, original_game_executed=False,
                  root_sampling_rule=pose.RULE_VERSION, root_sampler=identity(native.UPSTREAM / "core/formats/lmt/pose_evaluation.py"),
                  source_reader=identity(native.UPSTREAM / "core/formats/lmt/reader.py"),
                  source_root_records=root_records, samples=samples,
                  source_frame_count=action.header.frame_count,
                  source_timeline_groups=entry["groups"],
                  ue_sequence=f"/Game/MHWI/Rathalos/Animations/A_{bank_name}_{slot:03}",
                  native_action_binding_status="candidate; current native descriptor/registration evidence is separate",
                  interpolation="native v95 source root records sampled at every integer frame; this BITE root rotation is constant")
    write_json(output / "selected-source-track.json", report)
    return dict(path=str(output / "selected-source-track.json"), samples=len(samples),
                bytes=(output / "selected-source-track.json").stat().st_size,
                first=samples[0], last=samples[-1])

def run(args):
    if args.native_selected:
        if args.bank is None or args.slot is None:
            raise ValueError("--native-selected requires --bank and --slot")
        print(json.dumps(update_selected_from_native(args.bank, args.slot, args.native_action_id, args.output, args.units_per_second)))
        return
    manifest = json.loads((BASE / "extraction-manifest.json").read_text(encoding="utf8"))
    pinned = {row["path"]: row for row in manifest["files"]}
    group_names = names(ROOT / "Saved/MHWI/TIMLTimelineParam.txt")
    field_names = names(ROOT / "Saved/MHWI/TIMLDatatypes.txt", True)
    field_names.update({2996226662: "NodeID[0]", 3213885619: "Bank[0]", 150806694: "mFlag"})
    group_names[956269290] = "CollisionTimelineObject"
    decoder = load_lmt_decoder() if args.decode_roots else None
    model = read_model_bones(NATIVE / "em/em001/00/mod/em001_00.mod3")
    banks = []
    for path in sorted((NATIVE / "em/em001/00/mot").rglob("*.lmt")):
        relative = path.relative_to(NATIVE).as_posix()
        if hashlib.sha256(path.read_bytes()).hexdigest() != pinned[relative]["sha256"]:
            raise ValueError(("source differs from extraction manifest", relative))
        bank = parse_lmt(path, group_names, field_names)
        decoded = {}
        if decoder is not None:
            for action in decoder(str(path)).read():
                slot = int(action["name"].rsplit("_", 1)[1])
                decoded[slot] = {str(bone): channels for bone, channels in action["bone_action"].items()
                                 if bone in (-1, 0)}
        raw = path.read_bytes()
        for entry in bank["entries"]:
            entry["root_track_descriptors"] = root_track_headers(raw, entry["index"])
            entry["decoded_root_channels"] = decoded.get(entry["index"], {})
            entry["ue_sequence"] = f"/Game/MHWI/Rathalos/Animations/A_{path.stem}_{entry['index']:03}"
        banks.append(bank)
    report = dict(schema=1, target="MHWI em001/00", status="offline_static_source_inventory",
                  original_game_executed=False, ue_assets_modified=False,
                  converter=dict(parser=identity(ADDON / "lmt/lmt_parser.py"),
                                 mod3_loader=identity(ADDON / "mod3/mod3_loader.py"),
                                 lmt_loader=identity(ADDON / "lmt/lmt_loader.py")),
                  model=model, banks=banks,
                  counts=dict(banks=len(banks), motions=sum(len(bank["entries"]) for bank in banks)),
                  qualifications=dict(native_action_to_motion="unknown; use separate native registration evidence",
                                      native_time_rate="unknown; existing UE 60FPS is conversion sampling only",
                                      collision_tracks="raw keys retained; mask/node consumer requires independent qualification",
                                      root_consumer="bone -1 decoded, actor root-motion consumer still separate evidence"))
    output = args.output
    write_json(output / "motion-source-inventory.json", report)
    write_json(output / "source-bone-map.json", model)
    if args.bank is not None:
        if args.slot is None or decoder is None:
            raise ValueError("--bank requires --slot and --decode-roots")
        bank = next(bank for bank in banks if Path(bank["path"]).stem == args.bank)
        entry = next(entry for entry in bank["entries"] if entry["index"] == args.slot)
        track = build_engineering_track(entry, bank, args.native_action_id, args.units_per_second)
        track["evidence_path"] = (output / "motion-source-inventory.json").relative_to(ROOT).as_posix()
        write_json(output / "selected-source-track.json", track)
    print(json.dumps(dict(output=str(output), counts=report["counts"], native_bones=model["native_bone_count"],
                          imported_bones=model["imported_bone_count"],
                          selected=(dict(bank=args.bank, slot=args.slot) if args.bank else None))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--decode-roots", action="store_true")
    parser.add_argument("--native-selected", action="store_true")
    parser.add_argument("--bank")
    parser.add_argument("--slot", type=int)
    parser.add_argument("--native-action-id", type=int, default=-1)
    parser.add_argument("--units-per-second", type=float, default=0.0)
    options = parser.parse_args()
    if not math.isfinite(options.units_per_second) or options.units_per_second < 0:
        parser.error("--units-per-second must be explicit finite nonnegative; zero means unknown")
    run(options)
