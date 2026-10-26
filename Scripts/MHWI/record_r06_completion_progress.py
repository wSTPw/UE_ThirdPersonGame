"""Write B09 development handoff; does not run checks, tests, or Unreal."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run():
    policy = json.loads((ROOT/'Tools/MHW/native-link-motion-policy.json').read_text(encoding='utf8'))
    runtime = json.loads((ROOT/'Saved/MHWIRestoration/B09-20261025/runtime-source-data.json').read_text(encoding='utf8'))
    references = {f"R06-N{r['node']:02d}-P{r['phase']}": r for r in policy['references']}
    nodes = set(runtime['project_move_nodes'].values())
    path = ROOT/'Docs/Plans/MHWI-Connector-Progress.csv'
    with path.open(encoding='utf8', newline='') as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    for row in rows:
        ref = references[row['ID']]
        if ref['node'] == 86:
            row['状态'] = '原图无入边；0匹配记录；未测试'
            row['实施/下一步'] = '共享365与106@32保留；不得制造输入入口'
            continue
        missing = sorted({e['source_node'] for e in ref['incoming']} - nodes)
        row['状态'] = 'B09部分实施；来源玩法未齐；未编译/测试' if missing else 'B09角色适配已实施；原生混合仍开放；未编译/测试'
        row['实施/下一步'] = (
            f"{ref['runtime_record_count']}原生记录；实际来源实例/源帧、精确身份绑定接口、"
            '连接及直入主段MBD入帧、13主段绑定保护已接入；未启用猜测尾淡出'
        )
        if missing:
            row['实施/下一步'] += '；前置玩法调用方仍缺node'+','.join(map(str, missing))
        if ref['target_node'] in (1, 11):
            row['实施/下一步'] += '；目标自定义入口仍需迁移，连接表不代表完整入口'
        row['下一阶段通过准则'] = (
            f"真实来源/Phase{ref['phase']}→连接{ref['connector_motion']}→主段{ref['project_main_motion']}@{row['主段startFrame']}；"
            '先完成缺失来源及自定义入口、MotionTree/request门控/曲线/混合时钟，再安排编译/实际输入验收；'
            '连接期间无主招事件，入帧前事件不补播、费用不重复、低帧跨越/自然末帧/旧回调/死亡安全；'
            '不同段倍率/RateScale不混淆Montage秒与源帧；来源撤销令牌不能撤销新实例；'
            '保留原MBD专用行顺序/帧上限/第0行后备；根运动、武器时钟及混合须与原生消费者对应'
        )
    with path.open('w', encoding='utf8', newline='') as stream:
        writer = csv.DictWriter(stream, fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    intro = '''# R06连接动画逐条开发台账

更新：2026-10-25，B09。**部分实施，完整R06尚未达成，未编译/测试。** 已补真实来源交接接口、所有目标主段终点证据及统一MBD入帧；缺失前置玩法的实际调用方、自定义入口及原生混合门控仍须开发。不能将这些缺口写成“只待测试”。

关联：[B09现状](../Reference/MHWI-R06-Completion-Development.md)、[B09记录](../Changes/CHG-20261025-004-mhwi-r06-source-clock.md)、[CSV](MHWI-Connector-Progress.csv)、[通过准则](MHWI-Connector-Acceptance.md)。B04至B08历史保留。

30节点/32引用/124记录/26连接片段；13主段绑定含既有插入上挑。node86保持无入边。既有119自定义入口与112、129迁移沿用；气刃I、踏步斩新发现的专用入口不能被连接表替代。MBD overlap只有在原生MotionTree/request标志启用时才进入尾淡出，不能自动套到UE停播时长；没有启用未经证明的尾权重。

## 每条实施与下一阶段要求

'''
    lines = [intro, '| '+' | '.join(fields)+' |', '| '+' | '.join('---' for _ in fields)+' |']
    lines += ['| '+' | '.join(str(row[f]).replace('|', '\\|') for f in fields)+' |' for row in rows]
    (ROOT/'Docs/Plans/MHWI-Connector-Progress.md').write_text('\n'.join(lines)+'\n', encoding='utf8')
    progress = ROOT/'Docs/Plans/MHWI-Restoration-Progress.csv'
    with progress.open(encoding='utf8', newline='') as stream:
        reader = csv.DictReader(stream)
        progress_fields, items = reader.fieldnames, list(reader)
    for item in items:
        if item['项目'].startswith('R06 '):
            item['状态'] = 'B09部分实施，完整R06未完成；未编译/测试'
            item['证据和落点'] = '真实来源实例交接、13主段绑定、统一MBD入帧及源帧时钟；原生混合/专用入口新证据'
            item['本批及后续'] = '前置玩法调用方、SpiritI/StepSlash专用入口、MotionTree/request门控和混合时钟仍须开发；不测试'
    with progress.open('w', encoding='utf8', newline='') as stream:
        writer = csv.DictWriter(stream, progress_fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(items)
    print(json.dumps(dict(records_authored=True, tests_executed=False, r06_complete=False)))


if __name__ == '__main__':
    run()
