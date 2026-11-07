"""Owner-created, revocable report snapshots. Capability tokens never enter URLs on the API."""
import hashlib
import json
import math
import secrets
import time
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, Request
from pydantic import BaseModel, Field
from server import auth_recovery


class ShareOptions(BaseModel):
    hours: int = Field(default=24, ge=1, le=168)
    include_notes: bool = False


class ShareToken(BaseModel):
    token: str = Field(min_length=40, max_length=100, pattern=r'^[A-Za-z0-9_-]+$')


def snapshot(record, include_notes):
    # Explicit allowlist: never publish account IDs, uploaded media, URLs or raw landmarks.
    data = {'title': str(record.get('title', 'Practice report'))[:200],
            'kind': record.get('kind'), 'is_demo': record.get('is_demo') is True,
            'created_at': str(record.get('created_at', ''))[:40],
            'model_id': str(record.get('model_id') or '')[:100],
            'warning': 'Image-plane observations; not a validated cricket skill score.',
            'metrics': None}
    metrics = record.get('metrics')
    if isinstance(metrics, dict):
        data['metrics'] = {}
        for key in ('valid_frames', 'total_frames', 'coverage', 'left_knee', 'right_knee', 'stance_ratio'):
            value = metrics.get(key)
            data['metrics'][key] = value if type(value) in (int, float) and math.isfinite(value) else None
    if include_notes:
        data['notes'] = str(record.get('notes', ''))[:2000]
    return data


def install(app, db, identity, own_record, audit):
    @app.post('/api/records/{record_id}/shares')
    def create(record_id: str, options: ShareOptions, request: Request):
        user, record = own_record(request, record_id)
        token = secrets.token_urlsafe(32)
        share_id = str(uuid.uuid4())
        expires = time.time() + options.hours * 3600
        payload = snapshot(json.loads(record['payload']), options.include_notes)
        with db() as conn:
            conn.execute('BEGIN IMMEDIATE')
            count = conn.execute('SELECT count(*) FROM report_shares WHERE record_id=? AND expires>?',
                                 (record_id, time.time())).fetchone()[0]
            if count >= 10:
                raise HTTPException(409, 'Revoke an existing link before creating another')
            conn.execute('INSERT INTO report_shares VALUES(?,?,?,?,?,?,?)',
                         (share_id, hashlib.sha256(token.encode()).hexdigest(), user['id'], record_id,
                          expires, json.dumps(payload, ensure_ascii=False), datetime.now(timezone.utc).isoformat()))
        audit(user['id'], 'share_created', share_id)
        return {'id': share_id, 'token': token, 'expires': expires}

    @app.get('/api/records/{record_id}/shares')
    def listing(record_id: str, request: Request):
        user, _ = own_record(request, record_id)
        with db() as conn:
            return [dict(row) for row in conn.execute(
                'SELECT id,expires,created_at FROM report_shares WHERE record_id=? AND owner_id=? ORDER BY created_at DESC',
                (record_id, user['id']))]

    @app.delete('/api/shares/{share_id}')
    def revoke(share_id: str, request: Request):
        user = identity(request)
        with db() as conn:
            if not conn.execute('DELETE FROM report_shares WHERE id=? AND owner_id=?',
                                (share_id, user['id'])).rowcount:
                raise HTTPException(404, 'Share not found')
        audit(user['id'], 'share_revoked', share_id)
        return {'deleted': True}

    @app.post('/api/shares/read')
    def read(value: ShareToken):
        with db() as conn:
            row = conn.execute('SELECT report_shares.payload,report_shares.expires,users.verified '
                               'FROM report_shares JOIN users ON users.id=report_shares.owner_id '
                               'WHERE token_hash=? AND expires>? AND users.blocked=0',
                               (hashlib.sha256(value.token.encode()).hexdigest(), time.time())).fetchone()
        if not row or (auth_recovery.verification_required() and not row['verified']):
            raise HTTPException(404, 'This link is invalid, expired or revoked')
        return {'report': json.loads(row['payload']), 'expires': row['expires']}
