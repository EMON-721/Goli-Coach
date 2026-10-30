"""Download the version-pinned Apache-2.0 checkpoint; verify before replacing."""
import hashlib,json,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1];m=json.loads((root/'models/manifest.json').read_text())
data=urllib.request.urlopen(m['source'],timeout=90).read()
if hashlib.sha256(data).hexdigest()!=m['sha256']:raise SystemExit('Checksum mismatch: not installed')
p=root/'public/models/pose_landmarker_lite.task';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
print('Model installed and checksum verified.')
