"""Check TLS SMTP connectivity/authentication without sending an email.

Run inside the deployed app: python -m server.check_smtp
Reads environment only; never prints credentials or server exception text.
"""
import json
import os
import smtplib
import ssl
from server.auth_recovery import configuration


def check():
    result = {'configuration': False, 'tls_connection': False,
              'authentication': False, 'email_sent': False}
    try:
        configuration()
        mode = os.environ.get('SMTP_SECURITY', 'starttls')
        port = int(os.environ.get('SMTP_PORT', '465' if mode == 'ssl' else '587'))
        if not 1 <= port <= 65535:
            raise ValueError('Invalid port')
        result['configuration'] = True
    except (ValueError, KeyError):
        return result | {'error': 'configuration_invalid'}
    try:
        context = ssl.create_default_context()
        transport = smtplib.SMTP_SSL if mode == 'ssl' else smtplib.SMTP
        with transport(os.environ['SMTP_HOST'], port, timeout=15,
                       **({'context': context} if mode == 'ssl' else {})) as smtp:
            smtp.ehlo()
            if mode == 'starttls':
                smtp.starttls(context=context)
                smtp.ehlo()
            result['tls_connection'] = True
            if os.environ.get('SMTP_USER'):
                smtp.login(os.environ['SMTP_USER'], os.environ.get('SMTP_PASSWORD', ''))
                result['authentication'] = True
            else:
                return result | {'error': 'smtp_credentials_missing'}
        return result
    except smtplib.SMTPAuthenticationError:
        return result | {'error': 'smtp_authentication_failed'}
    except Exception:
        return result | {'error': 'smtp_tls_or_connection_failed'}


if __name__ == '__main__':
    result = check()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if all(result[k] for k in ('configuration', 'tls_connection', 'authentication')) else 1)
