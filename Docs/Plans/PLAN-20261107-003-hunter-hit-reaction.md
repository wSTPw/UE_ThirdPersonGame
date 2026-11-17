# PLAN-20261107-003：玩家受击姿态缺失修复

- 状态：completed（Impact时序修正及最终骨姿/实际位移验收）
- 日期：2026-11-07
- 用户报告：雌火龙命中玩家仅扣血，无明显位移/受击动作。
- 范围：现有三档动画及统一Native执行链；原作取证和Sandbox仍暂停。

## 官方、现状和推断

适用UE5.8：[UAnimInstance](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UAnimInstance)、[Slot](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/AnimGraphRuntime/FAnimNode_Slot)、[Montage](https://dev.epicgames.com/documentation/unreal-engine/animation-montage-in-unreal-engine)支持按实际播放位置/结束委托驱动生命周期、Slot输出与混合。具体代理扩展核本机5.8 AnimInstanceProxy源码；这些机制不证明MHWI原作条件和时间。

实际证据：最后用户游玩日志是Basic地图及BP_MHWI_Hunter，35/20/40全额伤害。6份受击源片有225骨有效轨迹，实际ABP有DefaultSlot。60FPS静止和出刀途中均可触发击飞和骨姿；3FPS无输入对照中，受击后0.333s已经Free/无Montage，短于实际co72长度0.533s，角色在空中显示站姿。证据在 Saved/RathianHitReaction-20261107/，不覆盖旧24报告。

源码对应：TickNativeSource消费ForwardEndFlags(Current.Frame, Advance)的预测结束位，相当于在已更新的当前帧再预测一次，长帧提前结束；NativeBlend首个目的姿态保持旧姿，短受击可能整段无可见姿态。ImpactCancelStart默认0也可能让连续攻击立即取消，已对照连续输入，未重现大受击立即取消，因此不改输入规则；不把候选当根因。

## 实施与边界

沿用既有Native代理/Slot和三档源片。冻结Luna修复只修改MHWIAnimInstance.h/.cpp和MHWICharacterNativeSources.cpp：给原生混合增加默认保留旧行为的首帧门选项，Impact专用消费实际owner delta；Impact完成以已经到达的当前源帧/实际Montage结束为准，其余类型预测语义、来源身份、死亡/中断/输入规则不变。无新增反射、资产或新动画系统。

若连续输入对照另证实恢复门配置问题，限Basic配置修正；不得随意重写原太刀数据。原先24项只证明编号/状态/速度，不能当最终显示骨姿完整验收。

## 验收

代码阶段：冻结UE5.8 Editor Target构建、全新Luna独立审查、主审及核hash合入；检查编译不包含PIE结论。随后关闭编辑器完整构建主项目并重启。

运行阶段：真实Basic PIE中小/中/大受击，两种持刀状态；至少复测3FPS短Large，比较命中前后最终骨姿、源片相对骨旋转和实际Actor位移，不能只验动作编号或速度峰值。包含出招中被击中、连续攻击输入、死亡/霸体边界；若发现其他问题据实修复。截图隔离怪物仅为观察玩家姿态，必须标注。

## 保护和回退

保留全部原动画、用户已有脏训练图/太刀DA、其他源码修改。不自动重启/关机。只保存本批Basic包；源码核hash逆序恢复备份，其他候选丢弃。更新系统/接口/已知问题及新CHG-003，旧CHG-002保留当时有限验证含义。

## 实际结果

冻结Luna执行→169.209s编译PASS→全新Luna独立审查/主审ACCEPTED→核hash合入3源码→主项目97.74s构建PASS→重启UE。固定3FPS旧二进制最终骨姿FAIL，新二进制PASS；12种受击场景、2次加强位移范围重测、死亡/实际居合反击霸体2种消费者检查，共16次成功运行121断言。12份v1原始数据按命中后基点另算位移均通过，姿态阈值未变。900资产hash不变，未改其他源码。

最终结果、失败夹具、复现脚本、限定和回退见[CHG-003](../Changes/CHG-20261107-003-hunter-hit-reaction.md)及[稳定清单](../../Tools/MHW/hunter-hit-reaction-repair-20261107.json)。UE保持Basic、PIE结束/无脏包；临时设置和回调已清理。原作完整击飞/倒地/起身状态机仍非本批范围。