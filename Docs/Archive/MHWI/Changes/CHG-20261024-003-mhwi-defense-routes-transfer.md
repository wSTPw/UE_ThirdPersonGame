# CHG-20261024-003：防御、逐输入窗口与连续武器交接

- 状态：partial，功能已构建/写入；全套运行与视觉验收尚未完成，用户随后要求优先原始参数批处理。
- 日期：2026-10-24。
- 关联：[PLAN-20261024-002](../Plans/PLAN-20261024-002-mhwi-defense-transitions-transfer.md)、DAMAGE-002、MHWI-007，R-ANIM-007..009、R-COMBAT-009。
- Git：工作区变更，未提交；保留本轮前其他源码和资产修改。

## 已实施

`MHWIMovesetData.h`新增独立半开防御窗、起始槽阈值、霸体/回槽数据及每条Route的CancelStart/End。`MHWICharacter`统一请求/缓冲/跨帧/保持入口的取窗，显式输入不能绕过条件走通用取消；左右袈裟仍动态解析。见切先确认避伤、回斩真实扣血才满槽；居合无敌/反击独立，霸体跨普通派生保留，显式中断/死亡清理；回槽只积分剩余有效秒。颜色计时与回旋升色暂停、低槽气刃I弱斩均已实现。

`IncomingDamageResponse`新增可选bool+out伤害调整，`AttributeComponent::ApplyDamage`在未被拦截后调用并复查生命周期，支持50%霸体减伤且真实扣血、致死照常处理。没有实现接口的旧角色继续原路径。

新增 `MHWIWeaponAttachment.h/.cpp`，BeginPlay/动作边界及Tick退出时统一更新；不持有UObject指针/Timer。开始交接保留世界姿态，按源接触和事件辅助的项目窗口连续切换；握柄参考点根据骨1/2蒙皮混合变换，特殊保持按掌心/鞘口对轴。原蓝图Transform仍提供基姿态，但不再是全部运行位置唯一来源。不是原作IK求解器或已解码的原始装配矩阵，原0.7组件比例保留。

## 资产与工具

- `author_combat_fidelity.py`定向写入 `/Game/MHWI/Data/DA_MHWI_LongSword` 的防御/资源规则；动画引用和源武器事件保留。
- `author_transition_calibration.py`依据 `transition_calibration.json` 保存23招/148个逐输入规则。数值是源阶段约束下的项目调校，原输入位未解码。包括翻滚提前接踏步斩、不同取消种类的窗口，以及登龙落地后的明确出口。
- `qualify_native_parent_pose.py`证明309/310/311与308共享同一完整骨轨块、量化和根初值。每招705个整帧/子帧时刻，最大标量差0；经原生`animation.set_montage_sequence`将 `/Game/MHWI/Montages/M_IaiSpiritSlashWhite/Yellow/Red` 各自的唯一段改为 `/Game/MHWI/Animations/NativeFidelity/LongSword/A_w03_00_308`。颜色Montage身份/DA速度与事件保留；前后metadata比较通过。通用NeedsParent语义没有因此完全解出。
- `pie_combat_fidelity.py`新增资源/防御/窗口验证；旧`pie_behavior_corrections.py`改为按实际输入路线取窗，`pie_native_weapon.py`补明确special参数；`pie_weapon_transfer.py`区分正式时钟功能验证与冻结姿态截图。

## 实际验证与未验证

| 检查 | 实际结果 | 证据 |
| --- | --- | --- |
| IntroCppEditor Win64 Development，关闭编辑器后的完整反射构建 | Succeeded，58.37秒 | Saved/MHWIImport/CombatFidelity-20261024/build-combat-fidelity.log |
| `pie_combat_fidelity.run('defense')` | 2026-10-24 07:22:00完成，911条断言通过，含重复采样；不是911个独立场景 | Saved/MHWIImport/PIE-combat-fidelity-defense.json |
| 三色骨轨别名资格/原生替换前后比较 | 三条同源骨轨/相同片段参数；公开可读通知/Blend/Section数量与名称、DA磁盘hash一致 | Saved/MHWIImport/NativeParentPose-20261024/ |
| 特殊交接源接触审计 | 845帧；近邻蒙皮权重/原blend未变有记录 | Saved/MHWIImport/WeaponTransfer-20261024/source-contacts.json、source-grip-skin-provenance.json |
| 交接PIE首次三视角采样 | 3594条先前断言后因截图超过正式保持时间失败；不算完整通过 | PIE-transfer-fail1-capture-budget.json |

前两次defense失败分别为夹具不存在的deferred spawn API、把is_alive属性当函数；均已修复并保留fail1/fail2报告，第三次通过。alias预检曾读受保护Notifies，改用公开AnimationLibrary API和稳定字段快照；Section内部时间/link没有独立核验。截图脚本已改为独立冻结视觉阶段，未将其算作节奏验证。

资源/全路由/新版交接完整PIE、最终多角度外观仍待验收；用户要求优先参数批处理后，不继续以逐动画目测作主路径。后续原始数值导入见 [CHG-20261024-004](CHG-20261024-004-mhwi-native-parameter-pipeline.md)。

## 回退和同步

源码/DA基线备份在 `Saved/MHWIImport/CombatFidelity-20261024/Backup/`；路由和三色Montage分别在TransitionCalibration/NativeParentPose目录独立备份。按指定文件回退再构建，不恢复整个Content。原LMT/blend、游戏安装和第三方工具源码未修改。

现状见 [系统](../Systems/MHWI-LongSword.md)、[接口](../Interfaces.md)、[逐路由矩阵](../Reference/MHWI-Transition-Calibration.md)、[交接说明](../Reference/MHWI-Weapon-Transfer-Fitting.md)、[已知问题](../Known-Issues.md)、[模块索引](../Reference/modules.json)。
