from server import check_smtp

def configured(monkeypatch):
    for key,value in {'APP_ORIGIN':'https://coach.example.test','SMTP_HOST':'mail.example.test','SMTP_FROM':'coach@example.test','SMTP_USER':'test-user','SMTP_PASSWORD':'private-test-value','SMTP_SECURITY':'starttls'}.items():
        monkeypatch.setenv(key,value)

def test_unconfigured_probe_has_no_network(monkeypatch):
    monkeypatch.delenv('SMTP_HOST',raising=False)
    def forbidden(*args,**kwargs):raise AssertionError('No network expected')
    monkeypatch.setattr(check_smtp.smtplib,'SMTP',forbidden)
    assert check_smtp.check()['error']=='configuration_invalid'

def test_probe_checks_tls_and_login_without_sending(monkeypatch):
    configured(monkeypatch);events=[]
    class Fake:
        def __init__(self,*a,**kw):events.append('connect')
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def ehlo(self):events.append('ehlo')
        def starttls(self,**kw):events.append('tls')
        def login(self,*a):events.append('login')
        def send_message(self,*a):raise AssertionError('Probe must not send email')
    monkeypatch.setattr(check_smtp.smtplib,'SMTP',Fake)
    result=check_smtp.check()
    assert result['tls_connection'] and result['authentication'] and result['email_sent'] is False
    assert events==['connect','ehlo','tls','ehlo','login']

def test_probe_failure_does_not_expose_server_details(monkeypatch):
    configured(monkeypatch)
    def failure(*a,**kw):raise RuntimeError('private-test-value recipient private@example.test')
    monkeypatch.setattr(check_smtp.smtplib,'SMTP',failure)
    result=check_smtp.check()
    assert result['error']=='smtp_tls_or_connection_failed'
    assert 'private' not in str(result)
