# PLAN-20261107-004：玩家受击、怪物攻击衔接与单火球动画修正

- 状态：implementing（2026-11-08续办）
- 日期：2026-11-07
- 用户要求：玩家受击动作选型错误、怪物攻击无过渡、单火球动作错误，立即修复。原三档玩家受击与力度约定继续有效；此前保留工程火球占位的选择已被本次要求取代。
- 范围：现有UE5.8 Native动画执行链；只恢复相关资产的定向取证，先现有源文件。原作不启动，Sandbox/系统不修复，不自动重启或关机。

## 官方机制与证据边界

先查UE5.8 [Montage属性](https://dev.epicgames.com/documentation/unreal-engine/animation-montage-editor-in-unreal-engine)、[Blend Nodes](https://dev.epicgames.com/documentation/unreal-engine/animation-blueprint-blend-nodes-in-unreal-engine)、[Root Motion](https://dev.epicgames.com/documentation/unreal-engine/root-motion-in-unreal-engine?lang=en-US)及本机引擎源码。Standard crossfade可在前片淡出时交接，不应以“未等零权重”单独判错；混合秒数不能补出缺失的原片起手/收招。新的实质架构方向若有多个候选，依AGENTS先呈现可复核方案再选择；优先修正现有执行路径与真实片段。

本批必须区分“播放了配置片段”“片段用途正确”“原作运行调度等价”。CHG-003仅修低帧可见性，没有证明选型语义；旧通过记录保留历史，不升级资格。

## 现状与已发现线索

- 已确认玩家三档选型错误：B10 remaining-native-functions.json 的 registry_name 明确指出 3:30/31/32 是 WP_03::STEP_S/M/L，1:103/110/115 是 Common::STEP_S/M/L；它们映射到 w03 61/62/63 和 co70/71/72。原生身份绑定确实存在，但它是STEP载体，不能证明受击资格。用户明确反馈小中大三档均不像原作。本批撤回其受击语义，定向定位 nHmAction 的 DamageS/Slip/Smash/DownStandup 真正入口与动画槽。
- 怪物多数阶段混合0.02/0.08秒；龙车前摇为idle短截、恢复为咬击后段。需实际端点/连续播放和正确起收动作，不能仅加blend时间。
- 当前火球00_081无shell事件。新候选02_081是4秒/241键，TIML frame23触发shell0；shll路径与维护方ACTION::NORMAL_BREATH_SHOT单弹映射吻合。需UE预览才能确认视觉，原作action→motion调用边仍不得宣称闭合。
- 多名原生Luna只读分工：玩家语义/根轨、火球事件、全848片启停曲线；主代理独占UE，避免并行改世界。

## 实施与验收

1. 建本轮保护指纹；原875文件不改，Basic资源仅明确本批差异，新片段独立命名。
2. 真实UE预览正确bank/slot、完整前摇→动作→恢复；核源事件和轨迹。玩家按用户已明确的“三档均错误”调查；禁止继续用STEP片段进行自比对验收。
3. 冻结需要改动的最小C++/脚本合同，Luna执行→固定检查→全新Luna审查→主审→核hash合入；主代理配置已确定资产。
4. 适量离线构建、重启实际UE；PIE验证语义表现、动作边界骨姿连续、单发时点、玩家三档/轨迹/落地恢复、低帧/中断/死亡。正确源片对应不能替代完整演出。
5. 更新现状/接口/模块/问题、CHG-004及交接，记录实际失败/未覆盖项。来源/候选不足且需决策时才向用户提出具体可审阅选项。

## 回退

源文件/配置逐字节备份并核hash；不reset工作区。只撤本批新资产/配置和接受后的源码差异；原训练地图、太刀DA和用户其他修改保留。所有瞬态预览Actor与调试设置必须清理。

## 2026-11-08实施拆分

- 继续使用devflow-orchestrator；怪物三文件合同已冻结到 MONSTER-ANIM-20261108-4157550ee1，尚未接受或合入。修正火球为02_078起势→02_081全片，在shot源帧23延迟发射；龙车取消idle前摇和咬击恢复；保持现有Standard Montage与资格边界。
- 新建1490个MHWI资产/Source文件保护基线 Saved/AnimationSemantics-20261108/baseline.json。昨天5个玩家姿态候选仍未用于正式受击，不能凭外观或编号认定用途。
- 本轮UE启动已完成并打开Basic地图，PIE未启动；startup日志的UnifiedErrorTest/Condition failed出现在引擎初始化自测阶段，未导致启动失败，不是本批玩法测试结果。瞬态预览与后台节流设置会在结束时清理。
