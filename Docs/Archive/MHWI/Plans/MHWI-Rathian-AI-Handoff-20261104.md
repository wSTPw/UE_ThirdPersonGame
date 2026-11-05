# 交接：MHWI 雌火龙还原项目（给下一个 AI）

- 日期：2026-11-04。
- 读者：**接手本项目的下一个 AI 或工程师**。本文自包含，不需要读历史对话。
- 性质：现状交接。文中每条"已证/候选/未解"都对应可复查的文件，不含推测。

---

## 0. 一分钟摘要

**2026-11-05 只读取证增补（优先于下文旧统计）**：用户已暂缓Sandbox修复；继续现有固定输入取证，不启动原作/UE、不改玩法代码。见[首链审查与证据台账](../Reference/MHWI-Rathian-FirstChain-Audit-20261105.md)。旧动作表导出记录起点错位，“344条完整name↔id↔vtable注册表已闭合”口径撤回；新候选布局下BITE=83、BITE_NO_BLEND=84，em001表285/285与固定维护方表一致，且新增表指针getter/原生注册循环字段支持；THK动作查找/启动及caller怪物归属仍开放。最小受控入口THK55/n200先补0x70、0x16和控制流；29根键/131样本已独立匹配，COL实际含三UID，时钟/原位资产/命中授权未闭合。下一步优先THK动作查找/启动消费者与注册caller对象归属，不以全58类条件审计或Sandbox就绪作只读前提。DevFlow冻结任务仍PREPARED、模型调用0；未执行候选。

**2026-11-04 DevFlow接手补充**：[首任务](PLAN-20261104-001-devflow-thk-condition-audit.md)已到PREPARED，doctor通过、8组验收冻结；尚缺真实隔离执行环境，模型调用0，未完成里程碑1。只读发现旧参数摘要截断及fexty重复选择器；另发现Approx当前AnimBP模式与SetAnimation接口不匹配，记录R-DATA-005/R-ANIM-012。以下11-04编译记录保留原范围，不当作播放运行已验。

**这个项目在做什么**：在 UE5.8 C++ 项目 IntroCpp 里，用 MHWI（怪物猎人：世界）原作 em001 雌火龙的真实数据、真实动画、真实动作链，还原一场"下位单人雌火龙"战斗。

**当前处于什么阶段**：数据侧基本到手（数值素材、848条动画、105个THK解析资格；旧344条完整动作表结论已撤回，新布局下em001的285项与固定维护方表一致、注册字段有原生静态支持，THK动作启动/对象归属待证），**行为语义（THK 条件函数）只到"社区命名候选覆盖 81.5%"这一步，验证为 0**。同时存在一条**近似可玩线（B1）**已代码落地并在 UE5.8 编译通过，但 PIE 实战验收尚未完成。

**你接手后最该做的第一件事**：读第 2 节（规矩）和第 7 节（阻塞），然后执行第 8 节的里程碑 1 与 2——这两项不需要用户授权、不需要开原作、不碰任何未提交代码，做完就能把"取证"从候选推到可验证状态。

**红线**：不得把社区命名当已证；不得把近似层行为写成"还原了雌火龙"；不得覆盖工作区里用户未提交的资产。

---

## 1. 环境与工程事实

| 项 | 值 |
| --- | --- |
| 引擎版本 | **UE 5.8**（`E:/UE/UE_5.8`）。所有结论只对该版本成立，换版本需重验 |
| 工程根 | `E:/Unreal Projects/IntorCpp`（路径含空格，命令必须加引号） |
| 实际编译源码 | `Source/`（`C++ Source/` 是参考副本，**不是** UBT 编译入口） |
| 编辑器 Target | `IntroCppEditor` |
| 待还原对象 | 雌火龙 em001/00，**下位 LR，单人**（首验收 profile） |
| 主机 | Windows，用户名含空格（`Butter cookies`），Shell 可能是 bash 或 PowerShell |

**可用的构建命令**（务必带 `-NoUBA`，原因见下）：

```powershell
& 'E:/UE/UE_5.8/Engine/Build/BatchFiles/Build.bat' IntroCppEditor Win64 Development `
  '-Project=E:/Unreal Projects/IntorCpp/IntroCpp.uproject' -WaitMutex -NoHotReloadFromIDE -NoUBA
```

**本机特有的两个构建坑**（已排查确认，不是项目代码问题）：

1. **UBA 存储服务写损坏**：不带 `-NoUBA` 时会出现 LNK1201（无法写 PDB）/ LNK1136（库损坏），且 UBT 日志可能**完全没有任何诊断输出**（静默失败）。带 `-NoUBA` 即正常。
2. **陈旧链接产物**：换批次构建前若出现莫名 LNK 错误，删掉下面四个再重建，并先杀 `mspdbsrv`：
   - `Binaries/Win64/UnrealEditor-IntroCpp.{dll,pdb,exp}`
   - `Intermediate/Build/Win64/x64/UnrealEditor/Development/IntroCpp/UnrealEditor-IntroCpp.lib`

**UE5.8 API 差异备忘**（编译时踩过，别照旧版教程写）：

| 旧写法 | 5.8 正确写法 | 依据 |
| --- | --- | --- |
| `SkinnedMeshComp->bUseUpdateRateOptimizations` | `bEnableUpdateRateOptimizations` | 引擎 `SkinnedMeshComponent.h`（成员已改名） |
| `SetAnimation(Seq, bLoop)` 两参 | `SetAnimation(Seq)` 单参 | 5.8 签名变更 |
| `Comp->SetPlaying(false)` | `Comp->Stop()` | `SetPlaying` 不在组件上 |
| UObject 接口类名任意 | **必须以 `I` 前缀**，如 `IMHWIRathianDecisionPolicy` | UHT 强制 |
| `TSoftObjectPtr<UAnimSequence>(TEXT("..."))` | `TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(TEXT("...")))` | 无法从字面量推导 |

---

## 2. 项目规矩（先读，违反会被用户当场纠正）

来自 `AGENTS.md` 与 `Docs/Decisions/ADR-0002-mhwi-rathian-source-runtime.md`。这几条不是建议，是这个项目的验收口径：

1. **证据五级分级**：官方机制 / 原始数据 / 原生消费者 / 运行验证 / 项目推断。写结论必须标级别。
2. **五维标注**（2026-11-03 起）：来源等级 / 验证状态（未验证·交叉一致·实验验证·原作对照通过）/ 适用范围（exe hash·怪物·任务·难度）/ 具体证据（文件 hash·字节偏移·函数地址·日志）/ 替换状态（近似·待替换·已接入·回归通过）。
3. **不得伪造完成**：`unknown` 就是 `unknown`。填 `unknown` 不是能力问题，填猜测才是事故。ADR-0002 明确把"混用上位/大师位数据冒充下位"定义为伪造完成。
4. **官方资料先行**：技术方案先查 Epic 官方文档 / 引擎源码，并给出版本与链接。但官方资料只证明"UE 能怎么做"，**不证明原作怎么做的**；忠实度主张必须另有原作数据或运行证据。
5. **先定位再修改**：动手前 `git status --short`，别覆盖用户未提交的资产；涉及蓝图/DataAsset/Montage 要核对完整 `/Game/...` 路径与父类，同名文件不等于同一资产。
6. **每次实质修改都要留记录**：`Docs/Plans/PLAN-YYYYMMDD-NNN-*`（复杂）或 `Docs/Changes/CHG-YYYYMMDD-NNN-*`（小改），并更新两个索引：
   - `Docs/Plans/README.md`
   - `Docs/Changes/README.md`
   新系统入口还要登记 `Docs/Reference/modules.json`（注意 `validation` 字段只能放命令/路径，塞说明文字会让 `check_docs.py` 报错）。
7. **文档改完必须跑**：
   ```bash
   python Scripts/Docs/check_docs.py     # 链接/索引一致性
   git diff --check                      # 空白字符
   ```
8. **不要为文档改动重新完整编译引擎**。
9. **用户的工作方式**：喜欢直接给命令/可执行结论，看到"你自己去配一下"会不满；会粘贴完整编译日志；代码质量要求高，同一处反复编译失败会明显不耐烦。所以：**提交前自己先把明显错误清掉**。

---

## 3. 两条产品线（不要混为一谈）

| 线 | 定位 | 证据资格 | 当前状态 |
| --- | --- | --- | --- |
| **忠实线**（解包/取证） | 用原作数据 + 原作 THK 决策还原 | 可宣称"还原" | 数据侧基本闭合；语义侧候选级 |
| **近似线 B1**（`PLAN-20261102-002`） | 真动画 + 真数值 + **自制决策层** | 永远只能叫"近似 profile" | 代码落地、编译通过、PIE 验收未完成 |

B1 的存在意义是：在语义闭合前先有一个能打的版本，且它的决策层做成**接口**（`IMHWIRathianDecisionPolicy`），THK 语义闭合后逐条替换为 `ThkPolicy`，执行层不动。

**已采纳的架构约束**（来自 2026-11-03 外部评审，`PLAN-20261103-001`）：

- **决策与执行必须分离**。决策器只决定"下一步做什么"，动作如何执行（动画/位移/碰撞窗/伤害事件/结束条件）由**同一套 ActionSpec** 驱动。
- **禁止两套执行逻辑**。B1 不得自己另写一套动画播放与判定——否则换忠实决策器时会把战斗系统一起推倒。
- 动作覆盖口径改为 **目标任务内可达动作覆盖率 = 已验证动作数 ÷ 实际可达动作数**，弃用"344 条全覆盖"。

---

## 4. 代码地图

### 4.1 首链（忠实线执行骨架，~1546 行 / 9 文件）

`Source/IntroCpp/MHWI/Monsters/`

| 文件 | 职责 |
| --- | --- |
| `MHWIRathianThkExecutor.{h,cpp}` | THK 指令执行器：未知 functionType **拒绝执行**（设计如此，别改成"猜一个默认值") |
| `MHWIRathianSourceMovementComponent.{h,cpp}` | 源数据驱动的位移 |
| `MHWIRathianSourceCollisionComponent.{h,cpp}` | 源 COL 攻击判定 |
| `MHWIRathianFirstChainPawn.{h,cpp}` | 首链组装（咬击链 83 / 冲撞 86-87） |
| `MHWIRathianFirstChainData.h` | 首链常量与数据结构 |

### 4.2 近似线 B1（~1172 行 / 11 文件）

`Source/IntroCpp/MHWI/Monsters/Approx/`

| 文件 | 职责 |
| --- | --- |
| `MHWIRathianApproxData.{h,cpp}` | 两个 PrimaryDataAsset：Stats（HP3000/发怒 600 · 80s · ×1.15 · ×1.05）+ Moveset（招式表，含动画软引用） |
| `MHWIRathianDecisionPolicy.h` | `IMHWIRathianDecisionPolicy` 接口（UHT 要求 I 前缀） |
| `MHWIRathianScriptedPolicy.{h,cpp}` | 手写规则：角度→转体、距离带→选招、否则接近 |
| `MHWIRathianDecisionComponent.{h,cpp}` | 决策循环 + 动画资格门 + 冷却 + `[Decision]` 日志 |
| `MHWIRathianApproxStateComponent.{h,cpp}` | 发怒累积/持续/衰减 |
| `MHWIRathianApproxPawn.{h,cpp}` | 执行侧：SingleNode 动画 + 攻击窗球扫 + 死亡闭环 + 猎人受击接口 |

**B1 已知缺陷（用户 2026-11-02 亲测反馈，部分已修、部分仍是工程夹具）**：

| 用户报的问题 | 状态 |
| --- | --- |
| 龙浮空 | 已加地面吸附（`LineTrace` 贴地），**待 PIE 复验** |
| 不会移动 | 已解阻并加位移，**移动时无迈步动画**（姿态冻结，明示的工程夹具） |
| 头不看向玩家 | 已加朝向插值，待复验 |
| 攻击动画无前后衔接 | 已用运行时 Montage + 混合处理，待复验 |
| 角色受击无反馈 | 已实现 `IMHWIContactResponse` 接口，接上猎人原生 `StartNativeImpact` 受击等级链 |

> ⚠️ **状态（2026-11-04 实测更正）**：这批五项修复在 11-02 当晚 **从未编译成功**（源文件 21:18 修改，21:21 构建日志为 `Result: Failed`，DLL 仍是 19:49 的旧版本）。11-04 已修掉 4 类错误并实测 `Result: Succeeded`（见 §4.4）。**但 PIE 验收至今一次没跑过**，别把这些修复当"已验证"。

### 4.4 2026-11-04 编译修复记录（四类错误，供后续避免重踩）

上一轮"五项修复"代码写完后构建被中断，实际从未通过编译。11-04 逐个抓错并修完，全部集中在 Approx 层：

| 错误 | 原因 | 修法 |
| --- | --- | --- |
| `C1083: 无法打开 MHWIContactResponse.h` | Approx 子目录不在 `MHWI/` 的包含搜索路径上 | 改为模块根相对写法 `#include "MHWI/MHWIContactResponse.h"`（`Build.cs` 的 `PublicIncludePaths` 含 `"IntroCpp"`） |
| `C2039: PlayAnimMontage 不是 USkeletalMeshComponent 成员` | **5.8 已移除该组件方法** | SingleNode 模式下改用 `Body->SetAnimation(Montage)`：`UAnimSingleNodeInstance::SetAnimation` 内部会注册槽位并 `RestartMontage` |
| `C2248/C2039: FAnimSegment::AnimReference 是 protected；EndPos/PlayingRate 无此成员` | 手工拼 Montage 段落在 5.8 不可行 | 改用引擎静态工厂 `UAnimMontage::CreateSlotAnimationAsDynamicMontage(Seq, Slot, 0.15f, 0.15f, 1.f, 1, 0.15f)`（`AnimMontage.h:978`） |
| `C2039: Montage_GetIsPlaying 不是 UAnimInstance 成员` | 5.8 改名 | `Anim->Montage_IsPlaying(Montage)`；配套 `Montage_GetPosition`、`Montage_Stop(0.15f, Montage)` 未变 |
| `C2065: bGroundBlockedLogged 未声明` | 漏声明成员 | 在 Pawn 头补 `bool bGroundBlockedLogged = false;` |

同时把 `RuntimeMontages` 补成 `UPROPERTY(Transient)`——运行时动态 Montage 若无 UPROPERTY 持有，二次 GC 后会悬空。


### 4.3 复现脚本（`Scripts/MHWI/`，全部带 `--self-check`）

| 脚本 | 作用 |
| --- | --- |
| `extract_rathian_thk_chain.py` | THK 链路提取（105 表 / 1795 节点 / 13015 段） |
| `extract_rathian_chain_motion.py` / `..._collision.py` | 动作 / 碰撞分支提取 |
| `correlate_rathian_first_chain_actions.py` | 5 动作 → ACTP2 → LMT → UE 动画 → COL 关联表 |
| `dump_action_registry.py` | 旧动作表转储（起点/过滤/去重有缺陷，见11-05增补；本轮未修脚本） |
| `map_thk_function_semantics.py` | fexty ↔ 本机 functionType 覆盖映射 |
| `disasm_thk_native_semantics.py` | 原生 VM 静态反汇编（载体 + 结构 + 统计） |
| `scan_thk_jump_tables.py` | 跳转表穷举扫描（**负结果**，结论见 §6.5） |
| `scan_thk_action_ctors.py` | 动作构造函数扫描（含噪声，未收敛） |
| `build_rathian_source_motion_map.py` | 848 条动画 → 源槽位映射表 |
| `rathian_damage_pipeline_stages.py` | 伤害分段结算原型（evidenced/unavailable 分离） |

---

## 5. 取证现状总账（四板块）

数据来源：`Docs/Reference/MHWI-Rathian-Completeness-Check-20261102.md`（编号体系 BEH/NUM/ANIM/AV 均出自此页，改状态请改那里，别另开一套）。

### 5.1 行为逻辑

| 编号 | 状态 | 实质 |
| --- | --- | --- |
| **BEH-01 条件语义** | ⚠️ **候选 81.5%，验证 0** | 58 类条件中 27 类有社区命名（1786/2191 次使用）；参数形态自洽；**未做任何运行验证**。31 类未命名（405 次），最大洞 `0x5a`（186 次，参数 [4,30,10,32] 像状态/区域 ID） |
| BEH-02 动作注册表 | ⚠️ 旧导出闭合口径撤回 | 11-05复核起点错位；新候选布局使BITE=83，em001表285/285与固定维护方dump一致；表getter/字段注册已有原生静态支持，THK动作查找/启动和对象归属仍开放，见顶部增补 |
| BEH-03 LR 资格 | ⚠️ 有路线、清单未生成 | `0xB8 = current_quest().is_rank(LR/HR/MR/AT)` 已定位，可从 THK 等级门控反推下位可达动作集 |
| BEH-04 同帧优先级 | ❌ 未动 | 无原作证据 |
| BEH-05 其余链路 | ❌ 未动 | 105 THK 中只提了咬击链 + 冲撞分支 |

### 5.2 数值

| 编号 | 状态 |
| --- | --- |
| 基础数值（HP 3000 / 12 组肉质 / 7 组硬直 / 发怒 / 疲劳 / 异常 / 陷阱 / 捕获） | ✅ 已证（本机解析） |
| **NUM-03 部位名映射** | ✅ **唯一真正闭合项**：本机 12 行肉质表与 monsterhunterwiki 逐行一致（行 0=Head…行 11=MR Tail，MR Wings 21/21/45 精确匹配）= cross-verified |
| NUM-01 任务倍率 | ❌ 未落表（Kiranico 每个任务有 HP/攻击倍率，可直接钉死一个 LR 任务） |
| NUM-02 伤害公式 | ❌ 未闭合（乘法顺序/上限/逐段取整全未知） |
| NUM-04 PBC 破坏耐久 | ❌ 未解（2006/2007 语义未知；Sever=300 ≠ 任务最终阈值） |
| NUM-05 气绝三套语义 | ❌ 未定（Stun / Dizziness / Concussion 不得合并） |
| NUM-06 断尾后毒 / 免疫递增 | ❌ 未取证 |
| NUM-07 分段结算原型 | ⚠️ 有原型，`overall_status=partial-unavailable`（斩味/技能/任务倍率/取整显式跳过，未填默认值） |

### 5.3 动画与模型

- ✅ 848 条 AnimSequence + 本体 `SK_EM001_Body`（142 骨/4 材质槽）+ 独立尾巴 `SK_EM001_Tail`（3 骨）+ 4 材质 12 贴图，全部导入并读回验证。
- ⚠️ ANIM-01 映射表首版已生成（848 条），**qualification 全部 unknown**（资产身份验证 ≠ 战斗招式资格）。
- ❌ ANIM-02 播放层（ABP/Montage）、ANIM-03 破坏网格映射、ANIM-04 `_fs` 叠加层语义、ANIM-05 染色/毛发/LOD、ANIM-06 逐帧对照——均未做。

### 5.4 音效与特效（四板块最薄）

- ⚠️ 73 个 raw 文件已清点（声音 8 / VFX 52 / 任务区域 13，SHA256 全部一致），扫出 395 个事件名**候选**（未解语义），映射表骨架已建（8 类必需事件仍 unknown）。
- ❌ AV-03 NBNK 未解码（候选工具 `wwiseutil`，已核实存在）；AV-04 EFX 未解码（`MHW-EFX-Editor` **未独立核实**）；AV-05 UE 侧零资产；AV-06 镜头震动/hit stop 无证据。

---

## 6. 五个已实锤的技术发现（省你几天弯路，别重推）

### 6.1 锁定的"VM 地址"在解包后的 `.text` 镜像里，不在 exe 文件

- 游戏：`F:/PCprogram/Steam/steamapps/common/Monster Hunter World/MonsterHunterWorld.exe`
  sha256 `c2ebbbd2c49f216d484e31a5219bed419eb1e5e7d206d02cba040a3ab79d90ea`（~84 MB，无壳无混淆）
- **真正的代码镜像是** `Saved/MHWIRestoration/B05-20261024/analysis-text.bin`（48,304,640 B，sha256 `9b48a8490df702ba9dc1cb95ffd387358ae2a639aa9675ad90719bd997124ebe`），VA = `0x140001000 + offset`
- 直接对 exe 文件偏移反汇编 → **乱码**。原因：exe 磁盘布局与解包后 .text 不同。**别重复这个错误。**
- 关键地址：`vm_tick=0x1423fe8d0`、`condition_evaluator=0x1423fc990`（实为 30 字节守卫小函数，**不是**分发器）、`context_setup=0x1423fd1a0`、`name_lookup=0x142400150`、`registrar=0x14216ed60`

### 6.2 THK 段字段偏移（格式侧铁证）

128 字节段：`functionType @+8 (int32)`、`parameter1 @+12`、`parameter2 @+32`、`actionID @+76`。
来源：Leviathon `common/thk.py` 定义 + 本机字节互证。

### 6.3 原生动作注册表布局（BEH-02 的核心产出）

- 条目 **32 字节**：`{name_ptr, runtime_id, vtable, 0}`
- 共 **344 条**，id 范围 10~212，名字形如 `ACTION::BITE`
- **exe 内是多张分系统注册表**（地面战/飞行/气球/骑乘各一套 ID 序列）
- ⚠️ **因此维护者历史 ActionDumps 的编号不是运行时命名空间**：BITE dump 83 / 注册表 84、DASH_BITE2 86/87、ROLLING_TAIL_ATTACK2_L 75/**101**，无统一偏移
- 运动编码解码算法在消费端指令级实证：`slot = packed & 0x1FF`、`bank = (packed >> 12) & 0xF`
- 未闭合：注册表 id ↔ motion 编码的桥接（`.data` 的 vtable 是运行时填充，磁盘上为空，静态拿不到）

### 6.4 条件函数语义有现成的社区映射表（本地已有）

- `Saved/MHWI-Rathian-FirstChain/Leviathon/Leviathon-1e647f08.../common/default.fexty`（144 行）
- 覆盖：`0x6`=dist3d≤p1、`0x8`=dist2d≤p1、`0x16`=angle_2d_cw、`0x1E`=enraged、`0x1F`=fatigued、`0x70`=flying、`0xB8`=is_rank(LR/HR/MR/AT)、`0x76`=part(p1).is_broken(p2)、`0x2C`=hp_percent…
- **这是候选映射，不是已证语义**。升级必须走参数形态逐项校验 + 原作受控观测。

### 6.5 两个"负结果"（有价值，别重跑）

1. **functionType 不走编译期跳转表**：全 .text 四种编码形式穷举 + 2857 个跳转站点解析，均未发现对应表。分发走**运行时注册的对象/字符串注册表 + 虚调用**（`name_lookup` 是字符串注册表遍历器可佐证）。表述请收敛为"在已检查的编码方式与代码范围内未发现"，不要宣称"绝对不存在"。
2. **数据侧数值匹配无法独立闭合语义**：60 个 functionType 中 11 个参数命中已知数值，但全是巧合级重叠（如 `0x0` 的参数 30/70/80 对上捕获 30%/疲劳 70s/发怒 80s），不能据此命名。

---

## 7. 当前阻塞（3 项）与需用户拍板（2 项）

**技术阻塞**：

| # | 阻塞 | 现状与出路 |
| --- | --- | --- |
| 1 | 条件语义到"候选"为止 | 静态路线已到边界（跳转表不存在、描述符运行时填充）。出路：①本机做参数形态逐项校验（可立刻做）②受控运行观测（需授权）③Ghidra 类型恢复（3~6 GB / 1~2 会话，70~85% 成功率） |
| 2 | 注册表 id ↔ motion 编码桥接 | 同上；`mhw-lmt-engine`（2026-09，FSM 动作号→候选 LMT 槽位）可作候选交叉，**不可直接采信** |
| 3 | 音画解码 | NBNK 用 `wwiseutil`（已核实）；EFX 工具未核实。优先级最低——只影响"资源近似"级，不影响战斗忠实度 |

**需用户拍板**：

1. **P0 基线提交**：工作区 **147 项未提交**（含用户的太刀修改与全部项目新增）。分拣"用户已有工作 / 项目新增"属于用户决定范围，**不要擅自 `git add -A`**。
2. **原作运行授权**：任何启动原作的验证（运行时 dump / 受控观测）都必须先拿到用户明确同意。约定：离线、隔离、关闭 `nativePC` 覆盖、记录原始目录快照。

---

## 8. 下一步执行清单（按此顺序）

### 里程碑 1：条件语义三栏表（本机可做，无需授权）

1. 用 `Scripts/MHWI/map_thk_function_semantics.py` 的输出（`Tools/MHW/rathian-thk-fexty-coverage-20261103.json`）为底；
2. 对 27 类已命名项，逐类校验**参数取值范围是否与命名语义自洽**（距离类应呈连续 cm 值；角度类应是 0~360 的对；布尔类必须参数全 0；rank 类必须 0~3）；
3. 产出"**已证 / 冲突 / 未知**"三栏表，进入 `Docs/Reference/`；
4. 对 31 类未命名项按使用次数排序，`0x5a`(186) 优先，做参数聚类（[4,30,10,32] 这类整数很像枚举 ID，可与动作/区域/状态枚举对照）。

### 里程碑 2：下位可达动作清单（本机可做，无需授权）

1. 遍历 105 THK 的节点树，找出被 `0xB8`（is_rank）门控的分支；
2. 提取各分支内 emit 的 actionID；
3. 与 344 条注册表交叉（注意 §6.3 的命名空间问题，映射关系本身待核验，需标注为候选）；
4. 产出"LR 可达动作集"作为新分母，替换 344。

### 里程碑 3：BITE 的 ActionSpec + 第一份差异报告（需授权开原作）

按 `PLAN-20261103-001` §三的字段清单落表；原作侧未观测字段一律写 `unobserved`。

### 里程碑 4：B1 PIE 验收（用户操作，你给清单）

零配置验证路径（用户已被告知）：

```
打开 L_MHWI_Training → PIE → 控制台：
summon /Script/IntroCpp.MHWIRathianApproxPawn
```

关注日志前缀 `[RathianApprox][Decision]` / `[RathianApprox] hit` / `Rage ON` / `DEAD`。
回归项：太刀五项（普攻/气刃/见切/居合/登龙）+ 训练靶不受影响。

---

## 9. 高风险提示（按严重度）

1. 🔴 **147 项未提交**。首链、B1、Approx 三大块代码与 10-30 以来全部文档都在工作区里，一次误操作全没。**第一优先级是让用户确认后提交基线**。
2. 🔴 **`Saved/` 被 .gitignore 忽略**（`.gitignore:11`），而关键证据就在里面：
   - `Saved/MHWI-Rathian-FirstChain/action-registry-dump-20261102.json`（344 条注册表，BEH-02 唯一产出）
   - `Saved/MHWI-Rathian-FirstChain/THK/thk-all-raw.json`（16.8 MB，全量段数据）
   - `Saved/MHWIRestoration/B05-20261024/analysis-text.bin`（48.3 MB，反汇编唯一可用载体）
   - `Saved/.../Leviathon/.../default.fexty`（社区映射表）
   建议动作：把可归档的证据 JSON 复制到 `Tools/MHW/`（该目录已跟踪，项目已有此惯例），大二进制登记为"可再生/本地必需"并在文档留 hash。**别只留在 Saved/ 里。**
3. 🟠 **B1 腐化**：B1 是脚手架。每闭合一条 THK 语义就应替换一层手写规则；若三个月后 B1 还在自己长功能，说明主线偏了。
4. 🟠 **社区数据污染**：fexty 是社区命名，可能存在错误映射；`mhw-lmt-engine` 是 2026 新工具，版本与数据包需固定。用前一律标注来源与验证状态。
5. 🟡 **第三方注入器安全**：LuaEngine 等来自 Gitee/社区的注入器，质量与安全性无法背书。只在离线环境、用户明确授权下使用。

---

## 10. 术语表（本项目行话）

| 词 | 含义 |
| --- | --- |
| **THK** | MHWI 怪物 AI 的"思考表"文件，存的是决策程序（节点+条件+指令），不是数值。em001 有 105 个 + 2 个 thklst |
| **THK VM 语义** | 原作 exe 里解释执行 THK 指令的虚拟机，以及每条指令/条件的真实业务含义。项目缺口编号 BEH-01 |
| **fexty** | Leviathon 的 THK 函数签名/命名定义文件，社区维护，给出 condition 的候选名字 |
| **ACTP2** | 动作参数表，342 条记录 / 142 启用 / 4295 属性项 |
| **LR 资格** | 有证据地判定"哪些记录/动画/攻击真的被下位配置消费"。文件里有 ≠ 下位用，数组下标 ≠ 动作 ID。缺口编号 BEH-03 |
| **B1 / 近似 profile** | 真动画+真数值+自制决策层的产品线，永远不能宣称"还原" |
| **首链** | 第一条端到端打通的链路：THK → 动作 → 位移 → 碰撞（咬击 83 / 冲撞 86-87） |
| **ActionSpec** | 单个动作的完整定义（资格/转向/动画/位移/碰撞窗/伤害/可打断/结束），决策层与执行层的共享契约 |
| **cross-verified** | 两个独立来源一致（如本机解析 + 公开数据库），可升入忠实 profile |

---

## 11. 相关文档地图（按需要查，别全读）

| 想知道什么 | 读哪个 |
| --- | --- |
| 四板块完整性与缺口编号（BEH/NUM/ANIM/AV） | `Docs/Reference/MHWI-Rathian-Completeness-Check-20261102.md` |
| 对外评审用自包含简报 | `Docs/Reference/MHWI-Rathian-Review-Brief-20261103.md` |
| 当前技术路线与阶段门（P0–P4） | `Docs/Plans/PLAN-20261103-001-rathian-review-adoption.md` |
| THK VM 语义三条恢复路线与复现命令 | `Docs/Plans/MHWI-Rathian-VM-Semantics-Handoff.md` |
| B1 近似线方案 | `Docs/Plans/PLAN-20261102-002-rathian-approximate-profile.md` |
| 下位数值全套（HP/肉质/硬直/发怒/异常） | `Docs/Reference/MHWI-Rathian-LR-Data-20261030.md` |
| 动画库现状（848 条） | `Docs/Systems/MHWI-Rathian-Animations.md` |
| 验收口径（什么算"还原"） | `Docs/Decisions/ADR-0002-mhwi-rathian-source-runtime.md` |
| 变更历史 | `Docs/Changes/README.md`（CHG-20261030-001 起） |

---

## 12. 一句话给接手者

**数据已经到手，代码已经能跑，缺的是"看懂原作的决策"和"把候选变成已证"。别再从零逆向，先复用 fexty；别再追 344 条全覆盖，先定下位可达集；别相信任何没跑过的验收。**
