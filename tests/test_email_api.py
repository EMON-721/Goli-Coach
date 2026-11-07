import json
import pytest
from server import auth_recovery

def configure(monkeypatch):
    for key,value in {'MAIL_TRANSPORT':'resend','MAIL_FROM':'verified@example.test','RESEND_API_KEY':'test-secret-not-real','APP_ORIGIN':'https://golicoach.example.test'}.items():monkeypatch.setenv(key,value)

def test_https_email_payload(monkeypatch):
    configure(monkeypatch);requests=[]
    class Response:
        status=200
        def __enter__(self):return self
        def __exit__(self,*args):pass
    def capture(request,**kwargs):requests.append(request);return Response()
    monkeypatch.setattr(auth_recovery.urllib.request,'urlopen',capture)
    auth_recovery.deliver('owner@example.test','verify','test-token')
    request=requests[0];payload=json.loads(request.data)
    assert request.full_url=='https://api.resend.com/emails'
    assert payload['to']==['owner@example.test']
    assert 'https://golicoach.example.test/#verify=test-token' in payload['text']
    assert 'test-secret-not-real' not in payload['text']

def test_https_email_errors_do_not_log_token_or_key(monkeypatch,caplog):
    configure(monkeypatch)
    def fail(*args,**kwargs):raise RuntimeError('test-secret-not-real test-token owner@example.test')
    monkeypatch.setattr(auth_recovery.urllib.request,'urlopen',fail)
    auth_recovery.deliver('owner@example.test','reset','test-token')
    assert 'account_email_delivery_failed' in caplog.text
    assert 'test-secret' not in caplog.text and 'test-token' not in caplog.text and '@' not in caplog.text

def test_api_configuration_requires_key_and_sender(monkeypatch):
    configure(monkeypatch);monkeypatch.delenv('RESEND_API_KEY')
    with pytest.raises(ValueError):auth_recovery.configuration()
