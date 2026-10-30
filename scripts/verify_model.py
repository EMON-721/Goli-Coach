import hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
m=json.loads((root/'models/manifest.json').read_text());p=root/'public/models/pose_landmarker_lite.task'
if not p.exists():sys.exit('FAIL: model missing; run scripts/download_model.py')
actual=hashlib.sha256(p.read_bytes()).hexdigest()
if actual!=m['sha256']:sys.exit('FAIL: checksum mismatch')
print(json.dumps({'verified':True,'model_id':m['model_id'],'sha256':actual}))
