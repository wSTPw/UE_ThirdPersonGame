# CHG-20261116-001：玩家受击改用原生 DAMAGE_S 四方向片段并补全大/中档

- 日期：2026-11-16
- 方案：[PLAN-20261116-001](../Plans/PLAN-20261116-001-hunter-damage-reaction.md)
- 结果：源码已合入并编译；13 个真实 PIE 用例通过（四方向小受击、四方向中受击、大小档起身链、持刀）
- 用户拍板（2026-11-16 问答）：中受击采用特征组 92/93/94/96 试验；特殊受击（WIND/QUAKE/EAR/SLIP）本轮只记录证据，不实现。

## 原因

2026-11-07 的注册表证据表明旧受击三档（`co00_00` 70/71/72、`w03_00` 61/62/63）实际是 `Common::STEP_*` / `WP_03::STEP_*` 台阶步进动作，不是受击反应；用户已明确反馈三档均不像原作。2026-11-08 批次已解包 `co00_01.lmt` 并导出/导入四个 DAMAGE_S 候选，但运行时从未引用。

## 源证据

| 证据 | 内容 |
| --- | --- |
| `Saved/MHWIRestoration/B20-20261027/native/common-source-actions.json` | `Common::DAMAGE_S_FRONT/BACK/LEFT/RIGHT`，action 335/336/337/338；`Common::DOWN_FACEUP/FACEDOWN_STAND_UP` 431/439；`DAMAGE_QUAKE_S=375`、`DAMAGE_EAR_END=379`、`DAMAGE_WIND_*=388-390`、`EM_125_SLIP_*=716/718` |
| `numeric-slot-provenance.json`（11-08） | `DAMAGE_S_entry 0x14334a760` selector `0x1068/0x1069/0x106b/0x106a` → bank 1 slot 104/105/107/106；posture_preview `0x141709540` packed `0x1007`，shared identity `0x431/0x439` → slot 7 |
| `co00_01_action_pose_report.json` + `Saved/damage_scan.json`（本批全量扫描） | slot 根轨/髋高特征：104-107 末髋 101.9 位移 62-85cm（短受击）；7 髋 12→70（起身）；92/93/94/96 髋 43-52→89-90、59-65 帧（踉跄恢复）；120-123 髋 14-23→89.7、位移 118-242cm（快速起身，本轮未采用） |
| `co00_00.lmt` 090/203 | 走跑根轨 `+Z`，据此源前向 `+Z`、右向 `+X` |

推断（PIE 实测确认）：攻击来自前 `→104`（后退）、后 `→107`（前冲）、左 `→105`（右移）、右 `→106`（左移）；Medium 组同理 96/92/94/93。**注册 action 与 selector 的序号顺序未证**；action 号仅作查表键。

## 源码改动

| 源文件 / 符号 | 改动 | 影响 |
| --- | --- | --- |
| `MHWILinkAnimation.cpp` `SequenceMotion` | 识别 `A_co00_01_` 前缀 | 动态 Montage 源身份可解析 |
| `MHWILinkAnimation.cpp` `IsKnownSourceIdentity` | 增查 `SourceBindings` | 受击身份（含工程键 340-343）通过绑定校验；此前 `{1,340}` 被白名单拒绝导致 Medium 静默失败（`bind_token` 日志定位） |
| `MHWINativeSources.cpp` `GetSourceBlends` | `co00_01` 返回空表 | 避免误用武器 blend |
| `MHWINativeSources.cpp` `GetSourceMotionInfo` | 新增 7/92/93/94/96/104-107 帧数 | `TickNativeSource` 按源帧结束 |
| `MHWINativeSources.cpp` `StartNativeSource` | 各失败分支加 `MHWI_SOURCE_FAIL` 日志 | 失败不再静默；定位了 `bind_token` 问题 |
| `MHWIR06SourceData.inl` | 新增 `{1,335..338}→104/107/105/106`、`{1,431}/{1,439}→7`、`{1,340..343}→96/92/94/93`（工程键） | 三档受击绑定 |
| `MHWICharacter.h/.cpp` `StartNativeImpact` | 增 `Direction` 参数；`bPendingLargeGetup`；Medium/Large 分支选表 | 按方向+等级选段；pending 保存方向 |
| `MHWICharacter.cpp` `HandleDamaged` | 按攻击者相对位置算前/后/左/右 | 方向来自伤害来源 |
| `MHWICharacter.cpp` `Tick` | 落地且受击结束后启动 `{1,431}` 起身，保持 `FlinchLarge` 锁输入 | 大受击落地起身链 |
| `MHWICharacter.cpp` 构造函数 | 加载 `DamageSource/A_co00_01_007/092/093/094/096/104-107` | 新片段进入 `NativeSourceSequences` |
| `MHWICharacter.cpp` `HandleDeath` | 清 `bPendingLargeGetup` | 死亡不起身 |
| `Scripts/MHWI/pie_hunter_hit_reaction.py` | bank 分支支持 `co00_01`；断言改 DAMAGE_S/Medium 集合；Large 增起身与锁输入断言 | 验证适配 |
| `Scripts/MHWI/mcp_animation.mjs` / `run_damage_matrix.mjs`（新增） | `run-py` 通用入口；四方向驱动 | 验证工具 |

## 运行时行为（当前）

| 等级 | 流程 | 证据资格 |
| --- | --- | --- |
| Small | `co00_01` 104/107/105/106 按方向 | 注册名 + selector 数值 + PIE 实测 |
| Medium | `co00_01` 96/92/94/93 按方向 | **无注册名**；特征匹配 + 用户批准试验 + PIE 实测 |
| Large | 同 Small 方向段 + 现有击飞物理 → 落地后 `co00_01` 7 起身（保持输入锁定） | slot 7 有 0x431/0x439 静态证据；"击飞落体段"仍缺（空中播短受击片段） |

持刀/纳刀统一走 Common；控制状态与击飞向量不变。

## 验证

构建：`-NoUBA` 全量重建通过（约 51s，3 chunks）。**陷阱**：UBT 的 git 工作集检测失败（`Failed to start git process`）会让自适应构建沿用陈旧文件集，增量编译看似成功但新代码不在 DLL 里（Medium 第一次 PIE 静默失败的根因）；需删除 `Intermediate/Build/Win64/x64/UnrealEditor/Development/IntroCpp` 与 `Binaries/Win64/UnrealEditor-IntroCpp.*` 后全量重建。

真实 PIE（`/Game/MHWI/Rathian/Basic/Maps/L_RathianBasic`，每例独立 PIE）：

| 用例 | 播放 | 结果 |
| --- | --- | --- |
| damage-front / back / left / right（小咬） | 104 / 107 / 105 / 106 | 4 例 PASS（7 断言/例） |
| damage-medium-front / back / left / right（火球） | 96 / 92 / 94 / 93 | 4 例 PASS（8 断言/例，含上升） |
| damage-large-getup-front（龙车） | 104 → 落地 → 7，起身期 `FlinchLarge` | PASS（9 断言） |
| damage-large-tail（尾翻） | 104 → 高抛 → 落地 → 7 | PASS（12 断言） |
| damage-drawn-front（持刀小咬） | 104 | PASS（7 断言） |
| damage-large-front（早期 Large 对照） | 104（起身链加入前） | PASS |

报告：`Saved/RathianHitReaction-20261107/regression/PIE-damage-*.json`。骨姿与源帧对比稳定段误差 0.1-0.4°，脊椎 4-5 骨实际变化，位移真实发生。

## 未验证 / 未覆盖

- Medium 的 92-96 组无注册名，slot 方向由根位移匹配；若后续拿到原作分派证据需重核。
- 击飞落体段（空中倒地姿态）缺失：Large 空中仍播短受击片段，落地才接起身；120-123 快速起身组未采用。
- 特殊受击（QUAKE 375 / EAR 379 / WIND 388-390 / SLIP 716/718）只有注册名，slot 未查证，本轮未实现。
- TIML 事件未迁移 AnimNotify；受击/起身无音效通知。
- selector 值与四方向的精确对应、action 335..338 与 slot 104..107 序号关系仍未证。
- `MHWILinkRuntimeData.inl` 的 `NodeIdentities` 未与 `SourceBindings` 交叉核对。

## 回退

还原以下源文件并全量重建即可；绑定表与构造加载都在源码内，无正式资产改写（`DamageSource` 下新增的 5 个导入片段可单独撤下）。

```text
Source/IntroCpp/MHWI/MHWILinkAnimation.cpp
Source/IntroCpp/MHWI/MHWINativeSources.cpp
Source/IntroCpp/MHWI/MHWIR06SourceData.inl
Source/IntroCpp/MHWI/MHWICharacter.h
Source/IntroCpp/MHWI/MHWICharacter.cpp
Source/IntroCpp/MHWI/MHWICharacterNativeSources.cpp
```
