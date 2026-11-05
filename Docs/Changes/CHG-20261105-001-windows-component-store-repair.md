# CHG-20261105-001：监督Windows组件库修复与Sandbox恢复

- 状态：partial；已监督完成本轮修复尝试，退出1、0x800f0915缺少修复源；组件库仍Repairable、Sandbox仍Disabled；无重启/关机。
- 日期：2026-11-05。
- 需求摘要：执行修复并监督全过程，本次操作不得自动重启或关机。
- 关联：[DevFlow任务方案](../Plans/PLAN-20261104-001-devflow-thk-condition-audit.md)、R-ENV-001；前次诊断见[CHG-20261104-004](CHG-20261104-004-windows-sandbox-enablement.md)。
- Git：工作区记录，未提交；保留用户已有未提交修改。

## 原因与结果

前次Sandbox启用失败0x80073712，CheckHealth报告Repairable。本次用户明确授权执行Repair-WindowsImage -Online -RestoreHealth -NoRestart，并要求全程监督。

2026-11-05 00:04:38（Asia/Shanghai）启动管理员PowerShell修复进程81496。修复及后续启用脚本经独立只读检查：系统变更调用均带NoRestart，无关机、重启或创建计划任务的代码。本轮在00:29:22结束，用时24分44.668秒，管理员进程退出1、completed=false。已下载270,942,503字节的第一批修复源并继续其他获取，但最终返回0x800f0915（CBS_E_REPAIR_CONTENT_MISSING）。00:31:27完成只读复查：ImageHealthState=Repairable、Sandbox=Disabled，未重试修复或功能启用。

NoRestart抑制本次命令发起重启；不宣称它能控制其他软件、Windows Update独立任务或断电。监督额外检查本次开始后的System事件1074。若操作返回需要重启，停止后续启用步骤，交由用户安排。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| Tools/DevFlow/Repair-WindowsComponentStore.ps1 | 原有已审核脚本，SHA256 29498b6f3b9efd672ebb7fd96d03a09f81883ad64c7952ead39191b2763bad02 | 本次运行，未改脚本 |
| Saved/DevFlow/WindowsSandbox-20261105/ | repair-launch.json、最终回执、进程退出记录、supervision.jsonl、监视脚本及日志片段 | 独立批次证据，不覆盖前次失败/健康检查记录 |
| Docs/Changes/README.md、Docs/Known-Issues.md | CHG索引与R-ENV-001 | 更新授权及当前实际状态 |

## 接口、事件与资源影响

无玩法接口、UE源码、蓝图、地图或资产改动。原工程未提交内容未暂存、提交或回退。DevFlow冻结run仍为PREPARED，执行模型调用0；本次系统修复不代表隔离执行与测试环境已完成配置。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| 两个系统脚本语法与无重启调用审查 | Windows PowerShell语法树、独立子代理只读审查 | 通过；修复/启用均带NoRestart | 原脚本及本次launch中的SHA256 |
| RestoreHealth -Online -NoRestart | 管理员进程81496 | 已结束：退出1、completed=false；最终错误0x800f0915，仍缺修复源 | Saved/DevFlow/WindowsSandbox-20261105/ |
| 进程、DISM/CBS日志、System事件1074监督 | 本次开始后 | 监督至修复结束及复查；全部采样的1074计数为0，进程已退出 | supervision.jsonl及日志片段 |
| 修复后CheckHealth及功能状态 | 管理员PowerShell5.1，退出0 | Repairable / Disabled；RestartNeeded=false；本机上次启动UTC为2026-10-30T00:02:27.8363770Z | Tools/DevFlow/WindowsSandbox-20261105/post-repair-health.json |
| python Scripts/Docs/check_docs.py | 工程目录 | PASS：210 Markdown / 1734本地链接 / 16模块及编辑器JSON | 本次终端输出 |
| git diff --check | 工程目录 | 退出0；仅已有文件LF/CRLF提示，无空白错误 | 本次终端输出 |

首次supervision样本的elapsed_seconds存在+28800秒时区错误；后续改用DateTimeOffset计算并明确标注。开始/观察的原始UTC时间戳不受影响，最终耗时以原始时间戳为准。

## 风险、遗留与回退

修复失败时，脚本restart_needed的初始false不代表已确认无需重启。以进程退出码、实际回执、健康复查和功能状态共同判断。不能用撤回项目文档来撤销Windows组件修复；本次不执行系统包删除、重置或自动重启。

Sandbox仍Disabled，无法做Sandbox运行验证；未执行CodeBuddy候选、UE构建、PIE或原作运行。原工程玩法代码/资产未改。

## 已同步文档

[变更索引](README.md)、[已知问题](../Known-Issues.md)、[DevFlow任务方案](../Plans/PLAN-20261104-001-devflow-thk-condition-audit.md)。

## 官方依据与适用版本

- [Repair-WindowsImage](https://learn.microsoft.com/en-us/powershell/module/dism/repair-windowsimage)：Windows 11在线组件库修复、RestoreHealth和NoRestart语义。
- [安装Windows Sandbox](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-install)：Windows 11可选功能安装及可能要求重启。

官方资料说明命令机制；实际结果只以本次进程、日志和复查为依据。

## 最终诊断与监督边界

- CBS 00:27:17明确记录Reboot required: no、RepairNeeded: yes，最终0x800f0915；修复进程81496在00:29:22结束、实际退出1。脚本失败回执中restart_needed初始false不单独作为结论，另由CBS和复查交叉确认。
- 全部监督样本未发现本次开始后的System事件1074；复查上次启动仍为2026-10-30，未发生本次重启。未调用关机、重启、更新安装重启、计划任务或shutdown取消操作。
- 监测期间新开PowerShell7曾报CoreCLR 0x8007000E，改用系统PowerShell5.1继续成功监督。只读检查当时系统可用提交内存约297MiB；WorkBuddy的独立Python进程110532（launch.py）私有内存约16.2GiB。未停止该进程，也未证明它与修复缺源存在因果关系。
- 实际系统报告DisplayVersion=26H2、build=26300.9711、Edition=Professional。只在E:/、F:/和用户Downloads顶层检查ISO，没有发现；此为有限目录检查，不代表全盘无ISO。
- 下一步是取得适用于本机系统与维护级别的官方修复源、核对镜像身份后制定Source+NoRestart修复。没有下载非官方镜像、修改组策略、重置Windows或执行就地升级。
- 可信回执、监督记录与最终日志片段已按字节复制到[证据归档](../../Tools/DevFlow/WindowsSandbox-20261105/supervision-summary.json)，逐文件SHA见[归档清单](../../Tools/DevFlow/WindowsSandbox-20261105/manifest.json)。关键原始Windows日志仍保留于C:/Windows/Logs/DISM及CBS。

官方修复源要求见[微软修复源配置](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/configure-a-windows-repair-source?view=windows-11)：可以指定WIM/挂载镜像等来源，目标更新级别高于来源时可能失败。因此不能把任意Windows 11 ISO当作已验证可用修复源。
