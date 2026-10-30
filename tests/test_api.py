import os,tempfile,uuid,json
os.environ['DATABASE_PATH']=tempfile.mktemp(suffix='.sqlite')
os.environ['SECURE_COOKIES']='0'
os.environ['REQUIRE_EMAIL_VERIFICATION']='0'
from fastapi.testclient import TestClient
from server import app as module
import pytest
@pytest.fixture(autouse=True)
def reset_rate():module.rate.clear()
def client(role='user'):
 c=TestClient(module.app);r=c.post('/api/auth/register',json={'email':str(uuid.uuid4())+'@example.test','name':'পরীক্ষা','password':'test-only-password-123'})
 assert r.status_code==200
 if role!='user':
  with module.db() as db:db.execute('UPDATE users SET role=? WHERE id=?',(role,r.json()['id']))
 return c,r.json()['id']
def record():return {'id':str(uuid.uuid4()),'kind':'batting','notes':'নিজের নোট','title':'পরীক্ষা','is_demo':True}
def test_health():assert TestClient(module.app).get('/api/health').json()['service']=='golicoach'
def test_no_identity_denied():assert TestClient(module.app).get('/api/records').status_code==401
def test_signup_and_me():
 c,u=client();assert c.get('/api/me').json()['id']==u
 assert 'password' not in c.get('/api/me').json()
def test_bad_password():
 c,_=client();assert c.post('/api/auth/login',json={'email':'missing@example.test','password':'bad-password-123'}).status_code==401
def test_logout_revokes_session():
 c,_=client();assert c.post('/api/auth/logout').status_code==200;assert c.get('/api/me').status_code==401
def test_save_get_edit_delete():
 c,_=client();r=record();assert c.post('/api/records',json=r).status_code==200
 assert c.get('/api/records/'+r['id']).json()['notes']=='নিজের নোট'
 assert c.patch('/api/records/'+r['id'],json={'notes':'নতুন নোট'}).status_code==200
 assert c.delete('/api/records/'+r['id']).status_code==200
 assert c.get('/api/records/'+r['id']).status_code==404
def test_cross_user_read_denied():
 a,_=client();b,_=client();r=record();a.post('/api/records',json=r)
 assert b.get('/api/records/'+r['id']).status_code==404
 assert b.get('/api/records').json()==[]
def test_cross_user_overwrite_denied():
 a,_=client();b,_=client();r=record();a.post('/api/records',json=r)
 assert b.post('/api/records',json=r).status_code==404
def test_cross_user_delete_denied():
 a,_=client();b,_=client();r=record();a.post('/api/records',json=r)
 assert b.delete('/api/records/'+r['id']).status_code==404
def test_admin_cannot_read_unrelated_private_record():
 a,_=client();b,_=client('superadmin');r=record();a.post('/api/records',json=r)
 assert b.get('/api/records/'+r['id']).status_code==404
def test_user_admin_denied():
 c,_=client();assert c.get('/api/admin/users').status_code==403
 assert c.post('/api/admin/content',json={'content':{'brand':'x'}}).status_code==403
def test_editor_model_denied():
 c,_=client('editor');assert c.post('/api/admin/models',json={'enabled':False}).status_code==403
def test_cms_publish_rollback():
 c,_=client('editor')
 for title in ['আগের শিরোনাম','নতুন শিরোনাম']:
  assert c.post('/api/admin/content',json={'content':{'hero_bn':title}}).status_code==200
  assert c.post('/api/admin/content/publish').status_code==200
 assert c.get('/api/content').json()['hero_bn']=='নতুন শিরোনাম'
 assert c.post('/api/admin/content/rollback').json()['hero_bn']=='আগের শিরোনাম'
def test_unknown_cms_field_rejected():
 c,_=client('editor');assert c.post('/api/admin/content',json={'content':{'script':'bad'}}).status_code==422
def test_rights_unknown_quarantined():
 c,_=client('curator');r=c.post('/api/admin/sources',json={'title':'Candidate','url':'https://example.org'})
 assert r.json()['state']=='quarantine' and r.json()['imported_rows']==0
def test_source_unsafe_url_denied():
 c,_=client('curator');assert c.post('/api/admin/sources',json={'title':'Unsafe','url':'file:///etc/passwd'}).status_code==422
def test_feedback_isolated_from_user():
 c,_=client();assert c.post('/api/feedback',json={'text':'পরীক্ষামূলক মতামত'}).status_code==200
 assert c.get('/api/admin/feedback').status_code==403
def test_cross_origin_write_denied():
 c,_=client();assert c.post('/api/records',headers={'Origin':'https://unrelated.invalid'},json=record()).status_code==403
def test_missing_model_not_fake_healthy():
 state=TestClient(module.app).get('/api/ai/health').json();assert state['status']!='ready' and state['sample_inference_tested'] is False
def test_model_kill_switch():
 c,_=client('superadmin');assert c.post('/api/admin/models',json={'enabled':False}).json()['status']=='disabled'
 c.post('/api/admin/models',json={'enabled':True})
def test_analyze_needs_identity():
 r=TestClient(module.app).post('/api/ai/analyze',data={'consent':'true'},files={'file':('test.mp4',b'bad','video/mp4')});assert r.status_code==401
def test_analyze_needs_consent():
 c,_=client();assert c.post('/api/ai/analyze',data={'consent':'false'},files={'file':('test.mp4',b'bad','video/mp4')}).status_code==422
def test_analyze_rejects_type():
 c,_=client();assert c.post('/api/ai/analyze',data={'consent':'true'},files={'file':('x.txt',b'bad','text/plain')}).status_code==415
def test_account_delete_cascades():
 c,u=client();c.post('/api/records',json=record());assert c.delete('/api/account').status_code==200
 with module.db() as db:assert db.execute('SELECT count(*) FROM records WHERE owner_id=?',(u,)).fetchone()[0]==0
def test_journal_isolation_and_cascade():
 a,uid=client();b,_=client('superadmin');note={'id':str(uuid.uuid4()),'text':'Private practice note','date':'2026-10-29T06:00:00Z'}
 assert a.post('/api/journal',json=note).status_code==200
 assert b.get('/api/journal').json()==[]
 assert b.post('/api/journal',json=note).status_code==404
 assert b.delete('/api/journal/'+note['id']).status_code==404
 note['text']='Updated';assert a.post('/api/journal',json=note).status_code==200
 assert a.get('/api/journal').json()[0]['text']=='Updated'
 a.delete('/api/account')
 with module.db() as db:assert db.execute('SELECT count(*) FROM journal WHERE owner_id=?',(uid,)).fetchone()[0]==0
def test_blank_journal_rejected():
 c,_=client();assert c.post('/api/journal',json={'id':str(uuid.uuid4()),'text':'  ','date':'2026-10-29T06:00:00Z'}).status_code==422
def test_selected_revision_publishes_exact_draft():
 c,_=client('editor');first=c.post('/api/admin/content',json={'content':{'brand':'Selected'}}).json()['id']
 second=c.post('/api/admin/content',json={'content':{'brand':'Other draft'}}).json()['id']
 assert c.post('/api/admin/content/publish',json={'id':first}).json()['brand']=='Selected'
 assert c.get('/api/admin/content/revisions').json()[0]['id']==second
 assert c.post('/api/admin/content/publish',json={'id':999999}).status_code==409
def test_full_content_collections():
 c,_=client('editor');value={'privacy_bn':'অতিরিক্ত নীতি','faq':[{'question_bn':'প্রশ্ন','question_en':'Question','answer_bn':'উত্তর','answer_en':'Answer'}]}
 revision=c.post('/api/admin/content',json={'content':value}).json()['id']
 assert c.post('/api/admin/content/publish',json={'id':revision}).json()==value
 value['faq'][0]['script']='bad';assert c.post('/api/admin/content',json={'content':value}).status_code==422
def test_duplicate_navigation_rejected():
 c,_=client('editor');assert c.post('/api/admin/content',json={'content':{'navigation':[{'id':'home','bn':'মাঠ','en':'Home'}]*4}}).status_code==422
def test_user_cannot_read_drafts():
 c,_=client();assert c.get('/api/admin/content/revisions').status_code==403
def test_feedback_resolution_authorization():
 c,_=client();id=c.post('/api/feedback',json={'text':'Issue'}).json()['id']
 assert c.patch('/api/admin/feedback/'+id,json={'status':'resolved'}).status_code==403
 support,_=client('support');assert support.patch('/api/admin/feedback/'+id,json={'status':'resolved'}).status_code==200
 assert support.patch('/api/admin/feedback/'+id,json={'status':'invalid'}).status_code==422
def test_source_approval_requires_rights_evidence():
 c,_=client('curator');id=c.post('/api/admin/sources',json={'title':'Source','url':'https://example.org'}).json()['id']
 assert c.patch('/api/admin/sources/'+id,json={'state':'approved'}).status_code==422
 r=c.patch('/api/admin/sources/'+id,json={'state':'approved','rights_confirmed':True,'license_evidence':'Written permission checked for evaluation and participant consent.'})
 assert r.status_code==200 and r.json()['imported_rows']==0
def test_blocking_revokes_sessions():
 admin,_=client('superadmin');user,uid=client();assert admin.patch('/api/admin/users/'+uid,json={'role':'user','blocked':True}).status_code==200
 assert user.get('/api/me').status_code==401
def test_last_superadmin_cannot_be_blocked():
 admin,uid=client('superadmin')
 with module.db() as db:db.execute("UPDATE users SET role='user' WHERE role='superadmin' AND id!=?",(uid,))
 assert admin.patch('/api/admin/users/'+uid,json={'role':'superadmin','blocked':True}).status_code==409
