# MHWI项目当前攻击判定（2026-10-30）

- 状态：当前源码静态核对；未运行游戏测试，未修改攻击检测。
- 依据：`Source/IntroCpp/MHWI/MHWICharacter.cpp` 的AdvanceAction、SweepWindow、ScheduleHelmShell、EmitDelayedShell；`MHWIMovesetData.h` 的FMHWIHitWindow、FMHWIResolvedHit。
- 原作对照：[B19碰撞取证](MHWI-Weapon-Collision-Evidence-20261026.md)。

## 怎样确定“打到了”

1. 每招数据里保存DamageWindows，即什么时候可伤害、伤害值和检测范围。角色读取实际Montage位置，检查上一位置到当前动画位置是否经过窗口；连接片段阶段不执行主段伤害。
2. SweepWindow在角色位置向上35cm处查询三个球体扫掠：从上一角色位置扫到当前朝向的前方Reach；另两条从前方0.3倍Reach起扫，终点分别向左右偏移SideExtent。半径与前伸距离取该伤害窗口数据，并有上限/下限。
3. 查询Pawn和WorldDynamic对象，排除自己，再要求目标有存活的AttributeComponent。WeaponMesh与ScabbardMesh自身均为NoCollision；检测没有读取可见刀刃的骨骼或Socket端点。
4. 按伤害窗口编号去重：同一窗口、同一目标只结算一次；不同窗口可再击中。因此多段招式来自多个窗口或专用延迟结算，不会因为一个窗口持续多帧就无限扣血。
5. 碰到显式DeflectsMHWIWeapon目标可进入弹刀响应；成功扣血后才确认命中、回槽、触发事件及相关派生。窗口回槽另有“该窗口只给一次”的去重。

UE 5.8 [UWorld碰撞查询API](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UWorld)和[球形扫掠API](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UKismetSystemLibrary/SphereTraceMultiForObjects?lang=en-US)说明扫掠会沿起终点测试指定形状/对象类型；项目实际直接调用UWorld::SweepMultiByObjectType。官方说明支持UE检测机制，不证明这是MHWI原作形状。

## 怎样计算伤害

普通直接命中按窗口基础值（或起招颜色对应值），乘起招捕获的颜色/基础伤害倍率、弱气刃倍率及合格反击倍率，调用目标AttributeComponent::ApplyDamage。伤害记录显式把尚未接入的斩味、会心和部位阶段标为Unavailable。完整武器面板、肉质/部位选择等原作伤害链没有据此实现。

登龙首次合格接触会锁定目标和相对接触点，排入延迟多段队列；居合追加也走专门延迟队列。后续EmitDelayedShell向已记录目标扣血，并不重新沿刀刃查询碰撞。

## 实际限制

目前可称“动画时间窗控制的角色前方范围判定”。球形扫掠覆盖范围与可见刀刃不完全一致，可能存在看似未贴刀却命中，或视觉贴刀但范围未覆盖的情况。时间跨帧检查能补经过的窗口，但不是对子帧刀刃轨迹做连续重建。查询未包含WorldStatic，也没有额外墙体视线检查，不能宣称实现墙体遮挡或原作部位命中。

原始COL攻击记录/动作时间轨已有证据，但精确碰撞形状、骨骼空间及部位肉质选择未闭合；此页不把现有范围近似称作原作刀刃碰撞。本轮只解释现状，不选定或实施碰撞重构。
