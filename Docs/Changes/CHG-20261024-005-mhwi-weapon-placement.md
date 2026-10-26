# CHG-20261024-005：太刀武器位置与交接收尾

- 状态：completed，此轮位置实现与构建完成；最终UE运行调试由用户验收
- 日期：2026-10-24
- 需求摘要：完成武器位置处理后通知，不做最终UE运行调试，由用户验收。
- 关联： [PLAN-20261024-004](../Plans/PLAN-20261024-004-mhwi-weapon-placement.md)、R-ANIM-007、MHWI-006、MHWI-009
- Git：工作区变更，未提交；保留此前源码/资产修改

## 原因与结果

静态检查发现：原helper仅识别独立Draw/Sheathe，遗漏纳刀直接攻击和大回旋动作内收刀；居合只混合组件原点，源内部动画更换之后材质握点未连续转移；每次新动作经过FinishMove中间默认姿态，并按动作编号重启刀鞘交接。

本轮将手掌接触约束放到最终变换混合之后，特殊武器独立的旋转/比例拟合也按原蓝图字段参与求解。纳刀攻击从实际部件入口姿态在0..10/60秒拔出，普通返回握点以0.16 Actor秒转移；居合以原0..8帧内部事件区间连续转移握点并维持左右掌接触。大回旋用显式静态纳刀0号事件作为拟合结束锚点，前12/60秒开始回背；视觉回背状态独立于玩法标志，后继攻击可识别该入口。直接派生推迟中间姿态重置，显式Tick依赖确保在猎人和武器Mesh之后更新。武器在不可见时仍更新骨姿态。

这些时间是项目位置拟合，不是解码出的原生装备挂点事件；本轮实现尚未经过用户要求保留的UE运行验收。原版初始装配、IK消费者、源73/80保持差异和全顶点穿插没有据此宣称解决。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/MHWIWeaponAttachment.h/.cpp` | Settings、Context、Update、Apply、IsBackMounted、Reset | 补两类交接、最终接触锁定、材质握点连续过渡；鞘按实际左右手/背部所有权保持过渡，不按动作编号重启 |
| `Source/IntroCpp/MHWI/MHWICharacter.h/.cpp` | StartResolvedMove、FinishMove、RefreshWeaponAttachment、BeginPlay、构造函数 | 记录入口装备状态、延迟派生中间重置、先选源姿态再装配；添加Mesh Tick依赖与武器不可见时刷新 |
| `Scripts/MHWI/audit_weapon_placement_sources.py` | run | 纯离线源曲线与哈希核对，不启动UE、无资产写入 |
| `/Game/MHWI/Blueprints/BP_MHWI_Hunter`、`/Game/MHWI/Data/DA_MHWI_LongSword`、`/Game/MHWI/Weapons/` | 现有正式资产 | 本轮未修改/保存；原模型、骨架、比例、掌心及背负基变换沿用现有项目拟合 |

## 接口、事件与资源影响

新增MHWI-009：普通C++ helper上下文/视觉回背getter。`FinishMove`增加私有可选参数`bDeferEquipmentReset=false`，仅直接启动后继动作时传true；真实结束/中断/死亡默认false。现有反射签名和UPROPERTY没有修改，无蓝图资产迁移，不改变输入许可、路由、消耗、伤害和原19条内部事件。角色新增非反射状态只影响装备表现。

历史45项固定挂接、3594条后失败的截图尝试、资源615断言均不是本轮运行结果。原训练场已确认无脏包、非PIE后干净关闭，以便构建；本轮不会重新启动编辑器作最终调试。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| `editor.get_world_state/list_dirty_packages`、`request_editor_shutdown(requireClean=true,endPIE=false)` | 已打开UE5.8训练场 | 非PIE、0脏包；干净关闭 | 本轮工具返回 |
| `python Scripts/MHWI/audit_weapon_placement_sources.py` | 本机Python，原始wg03_00与合格导出清单 | 6项源一致性通过；6个动作、原LMT/原blend/6FBX哈希相符，2/3起止与0/1相符 | `Saved/MHWIImport/WeaponPlacement-20261024/source-consistency.json` |
| `Build.bat IntroCppEditor Win64 Development -Project=... -WaitMutex -NoHotReloadFromIDE` | 首次普通执行 | 批处理报引擎目录定位错误，未进入C++编译；日志保留并按triage技能检查 | 同目录`build-editor.log` |
| 同上，工作目录改为引擎BatchFiles并使用工具链所需权限 | UE5.8/MSVC14.44 | Succeeded，468.85秒；随后入口连续性/注释有微调，以最终构建为准 | 同目录`build-editor-retry.log` |
| 最终构建同上，额外`-NoUBA -MaxParallelActions=2` | UE5.8/MSVC14.44 | Succeeded，8个构建动作，26.61秒；最后源码已进入DLL | 同目录`build-editor-final.log` |
| Python AST语法、`python Scripts/Docs/check_docs.py`、`git diff --check`及新增文本空白/冲突检查 | 本机 | PASS；73 Markdown/528本地链接/12模块，14个本轮文本文件空白检查通过 | 本轮命令输出 |
| 7个正式资产前后哈希对照 | 本机只读 | 全部一致；未保存UE资源 | 同目录`protected-assets.json` |
| 最终UE运行调试、PIE与多视角视觉验收 | 用户指定 | 本轮未执行，由用户验收 | 无本轮PIE报告 |

## 风险、遗留与回退

源内部动画依旧保留，具体抽出量/装配窗口的原版一致性需后续独立证据；普通源库以当前型号swo001的实测蒙皮参考点拟合，不对任意武器型号泛化。身体、衣物与武器的全顶点碰撞没有增加。用户验收重点为E拔纳刀、纳刀LMB、完整气刃链回背、Q接LMB/R居合、翻滚出口与受击中断。

修改前五个文件的原样备份在`Saved/MHWIImport/WeaponPlacement-20261024/Backup`，四个C++文件为本轮实际源码修改；`pie_weapon_transfer.py`仅备份，本轮未修改。恢复四个C++文件后重新编译即可回退本轮行为，无需恢复UE资产。`protected-assets.json`保留7个相关正式资产哈希。

## 已同步文档

[太刀现状](../Systems/MHWI-LongSword.md)、[武器交接](../Reference/MHWI-Weapon-Transfer-Fitting.md)、[接口](../Interfaces.md)、[模块索引](../Reference/modules.json)、[已知问题](../Known-Issues.md)、[方案索引](../Plans/README.md)、[变更索引](README.md)。
