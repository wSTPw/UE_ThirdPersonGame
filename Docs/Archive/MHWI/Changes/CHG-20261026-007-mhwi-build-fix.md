# CHG-20261026-007：B14/B15 提交的编译错误修复

- 状态：completed（编译通过；未运行 PIE）
- 日期：2026-10-26
- 需求摘要：拉取远端 `4b5361c` 后做按需编译验证，修复该提交自带的编译错误。
- 关联：CHG-20261026-006、PLAN-20261026-002、PLAN-20261026-003、接口 MHWI-014
- Git：本次提交

## 原因与结果

远端 `4b5361c`（B14 证据化机制 + B15 PC 键盘适配）自述“未编译、未运行 PIE，本机缺少 UE 5.8 引擎”。本机有 UE 5.8（`E:\UE\UE_5.8`），拉取后按 [开发与验证流程](../Development.md) 编译，暴露两处真实编译错误：

1. UHT 阶段失败：`MHWICharacter.h(77): Error: Type 'uint32' is not supported by blueprint. Function: GetInputRequestSerial Parameter ReturnValue`。蓝图不支持无符号整型，B15 新增的只读诊断 getter 用了 `uint32` 返回类型。
2. 通过 UHT 后，链接前的编译阶段失败：`MHWICharacter.cpp(1920,25): error C2665: TArray::RemoveAt 没有重载接受指定数量的参数`。UE 5.8 中 `TArray::RemoveAt` 第三参数已由 `bool` 改为 `EAllowShrinking` 枚举，`false` 不再匹配。

两处修复后编译通过，`UnrealEditor-IntroCpp.dll` 链接成功。修复不改变 B14/B15 的设计意图：诊断 getter 仍可从蓝图读取（改为 `int32`），延迟 shell 队列仍是“移除后不收缩”（`EAllowShrinking::No`）。**未运行 PIE，B14/B15 的运行时行为仍未验证。**

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/MHWICharacter.h` | `AMHWICharacter::GetInputRequestSerial()`（第 77 行） | 返回类型 `uint32` → `int32`，内部 `static_cast<int32>(InputRequestSerial)`；保留 `BlueprintPure`，蓝图诊断仍可读；成员 `InputRequestSerial` 仍为 `uint32`，`++` 语义不变 |
| `Source/IntroCpp/MHWI/MHWICharacter.cpp` | `AMHWICharacter::TickDelayedShells()`（第 1920 行） | `RemoveAt(0, 1, false)` → `RemoveAt(0, 1, EAllowShrinking::No)`；纯签名适配，队列收缩策略与原来一致 |

## 接口、事件与资源影响

接口变更 1 处：`GetInputRequestSerial() -> uint32` 改为 `-> int32`（蓝图可见类型的唯一变化，因为 `uint32` 根本无法注册）。语义不变：仍是“收到的命令尝试次数，含随后被拒绝的请求”，无写入口。C++ 侧无调用方（仅 `++InputRequestSerial`），蓝图若有引用已随本次编译重编。`RemoveAt` 改动属函数内部实现，无契约变化。

无反射字段增删、无委托签名变化、无资产/DA/Montage/地图改动、无迁移。用户既有修改未触碰。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| `Build.bat IntroCppEditor Win64 Development -Project=...IntroCpp.uproject`（拉取后首次） | 本机 Windows，UE 5.8，MSVC 14.44.35209 | Failed：UHT `Type 'uint32' is not supported by blueprint`（MHWICharacter.h:77） | `%LOCALAPPDATA%\UnrealBuildTool\Log.txt` |
| 修 `uint32`→`int32` 后重编 | 同上 | Failed，但 UHT 通过；失败于 UBA 写入 `Plugins/UE_MCP_Bridge/Intermediate` 报 `Access is denied` 并连带产生 0 字节 `UnrealEditor-UE_MCP_Bridge.lib`（LNK1136） | 同上 |
| 加 `-NoUBA` 重编 | 同上 | Failed：`MHWICharacter.cpp(1920,25): error C2665 TArray::RemoveAt` | 同上 |
| 修 `RemoveAt` 后加 `-NoUBA` 重编 | 同上 | **Succeeded**，4 个 action，20.08 秒，`UnrealEditor-IntroCpp.dll` 链接成功 | 同上 |

已执行：编译。未执行：PIE、运行自动化、命中/姿态行为验证、资产保存与读回。B15 记录的 49 项静态检查属历史结果，不作为本次已执行。

## 风险、遗留与回退

- B14/B15 的运行时行为（延迟 shell 计时、Ctrl 组合、纳刀/冲刺过滤、无关键重发保护）仍未经 PIE 验证。
- **B14 的变更记录 CHG-20261026-005 至今缺失**，编号已跳过；建议后续补录，本记录不代写。
- 本机 UBA 在 `Plugins/UE_MCP_Bridge/Intermediate` 上出现 `SetFileInformationByHandle (Access is denied)`，疑为杀软或 UBA 缓存目录权限问题，与代码无关。规避方式是用 `-NoUBA` 编译；用 UBA 时该插件链接可能产生 0 字节 `.lib`。
- 蓝图侧若已有节点引用 `GetInputRequestSerial` 并期望无符号语义，需确认其仅作诊断计数使用（当前范围内取值远小于 2^31，无实际差异）。
- 回退：还原上述两行即可，无数据或资产需要回退。

## 已同步文档

[接口契约 MHWI-014](../Interfaces.md)、[变更索引](README.md)。
