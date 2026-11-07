import hashlib,json,time
from fastapi.testclient import TestClient
from tests.test_api import client,record,module

def create():
    owner,uid=client();r=record();r.update(notes='Private note',frames=[{'private':'landmarks'}],email='private@example.test',metrics={'coverage':90})
    assert owner.post('/api/records',json=r).status_code==200
    share=owner.post('/api/records/'+r['id']+'/shares',json={}).json()
    return owner,uid,r,share

def test_shared_snapshot_excludes_private_data():
    owner,uid,r,s=create();anonymous=TestClient(module.app)
    value=anonymous.post('/api/shares/read',json={'token':s['token']}).json()['report']
    assert 'notes' not in value and 'frames' not in value and 'email' not in value and 'id' not in value
    assert value['metrics']['coverage']==90
    with module.db() as c:
        row=c.execute('SELECT * FROM report_shares WHERE id=?',(s['id'],)).fetchone()
        assert row['token_hash']==hashlib.sha256(s['token'].encode()).hexdigest()
        assert s['token'] not in json.dumps(dict(row))

def test_owner_can_revoke_other_owner_cannot():
    owner,uid,r,s=create();other,_=client('superadmin')
    assert other.delete('/api/shares/'+s['id']).status_code==404
    assert other.get('/api/records/'+r['id']+'/shares').status_code==404
    assert owner.delete('/api/shares/'+s['id']).status_code==200
    assert TestClient(module.app).post('/api/shares/read',json={'token':s['token']}).status_code==404

def test_expiry_and_blocking():
    owner,uid,r,s=create()
    with module.db() as c:c.execute('UPDATE users SET blocked=1 WHERE id=?',(uid,))
    assert TestClient(module.app).post('/api/shares/read',json={'token':s['token']}).status_code==404
    with module.db() as c:
        c.execute('UPDATE users SET blocked=0 WHERE id=?',(uid,));c.execute('UPDATE report_shares SET expires=? WHERE id=?',(time.time()-1,s['id']))
    assert TestClient(module.app).post('/api/shares/read',json={'token':s['token']}).status_code==404

def test_notes_opt_in_and_delete_cascade():
    owner,uid,r,s=create()
    s=owner.post('/api/records/'+r['id']+'/shares',json={'include_notes':True}).json()
    assert TestClient(module.app).post('/api/shares/read',json={'token':s['token']}).json()['report']['notes']=='Private note'
    owner.delete('/api/records/'+r['id'])
    assert TestClient(module.app).post('/api/shares/read',json={'token':s['token']}).status_code==404

def test_expiry_bounds_and_ownership():
    owner,uid,r,s=create();other,_=client()
    assert owner.post('/api/records/'+r['id']+'/shares',json={'hours':169}).status_code==422
    assert other.post('/api/records/'+r['id']+'/shares',json={}).status_code==404
