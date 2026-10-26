# CHG-20261024-007：原版还原开发台账与B01原生基础修复

- 状态：partial；B01确定修复已写入并通过针对性验证；全量重建和完整原版还原仍进行中。
- 日期：2026-10-24。
- 用户需求：先制定每项有状态的开发计划，随后直接开发；完整还原为目标，先修确定机制/数值，能解包的数据直接使用，未知参数不猜。
- 关联：PLAN-20261024-005、[开发台账](../Plans/MHWI-Restoration-Progress.md)、R-COMBAT-010、MHWI-005/008/010。
- Git：工作区变更，未提交；保留本轮开始前全部既有改动，未清理工作区。

## 原因与结果

先完成33项状态台账及B01七个可验收子项，通过文档检查后开始开发。B01只改变原文件可直接证明的基值、回槽、成本、颜色分支及五处已有路线，不引入新的取消/反击/根运动参数。

| 实施项 | 旧行为/值 → 当前 | 证据/边界 |
| --- | --- | --- |
| 气刃踏步 | cost12→20；回槽0→10 | W03P0x4b1与COL记录6；18/28条件MV消费者未证明，未盲改 |
| 普通/插入攻击 | 踏步24、纵斩21、突刺12、上挑18、袈裟22；回槽分别26/23/12/12/26 | 从原COL直接读，含DrawSlash、RollStepSlash和两条插入身份，共14招逐窗修正；不是最终原作HP公式 |
| 气刃III/居合二连 | 12+12+12→14+19+34；16+16→18+13 | 既有三个/两个窗口时序保持 |
| 居合气刃已有首击 | 四色一次42→无/白/黄/红17/19/31/39 | 新增颜色基值字段并实际消费；**尚无原版追加shell** |
| 登龙已有七窗 | 每段统一20→白10/黄15/红25 | 只修基值；原有标记、空间、延迟及阶段模型未在本批还原 |
| 普通突刺B | 删除接上挑的新增B出口 | A接上挑保留；上挑B回突刺保留，改为B/A交替 |
| 三种袈裟A | 上挑→突刺 | 保留原有窗口与先决条件；连接片段未在本批补全 |
| 见切A | 纵斩→踏步 | 缺失B/R+A出口未新造窗口；原有反击+回斩命中回旋条件保留 |
| 重建兼容 | 新入口预览/保存/读回/幂等；基础制作两处尾处理复用；窗口配置目标同步纠正 | 未重新制作全部材质/地图/动画；不宣称完成唯一完整生成入口 |

## 修改清单

| 文件/资产完整路径 | 类/符号或属性 | 效果 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/MHWIMovesetData.h` | `FMHWIHitWindow::SpiritLevelDamage` | 新增可选颜色→命中基值map，空map兼容旧Damage |
| `Source/IntroCpp/MHWIUI/MHWIHUD.cpp` | 操作提示 | 删除已不成立的右键循环说明 |
| `Source/IntroCpp/MHWI/MHWICharacter.cpp` | `SweepWindow` | 以动作启动捕获的颜色选择基值，再应用原有倍率/反击倍率；不改去重/提交/清理 |
| `Scripts/MHWI/native_reference_basics.py` | COL/W03P/FSM解析及已确认绑定 | 固定指纹原文件生产来源，保留索引/偏移/字段与未解项 |
| `Scripts/MHWI/author_reference_basics.py` | `run`、`apply_to_copies` | 白名单迁移、全结构保护、幂等/预览、不明路由冲突拒绝覆盖 |
| `Tools/MHW/native-combat-layout.json`、`native-reference-sources.json` | 原读法布局、原文件指纹 | 218字节ATK1记录，原作者布局SHA256可追溯；没有执行第三方模板代码 |
| `/Game/MHWI/Data/DA_MHWI_LongSword` | 既有DamageWindows、颜色map、SpiritCost、Routes | 正式DA已保存；32定义/148路由，只有该Content文件变化 |
| `Scripts/MHWI/author_assets.py` | `moveset`、`animation_corrections` | 完成旧基础制作后统一应用本批规则，防此批字段回退 |
| `Scripts/MHWI/author_native_parameters.py` | 费用白名单 | 增加气刃踏步cost，预览规模18个招式属性+4个全局属性 |
| `Scripts/MHWI/transition_calibration.json` | 五处路线目标/删除规则 | 原窗口数值保留，147条配置规则匹配148条实际路由；仍标项目调校 |
| `Scripts/MHWI/verify_reference_basics.py` | 原始记录重编码、独立基准及交叉检查 | 不启动UE，核对原记录/映射 |
| `Scripts/MHWI/pie_reference_basics.py` | 专项真实PIE | 原值独立预期、攻击回槽/派生正反例、四色首击/三色登龙、精确20槽资格 |
| `Scripts/MHWI/pie_behavior_corrections.py` | 普通连段与登龙预期 | 普通B/A交替替代自定B循环；不再接受旧统一20或降色后错误数值 |
| `Docs/Plans/MHWI-Restoration-Progress.md`及现状/接口/模块索引 | 状态与交接 | 33项逐一跟踪，首批完成范围与未解边界分开 |

## 接口、事件与资产迁移

新增反射map为可选字段，旧资产为空时沿用旧Damage。当前实际伤害仍为简化适配器，MV基值不等于完整原作HP计算。字段使用捕获颜色，正常颜色消费发生在已有流程；未更改事件顺序、回调身份或本地玩法/联网边界。

用户随后明确开发优先：本批现有结果保留，不再扩展/重复复杂长测。全量重建、复杂地形/技能/部位矩阵及原作逐帧录像列下一步验证。

按有限白名单变更采取“全文件备份→复制结构预览→幂等/保护检查→正式DA保存→新进程加载→真实PIE”，未为本批额外复制候选地图/Pawn。大规模后续动画/状态迁移仍按总方案使用候选资产。地图、Montage、Sequence、模型、材质和蓝图磁盘字节均保持。

## 实际验证

| 检查/命令 | 实际结果 | 证据 |
| --- | --- | --- |
| 文档先行 | 台账完成后文档检查通过，随后才改源码/资产 | 本轮工具记录 |
| `Build.bat IntroCppEditor Win64 Development -Project=... -WaitMutex -NoHotReloadFromIDE` | 完整UHT/C++构建Succeeded，63.88秒；受影响蓝图编译调用成功 | `Saved/MHWIRestoration/B01-20261024/build-full.log`、`apply-result.json` |
| `python Scripts/MHWI/verify_reference_basics.py` | 原COL共75攻击记录、4500字段重编码一致；与前轮独立提取75记录交叉一致，W03P425字段验证通过 | `source-verification.json` |
| 预览→保存→再预览 | 幂等/保护检查通过；首次保存只改正式DA；新编辑器进程加载后预览通过，证明磁盘序列化可读 | `preview.json`、`authored.json`、`apply-result.json` |
| 原生基础专项真实PIE | passed，120.734秒、186断言；19个普通/路线观察案例，另有白黄红首击及完整登龙链 | `PIE-reference-basics.json` |
| 气刃踏步实际成本/回槽及精确边界PIE | passed，8.953秒、66断言；生产动作构造0→23→8→20，低槽拒绝、恰20启动扣20、命中回10 | `PIE-reference-basics-step.json` |
| 窗口配置/旧参数入口预览 | 147项目窗口规则与修正后路由兼容；旧参数入口18+4预览成功，未执行其save | `compatibility-preview.json` |
| 本轮ground真实回归 | passed，54.125秒、97断言；气刃插入/B-A交替/翻滚出口/见切条件等 | `PIE-ground-regression.json` |
| HUD操作提示 | 移除失效的右键循环说明，普通C++ Live Coding编译success；核心反射已由前述完整构建验证 | 本轮工具返回及编辑器日志 |
| 最终文档/差异/资产范围检查 | 收尾报告记录实际结果 | `final-verification.json` |

上述证据均位于`Saved/MHWIRestoration/B01-20261024/`。专项目标跟随夹具隔离命中基值与路由消费，不证明原版刀刃空间、shell起算或逐帧取消；断言数量不代表完整还原率。

过程失败如实保留：第一次构建从项目目录调用报批处理目录错误；切换引擎Build/BatchFiles目录后完整构建成功。第一次Python命令行迁移调用不存在的LevelEditor UI状态查询，发生原生访问异常，正式DA哈希仍与备份一致；区分命令行环境后重试成功。相关原日志`build.log`、`apply.log`保留，失败场次未计通过。

未执行原作进程采集、游戏启动或安装目录修改；未猜Q衰减周期/十秒保护消费者/回旋清槽时点/连接入帧/延迟shell起算。未重新跑全部方向/空中/生命周期套件；新增专项已真实走过三色完整登龙阶段，其他历史验证仍属于历史。

## 遗留与回退

R04/R14/R15/R16/R32/R33仅部分覆盖，R18/R19/R22及其余完整主角问题继续开放；下一批优先从原文件和消费者证据解决条件攻击值、输入/派生资格及延迟命中，未确认时继续取证。

回退仅使用`Saved/MHWIRestoration/B01-20261024/Backup/`和`before.json`中的本批前副本，核对用户后续改动后恢复指定文件；反射回退需要重新编译。不要整体重置项目或删除用户未提交资产。原安装与原始源数据未改，不需要回退它们。

## 同步

[开发台账](../Plans/MHWI-Restoration-Progress.md)、[总方案](../Plans/PLAN-20261024-005-mhwi-original-restoration.md)、[系统现状](../Systems/MHWI-LongSword.md)、[接口](../Interfaces.md)、[参数批处理边界](../Reference/MHWI-Native-Parameter-Pipeline.md)、[修复前审查](../Reference/MHWI-Restoration-Review.md)、[已知问题](../Known-Issues.md)、总入口/方案/记录索引和模块索引同步更新。
