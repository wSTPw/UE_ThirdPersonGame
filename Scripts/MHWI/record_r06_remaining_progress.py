"""Author B10 completion records. Does not compile, check, or test the project."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = 'Docs/Reference/MHWI-R06-Remaining-Development.md'
CHANGE = 'Docs/Changes/CHG-20261025-005-mhwi-r06-remaining.md'


def read_csv(path):
    with path.open(encoding='utf8', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def write_csv(path, fields, rows):
    with path.open('w', encoding='utf8', newline='') as stream:
        writer = csv.DictWriter(stream, fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def run():
    policy = json.loads((ROOT/'Tools/MHW/native-link-motion-policy.json').read_text(encoding='utf8'))
    sources = json.loads((ROOT/'Tools/MHW/native-r06-source-owners.json').read_text(encoding='utf8'))
    imports = json.loads((ROOT/'Saved/MHWIRestoration/B10-20261025/r06-import-journal.json').read_text(encoding='utf8'))
    refs = {f"R06-N{r['node']:02d}-P{r['phase']}": r for r in policy['references']}
    path = ROOT/'Docs/Plans/MHWI-Connector-Progress.csv'
    fields, rows = read_csv(path)
    for row in rows:
        ref = refs[row['ID']]
        if ref['node'] == 86:
            row['状态'] = '开发处理完成：原图无入边；0记录；未测试'
            row['实施/下一步'] = '365片段及106@32数据保留；不制造可达入口'
            row['下一阶段通过准则'] = '若后续安排验证，确认node86仍为0入边/0匹配记录；共享片段不授予输入许可'
            continue
        row['状态'] = 'B10开发完成；未编译/测试'
        row['实施/下一步'] = (
            f"{ref['runtime_record_count']}原生记录；真实来源实例/源帧与精确身份；"
            '有序专用/通用入口；MBD入帧；求值前线性姿态混合与独立Actor时钟'
        )
        source_nodes = {e['source_node'] for e in ref['incoming']}
        if 0 in source_nodes:
            row['实施/下一步'] += '；实际IDLE/WALK叶或同Phase混合，其他原版移动族归R28'
        if 26 in source_nodes:
            row['实施/下一步'] += '；受击拥有者原生30/31/32，61/62/63源片段；非移动Step'
        if 41 in source_nodes:
            row['实施/下一步'] += '；WalkOnSlash原生7，115→101'
        if 43 in source_nodes:
            row['实施/下一步'] += '；明确弹刀接触触发原生34/221，恢复Light/Thrust接StepSlash'
        if source_nodes & set(range(66, 76)):
            row['实施/下一步'] += '；V/D-pad Left实际投射器连射；native mTrigger第36源帧发射后合法续段'
        if ref['target_node'] in (1, 11):
            row['实施/下一步'] += '；显式前请求→通用Phase采样→后覆盖及自定义主段提交已迁移'
        row['下一阶段通过准则'] = (
            f"开发已结束；如另行安排验证，按真实来源/Phase{ref['phase']}核对入口实际请求顺序，"
            f"连接{ref['connector_motion']}及主段{ref['project_main_motion']}@{row['主段startFrame']}；"
            '分清通用连接表与专用入口覆盖；费用一次，过去事件不补播，源秒/帧及段倍率分开；'
            '旧令牌/中断/死亡不提交；首帧捕获、重入、根运动、线性插值和独立步长；不得自动启用尾淡出'
        )
    write_csv(path, fields, rows)
    intro = '''# R06连接动画逐条开发台账

更新：2026-10-25，B10。**R06剩余三项开发全部完成；未编译、未测试。** 来源玩法拥有者、SpiritI/StepSlash专用入口、MotionTree/request门控与独立混合时钟均已接入正式角色代码；按用户要求，本次不执行验证。

关联：[B10现状](../Reference/MHWI-R06-Remaining-Development.md)、[B10记录](../Changes/CHG-20261025-005-mhwi-r06-remaining.md)、[CSV](MHWI-Connector-Progress.csv)、[后续验收要求](MHWI-Connector-Acceptance.md)。B04至B09历史保留，不改写为此次通过。

30节点/32引用/124有序身份记录/26连接片段；13主段绑定保护沿用。新增32段来源/专用片段、16个真实来源绑定及四向持刀翻滚和WalkOnSlash。node86保持无入边/0记录。逐行状态是开发交付状态，运行结果尚未取得。R07精确输入位、R24完整受击族、R25完整弹药系统、R28完整移动不随R06关闭。

通用表行保留原始主段与startFrame；SpiritI/StepSlash的有序显式请求可以覆盖该行，须结合专用入口理解，不能把表中路径当成每次必经的动画。

## 每条开发结果与后续验收依据

'''
    lines = [intro, '| '+' | '.join(fields)+' |', '| '+' | '.join('---' for _ in fields)+' |']
    lines += ['| '+' | '.join(str(row[f]).replace('|', '\\|') for f in fields)+' |' for row in rows]
    (ROOT/'Docs/Plans/MHWI-Connector-Progress.md').write_text('\n'.join(lines)+'\n', encoding='utf8')
    progress = ROOT/'Docs/Plans/MHWI-Restoration-Progress.csv'
    progress_fields, items = read_csv(progress)
    for item in items:
        if item['项目'].startswith('R06 '):
            item['状态'] = 'B10开发完成；未编译/测试'
            item['证据和落点'] = '真实Step/Creep/Shot拥有者；专用入口全分支；原生混合门控/曲线/独立时钟；32新增资产'
            item['本批及后续'] = '剩余三项开发已完成；依用户要求不测试；node86无入边保持；验证结果尚未取得'
        if item['项目'].startswith('R24 '):
            item['状态'] = '部分开发；未验证'
            item['本批及后续'] = 'B10完成R06需要的规范站立小中大受击拥有者；完整环境/行走/坐姿/镜像反应、恢复及死亡仍开放'
    write_csv(progress, progress_fields, items)
    adapter_path = ROOT/'Tools/MHW/r06-runtime-adapter.json'
    adapter = json.loads(adapter_path.read_text(encoding='utf8'))
    adapter.update(status='development_complete_uncompiled_untested', latest_batch='B10-20261025',
                   r06_complete=True, completion_meaning='Development complete; runtime validation not executed.',
                   latest_reference=REFERENCE, latest_change=CHANGE, tests_executed=False,
                   source_bindings=sources['bindings'], additional_assets=imports['imports'],
                   source_evidence='Tools/MHW/native-r06-remaining-evidence.json')
    adapter_path.write_text(json.dumps(adapter, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps(dict(records_authored=True, r06_development_complete=True,
                          references=len(rows), tests_executed=False)))


if __name__ == '__main__':
    run()
