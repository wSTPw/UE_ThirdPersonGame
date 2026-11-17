import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const require=createRequire(path.join(root,'Tools/ue-mcp/package.json'));
const {Client}=await import(pathToFileURL(require.resolve('@modelcontextprotocol/sdk/client/index.js')).href);
const {StdioClientTransport}=await import(pathToFileURL(require.resolve('@modelcontextprotocol/sdk/client/stdio.js')).href);
const [script,entry='run',kwargs='{}']=process.argv.slice(2);
assert(script && !script.includes('..') && script.endsWith('.py'),'Supply a Scripts/MHWI file name');
const client=new Client({name:'mhwi-five-controls',version:'1.0.0'});
const transport=new StdioClientTransport({command:process.execPath,args:[path.join(root,'Tools/ue-mcp/node_modules/ue-mcp/dist/index.js'),path.join(root,'IntroCpp.uproject')],cwd:root,env:{...process.env,UE_MCP_SERVER_MODE:'in-process'},stderr:'pipe'});
transport.stderr?.on('data',()=>{});
try {
 await client.connect(transport);
 const r=await client.callTool({name:'tools',arguments:{action:'call',category:'editor',method:'run_python_file',args:{filePath:path.join(root,'Scripts/MHWI',script),entryPoint:entry,kwargs:JSON.parse(kwargs),captureLog:false,maxLogChars:2500}}},undefined,{timeout:60000});
 console.log(JSON.stringify(r));
 assert(!r.isError,'MCP call failed');
 for (const c of r.content??[]) if(c.type==='text') {let v;try{v=JSON.parse(c.text)}catch{} if(v) assert(v.success!==false,'Editor script failed');}
} finally {await client.close().catch(()=>{});}
