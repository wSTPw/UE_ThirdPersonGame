# ADR-0002：MHWI雌火龙采用原作规则与源数据驱动的执行适配

- 状态：accepted。
- 日期：2026-10-31。
- 关联PLAN / 模块：[首条链路](../Plans/PLAN-20261031-007-rathian-first-chain.md)、[总体方案](../Plans/PLAN-20261031-002-rathian-restoration-master.md)；mhwi-unpack-data、mhwi-rathian-animation、mhwi-longsword。
- 决策依据：用户明确回复“采用推荐组合，按忠实还原优先开始实施，继续分子代理推进”。

## 背景与约束

目标为MHWI普通雌火龙em001，以原作忠实度为首。现有300主体源文件、73外部候选资料、848动画及结构读取不能独立证明行为已还原。真实运行源码为Source，旧C++副本不修改；已存在太刀、地图和资产修改保留。

## 选择与理由

采用用户选定组合：1C THK/thklst规则驱动的窄执行层；2B原作动作时间轴及显式子时钟；3B Pawn+专用Movement；4B原COL几何/骨映射+UE查询；5A专用C++结算与现有Attribute持有HP；6B原始资源→固定版本解析/编译→生成数据与DataAsset引用；7B静态消费者分析加受控原作运行对照。

选择强调原始身份、条件次序、时空轨迹和数值来源可追溯。第一批只覆盖一条有来源的受控子链；未知条件不自动判false，未知时钟不自动设60Hz，raw MV不当最终伤害。严格模式与明确的工程验证模式分开，工程通过不提升为原作运行已验。

这是已接受的目标架构，不等于各运行类/规则/原作验证已经完成。具体实现状态以首链现状及新CHG为准。

## 官方及维护者依据

[Epic UE5.8 PawnMovement示例](https://dev.epicgames.com/documentation/unreal-engine/quick-start-guide-to-components-and-collision-in-unreal-engine-cpp?lang=en-US)支持自定义移动承载；[Traces](https://dev.epicgames.com/documentation/unreal-engine/traces-with-raycasts-in-unreal-engine)支持查询机制；[Data Assets](https://dev.epicgames.com/documentation/unreal-engine/data-assets-in-unreal-engine?application_version=5.8)支持数据资产及软引用管理。它们不证明原作机制。

[Leviathon](https://github.com/AsteriskAmpersand/Leviathon)是THK参考编解码与语言来源；固定commit/本机源hash见取证产物。原生函数及消费时序仍须另行验证，不因外部工具能读取就视为等价。

## 比较过的方案

| 方案 | 成本/收益 | 本阶段未选理由 |
| --- | --- | --- |
| 手工StateTree/BT重写原作决策 | 可视化与维护方便，需重新表达原始规则 | 当前优先保留原条件、调用和事件次序；StateTree仍可用于外围编排 |
| Character/CharacterMovement宿主 | 地面/重力/根运动基础齐全 | 用户选择专用Pawn以直接控制原作运动；不能反推CMC必定无法满足 |
| Montage/Notify作为唯一行为时钟 | 编辑便利 | 原作时钟、层和事件关系需独立保留，UE播放只适配 |
| 自动物理体/简化球扫 | 原型快 | 缺少原生shape、骨与部位身份 |
| 全自研几何求交 | 控制细，验证与实现成本高 | 优先使用能表达原几何的UE查询；遇已证不匹配再局部补充 |
| GAS迁移 | 通用属性/效果及生命周期能力 | 不自动提供原作公式，本地首链不承担无关迁移 |
| 手填DataAsset原作参数 | 调整方便 | 来源、取整和再生成能力不足 |

## 后果与退出条件

必须维护原始资源、parser/tool pins、映射与运行数据的分层；每条已启用语义有证据及资格门。自研组件本身不能证明忠实。UE查询中的旋转扫掠等表达差异需显式记录，保守候选不能直接当精确命中。

不默认用Motion Warping修改原轨迹，不迁移现有848动画或旧训练地图，不为本批拆独立模块或迁入GAS。缺完整原生信息时先解包/追消费者和采样；必要工程夹具单列，保持严格路径拒绝未知。

若已证案例无法由所选UE承载复现、源格式/版本改变、性能无法满足实测要求，重新审查相应局部路线并新增替代ADR；用户已选择的方向不在每次调用前重新请求批准。
