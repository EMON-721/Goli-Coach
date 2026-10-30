"""Evaluate held-out, consented Bangladesh cricket frame annotations. No training.
Manifest JSON: country=BD, purpose=evaluation, consent_confirmed=true,
rights_evidence=<reference>, frames=[{player_id,discipline,image,sha256,points}].
points maps MediaPipe indices (11..32) to normalized [x,y]. Label all visible
joints; this reports accuracy on labelled joints only, not cricket skill.
"""
import argparse,hashlib,json,math,statistics
from pathlib import Path

def validate_manifest(manifest,base):
 if manifest.get('country')!='BD' or manifest.get('purpose')!='evaluation' or manifest.get('consent_confirmed') is not True or len(manifest.get('rights_evidence',''))<20:
  raise ValueError('Bangladesh provenance, evaluation permission and consent evidence required')
 frames=manifest.get('frames',[])
 if not frames:raise ValueError('No real labelled frames supplied; NOT EVALUATED')
 for frame in frames:
  path=(base/frame['image']).resolve()
  if not path.is_relative_to(base.resolve()):raise ValueError('Images must be inside the dataset directory')
  if frame.get('discipline') not in ['batting','bowling'] or not frame.get('player_id'):raise ValueError('Player and discipline required')
  if hashlib.sha256(path.read_bytes()).hexdigest()!=frame.get('sha256'):raise ValueError('Frame checksum mismatch')
  pts=frame.get('points',{})
  if not pts or any(not str(k).isdigit() or not 11<=int(k)<=32 or len(v)!=2 or any(type(x) not in [int,float] or not math.isfinite(x) or not 0<=x<=1 for x in v) for k,v in pts.items()):raise ValueError('Invalid labelled joints')
 return frames

def score_frame(labels,predicted,width,height,threshold=.05):
 # PCK threshold is 5% of image diagonal, explicitly not a body/torso threshold.
 diagonal=math.hypot(width,height);errors=[];hits=0
 for key,xy in labels.items():
  p=predicted[int(key)] if len(predicted)>int(key) else None
  if p is None or p.visibility<.5:continue
  error=math.hypot((p.x-xy[0])*width,(p.y-xy[1])*height)/diagonal
  errors.append(error);hits+=int(error<=threshold)
 return {'labelled_joints':len(labels),'visible_predictions':len(errors),'hits':hits,'errors':errors}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('manifest',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 manifest=json.loads(args.manifest.read_text());frames=validate_manifest(manifest,args.manifest.parent)
 import mediapipe as mp
 root=Path(__file__).resolve().parents[1];model=root/'public/models/pose_landmarker_lite.task';card=json.loads((root/'models/manifest.json').read_text())
 if hashlib.sha256(model.read_bytes()).hexdigest()!=card['sha256']:raise ValueError('Model checksum mismatch')
 options=mp.tasks.vision.PoseLandmarkerOptions(base_options=mp.tasks.BaseOptions(model_asset_path=str(model)),running_mode=mp.tasks.vision.RunningMode.IMAGE,num_poses=1)
 results=[]
 with mp.tasks.vision.PoseLandmarker.create_from_options(options) as detector:
  for frame in frames:
   image=mp.Image.create_from_file(str(args.manifest.parent/frame['image']));result=detector.detect(image)
   score=score_frame(frame['points'],result.pose_landmarks[0] if result.pose_landmarks else [],image.width,image.height)
   results.append(dict(player_id=frame['player_id'],discipline=frame['discipline'],**score))
 def aggregate(rows):
  total=sum(r['labelled_joints'] for r in rows);visible=sum(r['visible_predictions'] for r in rows);errors=[e for r in rows for e in r['errors']]
  return {'frames':len(rows),'labelled_joints':total,'prediction_coverage':visible/total if total else None,'pck_image_diagonal_0_05':sum(r['hits'] for r in rows)/total if total else None,'mean_normalized_error_detected_only':statistics.mean(errors) if errors else None}
 report={'status':'EVALUATED','model_sha256':card['sha256'],'manifest_sha256':hashlib.sha256(args.manifest.read_bytes()).hexdigest(),'country':'BD','unique_players':len({r['player_id'] for r in results}),'overall':aggregate(results),'by_discipline':{d:aggregate([r for r in results if r['discipline']==d]) for d in ['batting','bowling']},'limitations':['Labelled joints only; missing detections count as PCK misses.','No skill, injury or coaching validity claim.','Report sample composition and independent coach annotation quality before generalizing.']}
 args.output.write_text(json.dumps(report,indent=2));print('Evaluation written:',args.output)
if __name__=='__main__':main()
