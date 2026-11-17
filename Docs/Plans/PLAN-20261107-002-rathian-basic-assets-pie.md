# PLAN-20261107-002：雌火龙Basic资产配置与PIE

- 状态：completed（基础工程profile，用户接受工程火球演出）
- 日期：2026-11-07
- 用户需求：更新交接后启动UE，完成动画、碰撞盒及PIE剩余工作。
- 关联模块/接口/问题：mhwi-rathian-approx、MHWI-016、R-ANIM-012、R-AI-004；续接PLAN-001。
- 实施记录：142骨/848动画只读采样；25个Basic资产配置完成，20副本14活动；速度/地面间隙修复各经冻结Luna、独立审查及主项目编译。最终二进制24项PIE、101断言PASS，875保护文件hash不变；完整结果见[CHG-002](../Changes/CHG-20261107-002-rathian-basic-assets-pie.md)和[当前交接](MHWI-Rathian-Handoff.md)。

## 现状与目标

阶段起点是13份源码已合入并通过编译，但资产/运行未验证。现已完成独立Basic资源及关卡，真实PIE覆盖巡逻、发现/移动、4招与起落、玩家受击和死亡。健康Walk改用00_007；火球00_081保留工程演出，用户明确选择后续再替换原作片段。

## 范围与验收标准

沿用既有Native图、阶段数据和Decision/Policy；准确读取em001资产，选择/复制必要片段，配置Moveset/Stats及测试关卡。必须实际PIE观察全循环、4类攻击、盒窗/遮挡/去重、火球、受击防御拦截、丢失目标、空中中断/死亡。原作精确THK和COL几何不在本批宣称范围；未知动画不能凭编号填。

## 技术方案

单一UE写入者维护编辑器世界和新Basic资产；子代理可并行只读盘点/审查，避免同时修改同一世界。先核Skeleton/坐标与根轨，后在副本上按阶段处理；Native底层图与DefaultSlot不改为第二套动画权威。参数依实际姿态校准并标工程值；出现源码缺陷另建冻结Luna修复，不重写已接受旧run。

官方UE5.8：[Animation Sequence Editor](https://dev.epicgames.com/documentation/unreal-engine/animation-sequence-editor-in-unreal-engine?lang=en-US)、[Root Motion](https://dev.epicgames.com/documentation/unreal-engine/root-motion-in-unreal-engine?lang=en-US)、[AnimationBlueprintLibrary](https://dev.epicgames.com/documentation/unreal-engine/API/Editor/AnimationBlueprintLibrary/UAnimationBlueprintLibrary)支持预览、骨姿采样和动画数据处理；具体API以本机5.8引擎源码/运行反射为准。它们不证明原作招式语义；已导入根的层级需实测，不能假定ForceRootLock会锁住子bone_root。

## 接口与数据迁移

| 接口/路径 | 当前 | 目标 | 影响/顺序 |
| --- | --- | --- | --- |
| MHWI-016 | Basic实际数据/蓝图已读回并PIE | 4招使用统一执行链 | 修改数据后新spawn；Configure不当重载用 |
| `/Game/MHWI/Rathian/Basic/` | 25个新增包均已配置、保存 | 专用配置/副本/关卡 | 不覆盖848原片和用户脏训练关卡/太刀DA |

## 实施步骤与依赖

1. 更新交接/源码成功构建记录和最新UE授权；启动与握手，读dirty packages。
2. 骨架与动画只读盘点、可视预览及运动轨迹校验，确定各招片段。
3. 创建独立资源/场景，完整读回引用和参数；只保存本批包。
4. 逐招校准盒/窗/火球/根轨，再PIE全循环与反例。
5. 记录实际结果/未完成项并同步交接及系统页。

## 验证计划

| 场景 | 方法 | 期望 | 边界 |
| --- | --- | --- | --- |
| 资产资格 | UE反射/资产读回+预览 | 路径/类/Skeleton/片段/骨名一致 | 元数据不代替视觉确认 |
| 动画与位移 | 多时刻/多视角预览及真实PIE | 连续、无双根位移、脚底/起落合理 | 不宣称原作逐帧一致 |
| 判定/火球 | 调试盒、目标HP、墙体与低帧样本 | 窗内一次、遮挡、可躲避、单发 | 工程盒，非原作COL复刻 |
| 循环/死亡 | PIE日志/状态与受控伤害 | 巡逻/发现/选招/恢复；一次死亡，空中接地不复活 | 单机本地玩法 |

## 风险与回退

资源语义可能需多次预览；先测后配，不用猜的动作填清单。新增包独立命名，保存前核dirty集合；原片与用户已有修改保留。源码有已接受版本和逐文件备份；仅回退本批且先核hash。无需系统修复或自动重启。

## 文档同步清单

MHWI-Rathian-Handoff、MHWI-Current、Systems/MHWI-Rathian、Known-Issues、modules.json及CHG/索引。实际结果见CHG-20261107-002及Tools/MHW稳定清单。24用例不覆盖全部闪避/反击/霸体回归、复杂地形/多人、长时间游玩及原作逐帧对照；不把这些列为本轮已通过。
