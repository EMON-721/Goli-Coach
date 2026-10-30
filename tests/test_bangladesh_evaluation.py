import hashlib
from types import SimpleNamespace
import pytest
from scripts.evaluate_bangladesh import validate_manifest,score_frame

def test_missing_consent_rejected(tmp_path):
 with pytest.raises(ValueError):validate_manifest({'country':'BD','frames':[]},tmp_path)
def test_no_data_is_not_evaluated(tmp_path):
 with pytest.raises(ValueError,match='NOT EVALUATED'):validate_manifest({'country':'BD','purpose':'evaluation','consent_confirmed':True,'rights_evidence':'Written rights evidence reference','frames':[]},tmp_path)
def test_misses_remain_in_denominator():
 score=score_frame({'11':[.5,.5]},[],640,360);assert score['labelled_joints']==1 and score['hits']==0
def test_exact_annotation_hit():
 points=[SimpleNamespace(x=.5,y=.5,visibility=1)]*33
 assert score_frame({'11':[.5,.5]},points,640,360)['hits']==1
def test_checksum_required(tmp_path):
 (tmp_path/'frame.jpg').write_bytes(b'test fixture only')
 data={'country':'BD','purpose':'evaluation','consent_confirmed':True,'rights_evidence':'Written rights evidence reference','frames':[{'player_id':'anon-1','discipline':'batting','image':'frame.jpg','sha256':'wrong','points':{'11':[.5,.5]}}]}
 with pytest.raises(ValueError,match='checksum'):validate_manifest(data,tmp_path)
 data['frames'][0]['sha256']=hashlib.sha256(b'test fixture only').hexdigest();assert len(validate_manifest(data,tmp_path))==1
