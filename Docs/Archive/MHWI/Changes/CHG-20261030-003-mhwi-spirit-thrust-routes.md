# CHG-20261030-003：气刃连段突刺、见切续查与攻击判定说明

- 日期：2026-10-30
- 状态：partial；三条路线已保存，见切精确许可取证中；游戏测试由用户进行。
- 用户反馈：B23除03基本通过；此项来自用户实测，不是本轮代理运行验证。
- 关联：[方案](../Plans/PLAN-20261030-002-mhwi-spirit-thrust-routes.md)、B23-03、B24-01、MHWI-001。
- Git：工作区变更，未提交；B23已有改动与用户地图保留。

## 原因与结果

SpiritI/II/III缺少HELM_BREAKER→SpiritThrust路线。现已分别追加，沿用已有SPIRIT连携窗口59..110、44..118、110..160源帧/60秒。这些是既有项目配置，不宣称原作精确窗口。三条新增路线不要求命中、反击、足额气刃消费或颜色，require_drawn=true；气刃突刺入场与登龙命中/白刃门保持B23修复。

见切继续追查命令绑定与实际许可，未凭候选25/40/47帧修改。攻击判定只解释现状，未重构。

## 修改清单

| 文件 / 资产 | 实际内容 |
| --- | --- |
| `/Game/MHWI/Data/DA_MHWI_LongSword` | 仅SpiritI/II/III的Routes各增加一条气刃突刺路线；实际路线数量7→8、7→8、6→7 |
| `Scripts/MHWI/author_spirit_thrust_routes.py` | 编辑器非PIE迁移、备份、其他字段及其他招式序列化保护、保存读回和幂等预览 |
| `Scripts/MHWI/author_assets.py`、`author_behavior_corrections.py` | 同步新增路线以防重跑丢失 |
| `Scripts/MHWI/transition_calibration.json` | 三条HELM_BREAKER规则与明确的项目窗口边界；existing_route语义保持 |
| [当前攻击判定](../Reference/MHWI-Attack-Detection-20261030.md) | 记录实际伤害窗、三个球形扫掠、去重、倍率、延迟伤害及空间/部位缺口 |

RequestInput签名不变，新增数据路线复用ResolveInput/TryConsumeBuffered；不修改C++、反射、动画、IK或地图，不需要新编译。制作链顺序仍为基础动作→行为修正→校准；独立迁移可在当前正式DA直接应用。

## 官方方案与项目证据

适用UE 5.8：[Montage](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-montage-in-unreal-engine)、[动画通知](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-notifies-in-unreal-engine)说明玩法可控制动画分支；[UWorld查询](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UWorld)说明球形扫掠机制。实际落点为项目既有FMHWIRoute及SweepWindow；这些官方机制不证明MHWI原作窗口和碰撞形状。

## 本轮实际验证

- 编辑器预览成功；保存正式DA后完整Moves逐项序列化读回匹配，三个目标招式恢复原Routes后与原定义一致，其他招式完全一致。
- 再次预览changed=false，路线数量8/8/7，幂等；未运行游戏测试。
- 证据：`Saved/MHWIRestoration/B24-20261030/routes-saved.json`、`routes-preview.json`。
- 原DA备份：`Saved/MHWIRestoration/B24-20261030/Backup/DA_MHWI_LongSword.uasset`。
- 保存前SHA256：e0cb2b2cd2ca534eb7e38f8ea867a3561e9f85fd923e6869683e36b8b104d73a；保存后：b58018299805472fa2729fee8ab0577d41287cff7b64e51c2b1793d4b89df64c。
- Python三脚本AST检查通过；校准表23招式/150规则的schema和既有原文件指纹检查通过。以上均非游戏运行测试。

## 用户验收与回退

重新开始训练场Play，气刃I/II/III各自在连携窗输入气刃突刺（当前键盘Ctrl+左键）；分别检查空挥/命中、无色/有色，保留正常气刃续接。见切精确许可未闭合前不列为已修复。

只撤销本轮三条新增路线及制作/校准变更，或使用本轮B24备份（不能使用B23旧备份覆盖已验收内容）。用户地图SHA256与本轮之前一致：FEC1D1250C3C030764EB1FF72F29E8332044719F6B500CBA34284B7144BF8CAE。没有自动保存地图。

## 同步文档

[方案](../Plans/PLAN-20261030-002-mhwi-spirit-thrust-routes.md)、[当前系统](../Systems/MHWI-LongSword.md)、[问题](../Known-Issues.md)、[模块索引](../Reference/modules.json)、[记录索引](README.md)。见切新增材料随后归档引用。
