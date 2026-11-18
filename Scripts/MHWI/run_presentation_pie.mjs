// Runs Scripts/MHWI/pie_trail_damage_numbers.py and reports its JSON. Never writes gameplay assets:
// the only editor write is re-pinning the trail material's Intensity scalar to 1.0, because the
// component already premultiplies its own intensity into the vertex colours.
//
// A background editor cannot tick PIE at full speed, and the editor child process stops with this
// script, so startup, the material pin and the run share one process. Usage: node Scripts/MHWI/run_presentation_pie.mjs
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const toolRoot = path.join(root, 'Tools/ue-mcp');
const require = createRequire(path.join(toolRoot, 'package.json'));
const { Client } = await import(pathToFileURL(require.resolve('@modelcontextprotocol/sdk/client/index.js')).href);
const { StdioClientTransport } = await import(pathToFileURL(require.resolve('@modelcontextprotocol/sdk/client/stdio.js')).href);

const reportPath = path.join(root, 'Saved/MHWIPresentation/PIE-presentation.json');
const material = '/Game/MHWI/Materials/M_MHWI_WeaponTrail';
const client = new Client({ name: 'presentation-pie', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [path.join(toolRoot, 'node_modules/ue-mcp/dist/index.js'), path.join(root, 'IntroCpp.uproject')],
  cwd: root,
  env: { ...process.env, UE_MCP_SERVER_MODE: 'in-process' },
  stderr: 'pipe',
});
transport.stderr?.on('data', () => {});

const unpack = (response) => {
  // The bridge prefixes some replies with a plain-text notice; keep the first JSON object.
  for (const item of response.content ?? []) {
    if (item.type !== 'text') continue;
    try {
      const value = JSON.parse(item.text);
      if (value && typeof value === 'object') return value;
    } catch { /* not JSON */ }
  }
  return {};
};
const call = async (category, method, args = {}) => unpack(await client.callTool(
  { name: 'tools', arguments: { action: 'call', category, method, args } }, undefined, { timeout: 300000 }));

fs.rmSync(reportPath, { force: true });
// A high-res capture with an existing file name is silently dropped, so start clean.
const shotDir = path.join(root, 'Saved/Screenshots/WindowsEditor');
for (const entry of fs.existsSync(shotDir) ? fs.readdirSync(shotDir) : []) {
  if (entry.startsWith('MHWI_') && entry.endsWith('.png')) fs.rmSync(path.join(shotDir, entry), { force: true });
}
let report = null;
try {
  await client.connect(transport);
  const status = await call('project', 'get_status');
  if (!status?.editorConnected) {
    const started = await call('editor', 'start_editor', { timeoutMs: 420000 });
    assert(started !== undefined, 'editor did not start');
  }
  await call('material', 'set_expression_value',
    { materialPath: material, expressionIndex: 1, propertyName: 'DefaultValue', value: '1.0' });
  await call('material', 'recompile', { materialPath: material });
  await call('editor', 'save_dirty', {});

  const run = await call('editor', 'run_python_file', { path: path.join(root, 'Scripts/MHWI/pie_trail_damage_numbers.py') });
  assert(run.success !== false, JSON.stringify(run));
  for (let attempt = 0; attempt < 90; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    if (!fs.existsSync(reportPath)) continue;
    try { report = JSON.parse(fs.readFileSync(reportPath, 'utf8')); } catch { continue; }
    if (report.done) break;
  }
} finally {
  await client.close().catch(() => {});
}

assert(report, 'PIE report was not written');
console.log(JSON.stringify(report, null, 2));
assert.equal(report.passed, true, report.error ?? 'PIE checks failed');
