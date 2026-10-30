import json,sqlite3,time
from pathlib import Path
import pytest
from server.maintenance import backup,restore,cleanup

@pytest.fixture
def database(tmp_path):
 path=tmp_path/'source.sqlite'
 with sqlite3.connect(path) as db:
  db.executescript((Path(__file__).resolve().parents[1]/'server/schema.sql').read_text())
  db.execute("INSERT INTO users(id,email,name,password,created_at) VALUES('u','test@example.test','Test','hashed','2026-10-30')")
  db.execute("INSERT INTO journal VALUES('note','u','keep me','2026-10-30')")
  db.execute("INSERT INTO sessions VALUES('expired','u',?)",(time.time()-1,))
  db.execute("INSERT INTO sessions VALUES('live','u',?)",(time.time()+1000,))
  db.execute("INSERT INTO action_tokens VALUES('token','u','reset',?,?)",(time.time()+1000,time.time()))
 return path

def test_backup_restore_rehearsal_preserves_data_revokes_auth(database,tmp_path):
 snapshot=tmp_path/'backup.sqlite';meta=backup(database,snapshot)
 assert meta['tables']['journal']==1 and snapshot.stat().st_mode&0o777==0o600
 restored=tmp_path/'restored.sqlite';restore(snapshot,restored)
 with sqlite3.connect(restored) as db:
  assert db.execute('SELECT text FROM journal').fetchone()[0]=='keep me'
  assert db.execute('SELECT count(*) FROM sessions').fetchone()[0]==0
  assert db.execute('SELECT count(*) FROM action_tokens').fetchone()[0]==0
 with sqlite3.connect(database) as db:assert db.execute('SELECT count(*) FROM sessions').fetchone()[0]==2

def test_cannot_overwrite(database,tmp_path):
 snapshot=tmp_path/'backup.sqlite';backup(database,snapshot)
 with pytest.raises(ValueError):backup(database,snapshot)
 with pytest.raises(ValueError):restore(snapshot,database)

def test_tampered_backup_rejected(database,tmp_path):
 snapshot=tmp_path/'backup.sqlite';backup(database,snapshot)
 with snapshot.open('ab') as f:f.write(b'tamper')
 with pytest.raises(ValueError,match='checksum'):restore(snapshot,tmp_path/'restore.sqlite')

def test_cleanup_dry_run_and_apply(database):
 assert cleanup(database)['expired']['sessions']==1
 with sqlite3.connect(database) as db:assert db.execute('SELECT count(*) FROM sessions').fetchone()[0]==2
 assert cleanup(database,True)['applied'] is True
 with sqlite3.connect(database) as db:
  assert db.execute('SELECT count(*) FROM sessions').fetchone()[0]==1
  assert db.execute('SELECT text FROM journal').fetchone()[0]=='keep me'
