# CHG-20261027-007：MHWI 太刀攻击姿态右手握点约束

- 状态：completed（UE 项目适配范围）
- 日期：2026-10-27
- 需求摘要：修复 MHWI 太刀猎人在多数动作中手与刀柄脱节的现象。
- 关联 PLAN / ADR / 问题 / 接口 ID：[R-ANIM-010](../Known-Issues.md)、[B20动画开发](../Reference/MHWI-B20-Animation-Development-20261027.md)
- Git：工作区变更，未提交；涉及源码/测试脚本原有用户修改，变更仅追加于其上。

## 原因与结果

**项目现状证据：** `/Game/MHWI/Blueprints/ABP_MHWI_Hunter` 的 `AnimGraph` 在 DefaultSlot 后具有右臂 TwoBoneIK（IK骨 `bone_012`）；Profile `/Game/MHWI/Data/DA_MHWI_EquipmentIK_Profile` 定义右臂链 `bone_010/011/012`。`UMHWIAnimInstance::UpdateEquipmentIK` 先前用 `bHandPose = !bInAction || bSpecialSheathHold` 阻止所有普通战斗 Montage 更新手臂目标，因此战斗时右臂 Alpha 保持0。此前的 B20 PIE 脚本还把该门控当作预期行为。

**根因推断：** MHWI 源动作的手腕/手姿态与独立动画刀柄需要接触约束；战斗期间关闭右臂求解会让刀柄跟随挂接器的右腕标记，而动画手臂不再消费刀柄的握点。代码和本轮PIE验证了门控及其修复，但这项结论只适用于当前UE项目姿态适配，不能代表原作 IK 机制。

**官方资料：** UE 5.8 的 [Two Bone IK](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-blueprint-two-bone-ik-in-unreal-engine) 说明 Effector 控制两骨链末端位置、Joint Target 控制中间关节，并允许把 Effector 设置为交互物/Socket位置；[Skeletal Mesh Sockets](https://dev.epicgames.com/documentation/en-us/unreal-engine/skeletal-mesh-sockets-in-unreal-engine?application_version=5.8) 说明可将武器挂接到骨骼/Socket。官方资料说明UE机制，不证明MHWI原作姿态或IK目标。

**修改结果：** 拔刀状态和特殊纳刀保持期间继续计算右臂 IK；普通动作的目标握点取自武器挂接运行时最近一次实际使用的握点，能跟随拔纳刀和居合交接，而不是固定读取常规握点。纳刀且非特殊纳刀保持时右臂关闭；战斗中的左臂和双脚仍维持门控，不改变攻击主体动画。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/MHWIAnimInstance.cpp` | `UMHWIAnimInstance::UpdateEquipmentIK` | 让拔刀动作保留右臂刀柄接触求解；使用挂接器当前握点。 |
| `Source/IntroCpp/MHWI/MHWICharacter.h` | `AMHWICharacter::GetWeaponGripPoint` | 添加内部 C++ 读取口，使 AnimInstance 获得运行时最近握点；不是 UFUNCTION。 |
| `Source/IntroCpp/MHWI/MHWIWeaponAttachment.h` | `FMHWIWeaponAttachmentRuntime::GetLastGripPoint` | 只读返回已在 `Update` 中使用的实际握点。 |
| `Scripts/MHWI/pie_remaining_animation.py` | 战斗IK回归断言 | 将“攻击时所有IK为0”更新为“右臂握点求解为正、左臂/双脚为0”。 |
| `/Game/MHWI/Blueprints/ABP_MHWI_Hunter`、`/Game/MHWI/Data/DA_MHWI_EquipmentIK_Profile` | AnimGraph / Profile | 只读核对，没有保存或改动资产。 |

## 接口、事件与资源影响

新增两个内部非反射只读 C++ getter；没有 UFUNCTION、UCLASS/USTRUCT/UENUM、资产路径、Montage、委托或序列化字段变更，因此无需 Blueprint/DataAsset 重定向迁移。现有 `/Game/MHWI/Blueprints/ABP_MHWI_Hunter` 图结构与 Profile 保持不变。工作区中的 MHWI C++、Blueprint、训练地图和文档原有修改均先于本记录存在；本次没有保存 `.uasset` 或地图。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| `editor.build_project`：IntroCppEditor Win64 Development | UE 5.8 | 成功，10个UBT动作完成；含 `MHWIAnimInstance.cpp`、`MHWICharacter.cpp`、`MHWIWeaponAttachment.cpp` 编译 | `C:\Users\Butter cookies\AppData\Local\UnrealBuildTool\Log.txt` |
| `pie_remaining_animation.py`（新输出路径） | `/Game/MHWI/Maps/L_MHWI_Training` PIE | 38项通过；`OverheadSlash` 期间 Alpha 为 `[左臂0, 右臂1, 左脚0, 右脚0]`；特殊纳刀双臂、移动、地形、死亡等门控通过 | `Saved/MHWIRestoration/CHG-20261027-007/PIE-animation-consumers.json` |
| `pie_weapon_transfer.py`，30 FPS | 同一训练地图真实PIE | 3750项全部通过，包含1085项握点相关断言，失败0；覆盖 OverheadSlash、Thrust、Roll、Draw/Sheathe、特殊纳刀及居合 | `Saved/MHWIImport/WeaponTransfer-20261024/PIE-transfer-30fps.json` |
| PIE后编辑器状态 | UE 5.8 | 地图包无脏状态，未保存修改 | UE-MCP `editor.get_world_state` |
| `python Scripts/Docs/check_docs.py` | 工作区 | PASS：138 Markdown文件、1179本地链接、12个模块及编辑器快照JSON | 命令标准输出 |
| `git diff --check` | 工作区 | PASS；仅报告已有用户文件的CRLF行尾提示，无空白错误 | 命令标准输出 |

## 风险、遗留与回退

- 原始MHWI IK solver的限位、坐标/管理器语义仍未闭合；本次使用UE TwoBoneIK的项目目标适配，不宣称原版忠实复刻。
- 该方案约束右腕/手的握点位置，不重制手指弯曲或全部攻击帧手腕旋转；若视觉上仍有手掌姿势问题，应按具体动作采样检查，而非增加全局资产偏移。
- 回退：还原本次两处 getter 与 `UpdateEquipmentIK` 右臂门控改动，并将 `pie_remaining_animation.py` 的战斗断言恢复到原条件；删除本记录及索引/现状文档新增行后重新编译源码。

## 已同步文档

- `Docs/Systems/MHWI-LongSword.md`
- `Docs/Known-Issues.md`
- `Docs/Changes/README.md`
