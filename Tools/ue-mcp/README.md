# IntroCpp UE-MCP

This project uses [db-lyon/ue-mcp](https://github.com/db-lyon/ue-mcp), pinned to **1.4.7**.
The deployed Unreal plugin is `Plugins/UE_MCP_Bridge`; the Node server is installed here.

## Restore dependencies

Requires Node.js 20 or newer:

```powershell
npm.cmd ci --prefix Tools/ue-mcp --ignore-scripts --no-audit --no-fund
```

## Connect from Codex

Project-scoped configuration is in `.codex/config.toml`. It launches the local Node server
with the absolute path to `IntroCpp.uproject`. Update those paths if the checkout moves.
Open the UE 5.8 editor, then reload the Codex MCP connection or open a new Codex chat.

The WebSocket port and editor PID are published in `Saved/UE_MCP_Bridge/port.json`.
The server uses the default `micro` tool surface. For example:

```text
tools(action="call", category="project", method="get_status", args={})
tools(action="call", category="level", method="get_outliner", args={})
```

## Repeat the connection test

With the editor running:

```powershell
node Scripts/Tests/test-ue-mcp.mjs
```

The test performs MCP initialization, lists tools, verifies the connected project and
editor PID, checks that the plugin is current, and reads the live level outliner.
Results are saved to `Saved/Upgrade-UE58/McpSmoke.json`.

## Upgrade the bridge and server together

Update the pinned dependency, then deploy its matching plugin with the editor closed:

```powershell
node Tools/ue-mcp/node_modules/ue-mcp/dist/index.js init --yes --json "--project=E:/Unreal Projects/IntorCpp/IntroCpp.uproject" --clients= --install=source --no-feedback --no-hook --no-skills --pin
```

Rebuild `IntroCppEditor Win64 Development` using the project's UE 5.8 installation,
restart the editor, and repeat the connection test.

The former `UEBridgeMCP` plugin has been removed. It is a different project and had
UE 5.8 compilation errors. A local recovery archive is in
`Saved/Upgrade-UE58/UEBridgeMCP-retired.zip`.
