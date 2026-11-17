"""Hash-pinned offline Rathian THKLST/THK extraction and bounded native evidence.

The original game is never executed or modified. Format facts are checked against
the external Leviathon reference parser; upstream GPL code stays in Saved.
Raw fields and source offsets survive every projection. Unknown VM semantics
block execution rather than silently choosing a branch.
"""
from __future__ import annotations
import argparse
from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import sys
import zlib

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "ArtSource/ThirdParty/MHWRathalos/nativePC"
OUT = ROOT / "Saved/MHWI-Rathian-FirstChain/THK"
COMMIT = "1e647f08ed4356e9feac037ccec7c08149fa2ef5"
CACHE = ROOT / f"Saved/MHWI-Rathian-FirstChain/Leviathon/Leviathon-{COMMIT}"
DEPENDENCIES = ROOT / "Saved/MHWI-Rathian-FirstChain/Dependencies"
PINNED = {
    "common/thk.py": "fbd2da575135eda6f3c5f86a8f29ff2450f72fe9720c0013a75d3050e85ba807",
    "common/thklist.py": "0cad8a928999709755e6989663174b7691668140b1644bd56833ecc90eab14dc",
    "common/default.fexty": "bec8d55f350cbc269579043463acf3f6c3ed9da2d451b1b70a2327f355d075ed",
    "common/ActionDumps/em001.txt": "e8c9c926aa3be53bd89e0fd17075a4038efa013665cae2bd573e1100bc3f60b6",
    "decompiler/segmentDecompiler.py": "fc798f5af970f40a7407878eb73e1e1d8faa9dfdf96ae05067b34522a0552e32",
    "decompiler/thkDecompileUtils.py": "02e4f65fc839433c764f71ad773e932cbf81469fb795689d7970addba1d0f2ba",
}
# File layout facts, not inferred C++ object offsets. The final segment can omit
# the optional twelve-byte padding declared by the upstream format.
FIELDS = [
    ("endRandom", 0, "B"), ("flowControl", 1, "B"),
    ("branchingControl", 2, "B"), ("unkn1", 3, "B"),
    ("unkn2", 4, "i"), ("functionType", 8, "i"),
    ("parameter1", 12, "i"), ("unkn3", 16, "i"),
    ("unkn4", 20, "i"), ("comboSetting", 24, "i"),
    ("unkn6", 28, "i"), ("parameter2", 32, "i"),
    ("nodeEndingData", 36, "i"), ("extRefThkID", 40, "i"),
    ("extRefNodeID", 44, "i"), ("localRefNodeID", 48, "q"),
    ("unkn7", 56, "i"), ("unkn8", 60, "i"),
    ("unkn9", 64, "i"), ("unkn10", 68, "i"),
    ("unkn11", 72, "i"), ("actionID", 76, "i"),
    ("actionUnkn0", 80, "i"), ("actionUnkn1", 84, "i"),
    ("actionUnkn2", 88, "i"), ("unkn12", 92, "i"),
    ("actionUnkn3", 96, "i"), ("actionUnkn4", 100, "i"),
    ("unknExtra0", 104, "i"), ("unknExtra1", 108, "i"),
    ("unknExtra2", 112, "i"),
]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def identity(path):
    path = Path(path).resolve()
    return dict(path=path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT)
                else str(path), bytes=path.stat().st_size,
                sha256=sha(path.read_bytes()))

def parse_thklst(data):
    if len(data) < 12:
        raise ValueError("Truncated THKLST header")
    signature, count = struct.unpack_from("<Qi", data)
    if signature != 86302593025 or not 0 <= count <= 256:
        raise ValueError("Unqualified THKLST signature/count")
    offset = 12
    entries = []
    for ix in range(count):
        start = offset
        if offset + 8 > len(data):
            raise ValueError("Truncated THKLST entry")
        data_hash, resource_hash = struct.unpack_from("<II", data, offset)
        offset += 8
        path = ""
        if resource_hash:
            end = data.find(b"\0", offset)
            if end < 0:
                raise ValueError("Unterminated THKLST path")
            path = data[offset:end].decode("utf-8")
            offset = end + 1
        entries.append(dict(index=ix, offset=start, end=offset,
                            thinkTableDataHash=data_hash,
                            rThinkTableHash=resource_hash, path=path))
    if offset + 4 * count != len(data):
        raise ValueError("Unknown THKLST trailer/size")
    for ix, entry in enumerate(entries):
        entry["data_offset"] = offset + 4 * ix
        entry["data"] = struct.unpack_from("<I", data, offset + 4 * ix)[0]
    return dict(signature=hex(signature), count=count, entries=entries,
                consumed=len(data), roundtrip_exact=True)

def parse_thk(data):
    if len(data) < 32:
        raise ValueError("Truncated THK header")
    signature, version, count = struct.unpack_from("<4shh", data)
    if signature != b"THK\0" or version != 40 or not 0 <= count <= 6553:
        raise ValueError("Unqualified THK signature/version/count")
    unknown_hash = struct.unpack_from(">I", data, 8)[0]
    is_palico, monster_id, header_size = struct.unpack_from("<iqq", data, 12)
    if header_size != 32 or 32 + 16 * count > len(data):
        raise ValueError("Invalid THK node directory")
    nodes = []
    covered = bytearray(len(data))
    covered[:32 + 16 * count] = b"\1" * (32 + 16 * count)
    rebuilt = bytearray(data[:32 + 16 * count])
    for ix in range(count):
        pointer, segment_count, node_id = struct.unpack_from("<QII", data, 32 + 16 * ix)
        if pointer < 32 + 16 * count or pointer > len(data):
            raise ValueError("THK node pointer outside payload")
        if segment_count > (len(data) - pointer + 12) // 128:
            raise ValueError("THK segment count outside payload")
        segments = []
        for si in range(segment_count):
            begin = pointer + si * 128
            if begin + 116 > len(data):
                raise ValueError("Truncated THK segment")
            end = min(begin + 128, len(data))
            if any(covered[begin:end]):
                raise ValueError("Overlapping THK segment payload")
            covered[begin:end] = b"\1" * (end - begin)
            values = {name: struct.unpack_from("<" + fmt, data, begin + off)[0]
                      for name, off, fmt in FIELDS}
            values["padding_hex"] = data[begin + 116:end].hex()
            encoded = bytearray(end - begin)
            for name, off, fmt in FIELDS:
                struct.pack_into("<" + fmt, encoded, off, values[name])
            encoded[116:] = bytes.fromhex(values["padding_hex"])
            if len(rebuilt) < end:
                rebuilt.extend(b"\0" * (end - len(rebuilt)))
            rebuilt[begin:end] = encoded
            segments.append(dict(index=si, offset=begin, byte_size=end-begin,
                                 fields=values))
        nodes.append(dict(index=ix, id=node_id, directory_offset=32+16*ix,
                          offset=pointer, count=segment_count, segments=segments))
    unknown_ranges = []
    for m in re.finditer(b"\0+", bytes(covered)):
        unknown_ranges.append([m.start(), m.end()])
    if unknown_ranges:
        raise ValueError("Unconsumed THK byte ranges: " + str(unknown_ranges))
    if bytes(rebuilt) != data:
        raise ValueError("Independent THK re-encoding mismatch")
    return dict(header=dict(format_version=version, struct_count=count,
                            unknown_hash=hex(unknown_hash), is_palico=is_palico,
                            monster_id=monster_id, header_size=header_size),
                nodes=nodes, consumed=len(data), roundtrip_exact=True)

def qualify_external(records, list_records):
    for rel, expected in PINNED.items():
        if sha((CACHE / rel).read_bytes()) != expected:
            raise ValueError("External parser source changed: " + rel)
    sys.path.insert(0, str(DEPENDENCIES))
    import construct
    if construct.__version__ != "2.10.70":
        raise ValueError("Unqualified Construct version")
    def load(name, rel):
        spec = importlib.util.spec_from_file_location(name, CACHE / rel)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    thk_module = load("_rathian_external_thk", "common/thk.py")
    list_module = load("_rathian_external_thklist", "common/thklist.py")
    compared = 0
    for row in records:
        raw = (ROOT / row["source"]["path"]).read_bytes()
        parsed = thk_module.Thk.parse(raw)
        if thk_module.Thk.build(parsed) != raw:
            raise ValueError("External THK roundtrip mismatch")
        for node, upstream in zip(row["nodes"], parsed.nodeList, strict=True):
            if (node["id"], node["offset"], node["count"]) != (upstream.id, upstream.offset, upstream.count):
                raise ValueError("External node disagreement")
            for segment, original in zip(node["segments"], upstream.segments, strict=True):
                if any(segment["fields"][name] != getattr(original, name)
                       for name, _, _ in FIELDS):
                    raise ValueError("External segment disagreement")
                compared += 1
    for row in list_records:
        raw = (ROOT / row["source"]["path"]).read_bytes()
        parsed = list_module.ThkList.parse(raw)
        if list_module.ThkList.build(parsed) != raw:
            raise ValueError("External THKLST roundtrip mismatch")
        for a, b in zip(row["entries"], parsed.entries, strict=True):
            if (a["path"], a["thinkTableDataHash"], a["rThinkTableHash"]) != (
                    b.path, b.thinkTableDataHash, b.rThinkTableHash):
                raise ValueError("External THKLST disagreement")
    return dict(passed=True, thk_files=len(records), thklst_files=len(list_records),
                compared_segments=compared, construct_version=construct.__version__,
                boundary="Format agreement and byte re-encoding, not VM/business semantics.")

def source_records():
    manifest_path = BASE.parent / "extraction-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf8"))
    tables, lists = [], []
    for entry in manifest["files"]:
        if not entry["path"].endswith((".thk", ".thklst")):
            continue
        path = BASE / entry["path"]
        data = path.read_bytes()
        if len(data) != entry["size"] or sha(data) != entry["sha256"]:
            raise ValueError("Original source identity mismatch: " + entry["path"])
        parsed = parse_thklst(data) if path.suffix == ".thklst" else parse_thk(data)
        parsed["source"] = identity(path)
        parsed["archive"] = {k: entry[k] for k in ("archive", "offset", "size")}
        (lists if path.suffix == ".thklst" else tables).append(parsed)
    return tables, lists

def compact_tables(tables, normal_list):
    by_path = {row["source"]["path"].split("/nativePC/", 1)[1]: row for row in tables}
    selected = []
    for index in (0, 55):
        entry = normal_list["entries"][index]
        path = entry["path"].replace("\\", "/").lstrip("/") + ".thk"
        row = by_path[path]
        indices = range(len(row["nodes"])) if index == 0 else (0, 2, 6, 193, 198, 200, 201, 207)
        selected.append(dict(context_index=index, source=row["source"], header=row["header"],
                             nodes=[row["nodes"][ix] for ix in indices]))
    return selected

def references_to(tables, normal_list, target_table, target_index):
    by_path = {row["source"]["path"].split("/nativePC/", 1)[1]: row for row in tables}
    target_path = normal_list["entries"][target_table]["path"].replace("\\", "/") + ".thk"
    target_id = by_path[target_path]["nodes"][target_index]["id"]
    callers = []
    for entry in normal_list["entries"]:
        if not entry["path"]:
            continue
        path = entry["path"].replace("\\", "/") + ".thk"
        table = by_path[path]
        for node in table["nodes"]:
            for seg in node["segments"]:
                f = seg["fields"]
                external = f["extRefThkID"] == target_table and f["extRefNodeID"] == target_id
                local = path == target_path and f["extRefThkID"] == -1 and f["localRefNodeID"] == target_index
                if external or local:
                    callers.append(dict(context_index=entry["index"], node_index=node["index"],
                                        node_id=node["id"], segment_index=seg["index"],
                                        source_offset=seg["offset"], reference_kind="external_node_id"
                                        if external else "local_node_index"))
    return callers

def action_correlations():
    dump = (CACHE / "common/ActionDumps/em001.txt").read_text()
    mappings = {int(a): b for a, b in re.findall(r"ID:(\d+),Name:([^\r\n]+)", dump)}
    report = json.loads((ROOT / "Saved/MHWRathalos-20261030-Format/actp2.json").read_text(encoding="utf8"))
    rows = []
    for action_id in (75, 76, 83, 86, 87):
        name = mappings[action_id]
        crc = (~zlib.crc32(name.encode())) & 0xffffffff
        matches = [a for a in report["actions"] if a["name_crc"] == crc]
        rows.append(dict(action_id=action_id, historical_dump_name=name, name_crc=hex(crc),
                         actp2_matches=[dict(index=a["index"], offset=a["offset"],
                                            end=a["end"], used=a["used"]) for a in matches],
                         qualification="Pinned maintainer historical ActionDump + name CRC match; current action registration remains separate."))
    return rows

def native_evidence():
    from trace_native_connections import NativeTrace
    native = NativeTrace()
    addresses = {
        "bite_type_registration": 0x1400cb630, "bite_factory": 0x140d0b910,
        "bite_constructor": 0x1413ec130, "bite_enter": 0x14073ee50,
        "bite_update": 0x140741bf0, "dash_type_registration": 0x1400ccf30,
        "dash_factory": 0x140d0a660, "dash_constructor": 0x1413edae0,
        "dash_enter": 0x1407c3170, "dash_update": 0x1413fa290,
        "em001_type_registration": 0x1401fa050, "em001_factory": 0x141c28340,
        "motion_request_288": 0x141cc9fc0, "motion_request_adapter": 0x141c014b0,
        "motion_request_298": 0x141cca050, "motion_decode": 0x141c014f0,
        "motion_descriptor": 0x141cc9f10,
    }
    functions = []
    for name, address in addresses.items():
        row = native.function(address)
        if row["status"] != "chained_unwind_ranges_collected_not_runtime_verified":
            raise ValueError("Missing native owned range for " + name)
        for span in row["ranges"]:
            if span["decoded_bytes"] != span["expected_bytes"]:
                raise ValueError("Incomplete native owned range")
            begin, end = int(span["begin"],16), int(span["end"],16)
            span["sha256"] = sha(native.code[begin-native.begin:end-native.begin])
        functions.append(dict(name=name, **row))
    # Known virtual target with a two-instruction body and int3 padding to the
    # next actual pdata entry. This is an explicit leaf bound, not a size guess.
    leaf = native._decode(0x141caa0f0, 0x141caa100)
    if [(x["mnemonic"], x["operands"]) for x in leaf[:2]] != [
            ("mov", "eax, edx"), ("ret", "")] or any(x["mnemonic"] != "int3" for x in leaf[2:]):
        raise ValueError("Identity remap leaf changed")
    return dict(mode="hash_pinned_offline_native_instructions_not_execution",
                sources=native.pin, functions=functions,
                explicit_leaf=dict(start="0x141caa0f0", body_end="0x141caa0f3",
                                   next_pdata="0x141caa100", instructions=leaf,
                                   rationale="uEm001 vtable+0x3c0 target; terminal ret then only int3 up to next pdata."),
                facts=[
                    dict(id="BITE_MOTION_CONSTANT", source_va="0x1413ec145", object_offset="0x1e0", value="0x2001"),
                    dict(id="BITE_MOTION_REQUEST", source_va="0x140741c41", virtual_call_va="0x140741c4a", value_source="object+0x1e0"),
                    dict(id="EM001_VTABLE", source_va="0x141c283a1", value="0x143423d40"),
                    dict(id="MOTION_ENCODING", index_mask="0x1ff", bank_shift=12, bank_mask="0xf",
                         instruction_vas=["0x141c0158a","0x141c0159c","0x141c015a7"], call_va="0x141c015b0",
                         decoded_constant=dict(packed=8193, bank_index=2, motion_index=1))],
                unresolved=["Current THK action83->nActEm002::Bite action registry.",
                            "Bank index2->em001_02.lmt file registration.",
                            "THK predicate current native evaluator consumers, full motion clock and action completion.",
                            "Only owned ranges and one explicitly bounded leaf are decoded; indirect runtime calls are not observed."])


def compile_normalform(compact):
    """Project the explicitly bounded THK55 subgraph; preserve unsupported edges."""
    table = next(t for t in compact if t['context_index'] == 55)
    nodes = {n['index']: n for n in table['nodes']}
    result = []
    missing = set()
    def key(ni, si):
        return f't55.n{ni}.s{si}'
    for ni, node in nodes.items():
        segments = node['segments']
        # Scope matching comes only from original branch-control bytes.
        openings, ends, alternatives = [], {}, {}
        for si, segment in enumerate(segments):
            branch = segment['fields']['branchingControl']
            if branch == 2:
                openings.append(si)
            elif branch == 4:
                if not openings:
                    raise ValueError('Orphan THK else')
                alternatives[openings[-1]] = si
            elif branch == 8:
                if not openings:
                    raise ValueError('Orphan THK endif')
                begin = openings.pop()
                ends[begin] = si
                if begin in alternatives:
                    ends[alternatives[begin]] = si
        if openings:
            raise ValueError('Unclosed THK conditional')
        for si, segment in enumerate(segments):
            f = segment['fields']
            after = key(ni, si+1) if si+1 < len(segments) else ''
            row = dict(key=key(ni,si), op='Jump', next=after, otherwise='', call_target='',
                       function_type=f['functionType'], parameter1=f['parameter1'],
                       parameter2=f['parameter2'], native_action_id=-1,
                       source_path=table['source']['path'], source_sha256=table['source']['sha256'],
                       source_offset=segment['offset'], source_bytes=segment['byte_size'],
                       source_evidence=f"{table['source']['path']}#sha256={table['source']['sha256']};offset={segment['offset']};bytes={segment['byte_size']}",
                       native_consumer_verified=False, semantic_authority='pinned_maintainer_control_mapping_only')
            if f['branchingControl'] == 2:
                row['op'] = 'Branch'
                alt = alternatives.get(si)
                row['otherwise'] = key(ni,alt+1 if alt is not None else ends[si]+1)
            elif f['branchingControl'] == 4:
                row['next'] = key(ni,ends[si]+1)
                if f['functionType'] not in (0,2):
                    row.update(op='Stop',reason='Else-if lowering is outside this bounded compiler')
            elif f['branchingControl'] not in (0,8):
                row.update(op='Stop',reason='Unsupported original branching control')
            elif f['endRandom'] == 1 or f['flowControl'] == 8:
                row.update(op='Return',next='')
            elif f['endRandom'] != 0 or f['flowControl'] != 0:
                row.update(op='Stop',reason='Unsupported original random/flow control')
            elif f['localRefNodeID'] != -1:
                target=f['localRefNodeID']
                row.update(op='Call',call_target=key(target,0))
                if target not in nodes:
                    missing.add(target)
            elif f['extRefThkID'] != -1:
                row.update(op='Stop',reason='External call lies outside controlled THK55 subgraph')
            elif f['actionID'] != 0:
                if f['functionType'] not in (0,2):
                    row.update(op='Stop',reason='Combined predicate/action not supported')
                else:
                    row.update(op='YieldAction',native_action_id=f['actionID'],
                               action_args=[f[f'actionUnkn{i}'] for i in range(5)])
            elif f['functionType'] not in (0,2):
                row.update(op='Stop',reason='Unsupported unguarded original function')
            result.append(row)
    for index in sorted(missing):
        result.append(dict(key=key(index,0),op='Stop',next='',otherwise='',call_target='',
                           function_type=0,parameter1=0,parameter2=0,native_action_id=-1,
                           native_consumer_verified=False,
                           reason='Original called node intentionally outside bounded projection'))
    return dict(schema=1,entry=key(200,0),source_sha256=table['source']['sha256'],
                source_path=table['source']['path'],native_control_flow_verified=False,
                scope='Controlled original THK55 subgraph, not full automatic AI',instructions=result,
                qualification='Source-byte controls agree with pinned maintainer decompiler; current native VM dispatch/order still unqualified.')

def self_check(data):
    checks = []
    cases = []
    value = bytearray(data); value[0] ^= 1; cases.append(("signature", bytes(value)))
    value = bytearray(data); struct.pack_into("<h", value, 4, 99); cases.append(("version",bytes(value)))
    value = bytearray(data); struct.pack_into("<Q", value, 32, len(data)+1); cases.append(("node_pointer",bytes(value)))
    value = bytearray(data); struct.pack_into("<I", value, 40, 0xffffffff); cases.append(("segment_count",bytes(value)))
    cases.append(("truncated_core",data[:-13]))
    for name, corrupt in cases:
        try:
            parse_thk(corrupt)
        except (ValueError, struct.error):
            checks.append(dict(name=name, rejected=True))
        else:
            raise ValueError("Corruption accepted: "+name)
    return checks

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",type=Path,default=OUT/"thk-all-raw.json")
    ap.add_argument("--evidence",type=Path,default=ROOT/"Tools/MHW/rathian-thk-chain-evidence.json")
    ap.add_argument("--normal-form",type=Path,default=OUT/"bite-normal-form.json")
    ap.add_argument("--reuse-raw",action="store_true",help="Reuse the already qualified all-raw report; do not reparse original tables")
    ap.add_argument("--qualify",action="store_true")
    ap.add_argument("--native",action="store_true")
    ap.add_argument("--self-check",action="store_true")
    args = ap.parse_args()
    for rel, expected in PINNED.items():
        if sha((CACHE/rel).read_bytes()) != expected:
            raise ValueError("Pinned maintainer source mismatch")
    previous = json.loads(args.output.read_text(encoding="utf8")) if args.reuse_raw else None
    if previous:
        if previous["sources"]["manifest"] != identity(BASE.parent/"extraction-manifest.json"):
            raise ValueError("Cached extraction manifest identity changed")
        tables, lists = previous["tables"], previous["thklsts"]
    else:
        tables, lists = source_records()
    normal_list = next(row for row in lists if row["source"]["path"].endswith("/data/em001.thklst") and "/event/" not in row["source"]["path"])
    counts = dict(thk_files=len(tables),thklst_files=len(lists),
                  nodes=sum(len(t["nodes"]) for t in tables),
                  segments=sum(n["count"] for t in tables for n in t["nodes"]),
                  normal_context_slots=normal_list["count"])
    qualifications = qualify_external(tables,lists) if args.qualify else (dict(previous["qualification"], reused=True) if previous else dict(passed=False,reason="External reference comparison not requested"))
    normal_tables=compact_tables(tables,normal_list)
    common = dict(schema=1, mode="offline_source_extraction_not_original_game_execution",
                  sources=dict(script=identity(Path(__file__)),manifest=identity(BASE.parent/"extraction-manifest.json"),
                               leviathon=dict(repo="https://github.com/AsteriskAmpersand/Leviathon",commit=COMMIT,
                                              source_files=[identity(CACHE/p) for p in PINNED],
                                              license="GPL-3.0; external source cache only")),
                  counts=counts,qualification=qualifications,thklst=normal_list,
                  action_correlations=action_correlations())
    first_chain=dict(entry_scope="controlled_native_subchain_not_full_automatic_AI",
                     preferred_bite=dict(thklst_index=55,node_index=200,node_id=217,
                                         action_id=83,sequence=["localCall node_index2","localCall node_index198","emit original actionID83","return"],
                                         callers=references_to(tables,normal_list,55,200)),
                     dash_alternative=dict(thklst_index=55,node_index=201,node_id=218,
                                           sequence=["localCall node_index2","if functionType0x1f","emit87","else emit86","endif","return"],
                                           callers=references_to(tables,normal_list,55,201)),
                     supported_control_candidates=dict(noop_function_types=[0,2],conditional_begin=2,conditional_else=4,
                                                       conditional_end=8,return_flow=8,node_end_random=1,
                                                       local_reference_uses="node array index",external_reference_uses="node id"),
                     predicate_candidates=[dict(function_type=0x70,params=[0,0],maintainer_name="flying",native_semantics_verified=False),
                                           dict(function_type=0x1f,params=[0,0],maintainer_name="fatigued",native_semantics_verified=False),
                                           dict(function_type=0x16,params=[90,270],maintainer_name="angle_2d_cw_between",native_semantics_verified=False)],
                     execution_gate="Unknown predicate/control/call must stop; do not treat unknown as false or inject a hardcoded attack.")
    evidence=dict(**common,first_chain=first_chain,tables=normal_tables,normal_form=compile_normalform(normal_tables),
                  unresolved=["Raw parse/roundtrip does not prove VM semantics, LR eligibility or original automatic decisions.",
                              "Historical action names plus CRC are provisional until current native registration.",
                              "Complete timing and damage geometry/runtime chain are owned by separate work packages."])
    full=dict(**common,tables=tables,thklsts=lists)
    if args.self_check:
        evidence["self_checks"]=self_check((BASE/"em/em001/00/data/em001_00.thk").read_bytes())
    if args.native:
        evidence["native"]=native_evidence()
    for path,value in [(args.output,full),(args.evidence,evidence),(args.normal_form,evidence["normal_form"])]:
        path=path.resolve()
        if path.is_relative_to(BASE.resolve()):
            raise ValueError("Output may not overwrite original sources")
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf8")
    print(json.dumps(dict(**counts,qualification=qualifications,output=str(args.output),
                          evidence=str(args.evidence),native=args.native,
                          self_checks=len(evidence.get("self_checks",[]))),ensure_ascii=False))

if __name__ == "__main__":
    main()
