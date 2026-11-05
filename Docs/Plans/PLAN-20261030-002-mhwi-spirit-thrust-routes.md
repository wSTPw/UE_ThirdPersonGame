# PLAN-20261030-002：气刃连段突刺与见切续查

- 日期：2026-10-30
- 状态：in-progress
- 用户反馈：B23除03基本通过；游戏测试继续由用户操作。
- 范围：继续原作见切早期特殊纳刀/气刃突刺精确许可取证；气刃I/II/III新增气刃突刺路线；解释现有攻击判定。

## 官方机制、项目证据与目标

UE 5.8 [Montage](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-montage-in-unreal-engine)支持按玩法逻辑控制动画；[Animation Notifies](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-notifies-in-unreal-engine)说明同步分支机制。项目已使用FMHWIRoute、RequestInput、原生连接控制器，无需新架构。官方资料不能证明MHWI的精确窗口。

当前校准表SpiritI/II/III无HELM_BREAKER规则，制作源也未配置三条目标路线。方案是在既有Routes增加HELM_BREAKER→SpiritThrust，沿用各招现有SPIRIT连携窗口（59..110、44..118、110..160源帧/60秒）；这些沿用的是既有项目窗口，不宣称原作精确取消许可。不增加命中/颜色要求；登龙颜色与命中门保持现状。

见切另由专门取证组继续追属性→命令ID→执行/缓存生命周期。只有精确窗口证据闭合后才改正式路线，候选帧不作为依据。

## 数据迁移与验证

只复制三个定义并追加路线，备份正式DA，保证所有非Routes字段与其他招式序列化相同。同步author_assets、author_behavior_corrections和transition_calibration，防止重跑丢失路线；不修改C++/反射/动画资源。保存后读回并检查幂等性，不启动PIE或原作。

验收交用户：气刃I、II、III连携窗口内分别输入气刃突刺；无颜色仍可突刺、命中不登龙；白刃以上命中才登龙；原气刃后继路线保留。

攻击判定以实际AdvanceAction/SweepWindow/EmitDelayedShell代码说明，区分时间窗、空间扫掠、去重、命中结算和待还原部位/刀刃形状。

## 风险、文档与回退

保留B23已有修改及用户地图。只回退本轮三个Routes及制作源/校准新增规则；恢复DA时仅恢复本轮备份，不用B23旧备份覆盖用户已验收字段。更新现状页、问题、索引和新CHG。文档及脚本静态检查允许执行；游戏测试由用户进行。
