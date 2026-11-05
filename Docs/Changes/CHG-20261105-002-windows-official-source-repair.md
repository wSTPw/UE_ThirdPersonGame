# CHG-20261105-002：核对微软官方修复源并继续修复Sandbox

- 状态：partial；已完成官方WU源修复与SFC，Sandbox仍Disabled；OC压缩元数据异常未闭合，等待合格完整源/受支持后续路线。
- 日期：2026-11-05。
- 需求摘要：寻找匹配当前系统的官方修复源，继续修复Sandbox，全程不自动重启或关机。
- 关联：R-ENV-001、[前轮实际结果](CHG-20261105-001-windows-component-store-repair.md)、[DevFlow环境方案](../Plans/PLAN-20261104-001-devflow-thk-condition-audit.md)。
- Git：工作区记录，未提交；用户既有源码及资产修改保留。

## 原因与方案

本机实际为Professional/amd64、InstalledUICulture=zh-CN，DisplayVersion=26H2、26300.9711。前轮CBS细账显示FileFlags检测5959并修复5959，剩2个payload：隔离用户模式策略26100.1455的指定CIP及userexperience-lkg26100.1742的AccountsService.dll。Client.OS.rs2.amd64获取实际报0x8007000e（内存不足），不能据前轮最终缺源就断言微软不存在适配来源。

本轮只读核查时可用提交内存约6.9GiB；原高内存WorkBuddy Python进程已不在最高占用列表，本助手未停止它。先复用微软原生Windows Update修复源，在无并发修复且可用提交内存至少4GiB时重新获取适配文件。该内存阈值是本项目操作保护值，不是微软保证修复成功的规格。

微软官方下载页提供26H2简体中文x64 ISO及SHA256；Catalog存在KB5127648/x64/26300.9711的明确匹配。ISO只到来源候选，未读取内容，不宣称它含两份旧payload；链接生成接口返回SentinelReject后停止，没有绕过。官方更新缓存含KB5127648元数据及KB5043080 WIM，可作后续来源核验线索，不将整个缓存目录直接冒充合格Source。

## 实施边界与记录

修复调用仍为Repair-WindowsImage -Online -RestoreHealth -NoRestart，仅由主代理启动一个管理员进程。独立子代理只读查官方资料/缓存，不执行系统修复。保存新批次Saved/DevFlow/WindowsSandbox-20261105-source-repair，不覆盖前轮证据。原DevFlow冻结run保持PREPARED、模型调用0。

修复成功且无重启要求时才继续启用Sandbox，启用同样使用NoRestart；若必须重启，则停止并交由用户安排。本轮不运行安装助手/setup、旧更新安装、就地升级、重置Windows、组件库手工覆盖、用户进程终止或重启/关机命令。

## 实际验证

| 检查/命令 | 实际状态 | 证据 |
| --- | --- | --- |
| 官方ISO/Catalog与修复源文档 | 已核对来源与版本；ISO尚未下载/内容核验 | Saved/DevFlow/WindowsSandbox-20261105-source-repair/official-sources.json |
| 源获取修复及健康复查 | RestoreHealth退出0、Healthy；启用仍失败；外部重启后复查Repairable/Disabled | Tools/DevFlow/WindowsSandbox-20261105-source-repair/各自回执 |
| 文档与diff检查 | PASS：211 Markdown / 1742链接 / 16模块；git diff --check退出0，仅已有换行提示 | 本次终端输出 |

## 官方依据、现状与推断

- [微软Windows 11下载](https://www.microsoft.com/zh-cn/software-download/windows11)：当前26H2、x64多版本/简体中文及公开SHA256。
- [微软Catalog精确构建](https://www.catalog.update.microsoft.com/Search.aspx?q=26300%209711)：KB5127648、x64、26300.9711；不代表其旧组件一定完整。
- [微软修复源配置](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/configure-a-windows-repair-source?view=windows-11)：Windows Update默认修复源及WIM/语言/维护级别要求。
- [HRESULT定义](https://learn.microsoft.com/en-us/windows/win32/seccrypto/common-hresult-values)：0x8007000e是E_OUTOFMEMORY；这是前轮源获取错误的解释，不把单个高内存进程与整体缺源作未经证明的唯一因果关系。

官方资料支持机制；本机CBS/缓存/内存是现状；内存恢复后重试可能成功是待执行验证的判断。

## 风险与回退

NoRestart只抑制本次命令重启，不控制断电或其他软件；监督System1074及启动时间。失败时保存现场并按已确认缺口取源，不盲目循环。项目文档可单独撤回，但撤回文档不撤销Windows已完成的组件修复。

## 已同步文档

[变更索引](README.md)、[已知问题](../Known-Issues.md)。

## 本轮已执行结果与新增阻塞

- 管理员修复PID82780于00:45:37启动，01:17:48结束，退出0、completed=true、ImageHealthState=Healthy、RestartNeeded=false。该轮官方源下载先后包括270,942,503字节及1,525,973,164字节内容；实际进入DPX展开与CBS/CSI修复，并非只取得元数据。
- CBS 01:15:48统计本轮Detected3826、Repaired3826、FileFlags0；这是本轮会话统计，不将其与前轮“两条缺失payload”简单相加或推导为本轮新增损坏。CBS S_OK，无重启要求。
- 01:18:35独立CheckHealth退出0，Healthy、Sandbox Disabled，上次启动仍为2026-10-30。
- 01:19:19用已审核Enable脚本（NoRestart）尝试启用，PID117648退出1，仍0x80073712。精确原因是amd64_userexperience-lkg/26100.1742/LKG.AccountsService/AccountsService.winmd的CompressedFileType=0与ComponentFileFlags LZMS:3不一致，触发CorruptPayloadFile和OC解压失败。此前Healthy仅是当时复查结果，不能代替后续Sandbox成功。
- 只读查询该逻辑路径未取得文件；未区分所有访问/逻辑布局情况，不能仅凭Get-Item结果宣布新增文件丢失。缓存WIM通过WIMGAPI query-only查询成功：仅一个content索引，无Windows身份，尚未资格化为完整修复源。
- 未找到微软公开针对该CSI压缩状态冲突的专项修复指令。按微软Windows10/11支持的DISM成功后SFC顺序，01:23:47启动sfc /scannow，原生PID83048、监督PID116676；当时执行中，最终结果见下方续查。SFC无自动重启选项，监督脚本没有重启/关机调用；若要求手动重启则停止后续操作。
- 没有手动改COMPONENTS、takeown/icacls、compact WinSxS或复制覆盖受保护组件；没有安装旧KB、setup或系统升级。

[SFC官方步骤](https://support.microsoft.com/en-us/windows/experience/backup-recovery/use-the-system-file-checker-tool-to-repair-missing-or-corrupted-system-files)、[SFC命令](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/sfc)支持通用流程，不能证明它必然修复本次LZMS压缩标记；最终需新回执与实际Sandbox启用验证。

## 续查与当前交接状态（2026-11-05）

- SFC于01:27:30结束，完整输出为“Windows资源保护未找到任何完整性违规”，本次SR修复0组件。包装器未取得原生退出码，记录null；不能将监督器退出0替代SFC原生退出码，也不能据SFC无违规宣称OC压缩状态已修。
- 任务中断后，系统事件1074显示07:48:30由StartMenuExperienceHost.exe以登录用户账号发起重启，07:49系统启动。此为任务中断期间的外部事件；本助手的命令未请求重启/关机，不将当前整段时间写作“系统从未重启”。09:39独立复查仍Repairable、Sandbox Disabled。
- 官方KB5043080 x64包已下载，533,761,740字节，SHA256与Catalog公布值完全匹配；未运行MSU安装器。该包实际为MSWIM容器，expand.exe只复制了容器，未取得成员。原生WIMGAPI根路径提取/非提升提取分别遇到161/1314；管理员Python包装器退出1且无结果，未以这些失败尝试认定来源已合格。Expand-WindowsImage第一次因不支持NoAcl参数被拒，按实际API修正后仅在新工作区成功展开七个数据成员，没有应用到系统分区。
- 官方容器中含113,666,182字节组件WIM和386,541,934字节PSF。组件WIM列出98,933路径；AccountsService相关命中只有对应manifest、deployment manifest、MUM和CAT四项，尚未从PSF还原并资格化目标winmd，不能把此目录直接冒充完整Source。
- 容器目录查询后观察到原下载文件长度/摘要变化；提取前完整性保护阻止继续使用。完好副本仍保持官方SHA，已设为只读，数据展开前后校验均一致。组件WIM工作副本在Get-WindowsImageContent前后摘要也发生变化；以后该类调查先制作工作副本，不把显示目录的命令自动视作不会更改容器。未以不匹配摘要的容器修复系统。
- 当前未执行手改COMPONENTS、接管WinSxS权限、compact重压、覆盖受保护文件、旧KB安装或就地升级。缺少可直接套用的官方专项压缩元数据修复方案，不能据猜测定案。后续需要核验完整官方ISO源，或由用户选择受支持恢复路线；任何需要重启的步骤仍须用户安排，本助手不自动重启/关机。
- 小型回执/日志/工具与SHA清单已归档至[本轮摘要](../../Tools/DevFlow/WindowsSandbox-20261105-source-repair/source-repair-summary.json)和[清单](../../Tools/DevFlow/WindowsSandbox-20261105-source-repair/manifest.json)。大体积MSU/WIM/PSF只留Saved，未加入工程版本文件。

## 本轮最终验证边界

本轮只读官方源核验、独立健康检查、实际RestoreHealth、一次NoRestart启用、SFC均有各自回执。官方数据容器只在工作区展开，不作系统镜像安装。当前Sandbox未启用，未执行其运行测试、CodeBuddy工具实现、UE构建/PIE或原作。本次归档46份小型证据的大小/SHA核对通过；文档检查211 Markdown/1742链接/16模块通过，git diff --check退出0。
