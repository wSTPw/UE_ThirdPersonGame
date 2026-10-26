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
const action = process.argv[2];
const client = new Client({ name: 'mhwi-animation-' + action, version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [path.join(toolRoot, 'node_modules/ue-mcp/dist/index.js'), projectPath],
  cwd: root,
  env: { ...process.env, UE_MCP_SERVER_MODE: 'in-process' },
  stderr: 'pipe',
});
let stderr = '';
transport.stderr?.on('data', chunk => { stderr = (stderr + chunk.toString()).slice(-24000); });
const unpack = response => {
  assert(!response.isError, JSON.stringify(response));
  for (const item of response.content ?? []) {
    if (item.type === 'text') {
      try { return JSON.parse(item.text); } catch { /* continue */ }
    }
  }
  throw new Error('No JSON result: ' + JSON.stringify(response));
};
const call = async (category, method, args = {}) => {
  const listed = await client.listTools();
  return unpack(await client.callTool(
    listed.tools.some(tool => tool.name === 'tools')
      ? { name: 'tools', arguments: { action: 'call', category, method, args } }
      : { name: category, arguments: { action: method, ...args } },
    undefined,
    { timeout: 60000 },
  ));
};
const waitReport = async (relative, timeoutMs = 150000) => {
  const file = path.join(root, relative);
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const data = JSON.parse(await fs.readFile(file, 'utf8'));
      if (typeof data.passed === 'boolean') return data;
    } catch { /* not written yet */ }
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  throw new Error('Timed out waiting for ' + relative);
};

try {
  await client.connect(transport);
  let status;
  for (let attempt = 0; attempt < 20; attempt++) {
    status = await call('project', 'get_status');
    if (status.editorConnected) break;
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  assert(status.editorConnected, 'Editor is disconnected');
  assert.equal(path.resolve(status.editorTarget.projectPath).toLowerCase(), projectPath.toLowerCase());

  if (action === 'inspect') {
    const result = await call('editor', 'run_python_file', {
      filePath: path.join(root, 'Saved/inspect_animation_api.py'),
    });
    console.log(JSON.stringify(result));
  } else if (action === 'r06') {
    await fs.rm(path.join(root, 'Saved/MHWIRestoration/B19-20261026/PIE-r06-repairs.json'), { force: true });
    await call('editor', 'run_python_file', {
      filePath: path.join(root, 'Scripts/MHWI/pie_r06_repairs.py'),
    });
    const report = await waitReport('Saved/MHWIRestoration/B19-20261026/PIE-r06-repairs.json');
    console.log(JSON.stringify(report));
    assert(report.passed, 'R06 PIE failed');
  } else if (action === 'r28-preview') {
    await fs.rm(path.join(root, 'Saved/MHWIRestoration/B19-20261026/R28Preview/report.json'), { force: true });
    await call('editor', 'run_python_file', {
      filePath: path.join(root, 'Scripts/MHWI/pie_r28_preview.py'),
    });
    const report = await waitReport('Saved/MHWIRestoration/B19-20261026/R28Preview/report.json', 240000);
    console.log(JSON.stringify({ passed: report.passed, clips: report.clips?.length, error: report.error }));
    assert(report.passed, 'R28 preview failed');
  } else if (action === 'author-ik') {
    const result = await call('editor', 'run_python_file', {
      filePath: path.join(root, 'Scripts/MHWI/author_equipment_ik.py'), entryPoint: 'run',
    });
    console.log(JSON.stringify(result));
  } else if (action === 'read-graph') {
    const graph = await call('blueprint', 'read_blueprint_graph', {
      assetPath: '/Game/MHWI/Blueprints/ABP_MHWI_Hunter', graphName: 'AnimGraph',
    });
    console.log(JSON.stringify(graph));
  } else {
    throw new Error('Unknown action: ' + action);
  }
} catch (error) {
  console.error(error.stack ?? String(error));
  if (stderr) console.error(stderr);
  process.exitCode = 1;
} finally {
  await client.close().catch(() => {});
}
