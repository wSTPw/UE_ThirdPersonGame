# PLAN-20261026-003：MHWI 原游戏 PC 键盘适配

- 状态：implemented-scope，代码与静态校验完成；未编译/PIE
- 日期：2026-10-26
- 用户需求：只做键盘适配，不改手柄组合逻辑和过渡动画。
- 关联模块 / 接口 / 问题：`mhwi-longsword`；MHWI-001/MHWI-013/MHWI-014；R01/R08；R-COMBAT-015 的 A03 设备来源部分。
- 实施记录：[CHG-20261026-006](../Changes/CHG-20261026-006-mhwi-keyboard-adaptation.md)。

## 现状与目标

`BuildInputMapping` 当前把十类命令直接绑到 LMB/RMB/R/F/G/Q/Space/E/C/V，且键鼠与手柄共享 `MHWI_Command_*`。开启 `bOriginalInputPreset` 后所有设备又进入同一个手势解析器，产生 A03；解析器只按 Held 状态判组合，A02 的无关键重发风险也存在。

原游戏 PC 太刀公开操作资料交叉一致的核心输入为：LMB 普攻、RMB 突刺、Ctrl 气刃、Ctrl+LMB 登龙突刺、Ctrl+RMB 见切、LMB+RMB 袈裟、Ctrl+Space 特殊纳刀；Space 回避，E 使用道具/收刀，Shift 冲刺/收刀。项目训练场没有道具系统，因此键盘 E 只在拔刀状态请求纳刀，纳刀状态不伪造成拔刀；RMB 也只在拔刀状态提交突刺。V 保留气刃连段中的投射器连射适配，不扩建完整瞄准系统。

## 范围与验收标准

| 输入 | 目标行为 |
| --- | --- |
| LMB / RMB / Ctrl | 分别提交 Light / Thrust / Spirit，不再使用 R 作为气刃快捷键 |
| Ctrl+LMB / Ctrl+RMB | 分别只提交 HelmBreaker / Foresight，移除 G/F 独立快捷键 |
| LMB+RMB | 只提交 FadeSlash，移除 C 独立快捷键 |
| Ctrl+Space | 只提交 SpecialSheathe，移除 Q 独立快捷键；纳刀等待中 LMB/Ctrl 仍分别为小/大居合 |
| Space / E / V | Space 回避；E 仅拔刀状态纳刀，纳刀时不伪造道具或拔刀；V 保留投射器连射 |
| 纳刀 RMB | 不提交突刺或拔刀；LMB/Ctrl 仍按既有路线拔刀 |
| Shift | 纳刀空闲保持冲刺；拔刀状态按既有输入路由请求纳刀，不绕过动作许可 |
| HUD | 显示实际 PC 键位，不再提示已移除的 R/F/G/Q/C 快捷键 |

组合必须由本帧至少一个新成员边沿触发；按住旧组合后按无关键不得重发旧组合。每帧至多提交一个组合，重叠输入优先级 SpecialSheathe > HelmBreaker > Foresight > FadeSlash 是显式项目适配，不冒称原游戏全局仲裁。

只做 MHWI 键盘/鼠标与对应 HUD。不改变 `bOriginalInputPreset` 默认值、手柄映射、手柄 A02、跨帧缓存、动作取消窗、伤害、动画资产、DataAsset 或其他角色。

## 技术方案

- `CommandActions` 与 `MHWI_Command_*` 保留给手柄路径，维持既有脚本和调用的兼容性。
- 新增 `KeyboardCommandActions` / `MHWI_KeyboardCommand_*` 和独立键盘 SprintAction；无效的直接组合键不映射物理键，只由键盘手势解析器产生。
- 键盘与手柄分别保存 Held 和本帧边沿。`Tick` 先解析键盘边沿，再按既有开关解析手柄边沿；设备状态不混用。
- 键盘组合要求成员 Held 且至少一个成员出现在本帧边沿；组合消费其成员边沿，剩余边沿再走单键命令。释放事件只改变对应设备的 Held。
- 外部输入阻断清除键盘待发边沿；UnPossessed 清键盘状态，防止重新控制后沿用旧手势。
- HUD 仅改提示文本和面板高度，不新增 UI 资产。

## 接口与数据迁移

| 接口 / 路径 | 当前行为/值 | 目标行为/值 | 调用方/蓝图影响 | 迁移顺序 |
| --- | --- | --- | --- | --- |
| `AMHWICharacter::BuildInputMapping` | 键鼠/手柄共享动作，R/F/G/Q/C 直达命令 | 分离设备动作；PC 官方核心键位 | 旧 `MHWI_Command_*` 保留；新增键盘动作供测试/调试 | 先加独立动作，再替换键盘绑定 |
| `AMHWICharacter::Tick` | 只有原版预设解析共享边沿 | 键盘每帧独立解析；手柄原路径不变 | 不改变公开 `RequestInput` 签名 | 游戏线程内执行 |
| `AMHWIHUD::DrawHUD` | 自定义快捷键提示 | PC 组合键提示 | 原生 Canvas，无 UMG 迁移 | 与映射同批修改 |
| Content / Config | 现有资产 | 不修改 | 无需资产迁移 | 无 |

## 实施步骤与依赖

1. 保存方案与来源边界，确认 B14 工作区改动不覆盖。
2. 修改 `MHWICharacter.h/.cpp` 的设备映射、键盘手势与 Shift 行为。
3. 更新 `MHWIHUD.cpp` 提示。
4. 新增静态校验与真实 Enhanced Input PIE 脚本；本机无可用 UE 5.8 时只执行静态检查，明确未编译/未运行。
5. 更新系统现状、已知问题、模块索引、方案/变更索引和 CHG；不把键盘修复扩大为手柄 A02 已修复。

## 验证计划

| 场景 | 方法/命令 | 期望结果 | 覆盖边界 |
| --- | --- | --- | --- |
| 映射与设备分离 | `python Scripts/MHWI/verify_keyboard_adaptation.py` | 官方键位、无旧快捷键、独立动作/Held/边沿和 HUD 均静态一致 | 不证明 Enhanced Input 运行结果 |
| 单键与组合 | `pie_keyboard_adaptation.py` | 各键只产生目标命令；组合不拆成两个动作 | 需可用编辑器和新二进制 |
| 无关键重发 | 同上 | 保持组合后按无关键只处理无关键，不重复旧组合 | 键盘；手柄 A02 不在本批 |
| 预设隔离 | 同上分别切换 bool 重建输入 | 键盘行为不随手柄预设改变 | 手柄本身不做新版验收 |
| Shift/E/提示 | 同上及 HUD 检查 | Shift 不绕许可，E/V 保留，提示无旧键 | 不含完整道具/瞄准系统 |
| 构建与文档 | UBT、`check_docs.py`、`git diff --check` | 通过则记录；环境缺失则明确阻塞 | 编译不等于行为通过 |

## 风险与回退

- 同时按三个以上攻击键的全局优先级没有原游戏消费者证据，必须保留项目适配说明。
- 分离动作会改变自动化注入目标；旧名称保留给手柄，新键盘测试必须使用新名称。
- 物理按键松开顺序、失去焦点和菜单阻断可能造成 Held 残留；本批覆盖显式释放、UnPossessed 和输入阻断清理，焦点策略不扩建。
- 回退仅需还原本批 C++、HUD、脚本和文档；无 Content 资产或存档数据回退。

## 文档同步清单

完成后更新 `Docs/Systems/MHWI-LongSword.md`、`Docs/Known-Issues.md`、`Docs/Reference/modules.json`、`Docs/Plans/README.md`、`Docs/Changes/README.md`、工作日志及 CHG-20261026-006。方案状态按实际验证写 implemented-scope 或 partial。
