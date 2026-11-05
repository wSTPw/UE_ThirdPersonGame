# CHG-20261030-002：太刀五项操作修正

- 状态：partial；四项已实施，见切精确窗口未闭合；后续运行验收由用户操作
- 日期：2026-10-30
- 需求摘要：连携后侧后翻滚、特殊纳刀自由方向、见切早期派生、无刃突刺、独立气刃出刀；整体动画保留，IK暂缓。
- 关联：[方案](../Plans/PLAN-20261030-001-mhwi-five-controls.md)；B23-01..05；MHWI-001/MHWI-015。
- Git：工作区变更，未提交。

## 原因与结果

五项均记录于方案。显式Evade路线跳过方向选择；特殊纳刀沿用普通转向预算；SpiritThrust入场要求颜色；收刀Spirit映射DrawSlash。以上为静态发现。见切原始标志存在早窗，但精确命令许可尚未闭合，用户要求先取证再修复。

## 修改清单与接口影响

| 文件/资产 | 实际改动 |
| --- | --- |
| `Source/IntroCpp/MHWI/MHWICharacter.cpp` | ResolveInput的显式Evade→Roll按SelectRollMove选择四方向；保留来源条件及取消窗。SpecialSheathe成功启动后按Controller yaw与MoveInput一次选定朝向，不再消费普通有限转向预算；无输入保留朝向。中立Spirit统一进入SpiritI。 |
| `/Game/MHWI/Data/DA_MHWI_LongSword`（UMHWIMovesetData） | 仅SpiritThrust.bRequireSpiritLevel由true改false；所有其他招式序列化相同，该招式复原此字段后序列化亦完全相同。CanStartHelmStage仍要求SpiritThrust真实命中且SpiritLevel>=1。 |
| `Scripts/MHWI/author_assets.py`、`author_behavior_corrections.py` | 同步SpiritThrust制作默认值，避免重跑恢复旧限制。 |
| `Scripts/MHWI/author_followup_combat.py` | 单字段迁移、原文件备份、全招式保护和保存读回。 |
| `Scripts/MHWI/pie_followup_directions.py`、`mcp_five_controls.mjs` | 本轮方向回归与限定MHWI脚本目录的编辑器执行入口。 |
| `Scripts/MHWI/extract_foresight_window_evidence.py`、`Tools/MHW/foresight-window-evidence-20261030.json` | 固定原文件指纹、早期输入位及命令绑定取证；精确命令语义与许可生命周期未闭合。 |

现有RequestInput签名不变，MHWI-001中立收刀Spirit的返回动作由DrawSlash变为SpiritI；复用既有弱113/强116出刀后自然进入104主段，无新增动画资产。完整资源根为`/Game/MHWI/Animations/R06Remaining`，现有角色CDO追加片段绑定保持。方向修改不改变显式路由条件或窗口。

## 官方来源与证据边界

适用UE 5.8：[控制器朝向](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/AController/GetControlRotation)、[世界空间输入](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/APawn/GetLastMovementInputVector)、[Montage](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-montage-in-unreal-engine)。官方资料说明输入/动画机制；项目实际使用MoveInput及Controller Yaw。MHWI动作身份依据本地已核实原始数据与MHWILinkAnimation消费者，五项行为目标来自用户本轮反馈。候选标志帧不当成精确取消窗口。

## 实际验证

| 本轮实际检查 | 结果 / 证据 |
| --- | --- |
| UE5.8 IntroCppEditor Win64 Development | Succeeded，60.07秒；`Saved/MHWIRestoration/B23-20261030/build.log` |
| 方向真实PIE | PASS，21用例/131检查：四向显式连携翻滚；两种镜头朝向各八方向特殊纳刀；无方向纳刀。`Saved/MHWIRestoration/B23-20261030/PIE-directions.json` |
| 正式DA单字段迁移 | 保存及读回false；`Saved/MHWIRestoration/B23-20261030/author-combat-saved.json`；原文件备份`Backup/DA_MHWI_LongSword.uasset` |
| 见切离线原文件提取 | 实际执行并生成[证据](../../Tools/MHW/foresight-window-evidence-20261030.json)，属于静态证据，不是原游戏逐帧测试 |

首次迁移脚本把Moves误按数组读取，未写资产；修正为真实TMap后保存成功。方向脚本首次缺少导入目录，尚未启动PIE；修正后21例通过。两次失败不可计入通过结果。六例气刃/突刺测试脚本保存请求被用户拒绝，未创建文件、未执行该套测试；随后用户明确接管后续游戏测试。B23-04/05运行和人工手感结论待用户反馈；不以编译/DA读回代替运行通过。验收操作见方案末尾清单。

## 风险、遗留与回退

开始时已有Content/MHWI/Maps/L_MHWI_Training.umap用户修改，SHA256 FEC1D1250C3C030764EB1FF72F29E8332044719F6B500CBA34284B7144BF8CAE，必须保留。正式DA初始SHA256 97A78F601A3F0AAC7F83A82666779F4041D324F1812342FF3226BDC05FFC926A。精确见切许可未闭合时保持该项开放。回退本轮源码/脚本及有备份的DA字段；不回退用户地图。IK不在本轮范围。

## 已同步文档

[方案](../Plans/PLAN-20261030-001-mhwi-five-controls.md)、[方案索引](../Plans/README.md)、[修改索引](README.md)、[现状](../Systems/MHWI-LongSword.md)、[问题](../Known-Issues.md)。

本轮未新增IK、整体动画或地图保存；最终地图SHA与开始一致。见切报告：[精确窗口缺口](../Reference/MHWI-Foresight-Window-Evidence-20261030.md)。
