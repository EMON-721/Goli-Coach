"""Offline operations. Run with python -m server.maintenance; never exposed over HTTP."""
import argparse,hashlib,json,os,sqlite3,tempfile,time
from datetime import datetime,timezone
from pathlib import Path

REQUIRED={'users','records','journal','sessions','content_revisions','audit'}
def connection(path):
 if not path.is_file():raise ValueError('Database does not exist')
 return sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
def inspect(path):
 with connection(path.resolve()) as db:
  if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite integrity check failed')
  if db.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Foreign key check failed')
  if not REQUIRED<={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}:raise ValueError('Not a Goli-Coach database')
  return {table:db.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in sorted(REQUIRED)}
def backup(source,destination):
 source=source.resolve();destination=destination.resolve()
 if source==destination or destination.exists() or destination.with_suffix(destination.suffix+'.json').exists():raise ValueError('Choose a new backup path')
 destination.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(prefix='.backup-',dir=destination.parent);os.close(fd);tmp=Path(tmp)
 try:
  with connection(source) as src,sqlite3.connect(tmp) as dst:src.backup(dst)
  counts=inspect(tmp);digest=hashlib.sha256(tmp.read_bytes()).hexdigest()
  # Link creates the destination only if it still does not exist.
  os.link(tmp,destination)
  meta={'created_at':datetime.now(timezone.utc).isoformat(),'sha256':digest,'tables':counts,'contains_private_data':True}
  manifest=destination.with_suffix(destination.suffix+'.json')
  with manifest.open('x') as f:json.dump(meta,f,indent=2)
  os.chmod(destination,0o600);os.chmod(manifest,0o600)
  return meta
 finally:tmp.unlink(missing_ok=True)
def restore(source,destination):
 source=source.resolve();destination=destination.resolve()
 if destination.exists():raise ValueError('Restore only to a new database; never overwrite a live database')
 manifest=json.loads(source.with_suffix(source.suffix+'.json').read_text())
 if hashlib.sha256(source.read_bytes()).hexdigest()!=manifest['sha256']:raise ValueError('Backup checksum mismatch')
 inspect(source);destination.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(prefix='.restore-',dir=destination.parent);os.close(fd);tmp=Path(tmp)
 try:
  with connection(source) as src,sqlite3.connect(tmp) as dst:
   src.backup(dst)
   # Restoring a backup must never resurrect revoked authentication tokens.
   dst.execute('DELETE FROM sessions')
   if dst.execute("SELECT 1 FROM sqlite_master WHERE name='action_tokens'").fetchone():dst.execute('DELETE FROM action_tokens')
   if dst.execute("SELECT 1 FROM sqlite_master WHERE name='report_shares'").fetchone():dst.execute('DELETE FROM report_shares')
   dst.commit()
  counts=inspect(tmp);os.link(tmp,destination);os.chmod(destination,0o600);return counts
 finally:tmp.unlink(missing_ok=True)
def cleanup(path,apply=False):
 with sqlite3.connect(path.resolve().as_uri()+'?mode=rw',uri=True) as db:
  db.execute('BEGIN IMMEDIATE')
  queries={'sessions':('expires<?',time.time()),'action_tokens':('expires<?',time.time())}
  if db.execute("SELECT 1 FROM sqlite_master WHERE name='report_shares'").fetchone():queries['report_shares']=('expires<?',time.time())
  counts={table:db.execute('SELECT count(*) FROM '+table+' WHERE '+where,(cutoff,)).fetchone()[0] for table,(where,cutoff) in queries.items()}
  if apply:
   for table,(where,cutoff) in queries.items():db.execute('DELETE FROM '+table+' WHERE '+where,(cutoff,))
   db.commit()
  else:db.rollback()
  return {'applied':apply,'expired':counts,'reports_and_journal_unchanged':True}
def main():
 parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='action',required=True)
 for action in ['backup','restore']:
  p=sub.add_parser(action);p.add_argument('source',type=Path);p.add_argument('destination',type=Path)
 p=sub.add_parser('cleanup');p.add_argument('database',type=Path);p.add_argument('--apply',action='store_true')
 args=parser.parse_args()
 result=cleanup(args.database,args.apply) if args.action=='cleanup' else globals()[args.action](args.source,args.destination)
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
