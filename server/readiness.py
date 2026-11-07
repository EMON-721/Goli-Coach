"""Deployment readiness checks; no network requests or email delivery."""
import hashlib
import json
import os
from pathlib import Path
from server import auth_recovery


def checks(root: Path, db):
    result = {}
    try:
        with db() as conn:
            conn.execute('SELECT count(*) FROM users').fetchone()
            conn.execute('SELECT count(*) FROM records').fetchone()
        result['database'] = True
    except Exception:
        result['database'] = False
    result['web_build'] = (root / 'out/index.html').is_file()
    try:
        manifest = json.loads((root / 'models/manifest.json').read_text())
        digest = hashlib.sha256((root / 'public/models/pose_landmarker_lite.task').read_bytes()).hexdigest()
        result['model_checksum'] = digest == manifest['sha256']
    except (OSError, ValueError, KeyError):
        result['model_checksum'] = False
    result['secure_cookies'] = os.environ.get('SECURE_COOKIES', '1') == '1'
    result['email_verification'] = auth_recovery.verification_required()
    try:
        auth_recovery.configuration()
        result['email_configuration'] = True
    except ValueError:
        result['email_configuration'] = False
    return result


if __name__ == '__main__':
    from server.app import ROOT, db
    result = checks(ROOT, db)
    print(json.dumps({'ready': all(result.values()), 'checks': result,
                      'email_delivery_tested': False}, indent=2))
    raise SystemExit(0 if all(result.values()) else 1)
