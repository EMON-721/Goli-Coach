import hashlib,time,uuid
import pytest
from fastapi.testclient import TestClient
from server import app as module
from server import auth_recovery

@pytest.fixture
def auth(tmp_path,monkeypatch):
 monkeypatch.setattr(module,'DB',tmp_path/'auth.sqlite');module.migrate();module.rate.clear()
 monkeypatch.setenv('REQUIRE_EMAIL_VERIFICATION','1');monkeypatch.setenv('APP_ORIGIN','https://golicoach.example');monkeypatch.setenv('SMTP_HOST','smtp.example');monkeypatch.setenv('SMTP_FROM','accounts@golicoach.example')
 sent=[];monkeypatch.setattr(auth_recovery,'deliver',lambda email,purpose,token:sent.append((email,purpose,token)))
 return TestClient(module.app),sent

def credentials():return {'email':str(uuid.uuid4())+'@example.test','name':'Test','password':'old-password-12345'}
def registered(auth):
 client,sent=auth;data=credentials();r=client.post('/api/auth/register',json=data);assert r.status_code==200
 return client,sent,data

def test_verification_before_login_and_single_use(auth):
 c,sent,data=registered(auth);token=sent[-1][2]
 assert c.get('/api/me').status_code==401
 assert c.post('/api/auth/login',json=data).status_code==403
 assert c.post('/api/auth/verify-email',json={'token':token}).status_code==200
 assert c.post('/api/auth/verify-email',json={'token':token}).status_code==400
 assert c.post('/api/auth/login',json=data).status_code==200

def test_tokens_stored_as_hash_only(auth):
 c,sent,_=registered(auth);token=sent[0][2]
 with module.db() as db:row=db.execute('SELECT token_hash FROM action_tokens').fetchone()
 assert row[0]==hashlib.sha256(token.encode()).hexdigest() and row[0]!=token

def test_password_recovery_revokes_old_sessions(auth):
 c,sent,data=registered(auth);c.post('/api/auth/verify-email',json={'token':sent[-1][2]});c.post('/api/auth/login',json=data)
 assert c.post('/api/auth/forgot-password',json={'email':data['email']}).status_code==200
 token=sent[-1][2]
 assert c.post('/api/auth/reset-password',json={'token':token,'password':'new-password-12345'}).status_code==200
 assert c.get('/api/me').status_code==401
 assert c.post('/api/auth/login',json=data).status_code==401
 assert c.post('/api/auth/login',json={**data,'password':'new-password-12345'}).status_code==200
 assert c.post('/api/auth/reset-password',json={'token':token,'password':'another-password-123'}).status_code==400

def test_unknown_account_has_same_recovery_response(auth):
 c,sent,data=registered(auth)
 known=c.post('/api/auth/forgot-password',json={'email':data['email']});unknown=c.post('/api/auth/forgot-password',json={'email':'missing@example.test'})
 assert known.json()==unknown.json() and len(sent)==2

def test_wrong_purpose_expired_and_blocked_links_fail(auth):
 c,sent,data=registered(auth);token=sent[-1][2]
 assert c.post('/api/auth/reset-password',json={'token':token,'password':'another-password-123'}).status_code==400
 with module.db() as db:db.execute('UPDATE action_tokens SET expires=?',(time.time()-1,))
 assert c.post('/api/auth/verify-email',json={'token':token}).status_code==400
 with module.db() as db:db.execute('UPDATE action_tokens SET expires=?',(time.time()+100,));db.execute('UPDATE users SET blocked=1')
 assert c.post('/api/auth/verify-email',json={'token':token}).status_code==400

def test_missing_mail_fails_closed(auth,monkeypatch):
 c,_=auth;monkeypatch.delenv('SMTP_HOST')
 assert c.post('/api/auth/register',json=credentials()).status_code==503
 assert c.post('/api/auth/forgot-password',json={'email':'test@example.test'}).status_code==503

def test_resend_cooldown_and_old_token_invalidation(auth):
 c,sent,data=registered(auth);old=sent[-1][2]
 c.post('/api/auth/resend-verification',json={'email':data['email']});assert len(sent)==1
 with module.db() as db:db.execute('UPDATE action_tokens SET created=0')
 c.post('/api/auth/resend-verification',json={'email':data['email']});assert len(sent)==2
 assert c.post('/api/auth/verify-email',json={'token':old}).status_code==400
 assert c.post('/api/auth/verify-email',json={'token':sent[-1][2]}).status_code==200

def test_untrusted_origin_configuration_rejected(auth,monkeypatch):
 c,_=auth;monkeypatch.setenv('APP_ORIGIN','http://untrusted.example')
 assert c.post('/api/auth/register',json=credentials()).status_code==503

def test_email_recipient_injection_rejected(auth):
 c,_=auth
 for email in ['first,second@example.test','bad\nBcc:other@example.test','Name <test@example.test>']:
  assert c.post('/api/auth/forgot-password',json={'email':email}).status_code==422
