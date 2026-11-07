import pytest
from server import storage

def test_hosted_configuration_refuses_temporary_database(monkeypatch,tmp_path):
    monkeypatch.delenv('DATABASE_URL',raising=False);monkeypatch.setenv('REQUIRE_REMOTE_DATABASE','1')
    with pytest.raises(RuntimeError):storage.connect(tmp_path/'temporary.sqlite')
    assert not (tmp_path/'temporary.sqlite').exists()

def test_row_preserves_named_and_positional_access():
    row=storage.Row({'id':'123','role':'user'})
    assert row[0]==row['id']=='123' and row[1]=='user' and dict(row)=={'id':'123','role':'user'}

def test_sqlite_migration_remains_compatible(monkeypatch,tmp_path):
    from pathlib import Path
    monkeypatch.delenv('DATABASE_URL',raising=False);monkeypatch.delenv('REQUIRE_REMOTE_DATABASE',raising=False)
    path=tmp_path/'local.sqlite'
    storage.migrate(Path(__file__).resolve().parents[1],lambda:storage.connect(path))
    with storage.connect(path) as conn:
        assert 'verified' in {r[1] for r in conn.execute('PRAGMA table_info(users)')}
