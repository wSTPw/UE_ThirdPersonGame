# MHWI 太刀训练模组

独立训练模组：原版太刀素材 + 原版动画 + 项目自研战斗层。素材来源与解包见 [MHWI 解包数据与工具链](MHWI-Unpack-Data.md)；数值/挂接/碰撞的取证结论见 [太刀取证总账](../Reference/MHWI-LongSword-Evidence.md)。

## 一、运行入口与资产

打开 `/Game/MHWI/Maps/L_MHWI_Training` 后 Play。`DefaultGameMode` = `/Game/MHWI/Blueprints/BP_MHWI_TrainingGameMode`，默认 Pawn = `BP_MHWI_Hunter`（父类 `AMHWICharacter`），HUD 为原生 `AMHWIHUD`。原项目菜单、Ninja 角色和默认地图保留。

| 资产路径 | 用途 |
| --- | --- |
| `/Game/MHWI/Character/SK_MHWI_Hunter` | 六部件统一的 225 骨猎人；Skeleton 在同目录 |
| `/Game/MHWI/Weapons/SK_MHWI_LongSword`、`SK_MHWI_Scabbard` | 独立武器/刀鞘骨架，按角色骨挂接 |
| `/Game/MHWI/Animations/LongSword/A_w03_00_###` | 164 条有效太刀动作，保留源序号；未映射 ≠ 已接入玩法 |
| `.../NativeFidelity/LongSword/A_w03_00_###`、`.../Common/A_co00_00_###` | 平行采样库 36 段；正式 Montage 累计迁移 30 组引用 |
| `/Game/MHWI/Animations/Weapons/A_wg03_00_000..005` | swo001 独立骨架上六段内部动画，由 DA 的 `WeaponMotions` + 每招 `WeaponMotionEvents` 驱动 |
| `.../Common/A_co00_00_001`、`203`、`090`、`130` | 纳刀待机、步行、跑步、翻滚 |
| `/Game/MHWI/Blueprints/ABP_MHWI_Hunter` | 父类 `UMHWIAnimInstance`；Speed 驱动两个 BlendSpace，经 `bSheathed` 混合进 DefaultSlot |
| `/Game/MHWI/Animations/BS_MHWI_Drawn`、`BS_MHWI_Sheathed` | 基础速度混合 + 0.14 秒输入平滑 |
| `/Game/MHWI/Data/DA_MHWI_LongSword` | `UMHWIMovesetData`，32 个招式定义 |
| `/Game/MHWI/Montages/M_*` | 全身根运动 Montage；居合按气刃颜色选源动画 |
| `/Game/MHWI/Materials/M_MHWI_Surface`、`MI_*` | 18 个部件材质实例，71 张贴图；**未还原完整原版 shader** |

## 二、操作与派生

| 输入 | 行为 |
| --- | --- |
| WASD / 鼠标 | 移动 / 观察 |
| Shift | 纳刀空闲按住奔跑；拔刀时经普通输入许可请求纳刀，不绕过动作窗口 |
| E | 仅拔刀状态请求纳刀 |
| 左键 / 右键 | 纳刀左键拔刀；纳刀右键不提交突刺。拔刀左键纵斩循环、右键突刺；突刺后左键接上挑，上挑右键接突刺 |
| W + 左键 | 持刀前进斩 WalkOnSlash（原生 7 的 115→101 专用入口） |
| 左键 + 右键 + 移动 | 袈裟。按镜头水平朝向把移动输入转世界方向，相对角色右轴决定左右，无输入/死区默认后退 |
| Ctrl | 气刃 I → II → III → 大回旋；逐段消耗槽，大回旋命中升色并最终纳刀 |
| 气刃 I/II 后左键或右键 | 分别插入突刺 / 上挑，用独立 `SpiritComboThrust` / `SpiritComboRisingSlash` 身份 |
| 气刃踏步后左键/右键；插入上挑后 Ctrl | 均接气刃插入上挑；Ctrl 先判目标气刃 III 完整槽成本，够则 III，不够后备 I |
| 攻击后 Ctrl + 右键 | 见切。区分低槽/正常保护，消耗剩余槽；成功反击须回斩真实命中才补满槽 |
| 攻击后 Ctrl + Space | 特殊纳刀定格持刀姿态最多 3.5 秒；左键居合二连，Ctrl 居合气刃，Space 翻滚 |
| Ctrl + 左键，升空后再按攻击 | 气刃突刺，需白刃以上。命中后上升进入物理滞空；空中攻击请求下劈，173 播到 25/60 秒才提交下砸与七段授权 |
| Space，随后左键 | 纳刀/拔刀各用对应根运动翻滚，只在设定窗口免伤；持刀翻滚结束 0.15 秒内左键接 `RollStepSlash` |
| V / 手柄 D-pad Left | 气刃连段合法窗口进入投射器连射；方向随移动意图，源第 36 帧发射并扣弹 |

手柄 `bOriginalInputPreset` 默认关闭，只影响手柄；键盘始终走独立 PC 组合解析。手柄旧组合重发、RT+A、跨帧窗与全局仲裁仍未处理。

## 三、数值实现

气刃槽 0–100；白/黄/红伤害系数 **1.05 / 1.1 / 1.2**，基础持续 **195 / 135 / 60 秒**。

| 项 | 实现值 |
| --- | --- |
| 气刃 I/II/III/回旋消耗 | 15 / 15 / 20 / 25（I 不足槽可弱斩） |
| 气刃踏步强化消费 | 不足 20 时走 18 弱斩且不扣槽；够 20 用 28 扣 20；两者命中回槽 10 |
| Q 自然衰减 | 名义每 6 秒扣 5% |
| 回旋升色 | 合格命中后退出提交：清 Q、升色、刷新颜色余量 + 10 秒暂停衰减 |
| 居合回槽 | 二连真实命中 15 秒；反击后命中 30 秒 |
| 登龙回槽 | 非红 10 秒 / 红 15 秒；速率 100/15 每秒 |
| 居合气刃首击 | 无/白/黄/红 = 17 / 19 / 31 / 39 |
| 登龙空中首击 | MV 126（COL #28，源碰撞 25–112 帧） |
| 登龙延迟 shell | 按颜色 10 / 15 / 25；0.4 秒起、0.05 秒间隔、最多七段 |
| 有色居合追加 | 接触后 0.5 秒，白/黄/红 55 / 72 / 86 |
| 气刃 III 动作基值 | 14 + 19 + 34 |
| 居合二连 | 18 + 13 |

**防御窗口**（半开区间，Montage 秒）：见切正常反击 `0..33/60`、无敌 `0..45/60`；起始槽不足 10 时无反击、仅 `0..13/60` 基础无敌，回斩实际扣血才满槽。居合斩 5 帧；居合气刃反击 12 帧，无敌无色 12 / 有色 14 帧。见切/居合成功给 1/2 秒霸体，减伤 50% 但仍实际扣血，死亡仍发生。

上述数值中，消耗/持续/回槽/首击/延迟均直接取原版 W03P/COL；**取消窗、转向、0.3 秒缓冲、1.3 部位倍率属项目调校**。

## 四、调度、根运动与伤害契约

实现入口：[MHWICharacter.h](../../Source/IntroCpp/MHWI/MHWICharacter.h)、[MHWICharacter.cpp](../../Source/IntroCpp/MHWI/MHWICharacter.cpp)、[MHWIMovesetData.h](../../Source/IntroCpp/MHWI/MHWIMovesetData.h)。接口契约见 [Interfaces](../Interfaces.md) MHWI-001..015。

- 基础移动由 CharacterMovement 驱动，移动动画锁根；所有锁根用 REF_POSE 保留导入根骨旋转基底。攻击与翻滚保留 Root Motion。
- 登龙链 `Rise → Air → 可选 Strike → Land`：172/173 忽略零根轨迹改用 Falling 物理速度/重力；整链只保存一次移动/根运动快照，着地、打断、死亡、退出时恢复。Air/Strike 禁止从中立 `StartMove` 绕过合法链启动。
- 普通动作/派生在 Montage `0..0.12` 秒内按镜头相对移动意图有限转向，默认最多 25°、360°/秒；只动相机不转身。见切返回段另有 `46..68/60` 秒、45° 预算。袈裟/翻滚不叠加通用转向。
- 命中/派生/反击以 Montage 秒为准，源 TIML 帧按 60 FPS 转换。窗口检查用前后帧区间交集，窗口内每目标只扣一次；多段独立去重，槽收益每窗口一次。
- 伤害检测是**随胶囊根位移的球形前向/侧向扫掠**（高度偏移 35 cm），查询 `Pawn`/`WorldDynamic`，`WeaponMesh`/`ScabbardMesh` 碰撞关闭。**它不是原作刀刃几何复刻**——原作 `.col` 的 39 条碰撞轨虽 39/39 匹配时间 UID，但 CLGM 几何参数未映射到骨骼/形状/空间变换，见[总账第三节](../Reference/MHWI-LongSword-Evidence.md)。
- `RequestInput` 活跃时返回 true 只表示**缓冲**，不保证派生成功；0.3 秒缓冲仍需满足取消窗口、资源与命中/反击条件。缓冲记录实际收到输入的 Montage 位置，不能追溯已关闭的历史窗口。
- 动作拥有执行序号和 Montage 实例身份；死亡、UnPossessed、EndPlay、外部结束走同一清理路径，避免旧回调结束新动作。

玩家受击自 2026-11-16 起使用原生 `co00_01` 片段并按攻击来源方向与等级选段：小/中受击分别用 `DAMAGE_S_*`（104/107/105/106，注册名+selector 证据）与特征组 96/92/94/93（无注册名，用户批准试验）；大受击先播方向短受击片段并按现有力度击飞，落地后接 `DOWN_*_STAND_UP`（slot 7，0x431/0x439 静态证据）起身且保持输入锁定。持刀与纳刀统一走 Common；旧 `co00_00` 70/71/72 与 `w03_00` 61/62/63 是 STEP 载体，已不再用于受击。Impact 在首次 owner delta 开始混合，并按已到达的源帧/实际 Montage 结束释放。这是 UE post-update 适配，不是原作完整击飞/倒地状态机证明。

四方向与三档已通过 13 例真实 PIE（含持刀、双 Large 来源）：实际 bank/body 与朝向一一对应，稳定段骨姿相对源帧平均误差 0.1–0.4°，真实位移与起身链锁输入均已断言。击飞空中段仍用短受击片段（缺落体姿）；TIML 事件未迁移通知。详见 [CHG-20261116-001](../Archive/MHWI/Changes/CHG-20261116-001-hunter-damage-reaction.md)。

## 五、刀光与命中数字

`AMHWICharacter` 自带 `UMHWIWeaponTrailComponent`（父类 `UProceduralMeshComponent`，挂 `RootComponent`），刀光只在动作的**源命中窗口**内采样，命中数字只在真实扣血时记录。二者都属于表现层：不读也不改伤害、许可、槽或计时。

| 项 | 实现 | 边界 |
| --- | --- | --- |
| 刀光采样窗口 | `TrailWindowLead`（默认 0.06 秒）内的窗口区间判定，与 `AdvanceAction` 同一条件；命中停帧时姿态不动、不再累积 | 不是原作 EFX 起止帧；`wp03_*.efx` 的 WorkNo 未取证，未接 TIML 特效轨 |
| 刀刃采样点 | `TrailBaseBone=bone_100`、`TrailTipBone=bone_101`（武器骨架，刀身 142–150 cm） | 骨名可在 Details / 蓝图子类覆盖；换武器模型需重新核对 |
| 几何 | 每帧按历史样本重建三角带：3 列顶点跨外观色带，顶点色预乘「年龄幂次 × 内缘渐隐」，尾段在带内向刀梢收敛 | 样本上限 20；低帧率时段数变少，属采样不足不是逻辑缺陷 |
| 外观（两版） | `Style` 默认 `TipOnly`：只取刀尖约 4 cm 的淡红细线；`FullBlade` 为备用整刀观感（外半刃柔边白雾） | 两份 `FMHWIWeaponTrailLook` 都在组件上，带范围/颜色/强度/寿命/边缘渐隐各自独立 |
| 切换 | `SetWeaponTrailStyle`（蓝图）/ 控制台 `MHWITrailStyle 0` / `1`；切换先丢弃已有样本再换外观 | 中途切换会丢一瞬尾迹，换来不出现"半截错带"的跳变 |
| 材质 | `/Game/MHWI/Materials/M_MHWI_WeaponTrail`，Unlit + Additive + TwoSided，`VertexColor.RGB × Intensity` 进自发光 | 亮度由 look 的 `Intensity`（整刀 0.55 / 刀尖 1.8）预乘进顶点色，材质标量保持 1.0；无贴图、无光照 |
| 命中数字 | 真实扣血后记录世界接触点，`AMHWIHUD` 投影绘制：上浮 56 px、先放大后回落、62% 后淡出、深色四向描边 + 暖橙填充 | 只有玩家造成的伤害；寿命 `DamageNumberLifetime`（默认 0.75 秒） |

两版当前参数：`TipOnly`（默认）= 带 0.97→1、`(1.0, 0.34, 0.30)`、强度 1.8、寿命 0.26 秒、`bSoftBothEdges`（两侧渐隐成一条发光细线）；`FullBlade` = 带 0.35→1、`(0.86, 0.94, 1.0)`、强度 0.55、寿命 0.08 秒、同样两侧渐隐。整刀版最初用 0→1 + 单边渐隐 + 强度 1.4，实测在低采样帧数下叠成一张不透明白帆，已按此收敛。刀尖版的红色是项目选定的外观预设，**不是**从原作 EFX 取证的颜色；它只说明"两版并存可对比"，不宣称等于原作。HUD 左上角 `TRAIL FULL / TIP` 显示当前外观。

命中数字颜色只实现 MHW 的「有效部位」橙色。白色/灰色（低肉质）与龙属性异常蓝框需要肉质与属性伤害数据，`FMHWIResolvedHit` 的 `Part/Sharpness/Affinity` 仍为 `Unavailable`，因此不做区分而不是猜一个阈值。

## 六、训练场
三个原生 `AMHWITrainingTarget` **默认均为被动木桩**，普通连招不会受到周期伤害。目标有真实属性血量，不用假命中计数。

需要见切/居合反击练习时：选中目标（如 `MHWI_CounterTarget`），Details 的 MHWI 分类勾选 `Enable Attacks`，再 Play。距离内按 `AttackInterval` 周期、提前 `TelegraphSeconds` 预警并造成 `Damage`；**不是被打时立即反伤**。取消勾选恢复被动。

原生类缺省值仍为 true，手工新增目标时须显式设置该属性。

## 七、已实现 vs 未闭合

已实现：32 招定义 / 149 路由 / 29 Montage；原生装备父骨选择与导入基变换（84 组坐标对照误差 <1e-4）；四链 IK 与六段移动过渡；命中缓冲、结构化命中结果、登龙阶段机与延迟 shell；键盘/手柄输入源分离；受击四方向 DAMAGE_S（含持刀统一）；命中窗口驱动的刀光与命中数字。

未闭合（详见[总账第五节](../Reference/MHWI-LongSword-Evidence.md)）：

- 精确取消窗、输入缓存跨帧语义、手柄组合键
- 10 秒字段真实消费者、回旋清槽精确帧、耐力/回避保护完整判定
- 斩味/会心/肉质/攻击力表 → 完整伤害管线
- 刀刃几何、部位选择、原作 IK solver/CTM
- 受击击飞落体段（空中倒地姿）、TIML 事件到 AnimNotify 的迁移、特殊受击（QUAKE/WIND/EAR/SLIP）slot 查证
- 全程运行验收（多段 PIE 曾通过，但完整场景未覆盖）

历史批次报告见 [Archive/MHWI/](../Archive/MHWI/README.md)。
