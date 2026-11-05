# CHG-20261104-004：选择Windows Sandbox及启用失败诊断

- 状态：partial；已选择环境并尝试启用，Windows组件存储损坏阻止启用；系统修复尚未执行。
- 日期：2026-11-04。
- 用户需求：由助手推荐并选择更顺手的DevFlow执行环境。
- 关联：[DevFlow任务方案](../Plans/PLAN-20261104-001-devflow-thk-condition-audit.md)、R-ENV-001。
- Git：工作区记录，未提交。

## 原因与结果

选择Windows Sandbox用于当前小型Python取证/审计任务；现有DevFlow套件已提供对应双目录映射配置，新版可用wsb CLI调度。常驻UE编译环境需另按资源及持久性评估。

按用户交由助手选择环境的指示，准备并通过管理员进程执行Enable-WindowsOptionalFeature，指定Containers-DisposableClientVM、All及NoRestart。执行前功能状态Disabled；操作返回“组件存储已损坏”。系统DISM日志确认本次进程117196对应0x80073712；未成功启用。

随后仅执行Repair-WindowsImage -Online -CheckHealth：功能仍Disabled，ImageHealthState=Repairable，RestartNeeded=false。此检查没有执行RestoreHealth。没有重启、没有启动执行模型，DevFlow仍PREPARED/模型调用0。

## 修改清单

| 路径 | 内容 |
| --- | --- |
| Tools/DevFlow/Enable-WindowsSandbox.ps1 | 管理员启用助手，明确NoRestart并写结构化回执 |
| Tools/DevFlow/Repair-WindowsComponentStore.ps1 | 待用户另行授权的修复助手；RestoreHealth+NoRestart，尚未运行 |
| Tools/DevFlow/WindowsSandbox-20261104/enable-result.json | 实际启用失败回执 |
| Tools/DevFlow/WindowsSandbox-20261104/health-check.json | 实际只读健康诊断回执 |
| Saved/DevFlow/WindowsSandbox-20261104/ | 原始回执及只读诊断脚本，未执行修复 |
| Tools/DevFlow/Rathian-Condition-Audit-20261104/readiness.json | 补记环境选择、Disabled与Repairable；不修改冻结run任务或状态 |
| Docs/Plans/PLAN-20261104-001-devflow-thk-condition-audit.md、Docs/Known-Issues.md、Docs/Changes/README.md | 当前阻塞与导航 |

## 官方结论及项目事实

[微软Sandbox CLI](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-cli)支持启动/执行/共享/停止；[FAQ](https://learn.microsoft.com/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-faq)说明其关闭会清除安装软件和状态，因此需要可重复初始化。它比常驻VM更适合本批轻量任务是项目选型判断，不是官方对本项目的裁决。

[Repair-WindowsImage官方说明](https://learn.microsoft.com/en-us/powershell/module/dism/repair-windowsimage)区分CheckHealth与RestoreHealth；本机命令参数元数据已确认存在NoRestart。启用错误及Repairable来自本轮实际回执，不由文档推断。修复成功与所需源文件仍未知，不能承诺一次修复必成功。

## 实际验证

| 检查 | 结果 |
| --- | --- |
| 启用helper的PowerShell语法 | 通过；管理员操作产生结构化失败回执 |
| Sandbox启用 | completed=false；Windows报告组件存储损坏，DISM日志0x80073712 |
| CheckHealth | completed=true；image_health=Repairable，sandbox_state=Disabled，repaired=false |
| 拟议RestoreHealth命令 | 本机参数元数据确认Online/RestoreHealth/NoRestart存在；脚本仅准备、未执行 |
| 文档及diff检查 | check_docs通过：209 Markdown/1725本地链接/16模块；git diff --check退出0，仅LF/CRLF提示 |

## 接口、风险与回退

无玩法接口、Source、Content、原作或CodeBuddy登录变化。没有自动重启。管理员启用操作失败后重新读取状态仍Disabled，不据此保证Windows内部没有任何诊断日志或临时服务变化。

下一步需要用户明确同意修复Windows组件存储，这是比“选择执行环境”更广的系统维护操作。拟执行Repair-WindowsImage -Online -RestoreHealth -NoRestart；可能使用Windows Update获取修复源，不执行卸包、重装系统或自动重启。修复后再按已选路线重验并启用Sandbox。

未执行修复，因此没有修复回退可做；本次新增脚本/回执/文档可定点撤回，保留系统原始DISM日志。不要删除旧DevFlow冻结任务、原始数据或用户未提交文件。
