# CHG-20261028-001：原版挂接骨驱动刀与刀鞘

- 状态：partial（源码与编译完成，最终实际握持验收由用户进行）
- 日期：2026-10-28
- 需求摘要：依据指定原游戏安装、解包动画与原生消费者定位武器脱手原因，完成修复和编译。
- 关联：[PLAN-20261028-001](../Plans/PLAN-20261028-001-mhwi-native-equipment-mount.md)、R-ANIM-010、MHWI-006/009/015。
- Git：工作区变更，未提交。

## 原因与结果

旧路径把刀固定在腕骨 bone_012，并用手工交接窗口、掌心标记和蒙皮拟合移动装备，再让手臂 IK 追踪上一帧装备点。原版通过猎人动画 usage2/function30、47 的控制轨分别选择主装备和副装备挂点；这些辅助骨已携带装备原点所需的平移与旋转。旧路径绕过了这些源轨，测试也只证明拟合目标自洽，不能证明与源动作握持一致。

本次刀和刀鞘按实际正在播放的主段、连接段或基础动画身份及源整数帧，独立选择 bone_030、bone_047 或 bone_002。有效动作中的选择0保留原版背部描述含义，不借用被全身 Slot 覆盖的中立持刀姿态。导入基转换为局部 X +90°，辅助骨选择缩放从装备视觉缩放剥离。背部使用原版配置与0.8比例，标准辅助骨挂接比例1；目标比例变化使用原版0.15秒圆形曲线。移除双臂装备反馈，保留既有足部地形约束。

官方实现机制与版本依据是 Epic [UE 5.8 Skeletal Mesh Sockets](https://dev.epicgames.com/documentation/unreal-engine/skeletal-mesh-sockets-in-unreal-engine)。MHWI 挂点语义来自指定 EXE 同版本消费者与原始 LMT；官方资料不证明 MHWI 机制。完整地址、指纹、切换帧与坐标对照见[本轮证据](../Reference/MHWI-Native-Mount-20261028.md)。

## 修改清单

| 文件 | 符号或数据 | 影响 |
| --- | --- | --- |
| [挂接实现](../../Source/IntroCpp/MHWI/MHWIWeaponAttachment.cpp)、[头文件](../../Source/IntroCpp/MHWI/MHWIWeaponAttachment.h) | FMHWIWeaponAttachmentRuntime | 以原版挂点与描述替代整件装备的掌心拟合路径；独立处理刀／刀鞘 |
| [角色](../../Source/IntroCpp/MHWI/MHWICharacter.cpp)、[角色声明](../../Source/IntroCpp/MHWI/MHWICharacter.h) | RefreshWeaponAttachment | 读取真实 Montage 实例位置和基础动画来源；移除旧非反射握点辅助访问器 |
| [动画实例](../../Source/IntroCpp/MHWI/MHWIAnimInstance.cpp) | UpdateEquipmentIK | 双臂装备 IK 权重保持0，停止手臂追踪旧拟合点 |
| [提取脚本](../../Scripts/MHWI/build_native_mount_data.py)、[生成数据](../../Tools/MHW/native-mount-curves.json)、[运行时表](../../Source/IntroCpp/MHWI/MHWINativeMountData.inl) | 两库482片段、576区间 | 保留原始控制记录顺序及整数帧首个匹配语义，可重复生成 |

## 接口、资产与既有修改

公开蓝图反射签名未新增或删除；FMHWIWeaponAttachmentContext 改为源动作／基础姿态及其源帧，属于项目内部 C++ 接口。旧 Blueprint 挂点／拟合字段保留序列化兼容，新的正式挂接不再读取其值。独立武器内部动画、正式招式数值、FBX 与原游戏文件未改。此次未保存蓝图、数据资产或地图。

开始时工作区已有动画覆盖、IK、Source、Docs、资产及用户规则修改；此次仅在列出的实现及文档范围继续修正，未回滚其他已有改动。历史 CHG-20261027-007 和 B21 报告保留其当时含义，当前证据页明确更正其握持与挂接结论。

## 实际验证

| 检查 | 实际结果 | 证据 |
| --- | --- | --- |
| 指定原游戏 EXE SHA256 | 与已有同版本证据匹配 | 本轮证据页及 Saved/MHWI-HandGrip/native/ |
| `python Scripts/MHWI/build_native_mount_data.py --check` | 通过；482片段、51,201源帧、576区间，逐帧选择结果复核并精确重建 | Tools/MHW/native-mount-curves.json |
| 正式 UE Sequence 与原始 LMT 坐标比较 | 84组；最大位置误差0.0000828cm、旋转误差0.0000744° | Saved/MHWI-HandGrip/mount-basis-verification.json、ue-mount-poses.json |
| IntroCppEditor Win64 Development / UE5.8，`Build.bat … -WaitMutex -NoHotReloadFromIDE -NoUBA` | Succeeded，10项构建动作，88.34秒 | Saved/MHWI-HandGrip/build-native-mount.log |
| 新二进制编辑器重启 | 编辑器ready，70.7秒；训练场准备结果见下方记录 | UE-MCP start_editor 本轮结果 |
| 文档检查、diff检查 | 待本轮最终执行后更新 | — |
| 实际握持、连续动作、多视角验收 | 未执行；用户最新指令“验收我自己来”，最终验收由用户操作 | 不复用历史拟合测试或旧截图作为此次通过 |

普通权限首次构建在引擎目录切换前被拒绝，批处理只输出目录位置错误；核对引擎目录存在后通过正常权限申请执行同一构建入口，完成上述成功构建。未改引擎脚本。

## 风险、遗留与回退

当前修复标准主姿态装备挂接。原版额外动画层、特殊强制状态、条件比例覆盖、缩放变化期间的附加旋转补偿、原生手臂 IK solver／CTM，以及每段动画的实际接触／穿插仍未完整还原或验收；不把此次坐标与编译结果写成完整原作保真通过。

回退只针对本次挂接实现、调用接线、生成表和双臂反馈相关差异；须保留原有用户改动，不能整文件覆盖回 HEAD。未改资产，无资产回滚需求。重新构建后才能运行回退版本。

## 已同步文档

[现状](../Systems/MHWI-LongSword.md)、[接口](../Interfaces.md)、[问题](../Known-Issues.md)、[证据](../Reference/MHWI-Native-Mount-20261028.md)、[模块索引](../Reference/modules.json)、[技术入口](../README.md)、[方案索引](../Plans/README.md)、[记录索引](README.md)。
