# PLAN-20261116-001：玩家受击四方向动画还原

- 状态：implemented（2026-11-16）
- 日期：2026-11-16
- 用户需求：解包游戏角色的受击相关数据动画（受击动作、蒙太奇、通知及相关资源），在项目中还原实现，并验证 UE 播放效果。
- 关联模块 / 接口 / 问题：`MHWI-001..015`、`R-ANIM-014`、`R-ANIM-016`、`PLAN-20261107-004`
- 实施记录：[CHG-20261116-001](../Archive/MHWI/Changes/CHG-20261116-001-hunter-damage-reaction.md)

## 现状与目标

事实：

- 现有受击三档在 `AMHWICharacter::StartNativeImpact` 里用 `Common[]={103,110,115}` / `{30,31,32}`，绑定表落到 `co00_00` 70/71/72 与 `w03_00` 61/62/63。2026-11-07 的注册表证据表明这些是 `Common::STEP_*` / `WP_03::STEP_*`，即台阶步进载体，不是受击动作；用户已明确反馈三档均不像原作。
- `Saved/MHWIRestoration/B20-20261027/native/common-source-actions.json` 记录 `Common::DAMAGE_S_FRONT/BACK/LEFT/RIGHT` 注册项，action 335/336/337/338。
- `Saved/AnimationSemantics-20261108/RealDamage/Common1/numeric-slot-provenance.json` 记录 `DAMAGE_S_entry 0x14334a760` 的 selector `0x1068/0x1069/0x106b/0x106a` 数值对应 bank 1 slot 104/105/107/106；该文件同时声明这只是数值对应，方向语义未断言。
- 上述四个 slot 的 LMT 根轨位移（`co00_01_action_pose_report.json`，源轴 cm）：104 `(3.1,0,-68.8)`、105 `(84.3,0,-2.8)`、106 `(-61.3,0,2.5)`、107 `(3.6,0,63.2)`。`co00_00` 的 090/203 根轨为 `+Z`（走跑前进），据此源坐标前向为 `+Z`、右向为 `+X`。
- 五个候选 FBX 已由 2026-11-08 批次导出并导入到 `/Game/MHWI/Animations/DamageSource/`（`A_co00_01_104/105/106/107/007`），但运行时从未引用；`StartNativeImpact` 仍走 STEP 绑定。

推断（未证）：

- slot → 受击来源方向按根位移取反匹配：攻击来自前 `→104`（后退）、后 `→107`（前冲）、左 `→105`（右移）、右 `→106`（左移）。
- 注册 action 335..338 与 slot 104..107 的序号顺序、selector 值与四方向的精确一一对应均未证；本轮只把 action 作唯一键，slot 由位移方向决定。

目标：玩家受击改用 `co00_01` 的真实 DAMAGE_S 片段，按攻击来源方向选段，持刀/纳刀统一走 Common；删除 STEP 受击绑定在运行时的使用。大受击倒地链本轮不接（缺 DAMAGE_DOWN 落体段），保持现有击飞力度与 `EMHWIImpactSize` 接口。

## 范围与验收标准

范围内：

- 四方向短受击（Small/Medium）在持刀与纳刀状态均使用对应方向片段。
- Large 沿用同一套 DAMAGE_S 片段，保留现有击飞向量与控制状态；文档明确它不是完整倒地链。
- PIE 断言：实际播放的 bank/body、方向与攻击来源一致、actor 实际位移方向、骨姿与源帧对比、结束后恢复站姿。

范围外：

- 倒地/起身（`A_co00_01_007`）未接入，只保留资产与证据。
- 气绝、麻痹、睡眠、地形伤害等特殊受击；TIML 事件到 UE AnimNotify 的完整迁移。
- 原作 `nHmAction` 运行时分派等价的声明。

## 技术方案

1. `SequenceMotion` 增加 `A_co00_01_` 前缀识别，使动态 Montage 的源身份可解析；`GetSourceBlends` 对 `co00_01` 返回空表，避免误用武器 blend。
2. `MHWIR06SourceData.inl` 增加四条绑定：`{1,335}→co00_01 104`、`{1,336}→107`、`{1,337}→105`、`{1,338}→106`。表中 slot 由根位移方向决定，action 仅作键。
3. `StartNativeImpact(Size, Direction)` 新增方向参数；`HandleDamaged` 用 `DamageInstigator` 相对角色的前/右点积判定方向；重入 pending 时同时保存方向。
4. 构造函数把 `DamageSource/A_co00_01_104..107` 装入 `NativeSourceSequences`（键 `co00_01_%03d`）。
5. 受击不再按 `bSheathed` 分支，统一使用 Common bank；控制状态与击飞向量仍由 `Size` 决定。

失败处理：任一片段缺失、骨架不符或 `MotionPosition` 失败时 `StartNativeSource` 返回 false，沿用现有 `InterruptMove` 路径，不静默回退到 STEP 片段。

## 接口与数据迁移

| 接口 ID / 路径 | 当前行为/值 | 目标行为/值 | 调用方/蓝图影响 | 迁移顺序 |
| --- | --- | --- | --- | --- |
| `AMHWICharacter::StartNativeImpact` | `(EMHWIImpactSize)`，按持刀状态选 STEP | `(EMHWIImpactSize, int32 Direction=0)`，统一 DAMAGE_S | 仅 C++ 内部调用；`HandleDamaged` 与 pending 分支 | 先改签名再改调用 |
| `MHWI::Native::SourceBindings` | `{1,103/110/115}`、`{3,30/31/32}` → STEP | 新增 `{1,335..338}` → `co00_01` DAMAGE_S | `GetSourceBinding` 全局查表 | 绑定先于运行时 |
| `NativeSourceSequences` | 仅 `w03_00_*`、`co00_00_*` | 增 `co00_01_104..107` | 构造期软加载 | 与绑定同批 |

旧 STEP 绑定保留在表中（拔刀 STEP 等仍可能被其他路径使用），但受击运行时不再引用；不得删除未经核查的旧条目。

## 实施步骤与依赖

1. 修改 `MHWILinkAnimation.cpp`、`MHWINativeSources.cpp`、`MHWIR06SourceData.inl`、`MHWICharacter.h/.cpp`、`MHWICharacterNativeSources.cpp`。
2. 用 `-NoUBA` 构建 `IntroCppEditor Win64 Development`。
3. 启动 UE 5.8，确认 `Saved/UE_MCP_Bridge/port.json`。
4. 在 `L_RathianBasic` 用四招分别触发四方向受击，跑 PIE 报告。
5. 更新验证脚本的 bank 分支与断言，保留旧报告不改写。

## 验证计划

| 场景 | 方法/命令 | 期望结果 | 覆盖边界 |
| --- | --- | --- | --- |
| 正面小咬 | PIE，玩家面向怪物 | bank=`co00_01`，body=104，actor 后退 | 仅短受击 |
| 背后来击 | PIE，背对怪物 | body=107，actor 前冲 | 仅短受击 |
| 左侧来击 | PIE，怪物在左 | body=105，actor 右移 | 仅短受击 |
| 右侧来击 | PIE，怪物在右 | body=106，actor 左移 | 仅短受击 |
| 骨姿一致 | 逐帧对比源片段 | 相对旋转平均误差 <12°，脊椎变化 ≥2 骨 | 采样帧非全帧 |
| 恢复 | 受击结束后 | 控制状态回 None，可再出招 | 不含倒地链 |

## 风险与回退

- 方向映射依赖源坐标前向 `+Z` 的推断；PIE 位移方向不符时只调整绑定表 slot，不改代码结构。
- 受击统一走 Common 会改变拔刀状态的旧表现；旧 STEP 绑定仍在表中，可按记录回退。
- 动态 Montage 每次重建，无资产写入；回退只需还原 5 个源码文件并重新编译。
- `A_co00_01_007` 未接入，不存在"半倒地"状态跳变。

## 文档同步清单

- `Docs/Systems/MHWI-LongSword.md` 受击段
- `Docs/Known-Issues.md` R-ANIM-014 / 新增受击条目
- `Docs/Reference/MHWI-LongSword-Evidence.md` 受击证据小节
- `Docs/Reference/modules.json` 如新增源文件
- `Docs/Changes/README.md` 与 `CHG-20261116-001`
