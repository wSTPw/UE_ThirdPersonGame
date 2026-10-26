"""Build a self-contained, read-only source-fidelity evidence browser.

This script consumes audit JSON files. It never launches Unreal Engine, touches
game assets, infers original cancel windows, or fetches network resources.
Example: python Scripts/MHWI/build_fidelity_report.py
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE = ROOT / "Saved/MHWIImport/SourceFidelity-20261024"
SEQUENCE_RE = re.compile(r"A_((?:w03|co00)_00)_(\d+)(?:\.|$)")
MOVE_NAMES = {
    "StepSlash": "踏步斩", "OverheadSlash": "纵斩", "FadeSlash": "后退袈裟斩",
    "SpiritI": "气刃斩 I", "Thrust": "突刺", "RisingSlash": "上挑",
    "SpiritII": "气刃斩 II", "SpiritIII": "气刃斩 III",
    "SpiritRoundslash": "气刃大回旋", "SpiritStepSlash": "气刃踏步斩",
    "FadeSlashLeft": "左移袈裟斩", "FadeSlashRight": "右移袈裟斩",
    "SpiritThrust": "气刃突刺", "ForesightSlash": "见切斩",
    "HelmRise": "登龙上升", "HelmAir": "登龙滞空",
    "SpiritHelmBreaker": "登龙下劈", "HelmLand": "登龙着地",
    "SpecialSheathe": "特殊纳刀", "IaiSlash": "居合二连",
    "IaiSpiritSlash": "居合气刃·无色", "IaiSpiritSlashWhite": "居合气刃·白",
    "IaiSpiritSlashYellow": "居合气刃·黄", "IaiSpiritSlashRed": "居合气刃·红",
    "Draw": "拔刀", "Sheathe": "纳刀", "Roll": "持刀翻滚",
    "RollSheathed": "纳刀翻滚", "DrawSlash": "拔刀斩",
    "SpiritComboThrust": "气刃插入突刺", "SpiritComboRisingSlash": "气刃插入上挑",
    "RollStepSlash": "翻滚踏步斩",
}
BOUNDARIES = [
    "这是离线证据调查；没有修改玩法、动画资产或武器位置，也没有执行本轮 PIE。",
    "TIML frame 是源动画帧坐标，不是墙钟时间。除以 60 仅为项目导入基准；MotionSpeed、原生求值和其他倍率仍会改变播放时序。",
    "PlMotionInput 的 raw flags 尚未映射到原生逐按键判定。候选 bit spans 仅按前值保持计算，禁止标作原作取消、输入接受或缓冲窗口。",
    "FSM 可证明静态路由与条件树存在；ActionNo 原生实现、连接帧、混合规则、原生按键语义尚未由这些文件完整解码。",
    "UE cancel_start / cancel_end 是读取时的项目 Montage 秒数，属于当前项目调校，不能证明与原作一致。",
    "源 track / group 的 hash 与顺序保留；公开格式标签及插值名称不等同于游戏原生求值器。乱码名称按原文件保留，定位使用节点编号和 hash。",
]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def process_parameter(node):
    return node.get("process", {}).get("mpParameter", {})


def compact_weapon(weapon):
    if not weapon:
        return {"status": "not_supplied"}
    return {
        "status": weapon.get("status"), "utc_time": weapon.get("utc_time"),
        "files": weapon.get("files", {}), "weapon_models": weapon.get("weapon_models", {}),
        "decoder_diagnosis": weapon.get("decoder_diagnosis", {}),
        "limits": weapon.get("limits", []),
        "protected_sources_unchanged": weapon.get("protected_sources_unchanged"),
        "mapped_moves": {
            clip: {"project_move_names": info.get("project_move_names", []),
                   "max_errors_by_kind": info.get("max_errors_by_kind", {}),
                   "focus_tracks": info.get("focus_tracks", [])}
            for clip, info in weapon.get("mapped_moves", {}).items()
        },
        "helper_bones": weapon.get("helper_bones", {}),
        "hunter_weapon_motion_events": weapon.get("hunter_weapon_motion_events", {}),
    }


def build_index(native, editor, mapping, verification, weapon, input_paths):
    entries = native["source"]["entries"]
    by_id = {int(entry["index"]): entry for entry in entries}
    if len(by_id) != len(entries):
        raise ValueError("Duplicate source MotionNo in native timing report")
    refs = defaultdict(list)
    formal = {}
    for move_name, move in editor["moves"].items():
        segments = []
        for order, segment in enumerate(move.get("segments", [])):
            match = SEQUENCE_RE.search(segment["sequence"])
            if not match:
                raise ValueError(f"Unrecognized source animation for {move_name}: {segment['sequence']}")
            bank, motion = match.group(1), int(match.group(2))
            clip = f"{bank}_{motion:03d}"
            audited = bank == "w03_00" and motion in by_id
            info = {"order": order, "source_clip": clip, "bank": bank, "motion": motion,
                    "timl_covered": audited, **segment,
                    "source_start_frame_at_import_60fps": numeric(segment.get("anim_start_time", 0)) * 60,
                    "source_end_frame_at_import_60fps": numeric(segment.get("anim_end_time", 0)) * 60,
                    "frame_conversion_status": "project_import_coordinate_only_not_native_wall_clock"}
            segments.append(info)
            refs[clip].append({"move": move_name, "segment": order,
                               "montage": move.get("montage"),
                               "source_start_frame_at_import_60fps": info["source_start_frame_at_import_60fps"],
                               "source_end_frame_at_import_60fps": info["source_end_frame_at_import_60fps"]})
        if not segments:
            raise ValueError(f"Formal move has no inspectable segments: {move_name}")
        formal[move_name] = {"label_zh": MOVE_NAMES.get(move_name, move_name), **move,
                             "segments": segments,
                             "timing_semantics": "current_project_montage_seconds_not_original_cancel_windows"}
    if editor.get("move_count") != len(formal):
        raise ValueError("Editor move_count differs from serialized formal moves")

    mapped_by_clip = defaultdict(list)
    for name, move in mapping.get("moves", {}).items():
        mapped_by_clip[move["clip"]].append({"move": name, **move})
    connector_nodes = defaultdict(list)
    for node in native.get("fsm_nodes", []):
        param = process_parameter(node)
        for field in ("MotionNo", "MotionNo_Phase1"):
            value = param.get(field)
            if isinstance(value, int) and value >= 0:
                connector_nodes[value].append(node["node_id"])
    audit_by_motion = defaultdict(list)
    for item in (verification or {}).get("per_action_timing_audit", []):
        audit_by_motion[item["motion"]].append(item)

    motions = []
    for motion, entry in sorted(by_id.items()):
        clip = f"w03_00_{motion:03d}"
        groups = entry.get("groups", [])
        labels = mapped_by_clip.get(clip, [])
        fsm_ids = sorted({m["fsm_node_id"] for m in labels if m.get("fsm_node_id") is not None}
                         | set(connector_nodes.get(motion, [])))
        tracks = [track for group in groups for track in group.get("tracks", [])]
        input_tracks = [track for group in groups if group.get("name") == "nTimelineParam::PlMotionInput"
                        for track in group.get("tracks", [])]
        bit_items = [row for row in native.get("input_bit_intervals", []) if row["motion"] == motion]
        motions.append({
            "motion": motion, "clip": clip, "source_frame_count": entry.get("source_frame_count"),
            "source_loop_frame": entry.get("source_loop_frame"), "timl": entry.get("timl"),
            "counts": {"groups": len(groups), "tracks": len(tracks),
                       "keys": sum(len(t.get("keys", [])) for t in tracks),
                       "input_tracks": len(input_tracks)},
            "project_labels": [m["move"] for m in labels],
            "formal_uses": refs.get(clip, []), "fsm_node_ids": fsm_ids,
            "fsm_mapping_status": "project_pose_mapping_or_literal_connector_motion_reference" if fsm_ids else "no_static_mapping_recorded",
            "input_key_frames": sorted({k["frame"] for track in input_tracks for k in track.get("keys", [])}),
            "candidate_bit_span_tracks": len(bit_items),
            "source_weapon_event_tracks": len((weapon or {}).get("hunter_weapon_motion_events", {}).get(clip, [])),
            "known": ["原始TIML轨道/key/值/control/transition保留", "源MotionNo与源帧数量可定位"],
            "unknown": ["逐按键输入接受/取消/缓冲窗口", "原生ActionNo派发和连接混合/起始帧规则", "原作墙钟节奏与角度索引参数"],
        })
    inputs = {relative(path): {"sha256": sha256(path), "bytes": path.stat().st_size}
              for path in input_paths if path is not None and path.exists()}
    verify_matches = []
    for path in input_paths:
        if path is None or not path.exists():
            continue
        for recorded, digest in (verification or {}).get("input_files", {}).items():
            if Path(recorded.replace("\\", "/")).name == path.name:
                verify_matches.append({"input": relative(path), "verification_recorded_path": recorded,
                                       "same_content_hash": digest == sha256(path)})
    common = sorted({seg["source_clip"] for move in formal.values() for seg in move["segments"]
                     if not seg["timl_covered"]})
    return {
        "schema_version": 1, "status": "offline_evidence_browser_no_gameplay_or_asset_changes",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "boundaries": BOUNDARIES,
        "input_files": inputs,
        "source_hashes": {"lmt": {k: v for k, v in native["source"].items() if k != "entries"},
                          "fsm_sha256": native.get("fsm_sha256"),
                          "label_dictionary_sources": native.get("label_dictionary_sources", {}),
                          "editor_disk_asset_sha256": editor.get("disk_asset_sha256", {})},
        "counts": {"source_motions": len(motions), "formal_moves": len(formal),
                   "formal_segments": sum(len(m["segments"]) for m in formal.values()),
                   "mapped_project_moves": len(mapping.get("moves", {})),
                   "fsm_nodes": len(native.get("fsm_nodes", [])),
                   "fsm_links": sum(len(n.get("links", [])) for n in native.get("fsm_nodes", [])),
                   "formal_source_clips_outside_w03_timing_audit": common},
        "editor_observation": {key: editor.get(key) for key in ("status", "generated_utc", "data_asset", "input_buffer_seconds")},
        "verification": {"present": verification is not None,
                         "status": (verification or {}).get("status"),
                         "assertions": (verification or {}).get("assertions"),
                         "error_count": len((verification or {}).get("errors", [])),
                         "input_content_comparison": verify_matches},
        "weapon": {"status": (weapon or {}).get("status", "not_supplied"),
                   "limits": (weapon or {}).get("limits", []),
                   "decoder_diagnosis": (weapon or {}).get("decoder_diagnosis", {})},
        "motions": motions, "formal_moves": formal,
    }


def markdown_table(index, native, mapping):
    by_motion = {row["motion"]: row for row in index["motions"]}
    nodes = {node["node_id"]: node for node in native.get("fsm_nodes", [])}
    lines = ["# MHWI 24 个项目动作：源数据与正式 UE 观察对照", "",
             f"生成时间（UTC）：{index['generated_utc']}。本表仅调查，不表示任何玩法修复。", "",
             "源帧为 TIML 坐标，UE 取消窗口为 Montage 秒数；二者不能直接等同。raw flags 尚未解码，输入 key 变化点不是原作取消帧。",
             "源 LMT MotionNo 与 FSM ActionNo 为不同编号空间。正式32定义和复合Montage的逐段来源见 fidelity-index.json / fidelity-report.html。", "",
             "| 项目动作（名称为项目推断） | 源动作 / 帧数 / TIML 长度 | 输入 key 帧（raw） | FSM 节点 / ActionNo / 出口数 | 正式 UE 取消秒 / 路由数 |", "| --- | --- | --- | --- | --- |"]
    for name, item in mapping["moves"].items():
        row = by_motion[int(item["clip"].rsplit("_", 1)[1])]
        formal = index["formal_moves"].get(name, {})
        node_id = item.get("fsm_node_id")
        node = nodes.get(node_id, {})
        frames = ", ".join(f"{n:g}" for n in row["input_key_frames"]) or "无"
        window = f"{numeric(formal['cancel_start']):.4f}–{numeric(formal['cancel_end']):.4f}" if "cancel_start" in formal else "未读取"
        lines.append(f"| {MOVE_NAMES.get(name, name)} `{name}` | `{row['clip']}` / {row['source_frame_count']} / {row.get('timl', {}).get('length', '无')} | {frames} | {node_id} / {item.get('fsm_action_no', '无')} / {len(node.get('links', []))} | {window} / {len(formal.get('routes', []))} |")
    lines += ["", "已知：源轨道、原始 key/control/transition、静态 FSM 连接和正式资产读取时的配置。",
              "未知：原生逐按键位语义、完整输入缓冲/取消优先级、ActionNo 派发/混合/起始帧规则、变速求值器及原作实测节奏。",
              "", "复合片段：`RollStepSlash` 正式 Montage 通过 segments 读取为 `w03_00_129` + `w03_00_101`；不按动作名称猜测来源。",
              "`RollSheathed` 使用 `co00_00_130`，属于通用动画库，当前 w03 TIML 审计未覆盖其轨道。", ""]
    return "\n".join(lines)


HTML = r'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'">
<title>MHWI 原作数据 · 工程证据报告</title>
<style>
:root{color-scheme:light;--ink:#203047;--muted:#596b80;--line:#d5dde6;--bg:#f3f6fa;--accent:#154f91;--warn:#854b04}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.65 system-ui,"Microsoft YaHei",sans-serif}header{padding:22px 28px;background:#172c46;color:#fff}h1{font-size:25px;margin:0 0 3px}h2{font-size:20px;margin:0 0 12px}h3{font-size:16px;margin:12px 0 7px}p{margin:6px 0}header p{color:#c2d2e5}button,input,select{font:inherit}input,select{padding:8px;border:1px solid #b9c8d9;border-radius:5px;background:#fff;width:100%;color:var(--ink)}button{border:1px solid #b8c6d6;padding:5px 9px;color:var(--accent);background:#fff;border-radius:4px;cursor:pointer}button:hover{background:#e8f0fa}.shell{display:grid;grid-template-columns:300px minmax(0,1fr);max-width:1900px;margin:auto}.sidebar{padding:18px;border-right:1px solid var(--line);position:sticky;top:0;height:100vh;overflow:auto;background:#fff}.sidebar label{display:block;margin:12px 0 5px;font-weight:650}.motion-list{display:grid;gap:5px;margin-top:10px}.motion-list button{text-align:left;line-height:1.5;padding:8px 9px}.motion-list button.active{background:#dceafb;border-color:#356ba5}.motion-list small{display:block;color:var(--muted)}main{min-width:0;padding:22px 26px 70px}.card{background:#fff;border:1px solid var(--line);padding:18px;margin-bottom:15px;border-radius:6px}.warning{border-left:4px solid #cc922e;background:#fff8e9;color:#674104;padding:12px 16px}.muted{color:var(--muted)}.stats{display:flex;flex-wrap:wrap;gap:12px;margin-top:14px}.stat{min-width:120px;padding:9px 16px;border-left:3px solid #9ab4d1;background:#f4f7fb}.stat strong{font-size:22px;display:block;color:#1c4f88}.tag{display:inline-block;background:#e6eef8;color:#305a8c;padding:1px 7px;border-radius:4px;margin:2px;font-size:12px}.tag.warn{background:#fff1ce;color:#775005}code,pre{font-family:Consolas,monospace;font-size:12px}code{overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f7fa;padding:10px;border:1px solid #e0e6ed;border-radius:4px;max-height:470px;overflow:auto}details{border-top:1px solid #e4e9f0;margin-top:8px;padding-top:8px}summary{cursor:pointer;font-weight:650;overflow-wrap:anywhere}.scroll{overflow:auto}table{width:100%;border-collapse:collapse;margin:7px 0 11px;font-size:12px}th,td{text-align:left;border-bottom:1px solid #e1e6ed;padding:7px 9px;vertical-align:top}th{background:#f0f4f8;position:sticky;top:0}td code{font-size:11px}ul{padding-left:22px}.track-meta{font-weight:400;color:var(--muted);font-size:12px}.timeline{height:14px;background:#e5ebf3;border-radius:3px;position:relative;margin:10px 0}.tick{position:absolute;height:14px;width:3px;background:#3c71a8}.route{border-left:3px solid #a2bad7;margin:8px 0;padding:7px 11px;background:#f7f9fc}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}.nav-actions{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}.small{font-size:12px}.nowrap{white-space:nowrap}.status{font-weight:650;color:#6c4d13}@media(max-width:1000px){.shell{grid-template-columns:245px minmax(0,1fr)}main{padding:18px 14px}.grid2{grid-template-columns:1fr}}@media(max-width:720px){.shell{display:block}.sidebar{height:auto;max-height:420px;position:relative;border-right:0;border-bottom:1px solid var(--line)}.motion-list{grid-template-columns:1fr 1fr}header{padding:18px}h1{font-size:20px}}
</style></head><body>
<header><h1>MHWI 原作数据 · 工程证据报告</h1><p>源动画 / TIML / FSM / 正式 UE 配置的离线调查 · 只读 · 无外部依赖</p></header>
<div class="shell"><aside class="sidebar"><label for="search">搜索原始动作</label><input id="search" type="search" placeholder="编号、项目名、轨道名、hash" autocomplete="off"><label for="scope">动作范围</label><select id="scope"><option value="all">全部原始动作</option><option value="formal">正式 UE 引用</option><option value="mapped">24 个映射动作</option><option value="connector">包含连接动作节点</option></select><p id="count" class="muted small"></p><div id="motion-list" class="motion-list"></div><label for="formal-select">按正式32定义查看</label><select id="formal-select"><option value="">选择项目动作…</option></select><label for="fsm-select">浏览全部 FSM 节点</label><select id="fsm-select"><option value="">选择源节点…</option></select></aside>
<main><section id="overview" class="card"></section><section class="warning"><strong>证据边界</strong><ul id="boundaries"></ul></section><div id="detail"></div><section class="card"><h2>可追溯输入与源 hash</h2><p class="muted">报告只读取以下文件；观察时间与文件指纹用于限定结论。展开可见完整 SHA-256。</p><details><summary>输入文件与校验</summary><pre id="provenance"></pre></details><details><summary>独立结构复核与待解问题</summary><pre id="verification"></pre></details><details><summary>武器调查概览</summary><div id="weapon-overview"></div></details></section></main></div>
<script type="application/json" id="report-data">__PAYLOAD__</script>
<script>
'use strict';
const DATA=JSON.parse(document.getElementById('report-data').textContent), IDX=DATA.index;
const motions=IDX.motions, sourceById=new Map(DATA.native.source.entries.map(x=>[x.index,x]));
const nodeById=new Map(DATA.native.fsm_nodes.map(x=>[x.node_id,x]));
let selected=motions[0].motion, currentMode='motion';
const el=id=>document.getElementById(id), esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const raw=x=>'<pre>'+esc(JSON.stringify(x,null,2))+'</pre>', code=x=>'<code>'+esc(x)+'</code>';
const fmt=x=>Number.isFinite(Number(x))?Number(x).toFixed(4).replace(/\.?0+$/,''):String(x??'—');
const hash=x=>x===undefined?'—':`${x} / 0x${(Number(x)>>>0).toString(16).toUpperCase()}`;
const table=(heads,rows)=>'<div class="scroll"><table><thead><tr>'+heads.map(h=>'<th>'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(c=>'<td>'+c+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
const tags=xs=>xs.map(x=>'<span class="tag">'+esc(x)+'</span>').join('');
function sourceButton(id,label){return '<button data-motion="'+id+'">'+esc(label??`源 ${id}`)+'</button>'}
function nodeButton(id){return '<button data-node="'+id+'">节点 '+id+'</button>'}
function actionNumber(node){const a=node?.process?.mpParameter?.ActionNo;return a?.EnumValue??a??'—'}
function timeline(keys,length){return '<div class="timeline" aria-label="源帧 key 分布（非墙钟）">'+keys.map(k=>'<span class="tick" title="frame '+esc(k.frame)+'" style="left:'+Math.max(0,Math.min(99.7,Number(k.frame)/Math.max(1,length)*100))+'%"></span>').join('')+'</div>'}
function renderTrack(track,length){const label=track.name||'未命名轨道';return '<details><summary>'+esc(label)+' <span class="track-meta">hash '+esc(hash(track.hash))+' · order '+esc(track.order)+' · kind '+esc(track.kind)+' · '+track.keys.length+' keys</span></summary>'+timeline(track.keys,length)+table(['源 frame','value（原值）','control_l','control_r','transition（原码）','key_kind'],track.keys.map(k=>[fmt(k.frame),code(JSON.stringify(k.value)),code(JSON.stringify(k.control_l)),code(JSON.stringify(k.control_r)),esc(k.transition),esc(k.key_kind)]))+'</details>'}
function routeList(node,depth=0,visited=new Set()){
 if(!node)return '<p class="muted">该节点未在源报告中找到。</p>';
 if(visited.has(node.node_id))return '<p class="muted">循环回到节点 '+node.node_id+'；停止展开。</p>';
 const seen=new Set(visited);seen.add(node.node_id);
 return (node.links||[]).map((link,order)=>{
  const dest=nodeById.get(link.mDestinationNodeId), par=dest?.process?.mpParameter||{}, motion=par.MotionNo;
  let nested='';
  if(dest?.process?.mContainerName?.startsWith('LinkMotion')&&depth<6){nested='<details><summary>连接节点后续路径（静态路径，不表示原生调度时间）</summary>'+routeList(dest,depth+1,seen)+'</details>'}
  return '<div class="route"><strong>#'+order+' '+esc(link.mName)+'</strong> → '+nodeButton(link.mDestinationNodeId)+' '+esc(dest?.process?.mContainerName||'')+' / ActionNo '+esc(actionNumber(dest))+(Number.isInteger(motion)&&motion>=0?' / '+sourceButton(motion,'MotionNo '+motion):'')+'<p class="small muted">ConditionId '+esc(link.mConditionId)+'；ExistCondition '+esc(link.mExistCondition)+'。数组顺序按本报告输入保留，不能据此断言运行优先级。</p><details><summary>条件树 / 原始 link</summary>'+raw(link)+'</details>'+nested+'</div>';
 }).join('')||'<p class="muted">无静态出口。</p>';
}
function renderNode(id){const node=nodeById.get(id);return node?'<h3>源 FSM 节点 '+id+' · '+esc(node.name)+'</h3><p>容器 '+code(node.process?.mContainerName)+' · ActionNo '+esc(actionNumber(node))+'</p><details><summary>process 原始参数</summary>'+raw(node.process)+'</details>'+routeList(node):'<p>未找到节点 '+id+'</p>'}
function formalCard(name){const move=IDX.formal_moves[name];if(!move)return '';
 const segs=table(['段号','实际动画资产','源标识 / 覆盖','Montage 起始秒','片段裁剪秒 / 导入60fps坐标','片段速率 / 循环'],move.segments.map(s=>[esc(s.order),code(s.sequence),s.bank==='w03_00'?sourceButton(s.motion,s.source_clip)+(s.timl_covered?'':' <span class="tag warn">未覆盖</span>'):code(s.source_clip)+'<br><span class="tag warn">通用库，当前 w03 TIML 未覆盖</span>',fmt(s.start_pos),fmt(s.anim_start_time)+'…'+fmt(s.anim_end_time)+' s<br>'+fmt(s.source_start_frame_at_import_60fps)+'…'+fmt(s.source_end_frame_at_import_60fps)+' f',fmt(s.anim_play_rate)+' / '+esc(s.looping_count)]));
 const routes=table(['项目输入','目标动作','需命中','需反击','需持刀'],move.routes.map(r=>[esc(r.input),'<button data-formal="'+esc(r.next_move)+'">'+esc(r.next_move)+'</button>',esc(r.require_hit),esc(r.require_counter),esc(r.require_drawn)]));
 return '<section class="card"><h2>正式 UE · '+esc(move.label_zh)+' <span class="small">'+esc(name)+'</span></h2><p>'+code(move.montage)+'</p><p class="status">当前项目取消窗口：'+fmt(move.cancel_start)+'…'+fmt(move.cancel_end)+' Montage 秒；这不是已还原的原作窗口。</p><p>播放速率 '+esc(move.play_rate)+' · 输入缓冲 '+fmt(IDX.editor_observation.input_buffer_seconds)+' s · 读取时间 '+esc(IDX.editor_observation.generated_utc)+'</p>'+segs+'<h3>当前项目派生路由</h3>'+routes+'<details><summary>全部正式读取字段（含 turn/counter/source_play_rates）</summary>'+raw(move)+'</details></section>';
}
function renderMotion(id){const info=motions.find(x=>x.motion===id),entry=sourceById.get(id);if(!entry||!info){el('detail').innerHTML='<section class="card"><h2>源 MotionNo '+id+'</h2><p>不在当前164条有效 w03 源动作范围内；此处不补造数据。</p></section>';return}
 selected=id;currentMode='motion';refreshList();
 const groups=entry.groups.map(g=>'<details'+(g.name==='nTimelineParam::PlMotionInput'?' open':'')+'><summary>'+esc(g.name||'未命名组')+' <span class="track-meta">hash '+esc(hash(g.hash))+' · order '+esc(g.order)+' · unknown '+esc(g.unknown)+' · '+g.tracks.length+' tracks</span></summary>'+g.tracks.map(t=>renderTrack(t,entry.timl?.length||entry.source_frame_count)).join('')+'</details>').join('')||'<p class="muted">此动作没有 TIML group/track；仍保留其源动画索引和采样帧数，无法据此推断输入或取消窗口。</p>';
 const bits=DATA.native.input_bit_intervals.filter(x=>x.motion===id);
 const audits=(DATA.verification?.per_action_timing_audit||[]).filter(x=>x.motion===id);
 const weapon=DATA.weapon, clip=info.clip;
 let w='<p class="muted">当前可选武器报告没有此动作的单独摘要；不表示动作没有武器数据。</p>';
 if(weapon.status!=='not_supplied')w=raw({helper_bones:weapon.helper_bones?.[clip]||[],mapped_move:weapon.mapped_moves?.[clip]||null,hunter_weapon_motion_events:weapon.hunter_weapon_motion_events?.[clip]||[],limits:weapon.limits,decoder_diagnosis:weapon.decoder_diagnosis});
 el('detail').innerHTML='<section class="card"><h2>'+esc(info.clip)+'</h2><p>'+tags(info.project_labels.length?info.project_labels:['未标注项目动作名称'])+'</p><div class="stats">'+[['源帧数',entry.source_frame_count],['TIML 长度',entry.timl?.length??'—'],['轨道',info.counts.tracks],['keys',info.counts.keys]].map(([k,v])=>'<div class="stat"><strong>'+esc(v)+'</strong>'+esc(k)+'</div>').join('')+'</div><p class="muted">source_loop_frame '+esc(entry.source_loop_frame)+'；TIML 末帧和源采样数可相差1，保留两者。所有横轴和 frame 均为源坐标。</p><details><summary>源 TIML 头字段</summary>'+raw(entry.timl)+'</details><p><strong>正式引用：</strong>'+(info.formal_uses.map(u=>'<button data-formal="'+esc(u.move)+'">'+esc(u.move)+' · segment '+u.segment+'</button>').join(' ')||'没有正式32定义的 segment 引用')+'</p><p><strong>FSM 来源关联：</strong>'+info.fsm_node_ids.map(nodeButton).join(' ')+' <span class="muted small">项目姿态映射或字面 MotionNo 引用；不是原生 ActionNo 实现已解码。</span></p></section>'
 +'<section class="card"><h2>全部 TIML groups / tracks / keys</h2><p class="muted">展开每条轨道查看全部 frame、value、control_l/r、transition、key_kind。数值、hash和原顺序完整保留；没有自动把插值改为线性。</p><input id="track-search" type="search" placeholder="在此动作内筛选轨道名或 hash"><div id="tracks">'+groups+'</div><details><summary>公开格式插值名称参考（非原生求值证明）</summary>'+raw({labels:DATA.native.interpolation_labels,reference:DATA.native.interpolation_reference})+'</details></section>'
 +'<section class="card"><h2>raw input flags：候选 spans</h2><p class="status">以下 spans 仅按 previous-key hold 得出。位语义未解码，不能当作原作取消、输入接受、缓冲或无敌窗口。</p><details><summary>查看全部候选 bit spans / 原始 input tracks（'+bits.length+' 条）</summary>'+raw(bits)+'</details></section>'
 +'<section class="card"><h2>源 FSM 静态路径</h2><p class="muted">先定位节点，再看连接动画和目标；condition_tree 原样可展开。路由存在不能证明触发时刻。</p>'+(info.fsm_node_ids.map(renderNode).join('')||'<p>当前文件没有把此源动画映射到 FSM 节点；不按序号猜测。</p>')+'</section>'
 +'<section class="card"><h2>对应正式 UE 配置</h2><p class="muted">来源由实际 Montage segments 解析，同一动画可被多个项目身份复用。</p>'+(info.formal_uses.length?'':'<p>当前没有正式定义使用此片段。</p>')+'</section>'
 +[...new Set(info.formal_uses.map(u=>u.move))].map(formalCard).join('')
 +'<section class="card"><details><summary>此动作独立静态复核记录（含历史 UE 快照，非本轮运行验证）</summary>'+raw(audits)+'</details><details><summary>武器 / 辅助骨 / 播放事件证据</summary>'+w+'</details></section>';
 el('track-search').addEventListener('input',event=>{const q=event.target.value.toLowerCase();for(const g of el('tracks').children){let n=0;for(const t of [...g.children].filter(x=>x.tagName==='DETAILS')){const yes=t.querySelector('summary').textContent.toLowerCase().includes(q);t.hidden=!yes;if(yes)n++}g.hidden=n===0;if(q&&n)g.open=true}});
}
function refreshList(){const q=el('search').value.trim().toLowerCase(),scope=el('scope').value;
 const shown=motions.filter(m=>{if(scope==='formal'&&!m.formal_uses.length)return false;if(scope==='mapped'&&!m.project_labels.length)return false;if(scope==='connector'&&!m.fsm_node_ids.some(id=>nodeById.get(id)?.process?.mContainerName?.startsWith('LinkMotion')))return false;
 const entry=sourceById.get(m.motion),text=[m.clip,m.motion,...m.project_labels,...m.formal_uses.map(x=>x.move),...entry.groups.flatMap(g=>[g.name,g.hash,...g.tracks.flatMap(t=>[t.name,t.hash])])].join(' ').toLowerCase();return !q||text.includes(q)});
 el('count').textContent=`显示 ${shown.length} / ${motions.length} 条有效源动画`;
 el('motion-list').innerHTML=shown.map(m=>'<button class="'+(selected===m.motion&&currentMode==='motion'?'active':'')+'" data-motion="'+m.motion+'">'+esc(m.clip)+'<small>'+esc(m.project_labels.join(' / ')||'未命名源动作')+' · '+m.counts.keys+' keys'+(m.formal_uses.length?' · UE '+m.formal_uses.length+'段引用':'')+'</small></button>').join('');
}
function showFormal(name){if(!IDX.formal_moves[name])return;currentMode='formal';el('formal-select').value=name;refreshList();el('detail').innerHTML=formalCard(name)}
el('overview').innerHTML='<h2>调查覆盖与结论强度</h2><p>可搜索164个原始动作、逐轨道查 key、沿 FSM 路径查看连接，以及对照正式32个项目动作。此报告提供继续还原所需的可追溯材料。</p><div class="stats">'+[['源动作',IDX.counts.source_motions],['正式定义',IDX.counts.formal_moves],['FSM 节点',IDX.counts.fsm_nodes],['静态出口',IDX.counts.fsm_links]].map(([k,v])=>'<div class="stat"><strong>'+v+'</strong>'+k+'</div>').join('')+'</div><p class="small muted">生成 UTC '+esc(IDX.generated_utc)+' · 正式资产观察 UTC '+esc(IDX.editor_observation.generated_utc)+'</p>';
el('boundaries').innerHTML=IDX.boundaries.map(x=>'<li>'+esc(x)+'</li>').join('');
el('provenance').textContent=JSON.stringify({source_hashes:IDX.source_hashes,input_files:IDX.input_files,editor_observation:IDX.editor_observation,verification:IDX.verification},null,2);
el('verification').textContent=JSON.stringify({status:DATA.verification?.status,assertions:DATA.verification?.assertions,errors:DATA.verification?.errors,warnings:DATA.verification?.warnings,next_evidence_required:DATA.verification?.next_evidence_required,native_limitations:DATA.native.limitations},null,2);
el('weapon-overview').innerHTML=raw({status:DATA.weapon.status,utc_time:DATA.weapon.utc_time,files:DATA.weapon.files,weapon_models:DATA.weapon.weapon_models,decoder_diagnosis:DATA.weapon.decoder_diagnosis,limits:DATA.weapon.limits,protected_sources_unchanged:DATA.weapon.protected_sources_unchanged});
for(const [name,m] of Object.entries(IDX.formal_moves)){const o=document.createElement('option');o.value=name;o.textContent=name+' · '+m.label_zh;el('formal-select').append(o)}
for(const n of DATA.native.fsm_nodes){const o=document.createElement('option');o.value=n.node_id;o.textContent=`节点 ${n.node_id} · ${n.process?.mContainerName??''} · ActionNo ${actionNumber(n)}`;el('fsm-select').append(o)}
el('search').addEventListener('input',refreshList);el('scope').addEventListener('change',refreshList);
el('formal-select').addEventListener('change',event=>showFormal(event.target.value));
el('fsm-select').addEventListener('change',event=>{if(event.target.value==='')return;currentMode='fsm';refreshList();el('detail').innerHTML='<section class="card"><h2>全局源 FSM 浏览</h2>'+renderNode(Number(event.target.value))+'</section>'});
document.addEventListener('click',event=>{const b=event.target.closest('button');if(!b)return;if(b.dataset.motion!==undefined)renderMotion(Number(b.dataset.motion));if(b.dataset.formal)showFormal(b.dataset.formal);if(b.dataset.node!==undefined){currentMode='fsm';el('fsm-select').value=b.dataset.node;refreshList();el('detail').innerHTML='<section class="card"><h2>源 FSM 静态路径</h2>'+renderNode(Number(b.dataset.node))+'</section>'}});
renderMotion(selected);
</script></body></html>'''


def build_report(base, mapping_path, out):
    native_path, editor_path = base / "timing-native-full.json", base / "editor-readback.json"
    verify_path, weapon_path = base / "timing-verification.json", base / "weapon-fidelity-summary.json"
    native, editor, mapping = read_json(native_path), read_json(editor_path), read_json(mapping_path)
    verification = read_json(verify_path) if verify_path.exists() else None
    weapon = read_json(weapon_path) if weapon_path.exists() else None
    index = build_index(native, editor, mapping, verification, weapon,
                        [native_path, editor_path, mapping_path,
                         verify_path if verification else None, weapon_path if weapon else None])
    # Keep the compact JSON index separate; embed full evidence in the HTML so
    # file:// opening needs no fetch, server, external script, or network call.
    payload = {"index": index, "native": native,
               "verification": {key: (verification or {}).get(key) for key in
                                ("status", "assertions", "errors", "warnings", "next_evidence_required", "per_action_timing_audit")},
               "weapon": compact_weapon(weapon)}
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    encoded = encoded.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    encoded = encoded.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    document = HTML.replace("__PAYLOAD__", encoded)
    # Guard against accidental future remote dependencies or active integrations.
    if re.search(r"<(?:script|link|iframe|img)\b[^>]*(?:src|href)\s*=", document, re.I):
        raise ValueError("Standalone report contains an external resource element")
    if re.search(r"\b(?:fetch|XMLHttpRequest|WebSocket|eval)\s*\(", HTML):
        raise ValueError("Report must not execute network/API calls")
    if json.loads(encoded) != payload:
        raise ValueError("HTML data escaping did not round-trip")
    out.mkdir(parents=True, exist_ok=True)
    (out / "fidelity-index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8")
    (out / "fidelity-report.html").write_text(document, encoding="utf-8")
    (out / "fidelity-move-table.md").write_text(markdown_table(index, native, mapping), encoding="utf-8")
    return {"status": "built_offline_no_ue_changes", "output": relative(out),
            "counts": index["counts"], "verification": index["verification"],
            "files": {name: {"bytes": (out / name).stat().st_size, "sha256": sha256(out / name)}
                      for name in ("fidelity-index.json", "fidelity-report.html", "fidelity-move-table.md")}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--mapping", type=Path, default=ROOT / "Scripts/MHWI/moveset_mapping.json")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    print(json.dumps(build_report(args.base, args.mapping, args.out or args.base), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
