# CHG-20261106-002：社区动作派发资料与本机签名交叉核对

- 状态：completed（只读研究/记录）；动作启动与完整首链仍partial。
- 日期：2026-11-06。
- 需求：遇到难点查社区网络资料，继续忠实还原取证，不动Sandbox。
- 关联：[当前M0](../Plans/MHWI-Current.md)、BEH-02、R-DATA-006。
- Git：未提交；已有源码/资产修改保留。

## 原因与结果

两个Luna分查LuaEngine、HunterPie、Leviathon、SharpPluginLoader维护者源码，主代理通过GitHub只读连接器锁提交/文件blob并独立复核本机字节。新增两个SDK签名入口候选：LaunchAction `0x141cc5360`、ForceAction `0x1413973b0`，各唯一命中；已知 `0x140269ce0` 与SDK DoAction签名相符。只证明签名及偏移对应，未证明THK83递交、实例/enter或SDK整体兼容。

来源、commit/blob、真实源码行与384字节窗口hash见[机器可读清单](../../Tools/MHW/rathian-community-dispatch-20261106.json)。维护者源码是对应社区工具的一手资料，不是Capcom原作证明；各库未锁定本项目EXE版本，故只对已匹配字节作静态结论。

## 修改清单与边界

项目根为 `E:/Unreal Projects/IntorCpp`。

| 路径 | 内容 |
| --- | --- |
| Tools/MHW/rathian-community-dispatch-20261106.json | 9份固定来源、3个已知/新入口匹配、字段/生命周期候选、原始窗口hash、未解项 |
| Docs/Reference/MHWI-Rathian-Evidence.md、Docs/Plans/MHWI-Current.md | 只增结论与下一步入口，不写全量推导 |
| Docs/Changes/README.md、Docs/Archive/MHWI/README.md | 最近5条索引与历史索引更新，最旧CHG-20261104-002移入归档，正文不改 |
| Docs/Changes/CHG-20261106-002-rathian-community-dispatch.md | 本记录 |

本轮是只读研究，不是新DevFlow执行候选；上轮ACCEPTED快照及其报告/证据/冻结检查不改。未改玩法源码、接口、资产、配置或module索引；未启动原作/UE、未安装/注入、未重解包、未修复Sandbox，无重启关机操作。

## 实际验证

| 检查 | 实际结果 |
| --- | --- |
| 维护者源码检索 | GitHub只读fetch固定commit；9个来源blob和真实源码行已记录。Leviathon BITE为源L84，撤回网页提取L919 |
| 本机固定镜像 | SHA256 `9b48a8490df702ba9dc1cb95ffd387358ae2a639aa9675ad90719bd997124ebe`；两新签名各唯一命中并按源码的signed offset求址；已知DoAction仅核现有窗口 |
| 主代理/子代理窗口复核 | 均用字面384字节（hex0x180）重算三窗口hash；修正早先将0x180B误作长度所得元数据，不使用旧hash作为384字节指纹 |
| python Scripts/Docs/check_docs.py | PASS：35活动Markdown、341本地链接、16模块及快照JSON；不代替原生运行验证 |
| git diff --check | exit0，无空白错误 |

未执行新的原作/UE测试或升级原作条件资格。官方ABI与PE机制沿用[上轮适用边界](../Archive/MHWI/Changes/CHG-20261106-001-rathian-bite-dispatch-devflow.md)；社区具体结论对应清单中各维护方源码及固定版本，不据UE官方机制证明MHWI行为。

## 遗留与回退

先追THK actionID到LaunchAction的输入，再对ForceAction及AiData/actor字段定位，核wrapper两个receiver与BITE实例/execute。SPL生命周期slot说明不自动适用于未知callback类型。原作运行/条件仍未验证，本轮没有缺失原始文件需解包。

回退仅撤销本轮清单、现状页增补和索引；归档CHG移回原处。保留已有用户修改和上轮冻结证据，不自动清理输入/缓存。

## 已同步文档

[总账](../Reference/MHWI-Rathian-Evidence.md)、[当前计划](../Plans/MHWI-Current.md)、[变更索引](README.md)、[历史索引](../Archive/MHWI/README.md)。
