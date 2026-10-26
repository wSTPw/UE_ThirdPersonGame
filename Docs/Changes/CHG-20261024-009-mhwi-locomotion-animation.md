# CHG-20261024-009：B03基础循环动画迁移

- 状态：completed（本批限定范围）
- 日期：2026-10-24
- 需求：继续按台账修复，优先动画；不猜参数，复杂测试后置。
- 关联：[PLAN-007](../Plans/PLAN-20261024-007-mhwi-locomotion-animation.md)、R28/R32/R33；工作区变更，未提交。

## 原因与结果

实际DA六个基础动画属性、两张BlendSpace六个样本仍指向旧采样库。原LMT的五段对应动画已有独立采样/FBX重读合格报告，旧转换器存在骨姿态采样误差。现统一改用NativeFidelity合格库，避免攻击动画已迁移而基础循环仍使用旧采样。

## 修改清单

| 文件/资产完整路径 | 修改 |
| --- | --- |
| `/Game/MHWI/Data/DA_MHWI_LongSword`，类`MHWIMovesetData` | idle/walk/run/sheathed_idle/sheathed_walk/sheathed_run六个引用 |
| `/Game/MHWI/Animations/BS_MHWI_Drawn`、`BS_MHWI_Sheathed`，BlendSpace | 六个样本只替换Animation，复制并核对其余样本配置 |
| `/Game/MHWI/Animations/NativeFidelity/LongSword/A_w03_00_001`、`A_w03_00_004` | AnimSequence；禁用根运动、REF_POSE强制锁根，沿用旧倍率 |
| `/Game/MHWI/Animations/NativeFidelity/Common/A_co00_00_001`、`A_co00_00_203`、`A_co00_00_090` | 同上；walk/run倍率沿用1.332921/1.149071，属于既有适配，不声称原版倍率 |
| [定向迁移](../../Scripts/MHWI/author_locomotion_fidelity.py) | 固定清单/源依赖/FBX指纹、资格、时长、Skeleton、导入来源预检；全预检后保存、备份、读回和幂等 |
| [制作入口](../../Scripts/MHWI/author_assets.py) | 基础制作与动画修正尾处理维持本批引用；不重跑全量制作 |
| [短冒烟](../../Scripts/MHWI/pie_locomotion_fidelity.py) | 真实Enhanced Input、纳刀/持刀待机与移动 |

## 接口与资源影响

无C++/反射签名改变，无需编译。动画仍由`/Game/MHWI/Blueprints/ABP_MHWI_Hunter`及既有BlendSpace调度，ABP没有保存改动。动作32定义/149路线/29Montage未变，B01/B02修复保留；移动速度180/420、混合设置及动画时长保留。旧Sequence、原LMT/FBX和用户其他资产未修改。

## 实际验证

证据目录：`Saved/MHWIRestoration/B03-20261024/`。

| 检查 | 实际结果 | 报告 |
| --- | --- | --- |
| MCP项目/PIE/脏包检查 | 正确项目；改动前后脏包均0 | 工具回读；`inspection.json` |
| 源/资产资格预检 | 固定清单SHA、全部源依赖及五个FBX指纹、225骨、采样/FBX资格、时长/Skeleton/导入路径通过 | `preview.json`、`authored.json` |
| 保存/读回/幂等 | 8资产保存；再次执行0修改，样本其余配置和动作数据未变 | `authored.json`、`idempotence.json` |
| 真实短PIE | **7.766秒通过**；纳刀待机/走/跑、持刀待机/走；速度0/180/420，姿态有限，无竖直根漂移 | `PIE-short-smoke.json` |
| 内容哈希白名单 | 仅预期8资产变化，另外341文件不变 | `before-assets.json`、`final-verification.json` |
| Python语法 | 三个相关脚本通过；首次检查命令编码名`utf8-sig`拼写错误，改为`utf-8-sig`后通过 | `final-verification.json` |
| 文档/差异 | `python Scripts/Docs/check_docs.py`与禁用命令级LFS过滤的`git diff --check`；实际结果见本批最终报告 | `final-verification.json` |

未重启编辑器做新进程重载，未重跑全量制作/战斗套件/地形生命周期/原作录像。短测只证明当前运行无明显退化，不证明每帧姿态及原版速度完全一致。

## 遗留与回退

R28部分完成：起停、转身、落地、方向/速度标定仍待开发；R06/R07/R29/R30没有改未知连接帧、取消、保持或IK参数。原生采样器仍属于逆向工具证据，并非原作运行验证。

目标资产与原制作脚本字节备份在本批`Backup/`。关闭编辑器后按原路径恢复并重载；移除两个新增脚本和本批制作尾处理可回退实现。所有349资产保存前指纹保留，禁止整目录覆盖用户改动。

## 已同步文档

[台账](../Plans/MHWI-Restoration-Progress.md)及CSV、[系统现状](../Systems/MHWI-LongSword.md)、[问题](../Known-Issues.md)、[开发流程](../Development.md)、[总方案](../Plans/PLAN-20261024-005-mhwi-original-restoration.md)、[模块索引](../Reference/modules.json)、计划/变更/文档入口。旧采样实施页保留历史范围并追加当前指针。
