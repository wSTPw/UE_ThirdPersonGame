// Minimal UE-MCP CLI: connect to the running editor through the project's pinned
// ue-mcp server (stdio) and execute one tool call.
//
//   node Scripts/MHWI/ue_mcp_call.mjs --list
//   node Scripts/MHWI/ue_mcp_call.mjs --describe <category>
//   node Scripts/MHWI/ue_mcp_call.mjs <category> <method> ['{"arg":1}']
//
// Prints the JSON result. Read-only unless the called method mutates the editor.
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const toolRoot = path.join(root, 'Tools/ue-mcp');
const require = createRequire(path.join(toolRoot, 'package.json'));
const { Client } = await import(pathToFileURL(require.resolve('@modelcontextprotocol/sdk/client/index.js')).href);
const { StdioClientTransport } = await import(pathToFileURL(require.resolve('@modelcontextprotocol/sdk/client/stdio.js')).href);

const argv = process.argv.slice(2);
const projectPath = path.join(root, 'IntroCpp.uproject');
const client = new Client({ name: 'introcpp-ue-mcp-cli', version: '1.0.0' });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [path.join(toolRoot, 'node_modules/ue-mcp/dist/index.js'), projectPath],
  cwd: root,
  env: { ...process.env, UE_MCP_SERVER_MODE: 'in-process' },
  stderr: 'pipe',
});
let stderr = '';
transport.stderr?.on('data', chunk => { stderr = (stderr + chunk.toString()).slice(-8000); });

const unpack = response => {
  if (response.isError) throw new Error('MCP error: ' + JSON.stringify(response).slice(0, 800));
  let parsed = null;
  for (const item of response.content ?? []) {
    if (item.type !== 'text') continue;
    try { parsed = JSON.parse(item.text); continue; } catch { /* notices or prose */ }
    const start = item.text.search(/[[{]/);
    if (start >= 0) {
      try { parsed = JSON.parse(item.text.slice(start)); continue; } catch { /* keep last */ }
    }
  }
  if (parsed !== null) return parsed;
  return response.content?.map(i => i.text).join('\n') ?? response;
};

const call = (name, args) => client.callTool({ name, arguments: args }, undefined, { timeout: 180000 });

try {
  await client.connect(transport);
  const tools = (await client.listTools()).tools.map(t => t.name);
  const hasTools = tools.includes('tools');

  if (argv[0] === '--meta') {
    const args = JSON.parse(argv[1] ?? '{}');
    console.log(JSON.stringify(unpack(await call('tools', args)), null, 1));
  } else if (argv[0] === '--list') {
    const out = { tools };
    if (hasTools) {
      for (const action of ['list', 'describe', 'categories']) {
        try {
          out[action] = await unpack(await call('tools', { action }));
          break;
        } catch (error) {
          out[action + '_error'] = String(error).slice(0, 200);
        }
      }
    }
    console.log(JSON.stringify(out, null, 1));
  } else {
    const [category, method, rawArgs] = argv;
    if (!category || !method) throw new Error('usage: <category> <method> [jsonArgs]');
    const result = hasTools
      ? await call('tools', { action: 'call', category, method, args: rawArgs ? JSON.parse(rawArgs) : {} })
      : await call(category, { action: method, ...(rawArgs ? JSON.parse(rawArgs) : {}) });
    console.log(JSON.stringify(unpack(result), null, 1));
  }
} catch (error) {
  console.error('ERROR ' + (error?.stack ?? error));
  if (stderr) console.error('--- server stderr (tail) ---\n' + stderr);
  process.exitCode = 1;
} finally {
  await transport.close().catch(() => {});
}
