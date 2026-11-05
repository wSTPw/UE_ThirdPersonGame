# PLAN-20261026-006：R06 / R28 / R30 动画全集覆盖处理

- 状态：partial，R06确定性修复完成；R28/R30数据层与逐项处置完成，全部运行覆盖未完成
- 日期：2026-10-26
- 用户需求：逐一处理 R06、R28、R30，覆盖每个对象的全部动画；无法处理的项目注明位置和原因，最后按该顺序汇总。后续用户要求不验证后交接。
- 关联模块 / 接口 / 问题：`mhwi-longsword`；R06/R28/R30；A01/A04；R-COMBAT-012/014/016、R-ANIM-007/008；既有[R28方案](PLAN-20261026-004-mhwi-locomotion-transitions.md)与[R30方案](PLAN-20261026-005-mhwi-equipment-ik.md)。
- 实施记录：[CHG-20261027-001](../Changes/CHG-20261027-001-mhwi-animation-coverage.md)。

## 现状与目标

当前审计不是简单的“动画未导入”：

- R06 有30节点/32引用/124身份记录/26连接片段及32个新增来源片段，但武器混合门控只接受`One0=1`，全部主段候选却为0；还存在受击恢复锁、来源缓存绕过菜单、部分真实前置缺失。`node86`原图不可达，必须保留。
- R28 六候选005/006/007/008/014/015均有旧Sequence，但当前没有NativeFidelity平行资产、正式消费者或逐条语义确认；原始LMT与游戏安装当前不可用。
- R30 六条`wg03_00`内部动画资产与DA映射齐全，0–3已有选择路径，4/5的实际选择待审计；四条IK链资源与225骨链明确，但运行消费者、Profile、目标快照和ABP节点均为0，原生solver坐标/参数未闭合。

目标不是用“文件存在”冒充“全部生效”，而是让每项都有明确处置：**已接入、已验证、保留不可达、项目预览、无法处理及具体原因**。能实现且有依据的部分直接修复；不能用相似片段或伪造入口凑覆盖数。

## 范围与验收标准

| 对象 | 本批实施 | 完成边界 |
| --- | --- | --- |
| R06 | 建立32引用+32新增片段清单；修复武器`One0=0`导致的全局播放拒绝，使用明确的项目UE混合后备；恢复真实受击来源的合法续段；菜单清来源缓存并阻断内部提交；编译及代表性运行检查 | 原生武器mode0 MotionTree/request仍不冒充完成；缺真实拥有者的来源、不可达N86及R07/R24/R25/R28依赖单列 |
| R28 | 六候选逐条读回Skeleton/帧数/时长/根设置/引用；恢复可用的预览与状态事实；只把能确认项目视觉语义的片段接入过渡，保留现有两张BlendSpace与移动物理 | 不把旧Sequence自动等同于合格NativeFidelity，不按编号或header translation猜原版语义；无法确认者列精确路径 |
| R30 | 枚举六条武器内部动画所有选择来源；核对4/5；建立四链IK覆盖清单，按既有项目方案实现可量测的目标/Profile/ABP层或记录阻断 | 原生solver、CTM、极向/限位不猜；TwoBoneIK只称项目适配；不能用六条映射代替实际播放 |

## 技术方案

1. **先修全局可播放性。** 保留`ResolveDirectBlendSettings`对原生合格路径的严格判断；在`ApplyNativeBlend`增加武器`One0=0`的显式ProjectAdaptation后备，以MBD插值帧/60作为项目UE BlendIn秒数，不启用原生代理混合或尾淡出。覆盖直接主段、连接前段、连接后主段和来源动画四个调用点。
2. **恢复来源专用输入。** `RequestInput`先把真实`NativeSourceMontage`交给来源分派，再执行普通Flinch锁；`RequestNativeSourceInput`仅接受该来源`ResolveNativeSourceInput`已有的合法出口，Impact允许Flinch状态，其他锁仍拒绝。保留真实身份到合法续段或自然结束。
3. **菜单一致性。** `SetInputBlocked(true`同时清`NativeSourceInput`；`StartResolvedMove`拒绝阻断期内部提交。不借机放开所有受击命令或改变手柄输入。
4. **逐项覆盖审计。** 新增只读审计脚本，汇总资产、CDO/DA引用、选择值、混合门控、可达性和运行结果；运行结果必须来自实际PIE，不能由静态检查自动写成已验证。
5. **R28先证据后状态机。** 复用现有`bInAir/bInAction/bDead`，只补真实移动事实。六候选经UE读回和预览后再决定正式引用；无法重放原始LMT资格链时明确降级为旧资产项目预览。
6. **R30分层。** 保留`FMHWIWeaponAttachmentRuntime`和六条SingleNode武器动画；IK使用独立项目Profile、游戏线程目标快照和ABP双骨节点，不在动画线程访问Actor，不把原`.ik`未知字段灌入UE配置。先双手后双脚，Montage/空中/死亡门控清晰。

## 接口与数据迁移

| 接口 / 路径 | 当前行为/值 | 目标行为/值 | 调用方/蓝图影响 | 迁移顺序 |
| --- | --- | --- | --- | --- |
| `ApplyNativeBlend` | 武器`One0!=1`直接失败 | 合格原生路径不变；mode0走显式项目UE混合后备 | 四个R06调用点恢复可播放，原生mode0语义仍开放 | 源码→构建→代表性PIE |
| `RequestInput` / `RequestNativeSourceInput` | Flinch全锁，真实恢复不可达 | 仅真实来源合法出口可在Flinch中排队 | 普通动作和手柄逻辑不变 | 先过滤合法出口，再测恢复 |
| `SetInputBlocked` / `StartResolvedMove` | 来源缓存和内部提交可绕过 | 清来源缓存，内部提交同样阻断 | A04局部关闭；Move/Look完整菜单另列 | 同步修改 |
| `UMHWIAnimInstance` | Speed/Direction等现有变量 | 只补R28/R30需要的只读事实/目标快照 | ABP读取；不改CharacterMovement | 先反射，再ABP |
| `/Game/MHWI/Blueprints/ABP_MHWI_Hunter` | 两张BlendSpace→DefaultSlot | 仅接入经核验的过渡/项目IK | 修改前单独备份并读回 | 资格→图修改→编译→PIE |

## 实施步骤与依赖

1. 保存本方案及受影响源码/资产哈希，建立三项全集清单。
2. 实施R06混合/A01/A04修复，编译并做针对性运行检查。
3. R28六候选读回、预览、项目语义判定；接入可确认项并记录不可处理项。
4. R30六条选择覆盖审计及四链项目IK实施；若原生或编辑器API阻断，保留具体位置与原因。
5. 运行相称验证，更新台账、系统现状、接口、已知问题、模块索引和CHG；按R06/R28/R30顺序汇总。

## 验证计划

| 场景 | 方法/命令 | 期望结果 | 覆盖边界 |
| --- | --- | --- | --- |
| 静态全集 | 新增覆盖审计脚本 | 每项有ID、资产、引用、状态、原因；30/32/124/26与32新增、R28六条、R30六条+四链无遗漏 | 不自动等同运行通过 |
| R06构建与混合 | UE5.8 `IntroCppEditor Win64 Development -NoUBA` | 编译通过；mode0不再在播放前拒绝 | 不证明原生mode0 |
| R06来源/菜单 | 真实PIE来源测试 | 合法受击恢复可提交，非法命令仍拒绝；菜单后无缓存续段 | 代表性来源，不冒充32引用全运行 |
| R28六候选 | UE资产读回/预览及状态PIE | 每条有骨架/时长/根/语义/引用结论；已接片段不卡态、不重复触发 | 原LMT缺失时明确资格降级 |
| R30选择与IK | DA事件审计、ABP读回、项目IK PIE | 0..5选择有结论；四链节点/目标/门控正确，误差和未测视角记录 | TwoBoneIK项目适配，不是原生solver |
| 文档 | `check_docs.py`、`git diff --check` | 新链接有效；失败逐项记录 | 历史测试不冒充本批执行 |

## 风险与回退

- mode0后备若误用原生代理会形成双重混合；后备只使用UE BlendIn并令NativeBlendFrames为负，不启用尾淡出。
- 受击恢复若直接放开`IsGestureLocked`会允许非法命令；必须按来源合法出口过滤。
- R28语义不清的候选不得为凑数接入；R30 IK目标可能因组件更新顺序滞后一帧，不能累积纠偏。
- 修改前源码备份在`Saved/MHWIRestoration/B19-20261026/Backup`；ABP/资产修改前另存哈希和副本。回退按本批文件逐项恢复，不影响B14/B15/B16。

## 文档同步清单

完成后更新`Docs/Systems/MHWI-LongSword.md`、`Docs/Interfaces.md`（如反射变化）、`Docs/Plans/MHWI-Restoration-Progress.md`、`Docs/Plans/MHWI-Connector-Progress.md`、`Docs/Known-Issues.md`、`Docs/Reference/modules.json`、方案/变更索引、工作日志和`CHG-20261026-011-mhwi-animation-coverage.md`。所有未运行/未证项保持明确状态。
