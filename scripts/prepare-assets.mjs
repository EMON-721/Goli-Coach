import {mkdir,copyFile,readdir} from 'node:fs/promises';
await mkdir('public/wasm',{recursive:true});
for(const file of await readdir('node_modules/@mediapipe/tasks-vision/wasm'))await copyFile('node_modules/@mediapipe/tasks-vision/wasm/'+file,'public/wasm/'+file);
await copyFile('models/manifest.json','public/models/manifest.json');
