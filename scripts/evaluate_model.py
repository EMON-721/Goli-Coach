"""Technical smoke only: official pose image versus blank clip. NOT cricket evaluation."""
import sys,os,tempfile,json,uuid,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
os.environ['DATABASE_PATH']=tempfile.mktemp(suffix='.sqlite');os.environ['SECURE_COOKIES']='0';os.environ['REQUIRE_EMAIL_VERIFICATION']='0'
import cv2,numpy as np
from fastapi.testclient import TestClient
from server.app import app,model_state
fixture=Path(sys.argv[1]) if len(sys.argv)>1 else None
if not fixture or not fixture.exists():raise SystemExit('Usage: python scripts/evaluate_model.py /path/to/official-pose-fixture.jpg')
image=cv2.imread(str(fixture));image=cv2.resize(image,(640,426))
c=TestClient(app);r=c.post('/api/auth/register',json={'email':str(uuid.uuid4())+'@example.test','name':'Synthetic QA','password':uuid.uuid4().hex});assert r.status_code==200
results=[]
for name,frame in [('pose_image_repeated',image),('blank_frames',np.zeros_like(image))]:
 with tempfile.TemporaryDirectory() as temp:
  path=Path(temp)/'fixture.mp4';writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'mp4v'),10,(640,426))
  for i in range(100):writer.write(frame)
  writer.release()
  response=c.post('/api/ai/analyze',files={'file':('fixture.mp4',path.read_bytes(),'video/mp4')},data={'consent':'true','start':'0','end':'10'})
  assert response.status_code==200,response.text
  payload=response.json();valid=sum(bool(f['landmarks']) for f in payload['frames'])
  results.append({'fixture':name,'sampled_frames':len(payload['frames']),'detected_frames':valid,'latency_ms':payload['latency_ms'],'model_id':payload['model_id']})
assert results[0]['detected_frames']>0
assert results[1]['detected_frames']==0
report={'status':'PASS','test_kind':'technical smoke; repeated still-image video and blank-video controls','not_a_cricket_benchmark':True,'bangladesh_evaluation':'NOT EVALUATED','genuine_bangladesh_rows':0,'results':results,'health':c.get('/api/ai/health').json()}
(root/'docs/MODEL_SMOKE_RESULTS.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
