"""SQLite for local runs, TLS PostgreSQL for durable hosted accounts."""
import os,re,sqlite3
from pathlib import Path


class Row(dict):
    def __getitem__(self,key):
        return list(self.values())[key] if isinstance(key,int) else super().__getitem__(key)


class Cursor:
    def __init__(self,cursor,lastrowid=None):
        self.cursor=cursor;self.lastrowid=lastrowid
    @property
    def rowcount(self):return self.cursor.rowcount
    def fetchone(self):
        value=self.cursor.fetchone()
        return Row(value) if value is not None else None
    def fetchall(self):return [Row(row) for row in self.cursor.fetchall()]
    def __iter__(self):return iter(self.fetchall())


class Postgres:
    def __init__(self,url):
        import psycopg
        from psycopg.rows import dict_row
        # Database credentials never reach logs or browser bundles.
        mode='require'
        # The isolated CI Postgres container has no TLS. Hosted URLs always require TLS.
        if os.environ.get('DATABASE_SSLMODE')=='disable':
            from urllib.parse import urlsplit
            if urlsplit(url).hostname not in ('localhost','127.0.0.1'):raise ValueError('TLS is required for remote PostgreSQL')
            mode='disable'
        self.connection=psycopg.connect(url,sslmode=mode,connect_timeout=15,row_factory=dict_row)
    def __enter__(self):return self
    def __exit__(self,kind,value,traceback):
        try:
            if kind:self.connection.rollback()
            else:self.connection.commit()
        finally:self.connection.close()
    def execute(self,query,parameters=()):
        import psycopg
        if query.strip().upper()=='BEGIN IMMEDIATE':
            # Serialize the ownership/token critical sections used by this app.
            return Cursor(self.connection.execute('SELECT pg_advisory_xact_lock(7305001)'))
        query=query.replace('?', '%s')
        returning=bool(re.match(r'INSERT INTO content_revisions\b',query,re.I))
        if returning:query+=' RETURNING id'
        try:
            cursor=self.connection.execute(query,parameters or None)
        except psycopg.IntegrityError as error:
            raise sqlite3.IntegrityError('Database constraint violation') from error
        return Cursor(cursor,cursor.fetchone()['id'] if returning else None)
    def executescript(self,script):
        for query in script.split(';'):
            if query.strip():self.connection.execute(query)


def connect(path):
    url=os.environ.get('DATABASE_URL','')
    if url:return Postgres(url)
    if os.environ.get('REQUIRE_REMOTE_DATABASE')=='1':raise RuntimeError('DATABASE_URL is required for this hosted deployment')
    connection=sqlite3.connect(path)
    connection.row_factory=sqlite3.Row
    connection.execute('PRAGMA foreign_keys=ON')
    return connection


def migrate(root,connect_db):
    with connect_db() as connection:
        if isinstance(connection,Postgres):
            connection.executescript((root/'server/schema.postgres.sql').read_text())
            connection.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS verified INTEGER NOT NULL DEFAULT 0')
        else:
            connection.executescript((root/'server/schema.sql').read_text())
            if 'verified' not in {row[1] for row in connection.execute('PRAGMA table_info(users)')}:
                connection.execute('ALTER TABLE users ADD COLUMN verified INTEGER NOT NULL DEFAULT 0')
