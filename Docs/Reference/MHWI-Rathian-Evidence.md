# 雌火龙取证结论总账

对象：`em001` = **雌火龙（Rathian）**，下位 LR，单人。火龙（Rathalos）是 `em002`，数据另行提取于 `ArtSource/ThirdParty/MHWRathalos-em002/`。

编号依据：`em001.dtt_epg` 的 `Monster_Id=9`、`em002` 为 1；名称表 ID 9=雌火龙。痕迹文本 `tr_em001_02`="金色的鳞片"、`em002_02`="银色的鳞片"。**此前把 em001 当火龙是判断失误**，所有"火龙"数值实为雌火龙。

本页汇总已确证结论与未解清单。原始报告在 [Archive/MHWI/](../Archive/MHWI/README.md)。

## 一、数据在哪、怎么复现

| 项 | 值 |
| --- | --- |
| 提取范围 | `em/em001/00/` 全部 297 项 + `common/item/em001{,_01,_02}.itlot` 3 份 = 300 |
| 体积 | 76.97 MiB |
| 落盘 | `ArtSource/ThirdParty/MHWRathalos/nativePC/`（保持游戏内相对路径） |
| 清单 | `ArtSource/ThirdParty/MHWRathalos/extraction-manifest.json`（逐文件包名/偏移/尺寸/SHA256） |
| 机器可读 | `Tools/MHW/em001-datamine-manifest.json` |
| 分组 | AI 思考表 105、碰撞 42、招式判定 37、贴图 20、动作库 19、动作混合 10、IK 4 |

**"下位"不在目录维度，在文件内部**：`em001.dtt_sta` 单文件并列 `Fatigue_LR_/HR_/MR_`；`Parts1/2/3` 同时含 `Part_Id_LR_HR1_*` 与 `Part_Id_MR1_*`。取 `00/` 目录中标注 `LR` 的段。

> 推断（未证实）：`00/01/02` 对应本体/亚种/稀少种。依据是 `actp2` 205,037 / 223,957 / 262,569 B 的差异、`02/` 独有 shell ID 100–151、以及三份 itlot。**不要据此主张变体身份**。

## 二、已解码数值（字节完全消费）

### 2.1 基础与部位（`dtt_epg`，Blowfish）

Monster_Id 9；Health 3000；部位组 7；命中部位 12；切断 1（`Sever=300`）。

肉质表（12 组，单位 %）：

| # | 斩 | 打 | 弹 | 火 | 水 | 冰 | 雷 | 龙 | 气绝 | 夺取 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 70 | 75 | 65 | 0 | 15 | 15 | 20 | 30 | 100 | 100 |
| 1 | 40 | 45 | 35 | 0 | 0 | 0 | 5 | 15 | 0 | 100 |
| 2 | 35 | 30 | 25 | 0 | 5 | 5 | 10 | 20 | 0 | 100 |
| 3 | 35 | 30 | 25 | 0 | 5 | 5 | 10 | 20 | 0 | 100 |
| 4 | 55 | 50 | 45 | 0 | 10 | 10 | 15 | 25 | 0 | 100 |
| 5 | 40 | 40 | 35 | 0 | 0 | 0 | 5 | 15 | 0 | 100 |
| 6 | 45 | 40 | 35 | 0 | 5 | 5 | 10 | 20 | 0 | 100 |
| 7 | 60 | 65 | 45 | 0 | 15 | 15 | 20 | 30 | 100 | 100 |
| 8 | 37 | 45 | 30 | 0 | 0 | 0 | 5 | 15 | 0 | 100 |
| 9 | 21 | 21 | 45 | 0 | 10 | 10 | 15 | 25 | 0 | 100 |
| 10 | 37 | 37 | 25 | 0 | 0 | 0 | 5 | 15 | 0 | 100 |
| 11 | 45 | 37 | 30 | 0 | 5 | 5 | 10 | 20 | 0 | 100 |

**组号→部位名已 cross-verified 闭合**（本机表 vs monsterhunterwiki.org 逐行一致，NUM-03）：行 0=Head、1=Neck、2=Body、3=Back、4=Wings、5=Legs、6=Tail、7–11=MR 各部位变体（MR Wings 21/21/45 精确匹配）。

硬直阈值（`Flinch_Value`，7 组）：**240 / 300 / 180 / 180 / 210 / 210 / 200**，对应 Head/Body/L翼/R翼/L脚/R脚/Tail。每组另带 `Special_Part_1..3`（最后一组为 0，其余 −1）、`Kinsect_Color`(0–3)、`Parts_Type`(1/2)。**累计伤害触发哪类硬直/倒地的语义未解**。

### 2.2 发怒（`dtt_agr`，明文 144/144）

2 组 `Rage_Stats`（偏移 16、80）数值相同：

| 字段 | 值 |
| --- | ---: |
| Build_to_Trigger | 600 |
| Duration | 80.0 s |
| Speed_Modifier | ×1.05 |
| Damage_Modifier | ×1.15 |
| Player_Damage_Modifier | ×1.10 |
| Out_of_Combat_Decay | ×0.10 |

血量分段累积倍率（HP 100 / 88–99 / 77–88 / 66–77 / 55–66 / 44–55 / 33–44 / 22–33 / 11–22 / 0–11）：
`0.5 / 0.5 / 1.0 / 1.0 / 0.5 / 0.5 / 0.5 / 2.0 / 2.0 / 2.0` — 低血量段（<33%）是常规段 4 倍。

### 2.3 疲劳（`dtt_sta`，明文 92/92）

| 等级 | 疲劳时长 | 耐力区间 | 基础值 |
| --- | ---: | ---: | ---: |
| LR | 70.0 s | 500–600 | 500 |
| HR | 60.0 s | 650–750 | 650 |
| MR | 50.0 s | 800–900 | 800 |

另有 `Stamina_Count=1`、`Fatigue_Speed=0.9`。

### 2.4 状态值与抗性（`dtt_eda`，Blowfish；888 B + 8 B 全零尾）

| 状态 | Base | 每次累积 | 上限 | 持续 |
| --- | ---: | ---: | ---: | ---: |
| 毒 | 250 | 150 | 700 | 15 s |
| 睡眠 | 150 | 100 | 550 | 40 s |
| 麻痹 | 180 | 130 | 570 | 10 s |
| `Stun`（上游命名） | 120 | 100 | 620 | 7 s |
| 疲劳累积 | 225 | 75 | 900 | — |
| 乘骑 | 40 | 70 | 460 | — |
| 爆破 | 120 | 60 | 720 | — |
| 捕获 | 150 | 200 | 300 | — |

毒衰减 10 s / 5 点；毒伤 5 点 / 每 2 s 一跳。其余：口水硬 `Clagger` 300/300；乘骑击倒伤害 100；爆破伤害 100；疲劳伤害 150；捕获阈值 LR·HR 30% / MR 25%；麻痹陷阱 8 s（每次 −2，最小 2）；落穴 10 s（每次 −2，最小 2）；藤蔓 8 s 无递减；粪 30 s。

**气绝三套并存，语义未定，不得合并**：`Dizziness_LR_HR`（20 s，每次 −4，最小 5）、`Dizziness_MR`（累积 60/上限 90/再充能 150 s）、`Concussion`（Base 100/上限 100）。

## 三、格式解析边界

| 数据 | 文件 | 状态 |
| --- | --- | --- |
| ACTP2 | `em001.actp2` 205,037 B | 完整消费/重编码一致；342 记录（142 启用）/4,295 属性项。111 种具名属性中**无直接数值型伤害/击退字段** |
| COL | 42 份（主 35 + shell 35 攻击记录，6 份无攻击） | Names/CLND/CLGM 边界与 70 条 Atk2 字段已读；几何语义与 OAP/CRC 尾部 opaque |
| SHLP | 37 份 | 只含 EPV 索引、关节号、碰撞/时间轴路径、子判定、音效、投射体，**无伤害/击退/气绝字段**。它引用 COL，不能推出数值只能在 ACTP2 |
| PBC | `em001.em_pbc` 256 B | 类 CRC 命名为 `rEmPartsBreakCtrl::PartsInfo/PartsStateInfo/PartsDetailInfo`；加载链 Info→State→Detail；48 B 只是当前计数展开长度，**不是通用步长**。耐久语义 unknown |
| EM_DMG | `em001.em_dmg` 7,620 B | 受击动作选择，未完整解码。**不是攻击伤害表** |
| THK | 105 + 1 thklst | 解析资格通过（1795 节点 / 13,015 段，Leviathon `1e647f08` 字节重编码一致）。语义见第四节 |
| 动作库 | 19 LMT（7 个 16 B 空壳，实有 12） | 848 非空动作已导出导入 |
| 模型 | 2 MOD3 + 2 MRL3 + 20 TEX | 本体 141 骨/25 网格/67,445 面；尾巴 2 骨 |

**原始攻击字段 ≠ 实战伤害**：`空中必殺キック` Motion_Value=75 / 击退 Type17 Lvl0，`地上かみつき` 30 / Type16 Lvl0 都是文件原字段。整个 `00/` 碰撞资源混含 G 级原名标签，不是下位专用表。

复现：

```powershell
python Scripts/MHWI/read_action_params.py --self-check
python Scripts/MHWI/read_monster_collision.py
python Scripts/MHWI/inspect_parts_break.py --self-check
python Scripts/MHWI/inspect_parts_break_native.py
```

## 四、THK 决策语义（BEH-01）

### 已闭合事实

| # | 事实 |
| --- | --- |
| F1 | 锁定地址对应 `analysis-text.bin` 的 VA，不是 exe 磁盘偏移 |
| F2 | `vm_tick`(0x1423fe8d0) 是主循环：`[rcx+0x10]` 计数门控，288 B 步长数组 + 64 B 节点槽两层迭代，每节点先调守卫 `0x1423fc990` |
| F3 | `0x1423fc990` 是 30 B 守卫函数（`cmp [rdx+0x30],0`），**不是** functionType 分发器 |
| F4 | THK 段 128 B：`endRandom@0`、`flowControl@1`、`branchingControl@2`、`functionType@+8`、`parameter1@+12`、`parameter2@+32`、`actionID@+76` |
| F5 | functionType 全量 13,015 段有值，**仅 60 种**（max 202）。头部 `0x2`(7947)/`0x0`(2877)/`0x70`(263)/`0x8`(258)/`0x5`(248)/`0x5a`(186)。32/60 参数组合唯一 |
| F6 | 咬击链 ctx55 画像：`(bc=2,ft=0x1f,p1=0,p2=0)`×43 = 冲撞分支谓词；ft6 参数 600、ft8 参数 1000（阈值类候选）；ft0 参数 20/25/30/35/50（权重类候选） |
| F7 | **负结果**：四种跳转表编码穷举 + 2,857 个 `jmp reg` 站点回溯，无 >202 条目分发表；VM 模块内 0 个注册器（0x14216ed60）调用 |
| F8 | `name_lookup`(0x142400150) 是字符串注册表遍历器（`[node+8]`=串指针、`[node+0x28]`=next） |

推论（未证）：functionType 分发走**运行时注册对象/字符串注册表**机制，注册发生在启动期静态初始化区（`0x1401e15c0` 一带），不是编译期 switch。

### 社区映射（2026-11-03 起的主路线）

Leviathon `default.fexty`（本地缓存，commit `1e647f08`）提供 **27/58 条件类型的社区命名，覆盖 81.5% 条件段使用**，参数形态全部自洽：

| functionType | 候选语义 |
| --- | --- |
| `0x6` / `0x8` | 距离（cm） |
| `0x16` | 角度对 |
| `0x1E` / `0x1F` | 发怒 / 疲劳 |
| `0x70` | 飞行 |
| `0xB8` | `current_quest().is_rank(LR/HR/MR/AT)` |
| `0x76` | 部位破坏 |

首链冲撞分支 `0x1F`=疲劳，与 86 常态 / 87 疲劳变体自洽。

**这些是社区命名，不是已证语义**。剩余 27 类逐项参数校验、33 类低频缺口未做；数值巧合（如 ft6 参数 600 恰等于 `Build_to_Trigger`）不得写入忠实 profile。

### 未闭合原因

分发是注册表 + 对象虚调用，闭合语义需要 Ghidra/IDA 级类型恢复（枚举 2.4 万注册桩→解析描述符→关联虚表→逐个反编译），ad-hoc capstone 脚本已用尽。运行采样（hook `vm_tick`/`name_lookup` dump 注册表）需用户授权启动原作。

## 五、动作身份与首链（2026-11-05 更正）

**旧"344 条 name↔id↔vtable 完整注册表"口径已撤回**——旧提取器 `dump_action_registry.py` 从名称指针起读，相位错位 +8。

新布局（stride 32 B）：`{id32+pad32, type_descriptor@+8, unknown_qword@+16, name@+24}`，记录步长 32 B。已由原生注册循环证实：`0x1413918b0`（表指针 getter，`0x143ef0590 + index*8`）、`0x141c29c92`（R9D=285）、`0x141c29ca0`（R8=0x142e62f60、EDX=1）、`0x141bfcfe0`（读 +8 描述符、+0 的 ID32）、`0x141bfd023`（+24 名称写对象+0x20）。

| 动作 | id | 描述符 |
| --- | ---: | --- |
| `ACTION::NONE` | 0 | 0 |
| `ACTION::IDLE` | 1 | `0x144f36fe0` |
| `ACTION::BITE` | **83** | `0x144f37c58` |
| `ACTION::BITE_NO_BLEND` | 84 | `0x144f391c8` |
| `ACTION::BITE_FLY` | 85 | `0x144f36b10` |
| `ACTION::DASH_BITE2` | 86 | `0x144f38518` |
| `ACTION::DASH_BITE_TIRED` | 87 | `0x144f38470` |
| `ACTION::RASH_BITE_FLY` | 88 | `0x144f39200` |

em001 表头（VA `0x142e62f60`，磁盘 `0x2e61560`；BITE83记录磁盘偏移另为 `0x2e61fc0`）索引 1 的 **285 条与固定维护方 dump 285/285 一致**；索引 2/3 分别 59/59、131/131 匹配 em002/em003。这是静态交叉一致，不是运行验证。

**仍未证**：THK actionID → 动作对象查找/启动；注册 caller 的怪物对象归属（注册 caller 范围 `[0x141c29c80,0x141c29dc9)` 与既有 em001 候选 vtable 写入点 `0x141c283a1` 属不同范围，地址相邻不等于同属）。

### 动作83查找与启动补证（2026-11-06）

本轮使用原生 `gpt-6-luna/high` 执行与全新Luna独立审查，DevFlow最终快照 `5735540e…8bb4564` 的静态证据产物为ACCEPTED；**这不表示原作启动链或完整首链通过**。[证据JSON](../../Tools/DevFlow/Rathian-BITE-Dispatch-20261106/accepted/evidence.json)、[原始报告](../../Tools/DevFlow/Rathian-BITE-Dispatch-20261106/accepted/report.md)、[验收回执](../../Tools/DevFlow/Rathian-BITE-Dispatch-20261106/accepted/acceptance.json)。

| 分段事实 | 资格及边界 |
| --- | --- |
| `0x140269c30` 在注册receiver上调用描述符虚表+0x10，并把返回指针存入selector/ID形状的槽 | 原生静态局部事实；尚不证明返回BITE、新建对象或与后续receiver同一实例 |
| `0x140269ce0` 按selector取得count、unsigned比较ID/count并检查槽非空，然后写键状态、返回bool | 原生静态局部事实；窗口内无明确selector范围检查，不称完整键校验 |
| `0x14026b410` 给helper传原RDX作receiver；成功后给 `0x14026b160` 传原RCX作receiver，同样转交key | 两次调用使用不同入参；两值相等/归属关系仍未知 |
| `0x14026b160` 的可见虚调用为+0x28；固定BITE虚表+0x28为 `0x14023d430`，+0x30为已知enter `0x14073ee50` | 不能把该回调直接当BITE enter；间接启动可能性未排除，仍需追消费者 |

四段连接当前为：THK83→动作键 **unresolved**；键→BITE对象 **candidate**；对象→enter **unresolved**；注册caller怪物归属 **unresolved**。14个原始锚、3段源码行hash及9项冻结数据检查只证明可追溯，不是原作运行验证。源码仍是本地executor yield后核对ID再启项目移动/碰撞，未据此声称原生BITE对象派发已接入。

下一顺序：先找THK action字段到键请求的递交者；核 `0x14026b410` 调用者提供的两个receiver；再追callback记录填充及 `0x14023d430 → +0x30` 的可能消费者，最后补caller对象归属。现有文件够本轮静态调查，未定向解包、未启动原作/UE，Sandbox保持暂缓。过程与未通过记录见[本轮CHG](../Archive/MHWI/Changes/CHG-20261106-001-rathian-bite-dispatch-devflow.md)。

### 社区资料定向补证（2026-11-06）

已查维护者一手源码并锁提交，[来源/本机匹配清单](../../Tools/MHW/rathian-community-dispatch-20261106.json)。这是只读研究，**没有把上轮冻结产物重标为完成，也没有新的运行验证**。

- SharpPluginLoader提交 `0790c5f1…` 的地址记录与解析代码给出扫描签名及有符号字节偏移。在固定.text中，`Monster:LaunchAction` 仅一处命中，解析为 `0x141cc5360`；`Monster:ForceAction` 仅一处命中，解析为 `0x1413973b0`。
- `ActionController:DoAction` 的签名在已有函数窗口匹配，应用-10字节偏移后正是 `0x140269ce0`；未额外声称其全镜像唯一。这是社区命名与本机字节的静态对应，不是Capcom符号或行为已证。
- HunterPie/LuaEngine/SPL的字段访问可互相对应：actor+0x61C8作controller基址，current相对+AC/+B0即actor+6274/+6278，next相对+BC/+C0即actor+6284/+6288。不能把绝对/相对偏移误判为版本冲突。
- SPL对 `cActionBase` 将slot5/6/7/8命名为初始化/执行/更新/结束，对应+28/+30/+38/+40；只有先证明回调对象类型，才可套用生命周期名称。其通用DoAction接口还明确建议怪物使用Monster.ForceAction，不能把玩家/通用接口直接当怪物递交。
- 尚缺THK83到LaunchAction输入的调用边、receiver/BITE实例归属和真正execute。下一步优先沿两个已定位地址查递交/对象关系，继续保留未知；未安装、注入或调用任何插件。[本轮记录](../Archive/MHWI/Changes/CHG-20261106-002-rathian-community-dispatch.md)。

### 首链最小候选

`em001_55.thk:n200/id217` → `raw emit 83`：段起点 199,712、段数 5，action 位于 199,968+76=**200,044**，值 83，五个附加动作参数均 0。

九步候选路径（假设 `0x70(0,0)=false`、`0x16(90,270)=false`），控制解释来自维护方反编译器和项目 normal form，**不是原作 VM 运行轨迹**：

| 步 | 段 | 偏移 |
| ---: | --- | ---: |
| 1 | n200.s0 调用 n2 | 199712 |
| 2 | n2.s0 `0x70` 假跳 | 5536 → 6432 |
| 3–4 | n2.s7/s8 branch8、flow8 | 6432 / 6560 |
| 5 | n200.s1 调用 n198 | 199840 |
| 6 | n198.s0 `0x16` 假跳 | 198816 → 199200 |
| 7–8 | n198.s3/s4 | 199200 / 199328 |
| 9 | n200.s2 yield action 83 | 199968 |

真实调用者 n314/315/316.s0 位于 381088/382368/383776，带 `endRandom=0x40`、权重候选 25/20/25。**LR 实际可达性必须单列**。

### 根轨与时钟

`em001_02.lmt` slot1 头@1968，`frame_count=131`。usage4 位置记录@13824（codec4，payload@23088，232 B，lerp@20016），29 键独立解码、0..130 整数采样与 `Saved/MHWI-Rathian-FirstChain-20261031/selected-source-track.json` 逐点误差 0。

项目映射 `[x,z,y]`：t10=t80 源 `[6.68205595,0,49.9655838]` → 映射后 `[6.68205595,49.9655838,0]`；t111=t130 源 `[51.3980103,0,-7.8466053]` → `[51.3980103,-7.8466053,0]`。

相邻组@41032 的轨 hash `0x2ac902e3`（dump 名 `mMotionSpeed`）键：`(0,0.9)/(25,0.9)/(35,0.35)/(70,0.9)`，插值 1/2/2/1。**须追实际消费者，不能据名字改播放速度**。

UE 时长 2.166666746 s ≈ 130/60，只证明导入采样映射。原生 clock/rate、速度键作用于动画还是位移、入动作朝向、根旋转消费均未知；`UnitsPerSecond=0` 保持不变。

### 三组碰撞通道

LMT Node0/1/2 原始键 @42128/42160/42192，值 **32/21/24**；flags@42224/42244 为 `(value7,mask7,frame0,type5)→(value0,mask7,frame23,type5)`。

| UID | COL 名称记录 | geometry | attack |
| ---: | --- | --- | --- |
| 32 | #22@861 | #14@11811，5 胶囊 | #7，`MotionValue=30`@31044 |
| 21 | #33@1365 | #29@19488，1 胶囊 | #14，`MotionValue=0`@32241 |
| 24 | #34@1405 | #30@19635，1 胶囊 | #14，同上 |

几何 14 的五胶囊子记录 @11827/11899/11971/12043/12115；MOD3 remap@21600 复核 `3→8, 4→9, 100→3, 101→4, 102→5, 103→7`。

**现状提取器 `extract_rathian_chain_collision.py` 只选 Node0**。三位 flags 各驱动哪个 Node、是否用于伤害，仍缺消费者。后两组 `MotionValue=0` 既不能证明无作用，也不能证明伤害。

## 六、未解清单

| 编号 | 问题 | 归属 |
| --- | --- | --- |
| BEH-01 | THK 条件语义：27 类待逐项校验，33 类低频缺口，验证数为 0 | E01 / 定向观测 |
| BEH-02 | THK83→动作键未证；键→BITE对象仅候选；receiver身份、callback→enter与caller怪物归属开放，见第五节11-06增补 | E02 / 当前M0 |
| BEH-03 | LR 招式资格表未建立（342 ACTP2 ≠ LR 招式表）。已有路线：用 `0xB8` 等级门控从 THK 反推下位可达动作，分母不再用全量 | P1 |
| BEH-04 | 同帧多事件状态优先级表无原作证据（工程幂等契约已有） | AI-08 / C5 |
| BEH-05 | 咬击/冲撞之外 105 THK 的其余链路未逐条提取 | E01 / AI-07 |
| NUM-01 | 任务倍率（任务 HP/攻击/部位耐久/体型）未闭合。HP 3000 不是任务实战 HP | E05 / C0 |
| NUM-02 | 最终伤害公式（乘法顺序/上限/逐段取整）未闭合 | E05 / C3 |
| NUM-04 | PBC 破坏耐久（2006/2007 语义）。`Sever=300` 不是任务最终阈值 | E04 / C4 |
| NUM-05 | Stun / Dizziness / Concussion 三套气绝语义未定 | C5 |
| NUM-06 | 断尾后毒判定资格、闪光/陷阱免疫递增未取证 | C4 / C5 |
| ANIM-01 | bank/slot → UE 资产语义映射表首版已生成，资格列仍多为 unknown | A0 |
| ANIM-02 | Rathian 专用 ABP/Montage/播放组件未建（当前零播放层资产） | A3 / M2 |
| ANIM-03 | 部位破坏/断尾网格映射（PBC → mesh section）未闭合 | E04 / A2 |
| ANIM-04 | `_fs` 叠加层/常量轨/NeedsParent 语义未解 | A1 |
| ANIM-05 | CMML 染色通道、FM 毛发 shader、LOD1/2 未做 | A2 |
| AV-01..06 | 73 个 raw 音画文件已清点；源事件→动作→UE 资产映射表有骨架无内容；NBNK/EFX 未解码；UE 侧零音频/特效资产 | A5 / E08 |
| R-DATA-007 | 首链分别配置移动/碰撞，不核对共享时间单位/速率/clip 身份；`EvidencePinsJson` 仅声明未消费 | 统一 ActionSpec |
| R-COMBAT-013 | 首链接触同 shape/同区间按 Actor 后写覆盖较早精确 TOI；首尾轴一致不证明中间骨轨纯平移 | TOI 与骨轨验证 |
| R-ANIM-013 | `InPlaceSequence` 只验骨架/时长；旧导出保留 `bone_root` 平移，导入未明设根提取/锁根。该 bank 历史抽检为 181 而非 001 | 只读 001 根轨 |
| R-AI-003 | strict 条件 resolver 只查工程条件；到 EndTime 直接 `Thk.Cancel`，未接 `ResumeAfterAction` | 原生条件 provider |

## 相关现状页

- 当前实现（首链 + B1 近似线）：[MHWI 雌火龙](../Systems/MHWI-Rathian.md)
- 架构决策：[ADR-0002](../Decisions/ADR-0002-mhwi-rathian-source-runtime.md)
- 历史报告：[Archive/MHWI/](../Archive/MHWI/README.md)
