# CHG-20261019-005：角色动作调度与事务提交实施

- 状态：partial；动作核心与样本迁移完成，MM按用户要求待资源后继续，视觉调参与扩展策略未全量验收。
- 日期：2026-10-19。
- 需求：用户授权实施动作管理重构，并允许模块分工；本轮补充要求列出Root Motion动画，资源处理完后再继续MM。
- 关联：[PLAN-20261019-003](../Plans/PLAN-20261019-003-character-action-refactor.md)，`ACTION-001..004`、`ATTR-006`、`EVT-ACTION-01/02`、`R-COMBAT-001..005`、`R-INV-004`、`R-MM-001`。
- Git：工作区变更，未提交；保留此前UE升级、插件、技能、UI和其他用户未提交修改。

## 原因与结果

原玩家通过全局布尔、匿名Timer和无身份Notify分散管理攻击/喝药，背包与快捷栏使用入口还可能产生不同效果与扣数。现在Attack、UseHeldItem和玩家库存使用都向同一组件请求；每次执行持有RunId、段代次、动画实例及事件索引。只有当前执行的合法事件可提交，终止统一释放，旧通知和旧段结束不能污染新动作。

长剑保留4段6命中和单目标球扫，迁入真正的单条缓冲与动画位置窗口。窗口内按键立即登记，修复了后台333ms帧间隔超过150msTTL而丢输入的问题。火球使用Deferred Spawn初始化真实伤害/Owner/Instigator并只扣一次蓝；用药预约原容器和版本，只消费原来源，HP/MP变化在数量就绪后广播。

## 修改清单

| 文件 / 资产 | 符号或属性 | 结果 |
| --- | --- | --- |
| `Source/IntroCpp/Actions/CharacterActionComponent.*`、`CharacterActionTypes.h` | 请求、Snapshot、RunId、窗口、去重、冷却、Finish | 权限统一，结束幂等，死亡/EndPlay与重入清理 |
| 同目录 `CharacterActionExecution.h`、`CharacterActionEffects.cpp` | Melee/Cast/UseItem执行器 | 运行对象强引用；效果提交需当前派发身份 |
| 同目录 `CharacterActionDefinition.h`、`AnimNotifyState_ActionWindow.h`、`LocomotionAnimContext.h` | 数据定义、Chain/Cancel、移动输入快照 | 数据化时序和未来MM接口；不代表MM已启用 |
| `MyPlayerCharacter.*`、`MyAnimInstance.*`、三个 `AnimNotify_*.cpp` | 请求转发、装备许可、镜像、NativeUpdateAnimation、EventReference | 删除旧玩家连击状态/Timer/pending逻辑；旧无身份入口保留警告拒绝 |
| `InventoryComponent.*`、`UW_InventoryUI.cpp`、`AttributeComponent.*` | 原来源提交、结构化结果、HP/MP事件批次、TrySpendMana | 全局库存写锁，关闭UI后核对来源；失败不扣/部分成功只扣一次 |
| `WeaponData.h`、`ConsumableData.h` | ActionDefinition | 保留旧配置适配，新增定义引用 |
| `/Game/Data/Actions/DA_Action_LongSword`、`DA_Action_Fireball`、`DA_Action_UseConsumable` | 父类 `/Script/IntroCpp.CharacterActionDefinition` | 新建并保存，分别引用原长剑/火球/喝药Montage，默认不移动/跳跃 |
| `/Game/Data/Items/Weapons/DA_WP_LongSword`、`DA_WP_FireStaff` | ActionDefinition | 保存为对应新定义 |
| `/Game/Data/Items/DA_HP_Potion`、`DA_MP_Potion` | ActionDefinition | 保存为共享UseConsumable定义 |
| `/Game/MyStuff/Model/Robot/M_LongSwordAttack` | `AnimNotifyState_ActionWindow` | 每段新增Chain相对0.3–0.8秒、Cancel相对0.9–1.15秒，共8个；原4段6命中未删除 |
| `Source/IntroCpp/Tests/`、`Scripts/Tests/action_refactor_pie.py` | 10项原生测试、真实PIE回归 | 覆盖状态/身份/事务/低帧与实际动画事件 |
| `Scripts/Animation/prepare_motion_matching_audit.py`、[MM审计](../Plans/MM-P5-Audit-20261019.md)、[资源清单](../Plans/MM-RootMotion-Resource-Checklist.md) | 本地候选、只读请求、根轨迹证据 | 确认当前移动动画缺Root平移；按用户要求未创建MM资产或替换ABP |

## 接口、事件与资源影响

`FCharacterActionRequestResult` 的Started/Buffered仅表示请求接受，不承诺效果已提交。原库存bool保留为接受语义，内部`FActionItemCommitResult`分开Applied/ConsumedQuantity/Partial。角色/ABP兼容字段为派生镜像；无参数FireFromHand/MeleeHitCheck等不再具有效果权限。

每个连击段使用新Montage播放实例，牺牲同实例跳段的优化换取可靠身份隔离。启动检查必需事件；转段/结束要求全部收齐。样本长剑已由NotifyState提供窗口，未迁移资产仍通过旧HitWindow字段按动画位置适配。自愿取消校验RunId和Cancel窗口，Interrupt是强制路径。

背包采用**全局公共写接口锁**，并非原计划的槽级并发预约；攻击中拾取也被拒绝。Inventory与QuickSlots仍是两份独立存储。自定义Legacy Action的false可能掩盖副作用，不能通用回滚；Partial只按报告结果记录。HP/MP Changed批次不延迟任意自定义死亡/受击或外部事件。

未引入GAS、网络预测、独立MP预约令牌、GameplayTags分类或FacingPolicy。普通受击尚未统一接成硬直，死亡已接入；现有硬直扩展可调用Interrupt。未改第三方UE-MCP源码；网关命名与Schema默认骨骼陷阱仅记录在审计文档。

## 实际验证

环境：Windows、UE5.8.3、VS2022 14.44、Windows SDK10.0.22621.0。

| 检查 / 命令 | 实际结果 | 证据 |
| --- | --- | --- |
| `Build.bat IntroCppEditor Win64 Development -Project=<project> -WaitMutex -NoHotReloadFromIDE` | build-06完整UHT/UBT成功；此前build-04/05也成功 | `Saved/ActionRefactor-20261019/build-06.log` |
| `editor.run_automation_tests(filter="IntroCpp.Actions", maxTests=20, latentTimeoutSeconds=60)` | 最终10/10通过，0错误/警告/abandoned | `Saved/ActionRefactor-20261019/verification-summary.json`、本轮编辑器日志 |
| 较早独立UnrealEditor-Cmd自动化 | 当时8/8通过；属于本轮中间版本，不代替最终10项 | `Tests02/index.json`、`automation-02.log`（同Saved目录） |
| 蓝图编译BP_MyPlayer、ABP_Move、UW_InventoryUI | 各0错误/0警告；未改图连线 | MCP结果与本轮编辑器日志 |
| 执行`action_refactor_pie.py`，MyLevel真实玩家/资产 | 最终41/41断言通过；四段到达、六次命中通知、自然结束；施法前中断不耗蓝，同Montage重启后生成火球/一次耗蓝/实际伤害覆盖/MP不足拒绝；喝药只扣快捷栏最后一件，背包同ID数量保持；使用中换槽/攻击拒绝；背包使用同链、提交前中断不扣；取消窗口/旧RunId与死亡清理通过 | `Saved/ActionRefactor-20261019/PIE.json`、`editor-validation.log` |
| MM真实只读检查 | 同骨架，Root/LeftFoot/RightFoot确认；走跑Root逐帧平移0，Hips不可代替，Turn180R有根旋转；未开启正式MM | `Saved/ActionRefactor-20261019/MM-*.json`及审计页 |
| 文档检查 / diff | 收尾时执行，结果写验证汇总 | `Scripts/Docs/check_docs.py`、`git diff --check` |

中间失败已保留：受限沙箱执行Build.bat未进入构建，提权后可构建；首编译含不存在的GetSectionStartTime和编译期间头文件变动导致生成行失配，均已修复。PIE脚本中非反射属性/原生非UFUNCTION方法的Python访问名修正后重跑；初次低帧输入丢失促成本轮实现修复。中间失败不计作最终通过。

## 风险、遗留与回退

- MM等待用户准备Root Motion资源，当前正式ABP保留；不得把本轮动作测试写成MM质量/性能验证。
- 视觉混合、滑步、30/60/120FPS完整手感、全蓝图无身份调用审计、自定义投射物和任意Legacy Action仍未全量覆盖。未执行打包/多人测试。
- 独立背包AddItem部分添加、Drop失败仍扣、装备索引随排序迁移、Widget重复绑定等旧问题保留，见Known-Issues。
- 修改前源码副本位于`Saved/ActionRefactor-20261019/Before`；五个原资产备份位于`BeforeAssets`，哈希为`assets-before.json`。这不是完整版本控制备份；新增源码和记录应一并纳入项目版本管理。
- 回退先关编辑器，还原本记录对应源码与五个已修改原资产，清除新ActionDefinition引用后再移除三个新定义；完整重编译并重启PIE。不要还原本轮之前的UI/UE升级等用户工作。运行对象不存档，不存在存档格式迁移。

## 已同步文档

[架构](../Architecture.md)、[战斗](../Systems/Combat-AI.md)、[背包](../Systems/Inventory.md)、[UI/资产](../Systems/UI-Assets.md)、[接口](../Interfaces.md)、[模块索引](../Reference/modules.json)、[已知问题](../Known-Issues.md)、[开发验证](../Development.md)、[方案索引](../Plans/README.md)、[变更索引](README.md)。
