# CHG-20261024-006：Content/MHWI原版还原批判性审查与修改方案

- 状态：completed，**本次审查与方案交付完成，玩法修复尚未实施**。
- 日期：2026-10-24。
- 需求摘要：以批判者检查Content/MHWI相对原游戏的不合理/不还原处，列问题表，再写原版还原修改方案。
- 关联：PLAN-20261024-005、R-COMBAT-010、MHWI-001..009、DAMAGE-001/002。
- Git：工作区变更，未提交；本次开始时存在大量既有修改/未跟踪资产与文档，未清理或覆盖。

## 原因与结果

上一轮独立调研原安装未读取项目；本轮按用户新授权进入Content/MHWI审查。先完成磁盘资产与支撑代码核对，再交付33项分级问题表和S0–S7修改方案。确认资源、攻击变体和部分派生存在实际差异，同时明确取消/连接/运动等待标定项。

保留已正确实现的映射、防御与生命周期边界；不将旧缺陷再次误报，也不把完整源码解析、源素材数量或历史测试数当作还原率。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Docs/Reference/MHWI-Restoration-Review.md` | R01–R33、数值对照、已正确项 | 新增批判性审查及来源/证据等级 |
| `Docs/Plans/PLAN-20261024-005-mhwi-original-restoration.md` | 数据、输入、资源、命中、时钟与阶段验收 | 新增可实施方案，所有验证场景均为计划 |
| `Docs/Systems/MHWI-LongSword.md` | 当前Q/T消费者、cost12、当前路由数 | 澄清现状与原版证据的区别，不改运行行为 |
| `Docs/Reference/MHWI-Native-Parameter-Pipeline.md` | 十秒字段及21处导入边界 | 记录导入成功不证明消费者正确 |
| `Docs/Known-Issues.md` | R-COMBAT-010 | 登记本轮确定偏差与还原缺口 |
| `Docs/README.md`、`Docs/Plans/README.md`、`Docs/Changes/README.md` | 导航与索引 | 添加审查/方案/本记录入口 |
| `Saved/MHWIReview-20261024/` | 临时只读脚本、资产读回、原版重点参考、指纹与CSV | 新增检查证据；不作为新正式玩法入口 |

## 接口、事件与资源影响

无运行时接口、事件、C++或正式资源改动；方案中的新数据结构、路径、接口及迁移尚未创建/实施。没有保存任何UAsset或地图。文档明确当前行为偏差，不把描述纠正写成玩法已修复。

349个`Content/MHWI`文件读取前后SHA256逐一一致；原LMT/FSM/W03P/近战COL/shell COL与上一轮原chunk独立提取一致，未使用本机模组覆盖作为基线。模块索引没有新系统/稳定入口变化，无需添加拟议源码。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| `git status --short` | 本机工作区 | 已辨别大量既有改动；本次仅新增/更新列出的文档和Saved证据 | 本轮工具记录 |
| UE5.8 `UnrealEditor-Cmd -run=pythonscript -script=.../inspect_saved_assets.py -unattended -nullrhi -nosound` | 无界面命令进程；未运行PIE | 最终退出0、completed=true、读取属性错误0；32定义/149路由/29Montage/30段引用/26不同Sequence，349文件哈希一致 | `Saved/MHWIReview-20261024/saved-assets-readback.json`、`readback-verified.log` |
| 源指纹与原版重点数据核对 | 标准Python，只读 | 五类源记录与独立提取哈希全部匹配，17个源码/制作脚本指纹已保存 | `Saved/MHWIReview-20261024/audit-manifest.json`、`native-attack-reference.json`、`native-fsm-focus.json` |
| `python Scripts/Docs/check_docs.py` | 本次文档交付 | 通过；76个Markdown及12模块；只验证链接/索引等，不是玩法验证 | `Saved/MHWIReview-20261024/document-validation.json` |
| `git diff --check`及进程内禁用LFS过滤的等价检查 | 本次工作区 | 普通命令因沙箱无法启动Git-LFS/MSYS辅助进程失败；以仅本次命令的`-c filter.lfs.process= -c filter.lfs.clean= -c filter.lfs.smudge= -c filter.lfs.required=false diff --check`完成，退出0，无空白错误；未改Git配置 | 同上 |
| 新文档UTF-8/尾空白、R01–R33唯一性及证据一致性 | 标准Python，只读 | 33项、27项P1/6项P2；3个新文档格式通过；349个Content文件和17个相关源码/脚本在交付前再次哈希一致 | 同上及`restoration-review.csv` |

只读脚本第一次在UE未暴露的`Blueprint.parent_class`查询失败，结果另存`readback-attempt1-partial.json`，不计为完整通过。随后修正为CDO原生类型检查、补混合时长与稳定资产类型序列化后完成最终读取。没有隐去失败场次。

本轮未执行：C++编译、蓝图保存/迁移、PIE操控、原作运行/录屏/进程采集、33项修复。用户只要求审查与方案；无须为文档重新构建引擎。历史PIE仅作资料，未当作本轮验证。

## 风险、遗留与回退

R01–R33均未修复；部分原生运行语义与视觉待标定。具体执行依赖和取证门槛见方案，不承诺仅凭静态包能还原所有原生程序行为。

回退本次新增文档与本次插入/澄清段落即可，Saved证据可独立归档；无需回退任何玩法或资产。不要删除整个既有Docs/Saved目录或重置用户工作区。

## 已同步文档

- [当前太刀模组](../Systems/MHWI-LongSword.md)
- [参数批处理边界](../Reference/MHWI-Native-Parameter-Pipeline.md)
- [批判性审查](../Reference/MHWI-Restoration-Review.md)
- [还原方案](../Plans/PLAN-20261024-005-mhwi-original-restoration.md)
- [已知问题](../Known-Issues.md)、[总入口](../README.md)、[方案索引](../Plans/README.md)、[记录索引](README.md)
