# CHG-20261020-003：移动根运动缓存与生硬衔接修复

- 状态：completed（配置修复已保存；实际效果未运行验证）
- 日期：2026-10-20
- 用户反馈：移动动画衔接非常生硬，移动不生效。
- 关联：ACTION-004、R-ANIM-001/002；前序 [Root Motion接入](CHG-20261020-002-ninja-root-motion.md)。
- Git：工作区变更，未提交。

## 原因与修复目标

制作前读取：Ninja跑步原Root从0移动到275cm，YBot输出到283.644409cm，证明抽样资源具有真实轨迹；提取设置已启用，ABP为RootMotionFromEverything，玩家网格实际使用ABP_Move。不能以缺Root轨迹或未开启提取解释此次问题。

ABP_Move的同一个PoseCache被DefaultSlot底层和UpperBodyOnly上层共同读取。LayeredBoneBlend配置Spine1上半身过滤、bBlendRootMotionBasedOnRootBone=true、bUpdateBasePoseFirst=false，因此上层先以全姿态权重1/根运动权重0请求缓存，底层再以相同姿态权重1/根运动权重1请求。UE5.8 SaveCachedPose.PostGraphUpdate仅在新姿态权重严格更大时替换请求；等权重沿用首个上下文，导致移动动画会播放但根运动被上层零权重抑制。这是资产和引擎源码的静态因果定位，尚未运行复现/验收。

三个BlendSpace此前输入InterpolationTime与TargetWeightInterpolationSpeedPerSec为0，数字键盘输入切换直接跳变。拟将底层缓存优先更新，并设置短时临界阻尼输入滤波和样本权重过渡；保留Root Motion、上半身过滤与五次命中时序。

## 制作修改

| 资产 | 设置 |
| --- | --- |
| `/Game/MyStuff/Model/Robot/ABP_Move` | LayeredBoneBlend.Node.bUpdateBasePoseFirst=true，保留按根骨权重混合；RootMotionFromEverything保留 |
| 同目录 `BS_Move`、`BS_LongSwordMove`、`BS_StaffMove` | Direction平滑0.10秒、Speed平滑0.16秒，SpringDamper、DampingRatio=1、MaxSpeed=0；样本权重插值8/s，EaseInOut=true |

实际写入：原生set_node_property保存Node.bUpdateBasePoseFirst=True；随后bulk_set_properties对三个BS均成功保存，各实际变更3个属性，0资产/属性/保存失败。相同批次提交ABP的RootMotionFromEverything返回unchanged，作为制作提交结果保留，并未追加独立读回。0.10/0.16秒与8/s为初始调参，不是视觉验收结论。完整调用及制作前诊断在 `Saved/NinjaLocomotionFix-20261020/authoring-log.json`。

## 接口与资产影响

无C++/反射签名变更；不改源动画、Root轨迹、输入绑定、Montage通知/窗口、伤害或移动组件默认模式。蓝图编辑工具内部更新生成类属于制作步骤，不安排额外编译检查。

## 诊断与验证边界

- 初始编辑器已关闭，为读取/编辑资产重新打开编辑器，未启动PIE。
- 只读诊断对照实际Root轨迹、提取设置、事件图连接、玩家网格AnimClass、姿态连接及平滑参数；因果依据为本机UE5.8的AnimNode_LayeredBoneBlend.cpp和AnimNode_SaveCachedPose.cpp。
- 按先前用户指令，不执行完工后的PIE、自动化、显式编译检查、资产读回、文档检查或diff检查。旧测试不作为本次修复通过的依据。

## 回退与后续

覆盖前4个资产备份在 `Saved/NinjaLocomotionFix-20261020/Before`。关闭编辑器后按原路径恢复即可回到此次修复前状态，勿与前两轮备份混用。保留R-ANIM-001的运行未验证范围；本次根运动缓存问题登记R-ANIM-002。

## 文档同步

已同步：[Ninja配置](../Systems/Ninja-Animation-Configuration.md)、[Combat-AI](../Systems/Combat-AI.md)、[UI资产](../Systems/UI-Assets.md)、[模块索引](../Reference/modules.json)、[Known-Issues](../Known-Issues.md)、[Changes索引](README.md)、[当前增量映射](../../ArtSource/Animation/NinjaLocomotionFix-20261020.json)。本轮按用户要求没有运行文档或diff检查。
