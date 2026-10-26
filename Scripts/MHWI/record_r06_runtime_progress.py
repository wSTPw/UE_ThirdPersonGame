"""Author B08 handoff records; does not execute checks or tests."""
import csv
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]


def run():
    policy = json.loads((ROOT/'Tools/MHW/native-link-motion-policy.json').read_text(encoding='utf8'))
    runtime = json.loads((ROOT/'Saved/MHWIRestoration/B08-20261025/runtime-source-data.json').read_text(encoding='utf8'))
    references = {f"R06-N{r['node']:02d}-P{r['phase']}": r for r in policy['references']}
    nodes = set(runtime['project_move_nodes'].values())
    relative = 'Docs/Plans/MHWI-Connector-Progress.csv'
    path = ROOT/relative
    backup = ROOT/'Saved/MHWIRestoration/B08-20261025/Backup'/relative
    if not backup.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
    with path.open(encoding='utf8', newline='') as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    for row in rows:
        ref = references[row['ID']]
        source_nodes = sorted({e['source_node'] for e in ref['incoming']})
        missing = [n for n in source_nodes if n not in nodes]
        node = ref['node']
        main = ref['project_main_motion']
        row['项目目标片段'] = str(main)
        row['MBD目标片段'] = str(main)
        if ref['mbd_main_candidates']:
            block = ref['mbd_main_candidates'][0]
            row['主段startFrame'] = str(block['start_frame'])
            row['字段字节偏移'] = str(block['fields_offset'] + 4)
        if node == 86:
            row['状态'] = '原图无入边；未制造可达入口；未测试'
            row['实施/下一步'] = '保持0匹配记录；共享365片段保留；不补造派生'
            continue
        if missing and len(missing) == len(source_nodes):
            row['状态'] = '原生表/片段/播放管线就绪；前置玩法未接入；未编译/测试'
        elif missing:
            row['状态'] = '角色播放管线已接入；部分前置玩法缺失；未编译/测试'
        else:
            row['状态'] = '角色选择/退出/入帧已接入源码；未编译/测试'
        row['实施/下一步'] = f"{ref['runtime_record_count']}条原生身份记录；源帧Phase采样、结束单次提交、MBD入帧及主招事件隔离已接入"
        if missing:
            row['实施/下一步'] += '；待接真实前置node'+','.join(map(str, missing))+'，不借用其他招式身份'
        row['下一阶段通过准则'] = (
            f"前置原生身份及Phase{ref['phase']}精确匹配；按实际源步进生成结束flags，低帧/自然尾帧均仅提交一次；"
            f"主段{main}从原MBD第{row['主段startFrame']}源帧进入；连接期间不触发主招命中/防御/取消；"
            '费用与动作事件不重复；过去事件不补播；中断/旧回调不提交；根运动、武器时钟及混合结果符合原始来源'
        )
        if missing:
            row['下一阶段通过准则'] += '；先接入缺失前置玩法，再验收真实输入路径，不能仅靠控制核心或片段存在判通过'
        if node == 40:
            row['实施/下一步'] += '；Action71原生入口已证明112；112物理共享105骨轨而使用独立TIML；正式DA已切新112 Montage'
            row['下一阶段通过准则'] += '；必须是118→112@14，不能只看姿态相同就继续引用105；112输入TIML不能被105吞掉'
        if node == 31:
            row['实施/下一步'] += '；cUpper自定义入口固定119，结束后107；没有通用入口的P1后备'
            row['下一阶段通过准则'] += '；覆盖自定义cUpper入口，119只播放一次'
        if node == 52:
            row['实施/下一步'] += '；正式RollStepSlash已迁到完整101主段，旧129前缀不再参与正式定义'
            row['下一阶段通过准则'] += '；129最多一次，主段101@48；无匹配直入主段时不复播历史复合前缀'
        if node == 44:
            row['实施/下一步'] += '；前置是Action34/cActCreepSingleMotion，不是项目Draw(002)'
        if node == 53:
            row['实施/下一步'] += '；前置是原生group1 Step系列，不是项目纳刀Roll'
        if node == 60:
            row['实施/下一步'] += '；1003是StepS/M/L及WpOnStep身份集合；纠正旧“攀爬”解释；152第2源帧武器事件已接'
            row['下一阶段通过准则'] += '；按真实Step系列片段/帧采Phase，分别152/P0和132/P1；152武器事件只在第2源帧触发'
        if node == 76:
            row['实施/下一步'] += '；308/309/310缺Phase轨归0，311独立TIML为1，骨轨共享不吞掉时间线'
            row['下一阶段通过准则'] += '；308/309/310→357→170@50；311→367→170@66；重入不继承旧Phase'
        if node in (80, 81):
            row['下一阶段通过准则'] += '；361为右127@22，362为左128@24'
        if node in (84, 85, 87, 88, 89):
            row['实施/下一步'] += '；前置为原生KijinComboShot/Slinger系列，不是居合方向变体'
    with path.open('w', encoding='utf8', newline='') as stream:
        writer = csv.DictWriter(stream, fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    intro = '''# R06连接动画逐条开发台账

更新：2026-10-25，B08。**角色消费路径已接入源码，26连接及原生主段112已制作；正式DA两项迁移已保存。未编译/测试。部分原生前置玩法尚未实现，原生混合权重尚有缺口，不能把32行全部记为原作还原通过。**

关联：[B08角色接入](../Reference/MHWI-R06-Character-Playback.md)、[本批记录](../Changes/CHG-20261025-003-mhwi-r06-character-playback.md)、[CSV](MHWI-Connector-Progress.csv)、[下一阶段准则](MHWI-Connector-Acceptance.md)。

30节点32引用，展开124条记录；node86无入边。通用选择首次匹配原生身份/Phase，不回退P0；上挑另沿已确认自定义入口119→107。连接结束不是固定秒数：使用前向原生步进的flags1/4；主段按原MBD提交。MBD专用行未命中使用序列化第0行；正式主段绑定仍要求明确连接匹配。原表其他字段保留，不把未知overlap语义猜成UE停播时长。

**本批纠正**：Action71的原生主段为112，118→112@14；正式插入突刺已换独立112资源。node43是CreepSingleMotion，不能贴项目Draw；1002/1003是Step系列身份，旧“攀爬”标签错误；后段365/366的前置是KijinComboShot/Slinger系列，不是居合方向变体。

下表“已接入源码”不是运行通过；缺失前置玩法的行保留真实缺口。完整来源及历史状态见B04至B08变更记录。

## 每条实现状态与下一阶段通过准则（本阶段均未执行）

'''
    lines = [intro, '| ' + ' | '.join(fields) + ' |', '| ' + ' | '.join('---' for _ in fields) + ' |']
    lines += ['| ' + ' | '.join(str(row[f]).replace('|', '\\|') for f in fields) + ' |' for row in rows]
    (ROOT/'Docs/Plans/MHWI-Connector-Progress.md').write_text('\n'.join(lines)+'\n', encoding='utf8')


if __name__ == '__main__':
    run()
