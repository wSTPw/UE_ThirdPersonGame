// Drives the four DAMAGE_S directions through one Basic PIE each. Never writes assets.
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
const out = path.join(root, 'Saved/RathianHitReaction-20261107/regression');
const cases = [
  { yaw: 180, tag: 'damage-front' },
  { yaw: 0, tag: 'damage-back' },
  { yaw: -90, tag: 'damage-left' },
  { yaw: 90, tag: 'damage-right' },
];
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const client = new Client({ name: 'damage-matrix', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [path.join(toolRoot, 'node_modules/ue-mcp/dist/index.js'), projectPath],
  cwd: root,
  env: { ...process.env, UE_MCP_SERVER_MODE: 'in-process' },
  stderr: 'pipe',
});
let stderr = '';
transport.stderr?.on('data', chunk => { stderr = (stderr + chunk.toString()).slice(-12000); });
const unpack = response => {
  assert(!response.isError, JSON.stringify(response));
  for (const item of response.content ?? []) {
    if (item.type === 'text') {
      try { return JSON.parse(item.text); } catch { /* not JSON */ }
    }
  }
  throw new Error('No JSON: ' + JSON.stringify(response));
};
const runPy = async file => unpack(await client.callTool(
  { name: 'tools', arguments: { action: 'call', category: 'editor', method: 'run_python_file', args: { filePath: path.join(root, file) } } },
  undefined, { timeout: 120000 }));
const waitReport = async (tag, timeoutMs = 150000) => {
  const file = path.join(out, `PIE-${tag}.json`);
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const data = JSON.parse(await fs.readFile(file, 'utf8'));
      if (typeof data.passed === 'boolean') return data;
    } catch { /* not written yet */ }
    await sleep(1000);
  }
  throw new Error('Timeout ' + tag);
};
const rows = [];
try {
  await client.connect(transport);
  let status;
  for (let i = 0; i < 20; i++) {
    const listed = await client.listTools();
    status = unpack(await client.callTool({ name: 'tools', arguments: { action: 'call', category: 'project', method: 'get_status', args: {} } }, undefined, { timeout: 30000 }));
    if (status.editorConnected) break;
    await sleep(1000);
  }
  assert(status?.editorConnected, 'Editor is disconnected');
  for (const item of cases) {
    await fs.writeFile(path.join(root, 'Saved/damage_case.json'), JSON.stringify({ ...item, move: 'bite' }));
    await runPy('Saved/damage_pie.py');
    await sleep(9000);
    await runPy('Saved/damage_case.py');
    const report = await waitReport(item.tag);
    const checks = report.checks ?? [];
    rows.push({ tag: item.tag, yaw: item.yaw, passed: report.passed,
      sources: checks.find(c => c.description?.startsWith('impact plays'))?.sources,
      checks: checks.map(c => ({ ok: c.passed, what: c.description, detail: c.detail ?? c.sources ?? c.motions })) });
    await sleep(4000);
  }
  console.log(JSON.stringify(rows, null, 2));
  assert(rows.every(r => r.passed), 'Some damage cases failed');
} catch (error) {
  console.error(error.stack ?? String(error));
  if (stderr) console.error(stderr);
  process.exitCode = 1;
} finally {
  await client.close().catch(() => {});
}
