import {connectors,type Frame} from './domain';

/** Pose-only WebM. Original footage and audio never enter the export canvas. */
export async function exportPose(frames:Frame[],signal:AbortSignal,onProgress:(n:number)=>void):Promise<Blob>{
 const usable=frames.filter(f=>f.landmarks.length===33).sort((a,b)=>a.time-b.time);
 if(!usable.length)throw Error('No pose frames available');
 if(typeof MediaRecorder==='undefined'||!HTMLCanvasElement.prototype.captureStream)throw Error('Video export is unavailable in this browser');
 const mime=['video/webm;codecs=vp9','video/webm;codecs=vp8','video/webm'].find(t=>MediaRecorder.isTypeSupported(t));
 if(!mime)throw Error('WebM recording is unavailable in this browser');
 const canvas=document.createElement('canvas');canvas.width=960;canvas.height=640;
 const ctx=canvas.getContext('2d');if(!ctx)throw Error('Canvas unavailable');
 const stream=canvas.captureStream(24),recorder=new MediaRecorder(stream,{mimeType:mime}),chunks:Blob[]=[];
 const start=usable[0].time,length=Math.min(30,Math.max(1,usable.at(-1)!.time-start+.25));
 return new Promise((resolve,reject)=>{
  let animation=0,timeout:ReturnType<typeof setTimeout>|undefined,cancelled=false;
  const clean=()=>{cancelAnimationFrame(animation);clearTimeout(timeout);stream.getTracks().forEach(t=>t.stop());signal.removeEventListener('abort',abort);};
  const abort=()=>{cancelled=true;if(recorder.state!=='inactive')recorder.stop();else{clean();reject(Error('Export cancelled'));}};
  recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
  recorder.onerror=()=>{clean();reject(Error('Video recording failed'));};
  recorder.onstop=()=>{clean();if(cancelled)reject(Error('Export cancelled'));else resolve(new Blob(chunks,{type:'video/webm'}));};
  signal.addEventListener('abort',abort,{once:true});if(signal.aborted){abort();return;}
  const beginning=performance.now();
  const draw=()=>{
   const elapsed=(performance.now()-beginning)/1000,time=start+elapsed;
   ctx.fillStyle='#123c2c';ctx.fillRect(0,0,960,640);ctx.fillStyle='#eff6e9';ctx.font='bold 26px sans-serif';ctx.fillText('Goli-Coach · Pose replay',32,44);
   ctx.font='16px sans-serif';ctx.fillText('Pose only · Original video and audio excluded',32,76);
   const f=usable.reduce((best,next)=>Math.abs(next.time-time)<Math.abs(best.time-time)?next:best,usable[0]);
   if(Math.abs(f.time-time)<.6){
    const aspect=f.aspect||16/9,w=Math.min(860,460*aspect),h=w/aspect,x=(960-w)/2,y=110+(460-h)/2;
    ctx.strokeStyle='#cbff77';ctx.lineWidth=4;
    for(const [a,b] of connectors){const p=f.landmarks[a],q=f.landmarks[b];if((p.visibility??0)<.5||(q.visibility??0)<.5)continue;ctx.beginPath();ctx.moveTo(x+p.x*w,y+p.y*h);ctx.lineTo(x+q.x*w,y+q.y*h);ctx.stroke();}
   }
   ctx.fillStyle='#eff6e9';ctx.fillText(`${Math.min(elapsed,length).toFixed(1)} / ${length.toFixed(1)} s · Approximate 2D observations`,32,610);
   onProgress(Math.min(100,Math.round(elapsed/length*100)));
   if(elapsed>=length){recorder.stop();return;}animation=requestAnimationFrame(draw);
  };
  try{recorder.start(250);draw();timeout=setTimeout(()=>{if(recorder.state!=='inactive'){cancelled=true;recorder.stop();}},35000);}catch(error){clean();reject(error);}
 });
}
