"""Single-use email verification/password recovery. No tokens in API responses or logs."""
import hashlib,logging,os,re,secrets,smtplib,ssl,time
from email.message import EmailMessage
from urllib.parse import urlsplit
from fastapi import BackgroundTasks,HTTPException
from pydantic import BaseModel,Field

logger=logging.getLogger('golicoach.mail')
def verification_required():return os.environ.get('REQUIRE_EMAIL_VERIFICATION','1')!='0'
def email_valid(value):return bool(re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+",value))
def configuration():
 origin=os.environ.get('APP_ORIGIN','').rstrip('/');parsed=urlsplit(origin)
 if parsed.scheme!='https' or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password:raise ValueError('APP_ORIGIN must be a bare HTTPS origin')
 if not os.environ.get('SMTP_HOST') or not email_valid(os.environ.get('SMTP_FROM','')):raise ValueError('SMTP_HOST and valid SMTP_FROM required')
 if os.environ.get('SMTP_SECURITY','starttls') not in ['starttls','ssl']:raise ValueError('TLS SMTP required')
 return origin

def deliver(recipient,purpose,token):
 try:
  origin=configuration();message=EmailMessage();message['From']=os.environ['SMTP_FROM'];message['To']=recipient
  message['Subject']='Goli-Coach: '+('verify your email' if purpose=='verify' else 'reset your password')
  message.set_content(f'You requested an account action at Goli-Coach.\n\n{origin}/#{purpose}={token}\n\nThis single-use link expires in 30 minutes. If you did not request it, ignore this message.\n')
  context=ssl.create_default_context();mode=os.environ.get('SMTP_SECURITY','starttls');port=int(os.environ.get('SMTP_PORT','465' if mode=='ssl' else '587'))
  transport=smtplib.SMTP_SSL if mode=='ssl' else smtplib.SMTP
  with transport(os.environ['SMTP_HOST'],port,timeout=15,**({'context':context} if mode=='ssl' else {})) as smtp:
   if mode=='starttls':smtp.ehlo();smtp.starttls(context=context);smtp.ehlo()
   if os.environ.get('SMTP_USER'):smtp.login(os.environ['SMTP_USER'],os.environ.get('SMTP_PASSWORD',''))
   smtp.send_message(message)
 except Exception:
  # Avoid traceback, recipients and tokens in logs. Monitor this event at deployment.
  logger.error('account_email_delivery_failed')

def queue_token(db,user,purpose,tasks):
 token=secrets.token_urlsafe(32);digest=hashlib.sha256(token.encode()).hexdigest()
 with db() as c:
  c.execute('BEGIN IMMEDIATE')
  old=c.execute('SELECT max(created) FROM action_tokens WHERE user_id=? AND purpose=?',(user['id'],purpose)).fetchone()[0]
  if old and time.time()-old<60:return
  c.execute('DELETE FROM action_tokens WHERE user_id=? AND purpose=?',(user['id'],purpose))
  c.execute('INSERT INTO action_tokens VALUES(?,?,?,?,?)',(digest,user['id'],purpose,time.time()+1800,time.time()))
 tasks.add_task(deliver,user['email'],purpose,token)

class EmailRequest(BaseModel):email:str=Field(min_length=3,max_length=254)
class TokenRequest(BaseModel):token:str=Field(min_length=32,max_length=128)
class ResetRequest(TokenRequest):password:str=Field(min_length=12,max_length=200)

def install(app,db,hash_password,audit):
 def require_mail():
  try:configuration()
  except ValueError:raise HTTPException(503,'Account email service is not configured')
 def request_action(payload,tasks,purpose):
  require_mail();email=payload.email.strip().lower()
  if not email_valid(email):raise HTTPException(422,'Valid email required')
  with db() as c:user=c.execute('SELECT id,email,blocked,verified FROM users WHERE email=?',(email,)).fetchone()
  if user and not user['blocked'] and (purpose=='reset' or not user['verified']):queue_token(db,dict(user),purpose,tasks)
  return {'message':'If this account is eligible, an email will arrive shortly.'}
 @app.post('/api/auth/forgot-password')
 def forgot_password(payload:EmailRequest,tasks:BackgroundTasks):return request_action(payload,tasks,'reset')
 @app.post('/api/auth/resend-verification')
 def resend_verification(payload:EmailRequest,tasks:BackgroundTasks):return request_action(payload,tasks,'verify')
 def consume(payload,purpose):
  digest=hashlib.sha256(payload.token.encode()).hexdigest()
  with db() as c:
   c.execute('BEGIN IMMEDIATE')
   row=c.execute('SELECT action_tokens.user_id FROM action_tokens JOIN users ON users.id=action_tokens.user_id WHERE token_hash=? AND purpose=? AND expires>? AND users.blocked=0',(digest,purpose,time.time())).fetchone()
   if not row:raise HTTPException(400,'Link is invalid or expired')
   uid=row['user_id']
   if purpose=='verify':c.execute('UPDATE users SET verified=1 WHERE id=?',(uid,))
   else:
    c.execute('UPDATE users SET password=?,verified=1 WHERE id=?',(hash_password(payload.password),uid))
    c.execute('DELETE FROM sessions WHERE user_id=?',(uid,))
   c.execute('DELETE FROM action_tokens WHERE user_id=?',(uid,))
  audit(uid,'email_verified' if purpose=='verify' else 'password_reset')
  return {'ok':True,'message':'Email verified. Sign in to continue.' if purpose=='verify' else 'Password changed. Sign in again.'}
 @app.post('/api/auth/verify-email')
 def verify(payload:TokenRequest):return consume(payload,'verify')
 @app.post('/api/auth/reset-password')
 def reset(payload:ResetRequest):return consume(payload,'reset')
