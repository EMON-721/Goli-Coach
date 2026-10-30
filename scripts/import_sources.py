"""Rights-gated local source-record validator; never fetch arbitrary URLs."""
import argparse,json,hashlib,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('path');p.add_argument('--dry-run',action='store_true',default=False);args=p.parse_args()
raw=Path(args.path).read_bytes();items=json.loads(raw)
if not isinstance(items,list):sys.exit('Expected JSON array')
required={'origin_url','owner','location_scope','date','source_version','permission_basis','license','attribution','checksum','review_status','is_demo','allowed_for_train','allowed_for_ui'}
approved=[];quarantined=[]
for i,row in enumerate(items):
 reasons=[]
 if not isinstance(row,dict):quarantined.append({'index':i,'reason':'not an object'});continue
 if required-set(row):reasons.append('missing provenance fields')
 if row.get('review_status')!='approved' or not row.get('permission_basis') or not row.get('license'):reasons.append('rights not reviewed')
 if row.get('is_demo') is not False:reasons.append('demo data excluded from real corpus')
 if row.get('allowed_for_train') is not True:reasons.append('training permission absent')
 (quarantined if reasons else approved).append({'index':i,'reasons':reasons,'record':row})
report={'sha256':hashlib.sha256(raw).hexdigest(),'approved':len(approved),'quarantined':len(quarantined),'records':approved+quarantined,'committed':False}
print(json.dumps(report,ensure_ascii=False,indent=2))
if not args.dry_run:print('Validation only; no dataset published or model trained.',file=sys.stderr)
