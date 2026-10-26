# R06 B10：剩余三项开发交付

更新：2026-10-25。**R06剩余三项开发全部完成；未编译、未测试，未取得运行验证结果。** 接续[B09历史快照](MHWI-R06-Completion-Development.md)，本页描述B10最终开发实现；不把B09当时的缺口或历史测试改写为本次结果。

## 三项实现

| 项目 | 正式调用及落点 | 开发结果 |
| --- | --- | --- |
| 真实前置玩法拥有者 | `MHWICharacterNativeSources.cpp`；`HandleDamaged`、`SweepWindow`、Enhanced Input、`StartNativeSource` | 小/中/大受击分别持有原生武器动作30/31/32（片段61/62/63），纳刀规范站立受击103/110/115（common70/71/72）；目标明确报告弹刀时接34/221；气刃段中V或D-pad Left进入104..112投射器连射。实际Montage实例和非零令牌交接来源，正常输入续段；失效、倒退、错片段、暂停、中断、死亡撤销控制。node0使用实际IDLE/WALK播放叶，WalkOnSlash原生7使用115→101；四向持刀翻滚为11/12/13/10 |
| SpiritI / StepSlash专用入口 | `MHWILinkAnimation::ResolveActionEntry`、角色`PrepareNativeLink/BeginNativeLink/CommitNativeMain` | 迁移前置拔刀状态、前置/当前身份、弱气刃身份、前请求、通用Phase采样、后覆盖、自定义状态和结束提交。完整保留113/116/126/130/132/152及151分支；保留中间请求对最终MBD来源的影响，不把所有路径简化成连接表查找 |
| 混合门控与独立时钟 | `MHWICharacterLinkMotion::ApplyNativeBlend`、`MHWIAnimInstance`动画代理 | 固定源的直接武器bank12请求没有MotionTree节点，因此没有初始/尾包络启用位；MBD mode1请求bit2使用显示姿态捕获与线性插值。新根运动载体求值前立即取得全权重，姿态在代理最终输出前混合；首个目标姿态求值前elapsed保持0，中途重入捕获当前显示结果。混合步进为动画Actor秒×60，独立于Montage播放倍率；规范common mode0即时换层请求的插值也交给该姿态管线 |

16个来源绑定来自原动作注册表/武器设置回调，而非FSM `ActionNo`猜测。`MHWIContactResponse`提供明确受击大小和是否弹刀；不从伤害数值推断原版硬直大小，也不把未扣血当弹刀。训练目标新增`ImpactSize`和`bDeflectsMelee`可编辑属性，旧地图被动木桩配置保留。启用目标攻击即可产生实际受击来源；启用弹刀属性后，其近战接触会进入恢复拥有者。界面显示投射器弹药及新增按键。

投射器在源TIML `mTrigger & 1`跨过第36源帧时发射一次并消耗一发；按实际104..112身份、前置70/78选择338..349或332..334的对应方向片段。方向由移动意图与角色右轴决定。射线命中使用项目属性伤害入口；输入和窗口仍采用项目适配契约。

## 专用入口的顺序

- 原`141f77722..2c`把前置`+76a8`拔刀状态复制到`+76aa`；`141bffa20/40`读取前置身份，`141bff740/760`读取当前目标身份。DTI实例虚表slot4是类型getter，不是初始化。
- 气刃I `1417fe610`先依拔刀状态和身份选择专用片段，再调用无默认主段的通用入口；TIML Phase在显式前请求之后采样。前置57/60/63的132覆盖在通用调用之后执行。保留“没有新请求，继续旧载体”的分支，随后由自定义状态提交104。已自然结束的拥有者直接提交应有主段，不收养已失效实例。
- 踏步斩`1417fed20`保留未拔刀规范站立Step直接151、其他来源通用入口，以及武器Step通用请求后再覆盖151的顺序。151后的101使用当时实际前段的MBD；没有主段提交的自定义状态也保留。
- Upper固定119→107、WalkOn固定115→101。原112主段与完整101迁移沿用B08/B09；13个既有主段绑定保护保留。新增专用前段的原TIML没有攻击碰撞轨，前段不运行主招伤害/防御/取消窗口；主段按实际startFrame初始化事件和倍率，过去事件不补播、费用不重复。

完整有序表仍为30节点、32引用、124记录、26连接片段。原图node86无入边，保持0匹配记录；共享365片段不构造输入入口。逐行结果见[连接台账](../Plans/MHWI-Connector-Progress.md)。

## 混合依据与范围

[B10静态证据](../../Tools/MHW/native-r06-remaining-evidence.json)保存固定二进制指纹、39个来源注册记录、入口/消费者范围、MotionTree原始512行和时钟链。SpiritI内嵌跳转表明确标为数据，不把误解码指令作为依据。`wp03_tree.at`版本7的头为12字节、节点32字节，节点ID为bank1，不能给直接bank12请求注入request100/200。`141c014f0`请求曲线选择器为0；`142255820`消费启用位；`14236a300/142368a90`处理插值捕获；`142256586`阻止首次姿态求值前推进elapsed。raw overlap数值继续保留，未启用时不转换成UE旧Montage的停播时长。`ResolveDirectBlendSettings`只接收已迁移的武器mode1与规范common mode0，其他模式/来源拒绝进入适配器，后续源数据变化不能静默套用现有规则。

时钟链：全局时间拥有者`0x1451c4148`，构造`14225c472`设置`+58=60`；`14225f9f0`写帧步长`+94`；`14221ada1`乘分组时间比例写manager`+a0`，除60写秒步长`+a4`；`142228f90`把帧步长复制到owner`+6c`；`141bffd26`传给树slot15 `1422564f0`，`142256594`推进混合。UE使用`Montage_UpdateWeight(DeltaSeconds)*60`，不乘动作/Sequence播放倍率。游戏线程通过`GetProxyOnGameThread`交接姿态缓冲，工作线程只操作骨变换和骨索引，不改UObject。

## 资源与重建

本批导出并导入32个225骨猎人AnimSequence：

- `/Game/MHWI/Animations/R06Remaining/A_w03_00_###`：010、011、012、013、061、062、063、113、115、116、126、130、151、221、332、333、334、338、339、340、341、342、343、344、345、346、347、348、349，共29段。
- `/Game/MHWI/Animations/R06Remaining/A_co00_00_###`：070、071、072，共3段。
- Skeleton为`/Game/MHWI/Character/SK_MHWI_Hunter_Skeleton.SK_MHWI_Hunter_Skeleton`；导入类为`AnimSequence`，制作时设置root motion开启、force root lock关闭、REF_POSE。上述信息来自制作日志，未做新的导入后验证。

完整对象路径/FBX SHA256见`Saved/MHWIRestoration/B10-20261025/r06-import-journal.json`及[部署记录](../../Tools/MHW/r06-runtime-adapter.json)。角色CDO硬引用保留Cook依赖；BeginPlay复制角色自己的Moveset，建立WalkOnSlash和四向Roll运行定义，不覆盖正式`DA_MHWI_LongSword`。原动画蓝图父类已在B09读取为`UMHWIAnimInstance`，本轮未保存蓝图或地图，也未用旧编辑器二进制证明新源码可运行。

开发重建入口（均不是测试）：

1. `python Scripts/MHWI/extract_r06_remaining.py`：固定源码取证，输出B10消费者及稳定证据。
2. `python Scripts/MHWI/build_native_link_policy.py` → `build_link_runtime_data.py` → `build_r06_remaining_data.py`：生成有序表、动作/Phase表及来源表，输出目录为B10，保留B09历史。
3. 源FBX制作使用Blender执行`export_r06_remaining.py`；manifest为`ArtSource/ThirdParty/MHWLongSword/R06Remaining-20261025/export-manifest.json`。`import_r06_staging.run`传该manifest、B10 journal及`destination='/Game/MHWI/Animations/R06Remaining'`导入；遇已有journal/包会拒绝覆盖，重做前先依日志处理目标。
4. `python Scripts/MHWI/record_r06_remaining_progress.py`更新32行/总台账CSV、连接Markdown及部署记录。旧B08/B09记录脚本只对应历史批次，不作为当前生成入口。

制作时曾附带尝试common181/182：181缺镜像上下文，182不在有效源条目，初次导出中止；恢复为本轮规范站立来源所需70/71/72后完成32段制作。181未导入；失败日志和附带blocked记录保留，不能记为通过或伪装成本轮缺失资源。

## 交付状态、相邻台账与回退

本轮没有运行编译、UHT、PIE、自动化、语法、文档或diff检查。以上提取、代码生成、FBX导出和资源导入均为开发制作。**开发完成不等于验证通过。** 用户以后另行安排验证时，使用[验收要求](../Plans/MHWI-Connector-Acceptance.md)，本次不执行。

R07精确输入mask/取消、R08原版缓存、R09精确方向、R24完整环境/行走/坐姿/镜像受击族和恢复死亡、R25完整投射器弹药/部位/伤害模型、R28完整起停/转身移动仍按各自台账推进。本轮规范来源和当前输入适配足以产生R06来源身份；不将相邻系统写成完整原版还原。新增`ImpactCancelStart=0`、`RecoilCancelStart=10/60`、`SlingerCancelStart=45/60`、侧向0.2及弹药30/伤害1为明确项目适配值，只有发射触发36取自原TIML。

修改前字节见`Saved/MHWIRestoration/B10-20261025/Backup`、`before-files.json`；HUD补充备份在相同源码相对目录。按[本批变更记录](../Changes/CHG-20261025-005-mhwi-r06-remaining.md)恢复本批覆盖文件，并依导入日志移除32个新增包即可回退；不要重置整个工作区、B08/B09资源或用户此前未提交内容。
