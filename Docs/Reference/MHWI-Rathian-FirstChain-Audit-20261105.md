# 雌火龙首链只读取证与源码审查（2026-11-05）

- 范围：em001/00；目标仍是下位单人。**本轮只读取原始数据、既有分析镜像与源码；只新增/更正文档，不改代码、资产或旧证据 JSON。**
- 结果：选定 `em001_55.thk:n200/id217 → raw emit83` 作为最小受控 BITE 候选；新增动作表布局、源根轨和三组碰撞通道的静态证据。**完整“THK→动作→移动→命中”仍未通过，原作条件语义验证仍为0。**
- 本轮用户已暂缓 Sandbox 修复；未执行系统修复、安装、重新解包、原作启动/附加/注入、UE 启动、构建或 PIE。DevFlow 冻结任务未执行，模型调用计数不变。
- 相关：[首链方案](../Plans/PLAN-20261031-007-rathian-first-chain.md)、[已选架构](../Decisions/ADR-0002-mhwi-rathian-source-runtime.md)、[评审约束](../Plans/PLAN-20261103-001-rathian-review-adoption.md)、[本轮记录](../Changes/CHG-20261105-003-rathian-first-chain-audit.md)。

## 证据口径与官方依据

1. **官方机制（UE 5.8）**：[UMovementComponent](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/UMovementComponent)规定扫掠只考虑 UpdatedComponent，附属组件随终点移动；[Root Motion](https://dev.epicgames.com/documentation/en-us/unreal-engine/root-motion-in-unreal-engine)解释根提取与 Force Root Lock。这些只支持 UE 实现机制，不证明 MHWI 的运动或时钟。
2. **官方引擎源码（本机 UE 5.8）**：`E:/UE/UE_5.8/Engine/Source/Runtime/Engine/Private/PhysicsEngine/CollisionQueryFilterCallback.cpp:32–38` 在多对象查询预滤中把 Block 转为 Touch；`Private/Collision/WorldCollision.cpp:262` 是对象扫掠入口。不能据“首个 Pawn 会阻断所有后续 Pawn”否定当前多对象查询。
3. **维护方资料**：[Leviathon](https://github.com/AsteriskAmpersand/Leviathon) 固定提交 `1e647f08ed4356e9feac037ccec7c08149fa2ef5` 的 ActionDump/FExtY/反编译器是社区候选。Capcom 原生消费者另列，不用社区名称补未知语义。
4. **原始数据**见下表；**原生消费者**只限固定镜像中已定位的指令；**项目静态发现/推断**另列。未经运行的构造反例不写成已复现缺陷；历史资产读回不写成本轮运行验证。

## 一条链路的当前状态

| 连接 | 本轮所得 | 尚缺 |
| --- | --- | --- |
| THK决策→raw83 | 原始 action 字节 `53 00 00 00`；最短受控路径9次访问、两个假设条件 | 两个条件的原生布尔/副作用、call/return/branch 消费者；从真实 LR 入口的随机选择可达性 |
| raw83→Bite类型 | 32B原生注册循环读ID32、类型和名称；83/BITE/描述符与维护方表一致 | THK actionID→动作对象查找/启动，以及注册caller的怪物对象归属 |
| Bite→0x2001 | 既有原生注册、工厂、构造器与运动请求锚；本轮复核身份解释 | bank2 到文件 `em001_02.lmt` 的加载/注册消费者 |
| LMT→源轨迹 | 29根位置键独立解码，131整数样本与既有轨迹逐点一致 | actor-root消费、尺度/坐标/入动作朝向、原生时钟与速度轨 |
| 同slot→COL | 三组UID32/21/24对应三组COL记录；几何/骨remap有静态依据 | flags三位→三Node绑定、源时钟、UE骨局部变换 |
| 接触→命中/结算 | 当前只生成接触观察；发现TOI覆盖与曲线近似边界 | 原作目标过滤、同帧优先级、重复命中/伤害授权及动作完成回VM |

## 1. 动作身份：旧83/84冲突首先是提取器缺陷

[旧提取器](../../Scripts/MHWI/dump_action_registry.py)将32B记录解释为 `{name,id,vtable,0}`，从名称指针处起读。现有 EXE 原始字节支持的新布局是 `{id32+padding32,type_descriptor,unknown_qword,name}`：同一名称指针之前24字节才是记录首，相对旧32B分组相位为+8。以下地址均为 VA，记录步长32B：

| 新记录起点 | id | +8类型描述符候选 | +16 | +24名称 |
| --- | ---: | --- | ---: | --- |
| 0x142e62f60 | 0 | 0 | 0 | ACTION::NONE |
| 0x142e62f80 | 1 | 0x144f36fe0 | 8 | ACTION::IDLE |
| 0x142e63960 | 80 | 0x144f390e8 | 0 | ACTION::BACK_STEP_BREATH_TO_AIR |
| 0x142e63980 | 81 | 0x144f383c8 | 0 | ACTION::BACK_STEP_BREATH_TO_GROUND |
| 0x142e639a0 | 82 | 0x144f39970 | 0 | ACTION::BACK_STEP_BREATH_FLY |
| 0x142e639c0 | **83** | **0x144f37c58** | 0 | **ACTION::BITE** |
| 0x142e639e0 | 84 | 0x144f391c8 | 0 | ACTION::BITE_NO_BLEND |
| 0x142e63a00 | 85 | 0x144f36b10 | 0 | ACTION::BITE_FLY |
| 0x142e63a20 | 86 | 0x144f38518 | 0 | ACTION::DASH_BITE2 |
| 0x142e63a40 | 87 | 0x144f38470 | 0 | ACTION::DASH_BITE_TIRED |
| 0x142e63a60 | 88 | 0x144f39200 | 0 | ACTION::RASH_BITE_FLY |

- BITE记录磁盘偏移 `0x2e61fc0`，32B SHA256：`9d5277e6c4c9515d4f8170c40eaf6cb45cda86184fbde16e5b49efe5b768738a`；主代理独立重读与子代理一致。
- 新表头 `0x142e62f60` 的数据段指针位于 `0x143ef0598`（磁盘 `0x3eeeb98`）。以 `0x143ef0590` 为候选数组起点，索引1的285条 id/name 与固定维护方 em001 dump **285/285一致**；索引2、3分别59/59、131/131匹配 em002/em003，仍是静态交叉一致。
- 固定ActionDump位于 `Saved/MHWI-Rathian-FirstChain/Leviathon/Leviathon-1e647f08ed4356e9feac037ccec7c08149fa2ef5/common/ActionDumps/`；em001/em002/em003.txt的SHA256依次为 `e8c9c926aa3be53bd89e0fd17075a4038efa013665cae2bd573e1100bc3f60b6`、`434725bcdac928e216fe11ff5d948e6c785f80002a03a77117dc37bd05e1f7d0`、`74f7cdf9f765b8065b227cd4001be99d089ee38d0364a924636d0e51ec6e4a52`。
- em001表块 `[0x142e62f60,0x142e65300)` SHA256：`e7689b9a3dbb12481145433bb40a8859ed910497463c1cd0a4b94e9b7d959e07`；其后32B为 `ffffffff0000000000000000000000000000000000000000700ce54201000000`，ID32=-1、名称指针指向NoAction，为尾哨兵候选。新增表指针getter与注册循环已在下节核实；该注册caller如何归属原生怪物对象仍未取证。
- 原生注册锚 `0x1400cb630` 将描述符 `0x144f37c58` 与字符串 `nActEm002::Bite` 传给 `0x14216ed60`；工厂 `0x140d0b910` 连到构造器 `0x1413ec130`。其类型名 em002 与资源目标 em001 不能自行等同或改名。
- 邻接注册 `0x1400cb6d0` 使用 `0x144f391c8` 与 `nActEm002::BiteNoBlend`；工厂 `0x140d0bc80` 连到 `0x1413ec170`。真正 BITE 对象虚表锚是 `0x14326af58`，enter/update为 `0x14073ee50/0x140741bf0`。描述符位于 `.data` 虚拟零填充区，不能当成磁盘可读的对象虚表。
- 旧脚本还有两处审计问题：全局按名称去重、输出不保留表地址；旧布局要求第四qword为0，实际限制的是新布局+16的未知字段；em001的285条中有155条该字段非零，不能据旧过滤结果声称完整。不能再把旧“344条 name↔id↔vtable 完整注册表”作为闭合证据，也不能据此建立统一ID偏移。**本轮不修脚本、不重写旧JSON，禁止把raw83改成84来迎合旧产物。**
- 已有项目脚本 `Scripts/MHWI/trace_outstanding_evidence.py:92–96` 对武器表使用 stride32、DTI+8、name+24，是另一个项目静态交叉锚；不替代本怪物的游戏消费者。

### 新补：动作表注册循环已有原生静态消费者

新目标的一次限定RIP签名搜索共命中两处；只读命中窗口与一个callee，未进行全镜像反汇编、重新解包或目标执行。主代理独立复核字节与计算地址：

| 原生地址 | 原始字节/操作 | 可支持的结论 |
| --- | --- | --- |
| 0x1413918b0/b2/b9/bd | `8bc1 / 488d0dd7ecb502 / 488b04c1 / c3` | 入参ECX→EAX，以 `0x143ef0590 + index*8` 返回表指针；尚不证明此入参是谁提供 |
| 0x141c29c92 | `41b91d010000` | R9D=285 |
| 0x141c29ca0/ca7/caf | `4c8d05b9922301 / ba01000000 / e8cc32fdff` | R8=0x142e62f60、EDX=1、RCX=RDI，调用0x141bfcf80；第五参数0 |
| 0x141bfcfac、0x141bfcfd2 | `498bd8 / 4883c310` | RBX接表头后加16 |
| 0x141bfcfe0/fe9 | `4c8b43f8 / 8b43f0` | 读记录+8类型描述符、记录+0的**ID32** |
| 0x141bfd019/01f | `488b0b / 48894f10` | 记录+16的未知qword写调用返回对象+0x10，尚不能给它最终flags语义 |
| 0x141bfd023/027 | `488b4b08 / 48894f20` | 记录+24名称指针写调用返回对象+0x20 |
| 0x141bfd031/035/039 | `4883c320 / 4883ee01 / 75a5` | 32B步长与计数循环 |

固定.text窗口SHA256：`0x1413918b0/16B=e46d294a6b4bd3d93264ab8a180f91e1e76e47c679fc9a8a382dafb4221db8ca`；`0x141c29c92/34B=39bea86288b5f3103329d9eb1cbbba1efce198d54e31a92475b42d396fe8aac5`；`0x141bfcf80/256B=84b86bf84a4dc5e14f658413522318cd56711802f5ab407a205a4a84bdb5c50a`。函数尾在0x141bfd05b前，后续字节不作为该函数逻辑。

因此，**stride32与ID32/+8类型/+16未知值/+24名称的布局已有原生静态注册消费者支持**。此前“字段消费者未证”缺口在此限定范围内得到补齐；不是仅凭维护方dump推导。尚未追进被调用函数0x140269c30，不能确定其返回新建实例还是已有对象；不能据调用形状宣布THK action83已经查找/启动正确实例。

对象归属仍开放：原EXE `.pdata` 中，注册caller范围 `[0x141c29c80,0x141c29dc9)`，既有EM001候选vtable写入点0x141c283a1属于另一范围 `[0x141c28340,0x141c283ba)`。有界读取vtable `[0x143423d40,+0x800)`（原EXE磁盘0x3422340，窗口SHA256 `23623a2b89a40243c687da8d6163a0f6160375c5e1da247a1c2aaf611b804ad2`）未见注册caller指针，不能因地址相邻称它是同一构造器或已属于em001。callee的链式unwind记录将循环和尾部链回0x141bfcf80；只支持本函数的字段消费归属。未发现窗口内某指针不排除窗口外或间接归属，不再扩大扫描。

## 2. THK：只需先补两个条件，但受控入口不等于真实AI入口

原 THK55 节点目录记录@3232指向 n200/id217：段起点199712、段数5。action位于199968+76=**200044**，值83，五个附加动作参数均0。既有 [normal_form](../../Tools/MHW/rathian-thk-chain-evidence.json)仍明确 `native_control_flow_verified=false`。

下列路径假设 `0x70(0,0)=false`、`0x16(90,270)=false`，控制解释来自固定维护方反编译器和现有项目normal form，**不是原作VM运行轨迹**：

| 步 | THK段 | 文件偏移 | 候选解释 |
| --- | --- | ---: | --- |
| 1 | n200.s0 | 199712 | 调用n2，保存返回199840 |
| 2 | n2.s0 | 5536 | 条件0x70假，跳6432 |
| 3 | n2.s7 | 6432 | branch8到6560 |
| 4 | n2.s8 | 6560 | flow8，返回199840 |
| 5 | n200.s1 | 199840 | 调用n198，保存返回199968 |
| 6 | n198.s0 | 198816 | 条件0x16(90,270)假，跳199200 |
| 7 | n198.s3 | 199200 | branch8到199328 |
| 8 | n198.s4 | 199328 | flow8，返回199968 |
| 9 | n200.s2 | 199968 | yield raw action83 |

固定 `default.fexty` 的行112/50分别给出 `flying()`、`angle_2d_cw_between(p1,p2)` 候选名；不能据名称注入真实布尔。ack后的 n200.s3@200096为候选返回点，原生动作完成通知尚未证明。

真实调用者 n314/315/316.s0 位于381088/382368/383776，带 `endRandom=0x40`、权重候选25/20/25；不能当成无条件直达n200。首链工程受控实验可从n200切入，但LR实际可达性必须单列。无需等待全部58类函数语义恢复后才推进这条受控链。

## 3. 根轨、TIML与时钟

原 `em001_02.lmt` 的slot1头@1968，frame_count=131：

- usage3根旋转记录@13776为单位四元数；usage4位置记录@13824，codec4，payload@23088、232B，lerp@20016。29键独立解码及整数采样0..130，与 `Saved/MHWI-Rathian-FirstChain-20261031/selected-source-track.json` 逐点误差0；payload SHA256：`457b8e0a0b50904f0fbadd89e693f5d12e234050e830028a97747ec9706df8d8`。
- 项目轨迹采用 `[x,z,y]` 映射。以下数值明确为映射前源坐标：t10=t80为 `[6.68205595,0,49.9655838]`，t111=t130为 `[51.3980103,0,-7.8466053]`；映射后分别为 `[6.68205595,49.9655838,0]`、`[51.3980103,-7.8466053,0]`。此处闭合的是“已有导出与原字节一致”，不是原作单位或actor运动资格。
- 同slot TIML@40960声明animation_length=130；碰撞组@41008。根轨0..130、碰撞边界23和TIML长度确在同一源slot中。
- 相邻组@41032的轨hash `0x2ac902e3`（既有dump名称 `mMotionSpeed`）键@42272/42292/42312/42332分别为 `(0,.900000036),(25,.900000036),(35,.350000024),(70,.900000036)`，插值码1/2/2/1；须追实际消费者，不能据名字自行更改播放速度。
- 历史 UE 时长2.166666746秒约等于130/60，只证明导入采样映射。原生 clock/rate、速度键作用于动画还是位移、入动作朝向和根旋转消费仍未知；当前源profile的 `UnitsPerSecond=0` 保持不变。
- UE-MCP本轮只读状态为 `editorConnected=false`、`mode=disconnected`、editor exited；未启动编辑器，因此实际 `/Game/MHWI/Rathalos` 下001片段的根提取/锁根/姿态属性没有新读回。

## 4. 命中前还有三组通道，不能只关闭bit0

LMT的Node0/1/2原始键分别@42128/42160/42192，值32/21/24；flags@42224/42244为 `(value7,mask7,frame0,type5)→(value0,mask7,frame23,type5)`。三位分别驱动哪个Node、是否用于伤害，仍缺消费者。

| UID | COL名称记录 | geometry | attack |
| ---: | --- | --- | --- |
| 32 | #22@861 | #14@11811，5胶囊 | #7，MotionValue30@31044 |
| 21 | #33@1365 | #29@19488，1胶囊 | #14，MotionValue0@32241 |
| 24 | #34@1405 | #30@19635，1胶囊 | #14，同上 |

几何14的五胶囊子记录@11827/11899/11971/12043/12115；MOD3 remap@21600复核 `3→8,4→9,100→3,101→4,102→5,103→7`。既有19处几何/骨映射指令锚字节匹配，限定为静态消费者证据。后两组的MotionValue0既不能证明无作用，也不能证明伤害。

[现提取器](../../Scripts/MHWI/extract_rathian_chain_collision.py)只选择Node0；[旧profile](../../Tools/MHW/rathian-first-chain-collision.json)仍保留 `action_binding/timeline_flags_uid/native_clock/ue_local_basis=false`，严格模式应拒绝。候选窗 `[0,23)` 不升级为原作活动窗。

## 5. 源码审查：验收前必须处理的边界

以下均是当前源码的静态发现；本轮未执行构造反例或UE测试，不作“运行已复现”主张。

| 问题 | 代码定位 | 影响与最小验收 |
| --- | --- | --- |
| 共享时钟缺少跨组件校验（R-DATA-007） | [Movement](../../Source/IntroCpp/MHWI/Monsters/MHWIRathianSourceMovementComponent.cpp)78–98、[Collision](../../Source/IntroCpp/MHWI/Monsters/MHWIRathianSourceCollisionComponent.cpp)109–123、[Pawn](../../Source/IntroCpp/MHWI/Monsters/MHWIRathianFirstChainPawn.cpp)127–140 | 移动容许Seconds/NativeTicks，碰撞只容许NativeFrames；Pawn只按时长映射后直接传同一数值，没有核对单位/速率/来源/clip身份 |
| 较早TOI被重叠覆盖（R-COMBAT-013） | Collision306、309–322 | 同一胶囊的map按Actor键写入；区间末重叠无条件覆盖扫掠，包括精确纯平移。应区分较早扫掠时间与当前姿态重叠观察 |
| 首尾相同不证明区间纯平移（R-COMBAT-013） | Collision285、Pawn212–218 | 只比较首尾轴和半径；根样本/窗边界不保证中间骨轨线性。不能把此结果当原作精确首次命中 |
| “InPlaceSequence”只有命名、未验证原位（R-ANIM-013） | [完整导出器](../../Tools/MHW/complete_rathian_animations.py)34–50、[导入器](../../Scripts/MHWI/complete_rathian_import.py)22–34、Pawn119–132 | `Tools/MHW/BlenderAddons/blender-mhworld-tools-suite-main/lmt/lmt_loader.py:13–40`将bone−1平移写入bone_root；导入未明确设置根提取/强制锁根。该bank历史抽检为181而非001，可能出现外移与姿态重复位移，尚未实读确认 |
| 严格条件提供器与动作完成回VM缺失（R-AI-003） | Pawn158–182、234–240 | Query仅查工程条件，注入接口只允许工程模式；动作到轨迹末端调用Thk.Cancel，没有接ResumeAfterAction。不能宣称已实现原生条件或动作完成后的下一决策 |
| EvidencePinsJson未消费（R-DATA-007） | [Data](../../Source/IntroCpp/MHWI/Monsters/MHWIRathianFirstChainData.h)21 | 仅声明、Source内无读点；64位hex字符串与资格bool不等同于运行时重新核验源文件 |

反例及限定：

- **时钟契约反例**：假定其他输入及各自资格真实满足，motion=Seconds/rate1、131点时间i/60、末时130/60，collision=NativeFrames/rate60、窗[0,23)。运动四项资格为NativeConsumerVerified，碰撞五项必需资格均true，action83、元数据/骨架/几何均合法；导入映射设为 `2.1666667461395264/(130/60)`。两组件各自的配置门和Pawn时长门不能排除该组合；Pawn把秒数直接用于碰撞帧域，动作约2.1667秒完成时碰撞仍未到23，理论上把应约0.3833秒关闭的窗口延长到动作完成。未运行、未证明当前Pawn能启动；真实profile两侧NativeFrames/rate0和工程资格会先被strict拒绝，THK等其他门也仍可先阻断。
- **TOI构造反例**：源时间[1,2]，胶囊中心x0→10，双方半径1，目标中心x10；按线性几何首次接触1.8，末态重叠会写成2并留下默认Hit。每个胶囊各有map，**没有跨胶囊全局覆盖/去重**；同胶囊中多个primitive属于同Actor时仍可能后写覆盖。
- **骨轨构造反例**：首尾轴相同、中心中途弯出再返回，端点线性扫掠可能漏接触，代码仍标非保守。未声称实际BITE轨迹已触发此例；需先证明原作使用离散姿态还是连续扫掠，不能擅改成自选碰撞算法。
- 当前Pawn根为无碰撞USceneComponent；按UE官方机制，运动组件的sweep设置本身不能证明世界阻挡成立。
- 当前接触不扣血、无跨区间重复命中账本；[现有3个测试](../../Source/IntroCpp/Tests/RathianFirstChainTests.cpp)覆盖THK未知拒绝、yield身份与源移动身份，没有Pawn/真实骨姿态/COL/伤害的完整集成验收。

## 推荐的后续次序（沿用已选路线）

1. **E02/动作身份**：表指针getter与stride32/字段注册消费已有静态支持；下一步从THK action83追注册对象的查找/动作启动及注册caller的怪物对象归属。工具修复任务需保留table地址/descriptor/未知字段和表内ID，不再跨表按名字去重；不同维度分别记资格，不把本轮字段证明直接当完整action绑定true。
2. **E01/最小THK切片**：只追0x70、0x16与本链的branch/call/return；另记真实调用者的随机选择/LR资格。严格模式未知必须拒绝，工程假设轨迹需显式标记。
3. **E03/运动与时钟**：先补bank2文件消费者、0x2001运动请求、速度轨/clock、根消费与坐标；恢复编辑器读通道后实读001序列根锁定和骨变换。统一ActionSpec/时钟身份约束后再做实现修正。
4. **E04/碰撞与命中**：追三位flags与三Node消费者，明确每组作用；比较0/23边界、多个Pawn/组件、较早TOI、非线性骨轨、重复观察不触发结算。命中授权和动作结束通知各自取证。
5. **工程与原作验证分开**：前者整步/分步推进0..23和0..130，核根位置、骨胶囊、取消后状态；后者需另有受控原作证据，才能升级忠实度。Sandbox修复及CodeBuddy执行不属于本轮；不因其暂缓停止可独立进行的只读工作。

## 固定输入与复查

项目根：`E:/Unreal Projects/IntorCpp`；原EXE：`F:/PCprogram/Steam/steamapps/common/Monster Hunter World/MonsterHunterWorld.exe`。下列偏移均是各源文件偏移，明确写VA的除外。

| 输入（项目相对路径或名称） | SHA256 |
| --- | --- |
| 原EXE | c2ebbbd2c49f216d484e31a5219bed419eb1e5e7d206d02cba040a3ab79d90ea |
| Saved/MHWIRestoration/B05-20261024/analysis-text.bin | 9b48a8490df702ba9dc1cb95ffd387358ae2a639aa9675ad90719bd997124ebe |
| ArtSource/ThirdParty/MHWRathalos/nativePC/em/em001/00/data/em001_55.thk | c724f8acb8a58efc200052bac2a642c9d5f34802d4f513df90b428f4533721f7 |
| ArtSource/ThirdParty/MHWRathalos/nativePC/em/em001/00/mot/em001_02/em001_02.lmt | 8c4c9c4bd9973f7b0d73f3ff915b6a734cf49215b138bcb43a8a531105f62063 |
| ArtSource/ThirdParty/MHWRathalos/nativePC/em/em001/00/collision/em001.col | 280bd35f01abdab2d2d54d397e21dd3db6b8b4cca8b1176c3a7f7bef3dd989a4 |
| ArtSource/ThirdParty/MHWRathalos/nativePC/em/em001/00/mod/em001_00.mod3 | f08e65e66495668872fc7818a1ca9597bc3186b4f9ca5cf6df9f4a37b061d7dc |
| Saved/MHWI-Rathian-FirstChain-20261031/selected-source-track.json | 429ee94bfe9ddfebba8a2f7b8e6515c92d64c4544305aedc55d0fbd036f1b15f |
| Tools/MHW/BlenderAddons/blender-mhworld-tools-suite-main/lmt/lmt_loader.py | f44cfe9249801327c3efd74c09250013c8b5df7d51cc506edaadf4023ffc97b8 |
| Scripts/MHWI/dump_action_registry.py | 00b84f2296a8789392e667c1ac22e60fcaebd3554c6cc750dd83958483ce11f2 |
| Tools/MHW/rathian-thk-chain-evidence.json | 8726c0794e581ce8ff75beba56de87035d567af0c73c4607a4896fbb74f9c474 |
| Tools/MHW/rathian-first-chain-collision.json | fa24214b81467f9f155fa076e98bb0184f4716ec6df72272c12d4f221df80b6c |

分析.text镜像VA基址为 `0x140001000`，镜像偏移=VA−该基址；不能把这些VA直接当原EXE磁盘偏移，原EXE磁盘.text与分析镜像不是同一内容。本轮只读现有固定载体；仅对三个新目标做一次限定RIP签名搜索，不重复跳转表穷举、不全镜像反汇编、不重新解包或运行旧提取器。

分工：决策/身份、运动/时钟、接触/命中三个子代理分别复核；主代理独立重读THK action字段、候选动作表/指针和关键源码，并再次逐项核对三个固定dump（285/285、59/59、131/131一致）后归并。三代理复审文稿，运动代理指出源坐标/映射后数值需区分，已更正。原始输入和既有源码/工具在归并前后做29文件SHA256比对；文档检查实际结果见本轮CHG。没有用源码审查、文档校验或历史构建替代端到端运行验收。
