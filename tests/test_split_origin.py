from tests.test_api import client,module,record

def test_public_origin_allowed_through_proxy(monkeypatch):
    c,_=client();monkeypatch.setenv('APP_ORIGIN','https://goli-coach.example.test')
    assert c.post('/api/records',json=record(),headers={'Origin':'https://goli-coach.example.test'}).status_code==200
    assert c.post('/api/records',json=record(),headers={'Origin':'https://unrelated.example.test'}).status_code==403
    assert c.post('/api/records',json=record(),headers={'Origin':'https://goli-coach.example.test.evil.test'}).status_code==403

def test_malformed_origin_is_rejected():
    for value in ['null','https://user:pass@testserver','https://testserver/path','https://testserver?x=1']:
        assert not module.origin_allowed(value,'testserver')

def test_disabled_server_video_advertised_and_enforced(monkeypatch):
    c,_=client();monkeypatch.setenv('SERVER_VIDEO_ENABLED','0')
    assert c.get('/api/health').json()['server_video_available'] is False
    result=c.post('/api/ai/analyze',data={'consent':'true'},files={'file':('test.mp4',b'not-a-video','video/mp4')})
    assert result.status_code==503
