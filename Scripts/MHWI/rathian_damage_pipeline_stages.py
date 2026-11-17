# -*- coding: utf-8 -*-
"""MHWI 雌火龙（em001）伤害分段结算流水线原型（P3 工作包）。

==============================================================================
!! 工程原型，非原作公式验证；不得用于忠实度验收或宣称原作伤害。!!
==============================================================================

设计边界：
- 纯数据分段演算：每个阶段为独立纯函数，输入上下文 dict，返回
  {stage, value, status, source}；无随机、无全局可变状态，
  同输入两次运行输出逐字节一致。
- 仅 "已证（evidenced）" 阶段参与乘法；status="unavailable" 的阶段
  一律跳过、不填任何默认值（不填 1.0/0 冒充通过），并在结果中列明。
- 任务倍率、最终伤害公式（乘法顺序/取整）、斩味/会心/技能修正均未闭合。
- 数据来源：Docs/Reference/MHWI-Rathian-LR-Data-20261030.md（下称 LR 数据页），
  仅硬编码该页第三节已证数值，不引入该页之外的"原作数值"。

上游要求：
- Docs/Plans/PLAN-20261102-001-rathian-completeness-parallel.md P3 工作包
- Docs/Plans/PLAN-20261031-006-rathian-combat-integration.md C3.1

CLI：
  python Scripts/MHWI/rathian_damage_pipeline_stages.py --self-check
  python Scripts/MHWI/rathian_damage_pipeline_stages.py --self-check --out <path>
  python Scripts/MHWI/rathian_damage_pipeline_stages.py --self-check --json
"""

from __future__ import annotations

import argparse
import json
import sys

DISCLAIMER = "工程原型，非原作公式验证；不得用于忠实度验收或宣称原作伤害"

SOURCE_PAGE = "Docs/Reference/MHWI-Rathian-LR-Data-20261030.md"

# ---------------------------------------------------------------------------
# 已证数据（硬编码，逐项标注 LR 数据页来源章节）
# ---------------------------------------------------------------------------

# LR 数据页 §3.1 肉质表（12 个部位组，单位 %），列：斩 / 打 / 弹。
# 原表含 火/水/冰/雷/龙/气绝/夺取 列，本原型仅闭合 斩/打/弹 三类物理伤害；
# 属性列与气绝/夺取列未接入，不据此推断。
# 注意：组号→部位名映射本条未解，行号不等于"头/背/翼"等部位名。
HITZONE_TABLE = {
    # zone_index: (斩, 打, 弹)   # 来源：LR 数据页 §3.1 肉质表第 0..11 行
    0:  (70, 75, 65),   # §3.1 肉质表 行0
    1:  (40, 45, 35),   # §3.1 肉质表 行1
    2:  (35, 30, 25),   # §3.1 肉质表 行2
    3:  (35, 30, 25),   # §3.1 肉质表 行3
    4:  (55, 50, 45),   # §3.1 肉质表 行4
    5:  (40, 40, 35),   # §3.1 肉质表 行5
    6:  (45, 40, 35),   # §3.1 肉质表 行6
    7:  (60, 65, 45),   # §3.1 肉质表 行7（与行0同为气绝值100的部位组，但组名未解）
    8:  (37, 45, 30),   # §3.1 肉质表 行8
    9:  (21, 21, 45),   # §3.1 肉质表 行9（弹45高于斩打21，翼膜类特征，组名未解）
    10: (37, 37, 25),   # §3.1 肉质表 行10
    11: (45, 37, 30),   # §3.1 肉质表 行11
}

DAMAGE_TYPE_COLUMNS = {"斩": 0, "打": 1, "弹": 2}  # 对应 HITZONE_TABLE 元组下标

# LR 数据页 §3.2 发怒（em001.dtt_agr）：Damage_Modifier ×1.15。
# 两组 Rage_Stats 数值完全相同；同页 Speed_Modifier ×1.05、
# Player_Damage_Modifier ×1.10 属怪物行动/对玩家侧，本原型不消费。
RAGE_DAMAGE_MODIFIER = 1.15


# ---------------------------------------------------------------------------
# 阶段函数：每阶段独立纯函数，输入上下文 dict，返回 {stage, value, status, source}
# ---------------------------------------------------------------------------

def s1_action_motion_value(ctx):
    """s1 动作值：外部输入参数，无原作默认值。

    来源：无——原作各招式 MV 未在本项目闭合
    （LR 数据页 §四：ACTP2 攻击字段"不是最终对玩家扣血"），
    故 MV 只能由调用方显式提供，本函数不提供任何默认值。
    """
    if "motion_value" not in ctx or ctx["motion_value"] is None:
        return {
            "stage": "s1_action_motion_value",
            "value": None,
            "status": "unavailable",
            "source": "外部输入缺失；原作招式 MV 未闭合（LR 数据页 §四）",
        }
    mv = ctx["motion_value"]
    if not isinstance(mv, (int, float)) or isinstance(mv, bool) or mv < 0:
        return {
            "stage": "s1_action_motion_value",
            "value": None,
            "status": "unavailable",
            "source": "外部输入非法（须为非负数值）；本阶段不提供默认值",
        }
    return {
        "stage": "s1_action_motion_value",
        "value": float(mv),
        "status": "evidenced",
        "source": "外部输入参数（调用方提供，非原作默认值）",
    }


def s2_sharpness_affinity(ctx):
    """s2 斩味/会心修正：unavailable，跳过，不参与运算。

    来源：LR 数据页未含斩味及会心修正数据；斩味/会心/技能修正
    在任务书中明确"均未闭合"。不填 1.0 冒充通过。
    """
    return {
        "stage": "s2_sharpness_affinity",
        "value": None,
        "status": "unavailable",
        "source": "斩味/会心修正未闭合（LR 数据页无此数据；任务书 C3.1 明示未闭合）",
    }


def s3_skill_armor_modifier(ctx):
    """s3 技能/防具修正：unavailable，跳过，不参与运算。

    来源：LR 数据页仅含怪物侧数值，玩家技能与防具修正未闭合。
    不填 1.0 冒充通过。
    """
    return {
        "stage": "s3_skill_armor_modifier",
        "value": None,
        "status": "unavailable",
        "source": "技能/防具修正未闭合（LR 数据页无此数据）",
    }


def s4_hitzone_multiplier(ctx):
    """s4 部位肉质倍率：已证，按 zone_index + damage_type(斩/打/弹) 查表。

    来源：LR 数据页 §3.1 肉质表（em001.dtt_epg，12 个部位组，单位 %）。
    肉质为百分比值，参与运算时除以 100；组号→部位名映射未解，
    仅以 zone_index 查表，不命名部位。
    """
    zone_index = ctx.get("zone_index")
    damage_type = ctx.get("damage_type")
    if zone_index not in HITZONE_TABLE:
        return {
            "stage": "s4_hitzone_multiplier",
            "value": None,
            "status": "unavailable",
            "source": "zone_index 越界（须为 0..11，LR 数据页 §3.1 仅 12 组）",
        }
    if damage_type not in DAMAGE_TYPE_COLUMNS:
        return {
            "stage": "s4_hitzone_multiplier",
            "value": None,
            "status": "unavailable",
            "source": "damage_type 须为 斩/打/弹（本原型仅闭合物理三类；LR 数据页 §3.1）",
        }
    percent = HITZONE_TABLE[zone_index][DAMAGE_TYPE_COLUMNS[damage_type]]
    return {
        "stage": "s4_hitzone_multiplier",
        "value": percent / 100.0,
        "status": "evidenced",
        "source": (
            "LR 数据页 §3.1 肉质表 行%d %s列=%d%%（em001.dtt_epg；组名未解）"
            % (zone_index, damage_type, percent)
        ),
    }


def s5_rage_modifier(ctx):
    """s5 发怒伤害修正：已证 ×1.15，仅当上下文 rage=True 时生效。

    来源：LR 数据页 §3.2 发怒（em001.dtt_agr）Damage_Modifier ×1.15。
    rage=False 时本阶段不参与运算（无发怒修正可乘），
    但属"已证且不适用"，不计入 missing_stages。
    """
    if ctx.get("rage"):
        return {
            "stage": "s5_rage_modifier",
            "value": RAGE_DAMAGE_MODIFIER,
            "status": "evidenced",
            "source": "LR 数据页 §3.2 发怒 Damage_Modifier ×1.15（em001.dtt_agr）",
        }
    return {
        "stage": "s5_rage_modifier",
        "value": None,
        "status": "not_applicable",
        "source": "上下文 rage=False，无发怒修正；数据本身已证（§3.2 ×1.15）",
    }


def s6_quest_multiplier(ctx):
    """s6 任务倍率：unavailable，跳过，不参与运算。

    来源：任务书 C3.1 明示任务倍率未闭合；LR 数据页亦无此数据。
    不填 1.0 冒充通过。
    """
    return {
        "stage": "s6_quest_multiplier",
        "value": None,
        "status": "unavailable",
        "source": "任务倍率未闭合（任务书 C3.1 明示；LR 数据页无此数据）",
    }


def s7_rounding_policy(ctx):
    """s7 取整策略：unavailable，跳过；输出标记"原作取整未闭合"。

    来源：任务书 C3.1 明示最终伤害公式（乘法顺序/取整）未闭合。
    本原型各已证阶段的乘法结果保留浮点精确值，不做任何取整，
    取整留待后续批次闭合。不填默认取整规则冒充通过。
    """
    return {
        "stage": "s7_rounding_policy",
        "value": None,
        "status": "unavailable",
        "source": "原作取整未闭合（任务书 C3.1：乘法顺序/取整未定）",
    }


# 阶段执行顺序（乘法结合律上不敏感，但输出轨迹固定，保证逐字节一致）
PIPELINE_STAGES = [
    s1_action_motion_value,
    s2_sharpness_affinity,
    s3_skill_armor_modifier,
    s4_hitzone_multiplier,
    s5_rage_modifier,
    s6_quest_multiplier,
    s7_rounding_policy,
]


# ---------------------------------------------------------------------------
# 流水线编排：仅 evidenced 阶段参与乘法；unavailable/not_applicable 跳过
# ---------------------------------------------------------------------------

def run_pipeline(ctx):
    """运行完整流水线，返回带逐阶段轨迹的结论 dict。

    纯函数：不修改 ctx、无随机、无时钟依赖。
    """
    traces = [stage_fn(ctx) for stage_fn in PIPELINE_STAGES]

    product = 1.0
    participated = []
    missing_stages = []
    for trace in traces:
        if trace["status"] == "evidenced" and trace["value"] is not None:
            product *= trace["value"]
            participated.append(trace["stage"])
        elif trace["status"] == "unavailable":
            missing_stages.append(trace["stage"])
        # not_applicable（如 rage=False 的 s5）：跳过且不计缺失

    # overall_status 规则：只要有任一 unavailable 阶段即为 partial-unavailable；
    # 若 s1（MV）本身缺失则连乘无意义，标记 blocked-no-input。
    if "s1_action_motion_value" in missing_stages:
        overall = "blocked-no-input"
    elif missing_stages:
        overall = "partial-unavailable"
    else:
        overall = "complete"  # 当前配置下不可能出现，仅作完备分支

    return {
        "disclaimer": DISCLAIMER,
        "input_context": {
            "motion_value": ctx.get("motion_value"),
            "zone_index": ctx.get("zone_index"),
            "damage_type": ctx.get("damage_type"),
            "rage": bool(ctx.get("rage")),
        },
        "stage_traces": traces,
        "participating_stages": participated,
        "missing_stages": missing_stages,
        "final_value_unrounded": product,
        "overall_status": overall,
        "notes": [
            "unavailable 阶段一律跳过、未参与乘法、未填默认值",
            "最终值未取整：原作取整未闭合（s7_rounding_policy）",
            "斩味/会心/技能/任务倍率修正均未参与（s2/s3/s6 unavailable）",
            "本值非原作对照期望，不得用于忠实度验收",
        ],
    }


# ---------------------------------------------------------------------------
# self-check 固定样例与 CLI
# ---------------------------------------------------------------------------

def self_check_samples():
    """固定样例（确定性，无随机）：MV=30、zone_index=0、斩击，rage 两态。"""
    return [
        {"case_id": "sample-a-no-rage", "motion_value": 30, "zone_index": 0,
         "damage_type": "斩", "rage": False},
        {"case_id": "sample-b-rage", "motion_value": 30, "zone_index": 0,
         "damage_type": "斩", "rage": True},
    ]


def build_self_check_report():
    """构造完整报告 dict（两次调用结果逐字节一致）。"""
    cases = []
    for sample in self_check_samples():
        result = run_pipeline(sample)
        result["case_id"] = sample["case_id"]
        cases.append(result)
    return {
        "disclaimer": DISCLAIMER,
        "source_page": SOURCE_PAGE,
        "tool": "Scripts/MHWI/rathian_damage_pipeline_stages.py",
        "self_check": True,
        "cases": cases,
    }


def dump_json(report):
    """确定性 JSON 序列化：固定键序、固定缩进、ensure_ascii，保证逐字节一致。"""
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="MHWI 雌火龙伤害分段结算流水线原型（工程原型，非原作公式验证）")
    parser.add_argument("--self-check", action="store_true",
                        help="运行固定样例自检并输出报告")
    parser.add_argument("--out", metavar="PATH",
                        help="将 self-check 报告写入指定文件（UTF-8）")
    parser.add_argument("--json", action="store_true",
                        help="将 self-check 报告输出到 stdout")
    args = parser.parse_args(argv)

    if not args.self_check:
        parser.print_help(sys.stderr)
        return 2

    report = build_self_check_report()
    text = dump_json(report)

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("已写出：%s" % args.out)
    if args.json or not args.out:
        sys.stdout.write(text)

    # 自检断言：两样例 overall 均为 partial-unavailable，缺失阶段固定，
    # unavailable 阶段未被填值。
    ok = True
    for case in report["cases"]:
        if case["overall_status"] != "partial-unavailable":
            ok = False
        if case["missing_stages"] != [
            "s2_sharpness_affinity",
            "s3_skill_armor_modifier",
            "s6_quest_multiplier",
            "s7_rounding_policy",
        ]:
            ok = False
        for trace in case["stage_traces"]:
            if trace["status"] == "unavailable" and trace["value"] is not None:
                ok = False
    print("self-check: %s" % ("PASS" if ok else "FAIL"), file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
