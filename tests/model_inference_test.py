"""Check model integrity. Input-dependent endpoint smoke: scripts/evaluate_model.py."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_checkpoint_sha256():
 manifest=json.loads((ROOT/'models/manifest.json').read_text())
 assert hashlib.sha256((ROOT/'public/models/pose_landmarker_lite.task').read_bytes()).hexdigest()==manifest['sha256']
