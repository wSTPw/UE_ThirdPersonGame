# CHG-20261117-002：太刀刀光与命中数字显示

- 状态：completed
- 日期：2026-11-17
- 需求摘要：还原 MHWI 太刀的挥刀刀光（刀刃残影）与命中伤害数字显示
- 关联 PLAN / ADR / 问题 / 接口 ID：[MHWI 当前计划](../Plans/MHWI-Current.md)、MHWI-017
- Git：工作区变更，未提交

## 原因与结果

**刀光**：此前太刀没有任何挥砍视觉反馈，命中窗口只有碰撞扫掠与命中停帧。现在动作在源命中窗口内（`FMHWIHitWindow::StartTime/EndTime` ± `TrailWindowLead`）记录刀刃基/梢两骨的世界位置，逐帧重建成带状三角面，顶点自带年龄，尾段渐隐。

- 触发条件镜像 `AdvanceAction` 自己的窗口区间判定（`StartTime <= CurrentPosition && EndTime >= PreviousPosition`），不是第二套时间轴；命中停帧时姿态不动、样本自然停止累积。
- 逐帧采样而不是按源 TIML 特效轨：`wp03_0xx.efx` 的 WorkNo 语义未取证，无法证实哪条轨就是刀光；本实现只宣称"跟随源命中窗口"，不宣称复刻原作 EFX 编号或曲线。

**命中数字**：`UAttributeComponent::ApplyDamage` 之后真实扣血的命中会记录一条数字（伤害值、世界接触点、起始时间、固定小抖动），由原生 Canvas HUD 投影绘制：接触点上浮、先放大回弹、后段淡出、深色描边 + 暖橙色填充。

- 颜色只取 MHW 的"有效部位"橙色。白色/灰色（低肉质）与龙属性异常蓝框需要肉质/属性伤害数据，本项目 `FMHWIResolvedHit::Part/Sharpness/Affinity` 仍是 `Unavailable`，不臆造区分。
- 只有玩家造成的伤害有数字；玩家受击仍走 HP 条与受击动作，与原作一致。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/MHWIWeaponTrailComponent.h/.cpp`（新增） | `UMHWIWeaponTrailComponent : UProceduralMeshComponent`、`UpdateTrail/ClearTrail/GetSampleCount`、`Lifetime/MaxSamples/MinTipTravel/Intensity/HiltAlpha/Color` | 刀光几何生成：3 列顶点跨刀身、年龄幂次渐隐、尾段向刀梢收缩；加法混合单 section，无光照、无碰撞 |
| `Content/MHWI/Materials/M_MHWI_WeaponTrail.uasset`（新增） | Unlit / Additive / TwoSided；`EmissiveColor = VertexColor.RGB * Intensity(默认1.0)`；Opacity 不连（加法混合下恒为 1） | 刀光材质。强度只在 C++ 顶点色里预乘，材质标量保留为美术旋钮 |
| `Source/IntroCpp/MHWI/MHWICharacter.h/.cpp` | `FMHWIDamageNumber`、`WeaponTrail`、`TrailBaseBone=bone_100` / `TrailTipBone=bone_101`、`TrailWindowLead`、`DamageNumberLifetime`、`UpdateCombatPresentation`、`PushDamageNumber`、`GetDamageNumbers`、`GetWeaponTrailSampleCount/GetActiveDamageNumberCount/GetMovePosition/GetPresentationDebug` | 组件挂接、窗口判定、命中记录；诊断 getter 只读，不参与伤害/许可 |
| `Source/IntroCpp/MHWIUI/MHWIHUD.cpp` | `DrawHUD` 末尾命中数字绘制 | Canvas 绘制、`Canvas->Project` 投影、轮廓 4 向偏移 + 填充、`GetLargeFont` |
| `Source/IntroCpp/IntroCpp.Build.cs`、`IntroCpp.uproject` | `ProceduralMeshComponent` 模块与插件 | 刀光三角面容器；引擎自带插件，非市场依赖 |
| `Scripts/MHWI/pie_trail_damage_numbers.py`（新增） | Slate post-tick 状态机 | 真实 PIE 验收：刀光采样、真实命中、数字出现与过期 |
| `Scripts/MHWI/run_presentation_pie.mjs`（新增） | MCP 驱动 | 一条命令跑完启动/材质钉值/执行/读报告；编辑器子进程随驱动退出，因此三步必须同进程 |

## 接口、事件与资源影响

- 新增 USTRUCT `FMHWIDamageNumber`（只读展示数据）与 MHWI-017 所列访问器；未改动任何既有签名、动态委托或蓝图绑定。
- 新增组件类 `UMHWIWeaponTrailComponent`：`BP_MHWI_Hunter` 不需要手工添加，`AMHWICharacter` 构造时创建并挂到 RootComponent；蓝图子类若覆盖组件列表需保留该默认组件。
- 新资产路径 `/Game/MHWI/Materials/M_MHWI_WeaponTrail` 由 C++ 构造函数硬引用，缺失时刀光不显示但不崩溃。
- 命中数字不写 `LastResolvedHit`、不广播新委托，`OnHitResolved` 语义不变。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| `Build.bat IntroCppEditor Win64 Development` | UE 5.8，编辑器关闭 | Succeeded（含新增模块依赖） | 本记录，构建输出 |
| `node Scripts/MHWI/run_presentation_pie.mjs`（启动编辑器 → 钉住材质标量 → `editor.run_python_file` 执行上面的 PIE 脚本） | `/Game/MHWI/Maps/L_MHWI_Training`，PIE，全局时间膨胀 0.05 | 11 项检查全 PASS：刀光在窗口内记录到样本（峰值 10）、挥砍真实扣血、命中数字出现、数字按生命周期过期、窗口关闭后刀光清空 | `Saved/MHWIPresentation/PIE-presentation.json` |
| 截图 `MHWI_01_swing` / `MHWI_02_trail` / `MHWI_03_hit` | 同上 | 刀光沿刀身出现；命中数字橙色带描边、在目标接触点上方 | `Saved/Screenshots/WindowsEditor/`（不入库） |

未执行：60 FPS 常规帧率下的观感验收。本机编辑器未在前台时 PIE 被限制到 2–3 FPS，脚本用时间膨胀保证可采样；因此截图中刀光段数偏少，不能替代真实帧率下的视觉判断。未在 Rathian Basic 地图、登龙七段与居合延迟 shell 上取景。

## 风险、遗留与回退

- 刀光窗口是"源命中窗口 + 0.06 秒"的工程映射，不是原作 EFX 起止帧；若后续取证到 TIML 特效轨，应替换窗口来源而不是叠加。
- 数字颜色缺肉质/会心分支（见上），属于数据缺口而非显示缺陷。
- 回退：删除两个新源码文件、`M_MHWI_WeaponTrail`、`IntroCpp.Build.cs` 与 `.uproject` 中的 `ProceduralMeshComponent`、HUD/角色中的相关块；无存档或数据迁移影响。

## 已同步文档

[太刀系统](../Systems/MHWI-LongSword.md)、[接口 MHWI-017](../Interfaces.md)、[开发流程](../Development.md)、[变更索引](README.md)。
