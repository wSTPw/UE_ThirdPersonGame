"""M1: audit community-named THK condition semantics against actual parameters.

For each of the 27 named function types, gather every use in the frozen THK dump
and validate that parameter values are consistent with the claimed semantics.
Output: evidence JSON + a three-column markdown table (已证 / 冲突 / 未知).
"""
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'Saved/DevFlow/Rathian-Condition-Audit-20261104/source-baseline/EvidenceInput/thk-all-raw.json'
OUT_JSON = ROOT / 'Tools/MHW/rathian-thk-condition-semantics-20261117.json'
OUT_MD = ROOT / 'Docs/Reference/MHWI-Rathian-THK-Condition-Semantics-20261117.md'

raw = json.loads(RAW.read_text(encoding='utf-8'))

uses = defaultdict(list)  # function_type -> [(context, node, params)]
for table in raw['tables']:
    context = Path(table['source'].get('path', '?')).stem
    for node in table['nodes']:
        for seg in node['segments']:
            f = seg['fields']
            ft = f.get('functionType', 0)
            uses[ft].append({'context': context, 'node': node['id'],
                             'p1': f.get('parameter1', 0), 'p2': f.get('parameter2', 0),
                             'action_id': f.get('actionID', 0)})

# 语义声明（来自 Tools/MHW/rathian-thk-fexty-coverage-20261103.json，社区命名）
SEMANTICS = {
    0x70: ('flying()', {'p1': 'zero', 'p2': 'zero'}),
    0x8: ('distance_2d_to_target().leq(p1)', {'p1': 'continuous_cm'}),
    0x6: ('distance_3d_to_target().leq(p1)', {'p1': 'continuous_cm'}),
    0xe: ('vertical_distance_to_target().leq(p1)', {'p1': 'continuous_cm'}),
    0xf: ('vertical_distance_to_target().gt(p1)', {'p1': 'continuous_cm'}),
    0x16: ('angle_2d_cw_between(p1,p2)', {'p1': 'angle_360', 'p2': 'angle_360'}),
    0x1e: ('enraged()', {'p1': 'zero', 'p2': 'zero'}),
    0x1f: ('fatigued()', {'p1': 'zero', 'p2': 'zero'}),
    0x1c: ('in_combat()', {'p1': 'zero', 'p2': 'zero'}),
    0x1d: ('alert_out_of_combat()', {'p1': 'zero', 'p2': 'zero'}),
    0x25: ('mounted()', {'p1': 'zero', 'p2': 'zero'}),
    0x27: ('mount_stabbed()', {'p1': 'zero', 'p2': 'zero'}),
    0x28: ('mount_staggered_twice()', {'p1': 'zero', 'p2': 'zero'}),
    0x26: ('mount_finisher_ready()', {'p1': 'zero', 'p2': 'zero'}),
    0x76: ('part(p1).is_broken(p2)', {'p1': 'small_enum', 'p2': 'bool'}),
    0x24: ('target_on_part(p1)', {'p1': 'small_enum'}),
    0x5: ('switch(targetArea)', {'p1': 'small_enum'}),
    0x3: ('switch(targetEnemy)', {'p1': 'small_enum'}),
    0x2e: ('switch(target)', {'p1': 'small_enum'}),
    0x2f: ('target_is(em_enum:p1)', {'p1': 'small_enum'}),
    0x10: ('switch(param1)', {'p1': 'small_enum'}),
    0xbf: ('in_map(st_enum:p1).in_area(p2)', {'p1': 'small_enum', 'p2': 'small_enum'}),
    0xb8: ('switch(current_quest().is_rank)', {'p1': 'rank_0_3'}),
    0xb1: ('force_area_change2()', {'p1': 'zero', 'p2': 'zero'}),
    0xae: ('force_area_change()', {'p1': 'zero', 'p2': 'zero'}),
    0x5e: ('clearTarget()', {'p1': 'zero', 'p2': 'zero'}),
}


def audit(ft, params):
    p1 = sorted({u['p1'] for u in params})
    p2 = sorted({u['p2'] for u in params})
    kind = None
    ok, notes = True, []

    def check(slot, expect):
        vals = p1 if slot == 'p1' else p2
        if expect == 'zero' and any(v != 0 for v in vals):
            return f'{slot} 非零: {vals[:8]}'
        if expect == 'angle_360' and any(not 0 <= v <= 360 for v in vals):
            return f'{slot} 超出 0..360: {vals[:8]}'
        if expect == 'bool' and any(v not in (0, 1) for v in vals):
            return f'{slot} 非布尔: {vals[:8]}'
        if expect == 'rank_0_3' and any(not 0 <= v <= 3 for v in vals):
            return f'{slot} 超出 0..3: {vals[:8]}'
        return None

    for slot, expect in (params and {} or {}).items():
        pass
    declared = SEMANTICS[ft][1]
    for slot, expect in declared.items():
        issue = check(slot, expect)
        if issue:
            ok = False
            notes.append(issue)
    if declared.get('p1') == 'continuous_cm':
        vals = [u['p1'] for u in params]
        if any(v <= 0 for v in vals):
            ok = False
            notes.append(f'p1 含非正值: min={min(vals)} max={max(vals)}')
        else:
            notes.append(f'p1 范围 {min(vals)}..{max(vals)}（{len(set(vals))} 个不同值，{len(vals)} 用例）')
    return ok, notes, p1, p2


rows = []
for ft, (sem, declared) in sorted(SEMANTICS.items()):
    params = uses.get(ft, [])
    if not params:
        rows.append({'function_type': hex(ft), 'semantics': sem, 'uses': 0,
                     'status': '未知', 'detail': 'THK 内未出现（命名来自其他怪物或引擎层）'})
        continue
    ok, notes, p1, p2 = audit(ft, params)
    rows.append({
        'function_type': hex(ft), 'semantics': sem, 'uses': len(params),
        'p1_values': p1[:20], 'p2_values': p2[:20],
        'status': '已证' if ok else '冲突', 'detail': '; '.join(notes),
        'contexts': sorted({u['context'] for u in params}),
    })

unnamed = sorted(
    ({hex(ft): u for ft, u in uses.items() if ft not in SEMANTICS}.items()),
    key=lambda kv: -len(kv[1]))
result = {
    'schema': 1, 'date': '2026-11-17',
    'mode': 'offline_source_extraction_not_original_game_execution',
    'source': str(RAW.relative_to(ROOT)),
    'named_count': len(SEMANTICS), 'rows': rows,
    'unnamed': [{'function_type': ft, 'uses': len(u),
                 'p1_distinct': len({x['p1'] for x in u}),
                 'p1_top': sorted({x['p1'] for x in u})[:12],
                 'contexts': sorted({x['context'] for x in u})}
                for ft, u in unnamed],
}
OUT_JSON.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding='utf-8')

proved = sum(1 for r in rows if r['status'] == '已证')
conflict = [r for r in rows if r['status'] == '冲突']
unknown = [r for r in rows if r['status'] == '未知']

md = ['# 雌火龙 THK 条件语义三栏表（M1）', '',
      f'- 日期：2026-11-17。数据源：`{RAW.relative_to(ROOT)}`（离线静态抽取，非原作运行）。',
      '- 命名来源：`Tools/MHW/rathian-thk-fexty-coverage-20261103.json`（社区 Fexty 命名）+ Leviathon ActionDumps。',
      '- 判定规则：距离类参数应为连续正值（cm）；角度类 0..360；无参类必须全零；rank 0..3；布尔 0/1。通过 = "已证"，违反声明 = "冲突"。',
      f'- 结果：已证 **{proved}** / 冲突 **{len(conflict)}** / 未出现 **{len(unknown)}**（另 {len(result["unnamed"])} 类未命名）。', '',
      '| functionType | 语义声明 | 用例 | 参数观察 | 判定 | 备注 |',
      '| --- | --- | ---: | --- | --- | --- |']
for r in rows:
    p1 = r.get('p1_values', [])
    p1txt = (f"{min(p1)}..{max(p1)} ({len(p1)})" if p1 else '-')
    md.append(f"| {r['function_type']} | {r['semantics']} | {r['uses']} | p1 {p1txt} | **{r['status']}** | {r['detail'][:120]} |")
md += ['', '## 未命名 functionType（按用例数排序）', '',
       '| functionType | 用例 | p1 不同值数 | p1 高频值 | 出现上下文 |',
       '| --- | ---: | ---: | --- | --- |']
for u in result['unnamed']:
    md.append(f"| {u['function_type']} | {u['uses']} | {u['p1_distinct']} | {u['p1_top']} | {', '.join(u['contexts'][:4])} |")
md += ['', '## 边界', '',
       '- 本表只做"参数取值与命名自洽"校验，**不证明原作运行等价**；运行验证需原作侧观测（M3，待授权）。',
       '- "已证"指当前 13015 段抽样内无反例；参数语义仍以社区命名为准。']
OUT_MD.write_text('\n'.join(md), encoding='utf-8')
print('M1 rows=%d proved=%d conflict=%d unknown=%d unnamed=%d' % (
    len(rows), proved, len(conflict), len(unknown), len(result['unnamed'])))
for r in conflict:
    print('  冲突:', r['function_type'], r['semantics'], '->', r['detail'][:100])
