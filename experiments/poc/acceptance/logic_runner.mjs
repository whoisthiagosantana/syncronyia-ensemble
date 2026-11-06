// This process runs candidate code and returns values. It owns no assertions.
import vm from 'node:vm';
import fs from 'node:fs';
const context=vm.createContext(Object.create(null),{codeGeneration:{strings:false,wasm:false}});
const mod=new vm.SourceTextModule(fs.readFileSync('/work/game.mjs','utf8'),{context});
await mod.link(()=>{throw new Error('Game logic must not import modules');});
await mod.evaluate({timeout:1000});
context.api=mod.namespace;
const request=JSON.parse(fs.readFileSync(0,'utf8'));
context.input=JSON.stringify(request.args);
context.randomValue=request.randomValue;
if (!['move','spawn','getStatus'].includes(request.name)) throw new Error('Unknown operation');
const code=request.name==='spawn'
  ? 'globalThis.args=JSON.parse(input); JSON.stringify({result:api.spawn(args[0],()=>randomValue),after:args})'
  : `globalThis.args=JSON.parse(input); JSON.stringify({result:api.${request.name}(...args),after:args})`;
const output=vm.runInContext(code,context,{timeout:1000});
process.stdout.write(output);
