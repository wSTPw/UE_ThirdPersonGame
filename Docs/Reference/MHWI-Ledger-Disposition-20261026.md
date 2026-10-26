# MHWI 台账全量处置矩阵（B12）

- 日期：2026-10-26。
- 执行者：WorkBuddy 代理会话（DeepSeek-V4.1-Flash），B12 批次。
- 输入：`Docs/Plans/MHWI-Restoration-Progress.md` 的 35 项；[33项审查](MHWI-Restoration-Review.md)保留修复前快照。
- 方法：每个条目统一走「固定源指纹复核 → 一手字段/FSM 证据 → 当前代码/资产落点 → 可否实施判定 → 实施或记录缺口」。证据全部来自 `Tools/MHW/native-reference-sources.json` 固定的 COL/W03P/FSM/LMT，不使用猜测值。
- 边界：本批完成一次增量编译（仅证明可构建/UHT 通过），**没有运行 PIE、自动化或行为矩阵**；因此“开发完成/部分完成”不等于行为通过。
- 并发：B11 及更早批次属于其他协作者；本批使用独立目录 `Saved/MHWIRestoration/B12-20261026/`，未改写他批证据。

## 一、总量

| 状态 | 数量 | 条目 |
| --- | ---: | --- |
| 已验证（保持） | 6 | R02、R03、R12、R17、R34、R35 |
| 开发完成；未运行 | 2 | R04、R06 |
| 部分完成（本轮有实施或证据推进） | 16 | R01、R05、R08、R11、R14、R15、R16、R22、R24、R25、R26、R27、R28、R31、R32、R33 |
| 取证中（源数据不足，不写猜测值） | 10 | R07、R09、R10、R13、R18、R19、R20、R21、R29、R30 |
| 待开发（契约已设计，未改接口） | 1 | R23 |

## 二、逐项处置

| ID | 本轮处理 | 落点/证据 | 状态 | 遗留/下一步 |
| --- | --- | --- | --- | --- |
| R01 原版设备/组合输入 | 新增 `bOriginalInputPreset`（默认关）。手柄 RT=气刃修饰键；RT+Y→登龙突刺、RT+B→见切、Y+B→袈裟；同帧边沿先聚合再解析，单手势不产生两条命令。键鼠快捷位不变。 | `MHWICharacter.h/.cpp`；FSM 条件变量 346 个叶子全为布尔，`R` 是保持态；`R+△`/`R+○`/`△+○` 是输入层合成状态 | 部分完成；未运行 | 全局仲裁顺序、按下/松开时长、RT+A 无源；跨帧手势窗仍需 PIE 标定 |
| R02 新增B无限循环 | 未改。 | B01/B02 已删除普通突刺与插入突刺的 B 循环 | 已验证 | 保持 |
| R03 袈裟A出口 | 未改。 | B01 三袈裟 A→突刺已保存并通过 | 已验证 | 连接/精确窗属 R06/R07 |
| R04 见切后续 | 未改；复核 B11 三条原边（△→11、○→4、R+△→45）均存在。 | [B11 记录](../Changes/CHG-20261026-001-mhwi-foresight-exits.md)；FSM node28 七条边 | 开发完成；未运行 | 精确输入位仍属 R07 |
| R05 居合气刃额外出口 | 复核 node65 唯一显式出口为 `R+△→node76(357/367)→node45`（SpiritThrust，不是普通突刺）；`Spirit→SpiritIII` 与 `SpecialSheathe→SpecialSheathe` 无源依据，已标记 `ProjectAdaptation`，原版预设跳过、快捷预设保留。 | DA `IaiSpiritSlash.routes`；`MHWICharacter.cpp ResolveInput` | 部分完成 | 成功反击前置、公共取消边界仍未解码 |
| R06 连接过程 | 未新增实现；B10 代码本轮编译通过（UHT/C++），但未运行。 | [B10 交付](MHWI-R06-Remaining-Development.md) | 开发完成；已编译，未运行 | 32 连接逐条行为、Phase/混合/时钟仍需下一阶段 |
| R07 精确取消窗 | 证据裁决：本地 `PlMotionInput` 的 8×u32 flag/trigger 位义与 transition 求值器未解码；不改任何窗口。 | `native_semantics_evidence.py`；`transition_calibration.json` 明写 `original_game_exact_frames=false` | 取证中 | 需原生求值器跟踪；现有窗全部保留“项目调校”标签 |
| R08 输入缓存 | 原版预设下同帧多条边先聚合再按手势解析，消除“后输入覆盖前输入”的同帧歧义；按住状态用 Started/Completed 维护。跨帧仍用现有单槽 0.3 s。 | `ResolveFrameInputEdges`；`MHWICharacter.h` | 部分完成 | 跨帧队列、来源优先级、逐条过期未实施；0.3 s 仍是项目常量 |
| R09 转向/方向 | 证据裁决：W03P 425 字段无角度索引，LMT 无 `mAngleInterpolationProgress`；25°/0.12 s/360°/s/0.2 死区全部保留项目调校。 | `MHWIMovesetData.h` 转向字段；`ApplyTurnWindows` | 取证中 | 需原始角度参数或可追溯录像标定 |
| R10 Q自然衰减 | 证据裁决：`Spirit_Gauge_Decay=0.05`（0x49d）确定，但周期、计时域、攻击重置、回气抑制均无源字段；ICE 的“6 秒/5%”仅低置信外部佐证，不实施。 | W03P 0x49d；COL `Energy_Gen` 无负值；FSM 无衰减操作 | 取证中 | 需原生消费者或运行时 Q 采样；禁止把 0.05 当每秒 5% |
| R11 十秒保护消费者 | 停止把 `Gauge_No_Decay_Time_after_Spirit_Gauge_Upgrade=10` 加到颜色 T：回旋升色不再设置 T 暂停；10 s 字段保留在 DA，供 R10 的 Q 抑制使用。 | W03P 0x51d；`MHWICharacter.cpp SetSpiritLevel/SweepWindow` | 部分完成 | Q 抑制起算/刷新/叠加未证；HUD 的暂停读数会归零，UI 批次需同步文案 |
| R12 气刃踏步cost | 未改。 | B02 已验证 18/28、强化 20、回 10 | 已验证 | 保持 |
| R13 回旋清余槽 | 证据裁决：FSM node5 只有 `ActionNo=69`、无边、无子簇；COL #19 无清槽字段；启动/命中/结束/打断四个提交点均无一手证据。 | `wp03_action.fsm` node5；`wp03.col` #19 | 取证中 | 需 ActionNo 69 实现或空挥/命中/打断四情形运行记录 |
| R14 各招回槽 | 复核 32 招 × 59 条近战记录：18 行一致、1 招项目调校、6 条记录未绑定、7 招无对应记录、33 条记录未被消费。新增 #28 的 DA 绑定（见 R15）；不把空中/滑坡/骑乘记录塞进现有招。 | [B12 覆盖矩阵](../Changes/CHG-20261026-002-mhwi-ledger-sweep.md)；`moveset_mapping.json` | 部分完成 | 未调度动作按 R25/R26/R16 归口；公共回槽修正未知 |
| R15 普通/多段MV | 补齐 `SpiritHelmBreaker` 的空中首击：COL #28 MV=126，源碰撞帧 25–112，写入 0.4167–1.8667 s，`ColRecordIndex=28`；登龙七段 `HelmLand` 窗口不变。 | `wp03.col` #28；DA `SpiritHelmBreaker.damage_windows` | 部分完成 | 其余未调度记录、部位/属性/完整伤害仍开放 |
| R16 四色居合 | shell 16 条分组闭合：白 8/9/10=10、黄 4/5/6=15、红 0/1/2=25；居合二击 12/13/14=86/72/55；melee 51/52/53 的“削除：居合気刃2”同值记录证明该段从 melee 迁到 shell。 | `object.col`；`wp03.col` #46–53；W03P 0.5/1.3 | 部分完成 | 0.5 s 起算、第二击目标获取、1.3 叠加方式未证；追加命中未实施 |
| R17 登龙颜色基值 | 未改；复核白/黄/红 10/15/25 七段与 COL/shell 分组一致。 | B01 已验证；shell 8/9/10、4/5/6、0/1/2 | 已验证 | 126 空中首击属 R15 新增，不替代七段颜色基值 |
| R18 刀刃/部位空间 | B19新增静态关联：39/39条太刀`CollisionTimelineObject`动作轨都能通过`NodeID[0]`匹配`wp03.col`的`timeline_uid`；55个表头引用涉及52条攻击记录和13组CLGM参数。续查将`CLND`类型1追到`cCollNodePl`节点工厂及读取函数；这不是几何形状映射。固定版引擎另有`nCollision::cGeometryJoint`类型和构造器，但未连到太刀`CLGM`组。指定安装覆盖与归档几何/UID相同，仅52条记录的`Flinch_Value`不同。原作数据当前不可直接作为忠实刀刃碰撞实现依据；具体形状、骨骼空间、运行时消费者及肉质选择仍未闭合。 | [B19武器碰撞取证](MHWI-Weapon-Collision-Evidence-20261026.md)；[CHG-20261027-001](../Changes/CHG-20261027-001-mhwi-collision-loader-trace.md)；`SweepWindow`；`weapon_attachment.json` | 取证中 | 继续复用原作数据需解码CLGM并证明几何/骨骼消费者；当前实现方向应转项目自有武器/骨骼扫掠。运行时部位命中需记录当前安装覆盖。 |
| R19 延迟shell | 确认 W03P：首击 0.4、间隔 0.05、末击 0.05、上限 7、红刃 0.5；当前七窗是项目自造 3–15 帧标记。未建独立 pending shell；126 首击已由 R15 补，0.4 hit lag 由 R31 消费。 | W03P 0x5F8–0x60C；`author_assets.py` 七窗 | 取证中 | 0.4/0.05 起算、Land 蒙太奇时长、红刃 0.5 语义未证 |
| R20 耐力 | 源字段定位：`Stamina_Max_Value=150`、`Stamina_Initial_Value=100`、`Stamina_Consumption_Dodge=25`、`LS_Counter=50`、`Evasion_0..5=13/15/17/19/22/25`；动作侧 `mStaminaParamIndex`、`mStaminaRecoveryRate`。未接入。 | `pl_param`；见 [B12 取证](../../Saved/MHWIRestoration/B12-20261026/evidence/stamina-R20-R21-R30.md) | 取证中 | 奔跑耗量、恢复延迟/速率、技能修正、50 的运行时消费者不足 |
| R21 普通回避保护 | 证据裁决：Roll 现窗 0.06–0.4 = 3.6–24 帧、长 20.4 帧；13 帧原值无起算/端点/行映射，保留项目窗并标注。 | DA `Roll`/`RollSheathed`；公共表 `Evasion_0=13` | 取证中 | 需原表行映射与起算；不得把 20.4 帧当原版 |
| R22 完整伤害管线 | 新增 `FMHWIResolvedHit`（MoveId/Window/ColRecordIndex/MV/颜色/弱斩/反击/FinalDamage）与 `GetLastResolvedHit()`；`FinalDamage` 保持原公式不变；斩味/会心/部位显式 `Unavailable`。 | `MHWIMovesetData.h`；`MHWICharacter.cpp SweepWindow` | 部分完成 | 武器攻击力、斩味倍率、肉质、会心、技能表均不在仓库 |
| R23 防御事件类型 | 证据裁决：现状 `HandleIncomingDamage(float,AActor*)` 无事件类型/攻击 ID/方向/接触类别；契约方案（kind + event + 兼容转发）与 3 处调用点已定位，未改接口。 | `IncomingDamageResponse.h`；`AttributeComponent`；`MHWICharacter` | 待开发 | 需接口/Blueprint 迁移；咆哮/风压/DOT 产生方尚不存在 |
| R24 受击/恢复/死亡 | 新增 `EMHWIControlState`（Free/Small/Medium/Large/Dead）；S/M/L 受击挂载时锁定输入并清 Pending/Helm 请求；受击结束由 `FinishMove` 回 Free；死亡置 Dead。B10 的 S/M/L 站立受击资产继续使用。 | `MHWICharacter.h/.cpp`；`MHWICharacterNativeSources.cpp` | 部分完成 | 击飞/倒地/起身/死亡动画无资产；行走/坐姿/镜像反应未做 |
| R25 射击/飞翔爪 | 证据修正：九方向强化射击**已实现**（ActionNo 104–112、源帧 36 发射）；真正缺的是拔刀投射器 node63/ActionNo 44 的 motion 绑定、弹药类型/部位/耐力、爪。 | `MHWICharacter.cpp` Slinger 分支；`MHWICharacterNativeSources.cpp FireNativeSlinger` | 部分完成 | ActionNo 44→motion 表缺失；爪无资产；不得把九方向完成当 R25 全完成 |
| R26 环境动作 | 新增 Falling 门控：非登龙、非翻滚的地面动作不能在 Falling 中启动；空中行为必须走显式分支。 | `MHWICharacter.cpp StartResolvedMove` | 部分完成 | 空中气刃/滑坡/墙/攀爬/骑乘片段与地形资产缺失 |
| R27 道具与菜单 | 新增 `SetInputBlocked(bool)`/`IsInputBlocked()`：阻断 RequestInput/StartMove，清 Pending 与 Helm 请求，供 UI/菜单在打开时调用。 | `MHWICharacter.h/.cpp` | 部分完成 | 猎人使用道具/磨刀动作、背包契约解耦未做 |
| R28 基础移动 | 证据裁决：持刀 walk/run 同用 `w03_00_004` 且 RateScale=1；ABP 无状态机；起步/转身/停步/落地片段（005/006/007/008/014/015）未进 NativeFidelity 合格库。未改资产。 | `author_assets.py`；ABP 二进制；B03 记录 | 部分完成 | 需片段资格、状态机、原版速度/姿态对照 |
| R29 特殊纳刀等待 | 证据定位：`w03_00.lmt` entry 306 的 `mWeaponMotionNo` 键 #1 frame73→3、#2 frame80→0；80 事件已进 DA，但 `EventLimit` 钳制 + 保持早退使其必然不触发；3.5 s 与 W03P 0x540 数值同源、语义未证。未实施桥接。 | `w03_00.lmt` entry306；DA `SpecialSheathe.weapon_motion_events` | 取证中 | 需等待期源时钟是否前进的一手证据；桥接版须标注 |
| R30 装配/IK | 证据裁决：四条 IK 链（`larm/rarm/lfoot/rfoot`，关节 6/7/8、10/11/12、14/15/16、18/19/20）已解码，但项目无消费者、无骨映射/求解器语义；保留 0.7 比例/0.16 s 交接拟合。 | `MHWIWeaponAttachment`；`native_parameter_sources`；ABP 无 IK 节点 | 取证中 | 需骨映射、求解器语义、多视角误差验收 |
| R31 声画/时钟 | 新增 `HitLagSeconds` 与 `PendingHitLag`：命中后冻结动作/武器表现时钟，不冻结槽/颜色计时；新增 `OnHitResolved` 广播（SourceTime/Window/ColRecordIndex）。当前仅 `SpiritHelmBreaker` 填 0.4 s。 | `MHWIMovesetData.h`；`MHWICharacter.cpp Tick/SweepWindow`；DA 窗口 | 部分完成 | 其余招 hit lag 未填；音效/刀光/相机/CMS/CSK 未做；0.10/0.12 混合保留 |
| R32 确定性重建 | 证据裁决：`author_assets.moveset()` 约 20 处写死，16 项 damage 中 12 项与现值不符、SpiritGain 统一 9/0、cost 12×5、HelmLand 7×20；`Tools/MHW`、`Scripts/MHWI`、`Docs`、`Content/MHWI` 在 git 中 0 个跟踪文件。未改生成入口。 | `author_assets.py`；git 跟踪清单 | 部分完成 | 需 base←ledger + overlay 的确定性入口；建议先把关键目录纳入版本控制 |
| R33 独立还原基准 | 新增 `Scripts/MHWI/verify_native_baseline.py`：51 项静态断言，覆盖 COL #6/#15/#17/#19/#18/#23/#24/#25/#28/#43/#44/#46–49、shell 三色/居合二击、W03P 关键字、FSM node65 单边，以及 DA 的 126 窗口/居合适配位。运行结果 PASS。 | `Scripts/MHWI/verify_native_baseline.py`；`B12/authored.json` | 部分完成 | 未覆盖 PIE/行为矩阵；期望只覆盖本轮相关值，不是完整还原率 |
| R34 气刃踏步插入出口 | 未改。 | B02 已验证 | 已验证 | 保持 |
| R35 插入上挑R后备 | 未改。 | B02 已验证 | 已验证 | 保持 |

## 三、本轮实际改动清单

### 代码

| 文件 | 改动 |
| --- | --- |
| `Source/IntroCpp/MHWI/MHWIMovesetData.h` | 窗口新增 `ColRecordIndex`、`HitLagSeconds`；路线新增 `ProjectAdaptation`；新增 `EMHWIDamageStageStatus`、`FMHWIResolvedHit` |
| `Source/IntroCpp/MHWI/MHWICharacter.h` | 新增原版输入预设、控制状态、命中结果 getter、输入阻断、受击/命中/hit-lag 状态 |
| `Source/IntroCpp/MHWI/MHWICharacter.cpp` | 原版手柄映射与同帧手势解析；R05 跳过适配路线；R11 停止延长颜色 T；R22 结构化命中；R24 控制状态；R26 Falling 门控；R27 输入阻断；R31 hit lag/事件广播 |
| `Source/IntroCpp/MHWI/MHWICharacterNativeSources.cpp` | 受击挂载时设置 S/M/L 控制状态并清缓存；受击期间拒绝输入 |

### 资产

| 资产 | 改动 | 证据 |
| --- | --- | --- |
| `/Game/MHWI/Data/DA_MHWI_LongSword` | `SpiritHelmBreaker` 新增 1 个窗口（MV126、0.4167–1.8667 s、COL #28、hit lag 0.4） | COL #28 + TIML 碰撞 25–112；磁盘 119387→125300 字节，SHA `490ab87f…`→`e09764d0…`；151 路由不变；脏包清零 |
| 同上 | `IaiSpiritSlash` 的 `SPIRIT→SpiritIII`、`SPECIAL_SHEATHE→SpecialSheathe` 标记 `ProjectAdaptation` | FSM node65 仅一条 `R+△→76` 边；两条为项目适配 |

### 脚本与证据

- `Scripts/MHWI/audit_ledger_sources.py`：统一导出 59 近战/16 shell/90 FSM/条件树/记录偏移，修正了此前 dump 的 FSM 键名与字段裁剪缺陷。
- `Scripts/MHWI/author_b12_ledger_sweep.py` + `Saved/MHWIRestoration/B12-20261026/b12_author_driver.py`：预览/保存/幂等/全字段保护/备份/读回。
- `Scripts/MHWI/verify_native_baseline.py`：51 项独立静态基准。
- `Saved/MHWIRestoration/B12-20261026/evidence/`：6 份只读取证报告与 `ledger-source-dump.json`、`w03p-fields.json`。

## 四、统一不实施原因

1. **没有消费者证据**：R10 的衰减周期/计时域、R13 的清槽提交点、R19 的 0.4/0.5 起算、R29 的等待期源时钟。字段值可读，但“何时/以什么量纲消费”没有一手证据。
2. **只有项目适配**：R07 的逐输入窗口、R08 的 0.3 s、R09 的 25°/45°/0.2、R21 的 0.06–0.4 回避窗、R28 的 180/420 速度与同用 004。保留标签，不冒称原版。
3. **缺数据表/资产**：R18 的刀刃几何与肉质、R20 的恢复/技能、R22 的攻击力/斩味/会心、R23 的事件产生方、R25 的拔刀投射器 motion 与爪、R26 的地形/空中片段、R27 的猎人道具动作、R30 的 IK 骨映射、R31 的音频/特效/相机资产。
4. **不能靠“看起来合理”补齐**：任何未列出的数值都没有写入；`FMHWIResolvedHit` 的 `Unavailable` 是唯一合法的“无数据”表达。

## 五、验证与未验证

已执行：

- 增量编译 `IntroCppEditor Win64 Development` 最终成功（约 29.6 s；含新增 UPROPERTY/USTRUCT/事件绑定）。首次链接因 UBA 残留的 0 字节 `.lib` 触发 LNK1136，清理后 `-NoUBA` 重建成功；这是文件锁/缓存问题，不是源码错误。只证明可构建，不证明行为。
- DataAsset 预览/幂等/全字段保护/保存/读回：仅 `SpiritHelmBreaker` 与 `IaiSpiritSlash` 变化，路由总数 151 不变，脏包清零。
- 关闭编辑器后重新启动、只读加载磁盘资产：32 招/151 路由；126 窗口与两条 `project_adaptation` 均存在，`HELM_BREAKER` 保持 false（`B12/disk-readback.json`）。
- `python Scripts/MHWI/verify_native_baseline.py --da Saved/MHWIRestoration/B12-20261026/authored.json`：51 项 PASS（静态源/资产期望，非 PIE）。
- `python Scripts/Docs/check_docs.py`：PASS（106 个 Markdown、885 个本地链接、12 个模块）。
- `git diff --check -- Docs Scripts Source`：退出 0；全量 `git diff --check` 因本机未安装 `git-lfs` 无法读取 `.uasset`，不是空白错误。

未执行：

- PIE、自动化、真实输入/命中/受击/派生矩阵、动画姿态/根运动对照、音频/特效/相机、低帧/地形/多部位。
- 因此 R01/R08/R11/R22/R24/R26/R27/R31 的行为仍属“开发完成/部分完成，未运行验证”。

## 六、并发与批次边界

- B11 及更早目录属其他协作者；本批未改写。
- 本轮证据与脚本只写 `Saved/MHWIRestoration/B12-20261026/` 与 `Scripts/MHWI/` 的新文件；共享 DA 仅按上述两处保存。
- 如后续协作者继续 R04/R06，请先读 [B11 记录](../Changes/CHG-20261026-001-mhwi-foresight-exits.md) 与本批记录，避免重复加边/重复加窗。

## 七、建议的下一步顺序

1. **先验证本轮改动**：PIE 检查原版预设的 RT+Y/RT+B/Y+B、受击锁定、126 首击与 0.4 hit lag、R11 颜色时长不再 +10。
2. R06/R04 的逐连接/逐窗口行为验证（B10/B11 已开发完成）。
3. R16/R19 的 shell 起算证据；R10/R13/R29 的原生消费者证据。
4. R32 的确定性生成入口与关键目录纳入 git；R33 扩展到 PIE/行为矩阵。
5. R23 的接口迁移；R25/R26/R27 的动作/地形/道具资产。
