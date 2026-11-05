# R06 / R28 / R30 专项验收（2026-10-27）

> 本文是B20开发前的专项验收历史。后续用户已授权实际调试，六段过渡、Profile及四链求解已在B20落地；当前结果见[B20开发与调试](MHWI-B20-Animation-Development-20261027.md)。本文将common181/182列为必需缺口的裁决已纠正：B10明确排除这两个附带失败请求，不再以它们阻塞完整资源统计。下文其余“本轮未运行”均指本次验收自身。

结论：**三项均不能按完整交付验收通过。** R06可接收代表性阻断的源码修复，保持部分完成；R28仍缺基础移动过渡消费者；R30仍缺Profile资产及四链姿态求解消费者，保持取证中。运行调试由用户操作，本轮没有启动游戏、编辑器、PIE或重新编译，没有修改玩法代码和资产。

基线提交`02a72404a5301c4b313e651b148775fca54193dc`，开始时工作区干净。范围是B19合并后的当前源码、资产字节、[B19交接](../Changes/CHG-20261027-001-mhwi-animation-coverage.md)、[逐连接台账](../Plans/MHWI-Connector-Progress.md)和[总台账](../Plans/MHWI-Restoration-Progress.md)。本轮记录为[CHG-20261027-003](../Changes/CHG-20261027-003-mhwi-r06-r28-r30-acceptance.md)。

## 逐项裁决

| 条目 | 当前可确认 | 不通过完整验收的原因 | 状态 |
| --- | --- | --- | --- |
| R06 连接过程 | 32引用/124身份记录仍在；当前C++有武器mode0的UE BlendIn后备、真实Impact合法恢复分派、菜单来源缓存清理及内部提交阻断 | 原生mode0仍是项目适配；N53/N60来源未全覆盖，332/333/334缺Action78前置，common181/182缺合格来源，32引用无完整运行证据；B19日志在本检出缺失 | 部分完成；修复静态确认，历史运行声明未能复核 |
| R28 基础移动 | 五个既有循环和六个候选文件存在；AnimInstance已新增加减速/落地/转向事实 | 六候选005/006/007/008/014/015没有过渡状态消费者；资格与最终动作语义未闭合，当前未获得运行回归 | 部分完成；候选未接入 |
| R30 装配/IK | 六条武器内部动画文件及四链Profile类型/目标生产代码存在 | 预定Profile资产不存在，ABP无本批节点交付；仅运行制作脚本也不会创建TwoBoneIK；原生solver/坐标/CTM仍未闭合 | 取证中；仅项目数据层落地 |

“87项已处置”指87行都有说明，不表示87项实现或运行通过。本轮重建得到R06 66行、R28 11行、R30 10行；其中81行为`.uasset`引用，共75个不同文件，均存在。其余6行为两个缺源公共motion描述和四条IK源链；不能把`missing_assets=[]`扩称“全部所需动画和求解器已部署”。重建状态标签沿用受版本控制的历史决策，不是此次UE元数据读回。

## R06：修复可以静态接收，完整连接仍开放

当前控制流可确认：

- `MHWICharacterLinkMotion.cpp:181`的`ApplyNativeBlend`遇武器`One0=0`时，使用`InterpolationPoint/60`作为UE BlendIn秒数并返回成功，`NativeBlendFrames=-1`。它解决了播放前拒绝，没有实现原生MotionTree/request mode0。
- `MHWICharacter.cpp:767`的`RequestInput`先保留死亡/阻断等门控，再将真实`NativeSourceMontage`交来源处理，最后才对普通动作施加`IsGestureLocked`。`MHWICharacterNativeSources.cpp:176`只允许Impact在Free/FlinchSmall/Medium/Large且存在合法恢复出口时缓存命令，不全面放开硬直输入。
- `SetInputBlocked:541`清`NativeSourceInput`，`StartResolvedMove:831`检查`bInputBlocked`。因此历史A01/A04中这两处源码缺陷已有对应修复；移动/视角的完整菜单策略仍属R27，不因此关闭。

仍不能关闭的对象：

| 对象 | 未完成边界 |
| --- | --- |
| N53-P0 | node0/node26拥有者完整覆盖仍缺；表中54个身份记录不等于54个已运行入口 |
| N60-P0/P1 | Phase选择与完整来源覆盖未逐条运行；每阶段12个身份记录不能由单条Step恢复代替 |
| 332/333/334 | 缺真实Action78/node51前置；资产存在不构成合法入口 |
| common181/182 | 缺合格来源上下文与导入，保持未处理，不别名补齐 |
| N86-P0 | 入边为空、0记录；继续不可达是正确负例，不计作需强行接入的功能 |
| 其他连接 | 需按实际来源/Phase、请求顺序、MBD入帧、费用一次、事件不补播、中断/死亡/旧令牌与低帧分别验证 |

`native-link-motion-policy.json`的`r06_development_complete=true`来自历史B10生成器；同文件`runtime_connections_verified=0`且32引用仍无运行认证。该历史字段不能覆盖B19及本次“部分完成”的裁决，本轮没有重写历史机器证据。

## R28：变量与资产尚未形成可播放过渡

`MHWIAnimInstance.cpp:155`更新`bAccelerating/bDecelerating/bJustLanded/TurnDirection`，只输出项目移动事实。它没有选择或播放005/006/007/008/014/015；B19提交也没有Content差异。当前`ABP_MHWI_Hunter`仍与其较早Git版本保持同一受跟踪资产，B19交接明确承认未写入状态机。本轮编辑器断开，未重新解析ABP图和父类。

候选路径为`/Game/MHWI/Animations/LongSword/A_w03_00_005`、`006`、`007`、`008`、`014`、`015`（后五项沿用相同目录与前缀）。本轮只核对文件及指纹；B19所述Skeleton、时长、RootMotion/REF_POSE读回文件当前缺失，不能写成本次检查通过。006/007左右转向与014/015落地语义仍未形成最终可靠映射。

关闭条件：先完成合格源采样/骨架与动作语义核验，再把确认的片段接入`/Game/MHWI/Blueprints/ABP_MHWI_Hunter`的真实过渡状态，读回状态条件、Sequence和Slot顺序；用户运行起停/急转/落地与Montage打断回归。五条既有循环的历史短测不替代六条新候选的验收。

## R30：目标生产不等于四链求解

当前`MHWIAnimInstance.h:41`只有可配置的`EquipmentIKProfile`引用；`UpdateEquipmentIK:198`在Profile为空时将四条Alpha清零后返回。磁盘不存在预定`Content/MHWI/Data/DA_MHWI_EquipmentIK_Profile.uasset`，本轮未加载ABP读取CDO，不以文件名推断存在其他Profile绑定。

`Scripts/MHWI/author_equipment_ik.py:20`只创建/保存Profile、写四链骨名并绑定ABP CDO，然后编译/保存ABP；**脚本没有创建TwoBoneIK节点或接通Pose链。** 即使后续执行该脚本，也只能完成配置绑定，不能直接交付四链生效。尚需把ComponentSpace目标/极向/Alpha接入真实求解节点，核对Slot顺序与姿态输出。

目标生产中的握点和脚部探测是项目适配。骨链布局已有来源，但原生solver的坐标、限位、极向、manager字段和CTM仍未解码。四链指`bone_006/007/008`、`010/011/012`、`014/015/016`、`018/019/020`；本轮没有以UE资产重新验证父子关系。

004/005武器内部动画应继续保留、不为凑覆盖编造触发。B19“正式32招只选0/1/2/3”的枚举报告当前缺失；受版本控制的决策仍这样记录，本轮不把它冒充当前DA重新枚举。武器SingleNode内部动画、整件装备挂接和角色骨骼IK是三套不同消费者。

## 证据完整性与实际检查

本次只读MCP状态显示`editorConnected=false`、`mode=disconnected`、`phase=editor exited`；未启动编辑器补验。七份B19引用证据当前均不存在：

`PIE-r06-repairs.json`、`build-r06.log`、`build-animation.log`、`animation-coverage.json`、`weapon-motion-coverage.json`、`editor-api.json`、`R28Preview/report.json`，均应位于`Saved/MHWIRestoration/B19-20261026`。此外待制作的`equipment-ik-profile.json`也不存在。B19“构建Succeeded、PIE 14/14”作为历史交付声明保留，**本轮未读到报告、未独立复核、未再次运行**；缺文件不等同于认定历史执行失败。

重建`audit_animation_coverage.main()`时只把`OUT`重定向到本次独立目录，未改实现或状态决策，未覆盖B19目录。原脚本在缺`weapon-motion-coverage.json`时采用空结果，但随后会用decisions覆盖标签；因此本次输出只能证明处置行/文件存在与历史状态，不能独立证明DA的选择覆盖。

本轮指纹、缺文件清单、Git基线和重建结果保存在[验收离线证据](../../Saved/MHWIRestoration/Acceptance-R06-R28-R30-20261027/offline-evidence.json)及同目录`coverage-rebuild/animation-coverage.json`。文档/diff结果见本轮CHG；本轮没有编译、PIE、姿态截图或UE资产内部属性读回。

## 后续通过标准（运行由用户执行）

| 条目 | 开发/资料前置 | 用户运行验收 |
| --- | --- | --- |
| R06 | 补齐实际来源/逐连接交接及可携带报告；明确原生mode0与项目后备范围 | 先复验拔刀/SpiritI、S/M/L受击两种姿态的合法恢复/非法拒绝、菜单前缓存/阻断/解除；再按32引用逐条记录来源、Phase、连接/主段入帧、费用、低帧、中断/死亡及旧回调。N86为不可达负例 |
| R28 | 六候选完成资格/语义与ABP消费者 | 静止→走/跑→停、前后左右快速起停/急转、落地一次性过渡；动作Montage和空中状态可打断、结束能返回循环，无卡态或脚步明显失配 |
| R30 | Profile保存/读回、四组求解节点实际接入及明确坐标系/更新顺序 | 多角度观察双手握持/纳刀/特殊纳刀和双脚接地；空中/攻击/受击/死亡门控清理；记录接触误差、抖动/漂移及低帧表现。建议2cm仅为项目验收目标 |

未完成上述前置的项目不能只列为“等待用户运行”。本轮验收不自动代做状态机、IK节点或运行调试；现有三项台账状态维持，不增加已完成数量。
