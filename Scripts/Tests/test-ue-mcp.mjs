// End-to-end, read-only MCP smoke test. Run: node Scripts/Tests/test-ue-mcp.mjs
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const toolRoot = path.join(root, 'Tools/ue-mcp');
const require = createRequire(path.join(toolRoot, 'package.json'));
const { Client } = await import(pathToFileURL(require.resolve('@modelcontextprotocol/sdk/client/index.js')).href);
const { StdioClientTransport } = await import(pathToFileURL(require.resolve('@modelcontextprotocol/sdk/client/stdio.js')).href);
const projectPath = path.join(root, 'IntroCpp.uproject');
const output = path.join(root, 'Saved/Upgrade-UE58/McpSmoke.json');
const client = new Client({ name: 'introcpp-mcp-smoke', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [path.join(toolRoot, 'node_modules/ue-mcp/dist/index.js'), projectPath],
  cwd: root,
  env: { ...process.env, UE_MCP_SERVER_MODE: 'in-process' },
  stderr: 'pipe',
});
let stderr = '';
transport.stderr?.on('data', chunk => { stderr = (stderr + chunk.toString()).slice(-24000); });
const result = { passed: false, date: new Date().toISOString(), projectPath };
const normalize = value => path.resolve(value).toLowerCase();
const unpack = response => {
  assert(!response.isError, JSON.stringify(response));
  for (const item of response.content ?? []) {
    if (item.type === 'text') {
      try { return JSON.parse(item.text); } catch { /* attribution is not JSON */ }
    }
  }
  throw new Error('No JSON result in MCP response: ' + JSON.stringify(response));
};
const timeout = setTimeout(() => {
  console.error('MCP smoke test exceeded 120 seconds');
  transport.close().finally(() => { process.exitCode = 1; });
}, 120000);

try {
  await client.connect(transport);
  result.server = client.getServerVersion();
  const listed = await client.listTools();
  result.tools = listed.tools.map(tool => tool.name);
  const call = async (category, method) => unpack(await client.callTool(
    result.tools.includes('tools')
      ? { name: 'tools', arguments: { action: 'call', category, method, args: {} } }
      : { name: category, arguments: { action: method } },
    undefined,
    { timeout: 45000 },
  ));
  // Give the bridge's initial WebSocket handshake a bounded opportunity to finish.
  for (let attempt = 0; attempt < 15; attempt++) {
    result.status = await call('project', 'get_status');
    if (result.status.editorConnected) break;
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  assert.equal(result.status.mode, 'live', 'Editor is not live');
  assert.equal(result.status.editorConnected, true, 'Editor is disconnected');
  assert.equal(normalize(result.status.editorTarget.projectPath), normalize(projectPath));
  assert(!result.status.editorTargetMismatch, 'Server is connected to another project');
  assert.equal(result.status.pluginStale, false, 'The loaded plugin is stale');
  const port = JSON.parse(await fs.readFile(path.join(root, 'Saved/UE_MCP_Bridge/port.json'), 'utf8'));
  result.portFile = port;
  assert.equal(result.status.answeringPid, port.pid, 'Responding editor PID differs from project port file');
  result.outliner = await call('level', 'get_outliner');
  assert(!result.outliner.error, JSON.stringify(result.outliner));
  assert.equal(typeof result.outliner.worldName, 'string', 'No live world name returned');
  assert(Array.isArray(result.outliner.actors), 'No actor list returned from the editor');
  result.passed = true;
  console.log(JSON.stringify({ passed: true, server: result.server, pid: result.status.answeringPid, port: result.status.editorTarget.port }));
} catch (error) {
  result.error = error.stack ?? String(error);
  result.stderr = stderr;
  process.exitCode = 1;
  console.error(result.error);
} finally {
  clearTimeout(timeout);
  await client.close().catch(() => {});
  await fs.mkdir(path.dirname(output), { recursive: true });
  await fs.writeFile(output, JSON.stringify(result, null, 2));
}
