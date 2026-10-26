# UE 5.8 升级与 UE-MCP 验证记录

验证日期：2026-10-17（Asia/Shanghai）。

## 结果

| 检查项 | 结果 |
| --- | --- |
| 引擎 | 本机 UE 5.8.3，CL 58210709 |
| `IntroCppEditor Win64 Development` | 编译、链接成功 |
| 安装 UE-MCP 后再次编译 | 成功，239 个构建步骤 |
| Visual Studio 工程重新生成 | 成功 |
| 起始地图 `/Game/MyStuff/Lvl_Start` | PIE 运行 10 秒，通过 |
| 游戏地图 `/Game/MyStuff/MyLevel` | PIE 运行 10.02 秒，通过，47 个运行时 Actor |
| 新插件启动 | 成功，最终编辑器打开 MyLevel |
| MCP 初始化、工具列表 | 通过，服务端 ue-mcp 1.4.7 |
| MCP `project/get_status` | `live`、`editorConnected=true`、`pluginStale=false` |
| 编辑器身份 | 项目路径匹配；响应 PID 与项目 port.json 匹配 |
| MCP `level/get_outliner` | 成功读取 MyLevel，37 个编辑器 Actor |
| 当前 Codex 的直接 MCP 调用 | get_status 与 get_outliner 均成功 |

最终连接端口：57605。端口、PID 以 `Saved/UE_MCP_Bridge/port.json` 的实时内容为准。
编译使用 Visual Studio 2022 MSVC 14.44 与 Windows SDK 10.0.22621.0。

## 升级变更

- 项目引擎关联升级到 5.8；Game/Editor Target 使用 V7 构建设置与 Unreal5_8 头文件顺序。
- StateTree 回调保留强执行上下文，保证读取实例数据期间其生命周期有效；替换弃用的实例数据宏。
- 为 UI 的 FReply 补齐 SlateCore 依赖。
- 为快捷栏动态委托回调补齐 UFUNCTION，修复游戏地图 BeginPlay 中的委托绑定错误。
- 移除触发 UE 5.8 启动 ensure 的弃用配置 `r.Mobile.VirtualTextures`。
- 按用户要求卸载旧 UEBridgeMCP 插件及项目启用项。旧源码和 Git 元数据的恢复归档在 `Saved/Upgrade-UE58/UEBridgeMCP-retired.zip`。
- 安装新 `Plugins/UE_MCP_Bridge` 1.4.7 与对应 Node 服务端；通过 package-lock.json 固定依赖。
- 配置项目级 `.codex/config.toml`。服务端使用项目本地依赖，绝对路径需在移动工作区后更新。

原有未提交的 ABP_Move.uasset、M_LongSwordAttack.uasset 已在操作前后核对 SHA-256，文件内容保持一致。

## 日志与复测

本地证据位于 `Saved/Upgrade-UE58/`：

- `Build-Editor-Project.log`：项目编译成功。
- `Build-Editor-MCP.log`：包含新插件的最终编译成功。
- `GenerateProjectFiles.log`：工程文件生成成功。
- `EditorSmoke.json`：两张地图的 PIE 结果。
- `Editor-Project.log`：双地图运行日志。
- `Editor-MCP.log`：安装新插件后的最终编辑器启动与 RPC 日志。
- `McpSmoke.json`：独立 MCP 客户端的完整握手、身份匹配与场景读取结果。

连接复测（编辑器保持运行）：

```powershell
node Scripts/Tests/test-ue-mcp.mjs
```

双地图 PIE 复测（先关闭其他使用本项目的编辑器实例）：

```powershell
$editorArgs = @(
  '"E:/Unreal Projects/IntorCpp/IntroCpp.uproject"',
  '-unattended', '-nosplash', '-windowed',
  '-ExecutePythonScript="E:/Unreal Projects/IntorCpp/Scripts/Tests/ue58_smoke.py"'
)
Start-Process -FilePath 'E:/UE/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe' -ArgumentList $editorArgs
```

原生插件编译存在上游 Landscape / ForEachObjectWithOuter 弃用警告，但编译结果为成功。
编辑器安装插件前后的日志均有 13 条引擎启动自检 `LogAutomationTest: Error: Condition failed`；
它们未阻止编辑器初始化、双地图 PIE 或 MCP 连接。最终启动日志没有 fatal error 或 ensure failure。

更多安装与配置说明见 [UE-MCP README](../Tools/ue-mcp/README.md)。
