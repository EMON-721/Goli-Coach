"""GoliCoach local/private server. Serves the Next static export and isolated APIs."""
import sys, os, json, sqlite3, secrets, hashlib, hmac, time, uuid, tempfile, threading
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict, deque
from urllib.parse import urlsplit
from fastapi import FastAPI, Request, Response, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from server import auth_recovery
DB=Path(os.environ.get('DATABASE_PATH',str(ROOT/'private/golicoach.sqlite')))
DB.parent.mkdir(parents=True,exist_ok=True)
app=FastAPI(title='GoliCoach AI',version='0.1.0')
rate=defaultdict(deque)
lock=threading.Lock()
model_lock=threading.Lock()
pose=None
model_state={'status':'not_loaded','model_id':'mediapipe-pose-landmarker-lite','model_version':'float16/1','model_loaded':False,'sha256':None,'runtime':'Python MediaPipe CPU','sample_inference_tested':False,'latency_ms':None,'last_success':None,'bangladesh_evaluation':'NOT EVALUATED'}

def now():return datetime.now(timezone.utc).isoformat()
def db():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');return c
def migrate():
 with db() as c:
  c.executescript((ROOT/'server/schema.sql').read_text())
  if 'verified' not in {r[1] for r in c.execute('PRAGMA table_info(users)')}:c.execute('ALTER TABLE users ADD COLUMN verified INTEGER NOT NULL DEFAULT 0')
migrate()
def audit(actor,action,target=''):
 with db() as c:c.execute('INSERT INTO audit(actor,action,target,created_at) VALUES(?,?,?,?)',(actor,action,target,now()))
def reject(code,text):raise HTTPException(code,text)
def identity(request):
 token=request.cookies.get('gc_session','')
 with db() as c:r=c.execute('SELECT users.* FROM sessions JOIN users ON users.id=sessions.user_id WHERE token_hash=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),time.time())).fetchone()
 if not r or r['blocked'] or (auth_recovery.verification_required() and not r['verified']):reject(401,'Sign in required')
 return dict(r)
def role(request,roles):
 u=identity(request)
 if u['role'] not in roles:reject(403,'Permission denied')
 return u
EDITORS={'superadmin','editor','manager'}
CURATORS={'superadmin','curator'}
AUDITORS={'superadmin','auditor','manager'}
def public_user(u):return {k:u[k] for k in ['id','name','role']}
def hash_password(p,salt=None):
 salt=salt or secrets.token_hex(16)
 return salt+':'+hashlib.scrypt(p.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()
def session(response,u):
 token=secrets.token_urlsafe(32)
 with db() as c:c.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),u['id'],time.time()+86400))
 response.set_cookie('gc_session',token,httponly=True,samesite='strict',secure=os.environ.get('SECURE_COOKIES','1')=='1',max_age=86400)
 return public_user(u)
@app.middleware('http')
async def boundary(request,call_next):
 if request.url.path.startswith('/api/'):
  if request.method not in ('GET','HEAD','OPTIONS'):
   origin=request.headers.get('origin')
   if origin and urlsplit(origin).netloc!=request.headers.get('host'):return Response('Origin denied',status_code=403)
   if int(request.headers.get('content-length','0'))>52*1024*1024:return Response('Upload too large',status_code=413)
  key=(request.client.host if request.client else 'unknown',request.url.path)
  limit=10 if '/auth/' in request.url.path else 120
  with lock:
   q=rate[key]
   while q and q[0]<time.time()-60:q.popleft()
   if len(q)>=limit:return Response('Rate limit exceeded',status_code=429)
   q.append(time.time())
 response=await call_next(request)
 response.headers['X-Content-Type-Options']='nosniff'
 response.headers['Referrer-Policy']='same-origin'
 if request.url.path.startswith('/api/'):response.headers['Cache-Control']='no-store'
 return response
class Credentials(BaseModel):
 email:str=Field(min_length=3,max_length=254)
 password:str=Field(min_length=12,max_length=200)
 name:str=Field(default='Player',min_length=1,max_length=60)
@app.get('/api/health')
def api_health():return {'service':'golicoach','status':'ready','account_storage':'sqlite','version':'0.1.0'}
@app.post('/api/auth/register')
def register(v:Credentials,response:Response,tasks:BackgroundTasks):
 email=v.email.strip().lower()
 if not auth_recovery.email_valid(email):reject(422,'Valid email required')
 if auth_recovery.verification_required():
  try:auth_recovery.configuration()
  except ValueError:reject(503,'Account email service is not configured')
 user={'id':str(uuid.uuid4()),'email':email,'name':v.name,'password':hash_password(v.password),'role':'user'}
 try:
  with db() as c:c.execute('INSERT INTO users(id,email,name,password,role,created_at) VALUES(?,?,?,?,?,?)',(*user.values(),now()))
 except sqlite3.IntegrityError:reject(400,'Account could not be created')
 audit(user['id'],'account_created')
 if auth_recovery.verification_required():
  auth_recovery.queue_token(db,user,'verify',tasks)
  return {'verification_required':True,'message':'Check your email before signing in.'}
 return session(response,user)
@app.post('/api/auth/login')
def login(v:Credentials,response:Response):
 with db() as c:u=c.execute('SELECT * FROM users WHERE email=?',(v.email.strip().lower(),)).fetchone()
 expected=u['password'] if u else hash_password('not-a-real-password')
 provided=hash_password(v.password,expected.split(':')[0])
 if not hmac.compare_digest(provided,expected) or not u or u['blocked']:reject(401,'Invalid email or password')
 if auth_recovery.verification_required() and not u['verified']:reject(403,'Verify your email before signing in')
 return session(response,dict(u))
@app.post('/api/auth/logout')
def logout(request:Request,response:Response):
 token=request.cookies.get('gc_session','')
 with db() as c:c.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),))
 response.delete_cookie('gc_session');return {'ok':True}
@app.get('/api/me')
def me(request:Request):return public_user(identity(request))
@app.get('/api/records')
def records(request:Request):
 u=identity(request)
 with db() as c:rows=c.execute('SELECT payload FROM records WHERE owner_id=? ORDER BY created_at LIMIT 500',(u['id'],)).fetchall()
 return [json.loads(r[0]) for r in rows]
def own_record(request,id):
 u=identity(request)
 with db() as c:r=c.execute('SELECT * FROM records WHERE id=? AND owner_id=?',(id,u['id'])).fetchone()
 if not r:reject(404,'Record not found')
 return u,r
@app.get('/api/records/{id}')
def get_record(id:str,request:Request):return json.loads(own_record(request,id)[1]['payload'])
@app.post('/api/records')
def save_record(payload:dict,request:Request):
 u=identity(request)
 try:uuid.UUID(payload.get('id',''))
 except (ValueError,TypeError):reject(422,'Valid record id required')
 if payload.get('kind') not in ['batting','bowling'] or not isinstance(payload.get('notes',''),str) or len(payload.get('notes',''))>2000:reject(422,'Invalid record')
 raw=json.dumps(payload,ensure_ascii=False)
 if len(raw)>2_000_000:reject(413,'Report too large')
 with db() as c:
  c.execute('BEGIN IMMEDIATE')
  previous=c.execute('SELECT owner_id FROM records WHERE id=?',(payload['id'],)).fetchone()
  if previous and previous[0]!=u['id']:reject(404,'Record not found')
  c.execute('INSERT INTO records VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',(payload['id'],u['id'],raw,now()))
 return {'id':payload['id'],'saved':True}
@app.patch('/api/records/{id}')
def edit_record(id:str,payload:dict,request:Request):
 _,r=own_record(request,id);old=json.loads(r['payload']);old.update({k:v for k,v in payload.items() if k in ['title','notes','favorite']});return save_record(old,request)
@app.delete('/api/records/{id}')
def delete_record(id:str,request:Request):
 u,_=own_record(request,id)
 with db() as c:c.execute('DELETE FROM records WHERE id=? AND owner_id=?',(id,u['id']))
 audit(u['id'],'record_deleted',id);return {'deleted':True}
@app.delete('/api/account')
def delete_account(request:Request,response:Response):
 u=identity(request)
 if u['role']=='superadmin':
  with db() as c:count=c.execute("SELECT count(*) FROM users WHERE role='superadmin' AND blocked=0").fetchone()[0]
  if count<=1:reject(409,'Transfer ownership before deleting the last superadmin')
 with db() as c:c.execute('DELETE FROM users WHERE id=?',(u['id'],))
 audit('deleted-user','account_deleted');response.delete_cookie('gc_session');return {'deleted':True}
class JournalNote(BaseModel):
 id:uuid.UUID
 text:str=Field(min_length=1,max_length=2000)
 date:datetime
@app.get('/api/journal')
def journal(request:Request):
 u=identity(request)
 with db() as c:return [dict(r) for r in c.execute('SELECT id,text,date FROM journal WHERE owner_id=? ORDER BY date DESC',(u['id'],))]
@app.post('/api/journal')
def save_note(payload:JournalNote,request:Request):
 u=identity(request);id=str(payload.id)
 if not payload.text.strip():reject(422,'Note cannot be blank')
 with db() as c:
  c.execute('BEGIN IMMEDIATE')
  old=c.execute('SELECT owner_id FROM journal WHERE id=?',(id,)).fetchone()
  if old and old[0]!=u['id']:reject(404,'Note not found')
  c.execute('INSERT INTO journal VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET text=excluded.text,date=excluded.date',(id,u['id'],payload.text,payload.date.isoformat()))
 return {'id':id,'saved':True}
@app.delete('/api/journal/{id}')
def delete_note(id:str,request:Request):
 u=identity(request)
 with db() as c:
  result=c.execute('DELETE FROM journal WHERE id=? AND owner_id=?',(id,u['id']))
  if not result.rowcount:reject(404,'Note not found')
 return {'deleted':True}
@app.get('/api/admin/content/revisions')
def revisions(request:Request):
 role(request,EDITORS)
 with db() as c:return [dict(r)|{'content':json.loads(r['payload'])} for r in c.execute('SELECT id,payload,status,actor,created_at FROM content_revisions ORDER BY id DESC LIMIT 100')]
@app.patch('/api/admin/feedback/{id}')
def resolve_feedback(id:str,payload:dict,request:Request):
 u=role(request,{'superadmin','support','moderator'})
 if payload.get('status') not in ['open','reviewing','resolved']:reject(422,'Invalid feedback status')
 with db() as c:
  result=c.execute('UPDATE feedback SET status=? WHERE id=?',(payload['status'],id))
  if not result.rowcount:reject(404,'Feedback not found')
 audit(u['id'],'feedback_'+payload['status'],id);return {'updated':True}
@app.patch('/api/admin/sources/{id}')
def review_source(id:str,payload:dict,request:Request):
 u=role(request,CURATORS)
 state=payload.get('state');evidence=payload.get('license_evidence','')
 if state not in ['quarantine','approved','rejected']:reject(422,'Invalid state')
 if not isinstance(evidence,str) or len(evidence)>3000:reject(422,'Invalid evidence')
 if state=='approved' and (len(evidence.strip())<20 or payload.get('rights_confirmed') is not True):reject(422,'Document rights and confirm permission before approval')
 with db() as c:
  old=c.execute('SELECT payload FROM sources WHERE id=?',(id,)).fetchone()
  if not old:reject(404,'Source not found')
  data=json.loads(old[0]);data.update(license_evidence=evidence,reviewed_by=u['id'],reviewed_at=now())
  c.execute('UPDATE sources SET state=?,payload=? WHERE id=?',(state,json.dumps(data,ensure_ascii=False),id))
 audit(u['id'],'source_'+state,id);return {'state':state,'imported_rows':0}
@app.get('/api/content')
def content():
 with db() as c:r=c.execute("SELECT payload FROM content_revisions WHERE status='published' ORDER BY id DESC LIMIT 1").fetchone()
 return json.loads(r[0]) if r else {}
@app.post('/api/admin/content')
def draft(payload:dict,request:Request):
 u=role(request,EDITORS);value=payload.get('content')
 from server.content import validate_content
 try:value=validate_content(value)
 except ValueError as error:reject(422,str(error))
 with db() as c:
  cursor=c.execute('INSERT INTO content_revisions(payload,status,actor,created_at) VALUES(?,?,?,?)',(json.dumps(value,ensure_ascii=False),'draft',u['id'],now()));revision=cursor.lastrowid
 audit(u['id'],'cms_draft',str(revision));return {'saved':True,'id':revision}
@app.post('/api/admin/content/publish')
def publish(request:Request,payload:dict|None=None):
 u=role(request,EDITORS)
 with db() as c:
  r=c.execute("SELECT * FROM content_revisions WHERE id=? AND status='draft'",(payload['id'],)).fetchone() if payload and 'id' in payload else c.execute("SELECT * FROM content_revisions WHERE status='draft' ORDER BY id DESC LIMIT 1").fetchone()
  if not r:reject(409,'No draft')
  c.execute("UPDATE content_revisions SET status='archived' WHERE status='published'")
  c.execute("UPDATE content_revisions SET status='published' WHERE id=?",(r['id'],))
 audit(u['id'],'cms_publish',str(r['id']));return json.loads(r['payload'])
@app.post('/api/admin/content/rollback')
def rollback(request:Request,payload:dict|None=None):
 u=role(request,EDITORS)
 with db() as c:
  r=c.execute("SELECT * FROM content_revisions WHERE id=? AND status IN ('archived','superseded')",(payload['id'],)).fetchone() if payload and 'id' in payload else c.execute("SELECT * FROM content_revisions WHERE status='archived' ORDER BY id DESC LIMIT 1").fetchone()
  if not r:reject(409,'No previous version')
  c.execute("UPDATE content_revisions SET status='superseded' WHERE status='published'")
  c.execute('INSERT INTO content_revisions(payload,status,actor,created_at) VALUES(?,?,?,?)',(r['payload'],'published',u['id'],now()))
 audit(u['id'],'cms_rollback',str(r['id']));return json.loads(r['payload'])
@app.get('/api/admin/users')
def users(request:Request):
 role(request,{'superadmin','manager','support'})
 with db() as c:return [dict(r) for r in c.execute('SELECT id,name,role,blocked,created_at FROM users ORDER BY created_at LIMIT 100')]
@app.patch('/api/admin/users/{id}')
def update_user(id:str,payload:dict,request:Request):
 u=role(request,{'superadmin'})
 valid={'user','superadmin','editor','manager','curator','reviewer','auditor','support','moderator'}
 if payload.get('role') not in valid:reject(422,'Unknown role')
 with db() as c:
  c.execute('BEGIN IMMEDIATE')
  previous=c.execute('SELECT role FROM users WHERE id=?',(id,)).fetchone()
  if not previous:reject(404,'User not found')
  if 'blocked' in payload and type(payload['blocked']) is not bool:reject(422,'blocked must be boolean')
  if previous[0]=='superadmin' and (payload['role']!='superadmin' or payload.get('blocked') is True):
   if c.execute("SELECT count(*) FROM users WHERE role='superadmin' AND blocked=0").fetchone()[0]<=1:reject(409,'Cannot remove last superadmin')
  c.execute('UPDATE users SET role=? WHERE id=?',(payload['role'],id))
  if 'blocked' in payload:c.execute('UPDATE users SET blocked=? WHERE id=?',(int(payload['blocked']),id))
  c.execute('DELETE FROM sessions WHERE user_id=?',(id,))
 audit(u['id'],'role_changed',id);return {'updated':True}
@app.get('/api/admin/audit')
def audit_events(request:Request):
 role(request,AUDITORS)
 with db() as c:return [dict(r) for r in c.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 200')]
@app.get('/api/admin/sources')
def source_records(request:Request):
 role(request,CURATORS|AUDITORS)
 with db() as c:return [dict(r)|{'payload':json.loads(r['payload'])} for r in c.execute('SELECT * FROM sources')]
@app.post('/api/admin/sources')
def add_source(payload:dict,request:Request):
 u=role(request,CURATORS)
 if not str(payload.get('url','')).startswith('https://') or not payload.get('title'):reject(422,'Title and HTTPS source URL required')
 id=str(uuid.uuid4())
 payload={k:str(payload.get(k,''))[:3000] for k in ['title','url','license_evidence']}
 with db() as c:c.execute('INSERT INTO sources VALUES(?,?,?,?)',(id,json.dumps(payload),'quarantine',now()))
 audit(u['id'],'source_quarantined',id);return {'id':id,'state':'quarantine','imported_rows':0}
@app.post('/api/feedback')
def feedback(payload:dict,request:Request):
 u=identity(request);text=payload.get('text','')
 if not isinstance(text,str) or not 1<=len(text)<=2000:reject(422,'Message must be 1–2000 characters')
 id=str(uuid.uuid4())
 with db() as c:c.execute('INSERT INTO feedback(id,owner_id,text,created_at) VALUES(?,?,?,?)',(id,u['id'],text,now()))
 return {'id':id,'status':'open'}
@app.get('/api/admin/feedback')
def list_feedback(request:Request):
 role(request,{'superadmin','support','moderator'})
 with db() as c:return [dict(r) for r in c.execute('SELECT id,text,status,created_at FROM feedback ORDER BY created_at DESC LIMIT 100')]
def model_enabled():
 with db() as c:r=c.execute("SELECT value FROM settings WHERE key='model_enabled'").fetchone()
 return r is None or r[0]=='true'
def load_model():
 global pose
 if pose is not None:return pose
 try:
  import mediapipe as mp
  manifest=json.loads((ROOT/'models/manifest.json').read_text());path=ROOT/'public/models/pose_landmarker_lite.task'
  actual=hashlib.sha256(path.read_bytes()).hexdigest()
  if actual!=manifest['sha256']:raise ValueError('Model checksum mismatch')
  pose=mp.tasks.vision.PoseLandmarker.create_from_options(mp.tasks.vision.PoseLandmarkerOptions(base_options=mp.tasks.BaseOptions(model_asset_path=str(path)),running_mode=mp.tasks.vision.RunningMode.IMAGE,num_poses=1))
  model_state.update(status='loaded',model_loaded=True,sha256=actual)
  return pose
 except Exception:
  model_state.update(status='unavailable',model_loaded=False);raise
@app.get('/api/ai/health')
def ai_health():return model_state|{'enabled':model_enabled(),'status':model_state['status'] if model_enabled() else 'disabled'}
@app.post('/api/admin/models')
def model_switch(payload:dict,request:Request):
 u=role(request,{'superadmin','reviewer'})
 if type(payload.get('enabled')) is not bool:reject(422,'Boolean enabled required')
 with db() as c:c.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',('model_enabled',str(payload['enabled']).lower()))
 audit(u['id'],'model_toggled');return ai_health()
def inference(path,start,end):
 import cv2,mediapipe as mp
 capture=cv2.VideoCapture(str(path));fps=capture.get(cv2.CAP_PROP_FPS);count=capture.get(cv2.CAP_PROP_FRAME_COUNT);seconds=count/fps if fps>0 else 0
 if not (0<=start<end<=seconds+.2 and 10<=end-start<=30.1):capture.release();reject(422,'Choose a valid 10–30 second segment')
 width=capture.get(cv2.CAP_PROP_FRAME_WIDTH);height=capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
 if width*height>3840*2160:capture.release();reject(422,'Maximum resolution is 4K')
 frames=[];begin=time.monotonic()
 try:
  with model_lock:
   loaded=load_model()
   for frame_time in range(int(start*1000),int(end*1000),250):
    if time.monotonic()-begin>60:reject(504,'Model timeout')
    capture.set(cv2.CAP_PROP_POS_MSEC,frame_time);ok,image=capture.read()
    if not ok:continue
    image=cv2.resize(image,(640,int(image.shape[0]*640/image.shape[1])))
    result=loaded.detect(mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)))
    points=[{'x':p.x,'y':p.y,'z':p.z,'visibility':p.visibility} for p in (result.pose_landmarks[0] if result.pose_landmarks else [])]
    frames.append({'time':frame_time/1000,'aspect':width/height,'landmarks':points})
 finally:capture.release()
 model_state.update(status='ready',sample_inference_tested=True,latency_ms=round((time.monotonic()-begin)*1000,2),last_success=now())
 return {'frames':frames,'model_id':model_state['model_id'],'model_version':model_state['model_version'],'model_loaded':True,'inference_mode':'server_cpu','source_ids':[],'is_demo':False,'verified_data_count':0,'warnings':['Not evaluated on Bangladesh cricket','2D observations, not a skill score'],'calibration_state':'not_calibrated','latency_ms':model_state['latency_ms']}
@app.post('/api/ai/analyze')
def analyze(request:Request,file:UploadFile=File(...),consent:str=Form(...),start:float=Form(0),end:float=Form(10)):
 u=identity(request)
 if consent!='true':reject(422,'Explicit video-processing consent required')
 if not model_enabled():reject(503,'Model disabled')
 if file.content_type not in ['video/mp4','video/webm','video/quicktime']:reject(415,'Unsupported video type')
 id=str(uuid.uuid4())
 with db() as c:
  c.execute('INSERT INTO jobs(id,owner_id,state,model_id,created_at) VALUES(?,?,?,?,?)',(id,u['id'],'running',model_state['model_id'],now()))
  c.execute('INSERT INTO consents VALUES(?,?,?,?,?)',(str(uuid.uuid4()),u['id'],'server_video_inference','v1',now()))
 path=None
 try:
  with tempfile.NamedTemporaryFile(suffix='.video',delete=False) as target:
   path=target.name;size=0
   while chunk:=file.file.read(1024*1024):
    size+=len(chunk)
    if size>50*1024*1024:reject(413,'Maximum video size is 50 MB')
    target.write(chunk)
  value=inference(path,start,end)
  with db() as c:c.execute('UPDATE jobs SET state=?,finished_at=? WHERE id=?',('succeeded',now(),id))
  return value|{'job_id':id}
 except HTTPException as e:
  with db() as c:c.execute('UPDATE jobs SET state=?,error_code=?,finished_at=? WHERE id=?',('failed',str(e.status_code),now(),id))
  raise
 except Exception:
  with db() as c:c.execute('UPDATE jobs SET state=?,error_code=?,finished_at=? WHERE id=?',('failed','model_unavailable',now(),id))
  reject(503,'Model unavailable; use private browser analysis or manual review')
 finally:
  if path:Path(path).unlink(missing_ok=True)
  file.file.close()
@app.get('/api/jobs/{id}')
def get_job(id:str,request:Request):
 u=identity(request)
 with db() as c:r=c.execute('SELECT * FROM jobs WHERE id=? AND owner_id=?',(id,u['id'])).fetchone()
 if not r:reject(404,'Job not found')
 return dict(r)
auth_recovery.install(app,db,hash_password,audit)
if (ROOT/'out').exists():app.mount('/',StaticFiles(directory=ROOT/'out',html=True),name='site')
if __name__=='__main__':
 import uvicorn
 uvicorn.run(app,host='127.0.0.1',port=int(os.environ.get('PORT','8000')))
