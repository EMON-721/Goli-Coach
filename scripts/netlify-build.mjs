import {spawnSync} from 'node:child_process';
import {writeFile} from 'node:fs/promises';
import {apiProxy} from './netlify-routing.mjs';
// Validate before spending time building or downloading assets.
const rule=apiProxy(process.env.BACKEND_ORIGIN,process.env.CONTEXT||'production');
for(const [command,args] of [['python3',['scripts/download_model.py']],['npm',['run','build']]]){
 const result=spawnSync(command,args,{stdio:'inherit'});
 if(result.error||result.status!==0)process.exit(result.status||1);
}
await writeFile('out/_redirects',rule);
console.log(rule?'Production API proxy configured. Verify the deployed backend before enabling accounts.':'Device mode: no production backend proxy.');
