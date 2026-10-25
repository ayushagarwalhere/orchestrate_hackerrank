"""General regressions for the local baseline; no case-ID rules."""
from pathlib import Path
import sys,csv,json
from types import SimpleNamespace
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from identity import IdentityResolver,IdentityError,parse_ts,norm_phone,sha256_email
from evidence.index import EvidenceIndex
from evidence.model import Observation,Coverage,Category,State
from evidence.activity import Activity
from evidence.images import _record_observation
from evidence import images
from evidence.common import EvidenceFile
from validate_output import validate

T0=parse_ts('2026-01-01T00:00:00Z')
T1=parse_ts('2026-01-02T00:00:00Z')
T2=parse_ts('2026-01-03T00:00:00Z')


def resolver(snapshot,updated):
    current=[dict(user_id='user_x',name='Test',email=snapshot,phone='+1 555 555 9000',
                  email_hash=sha256_email(snapshot),updated_at=updated)]
    events=[dict(audit_id='a1',user_id='user_x',field_name='email',old_value='a@example.test',new_value='b@example.test',event_time=T1.isoformat()),
            dict(audit_id='a2',user_id='user_x',field_name='email',old_value='b@example.test',new_value='c@example.test',event_time=T2.isoformat())]
    return IdentityResolver(current,events)


def test_future_intermediate_email_is_not_an_earlier_identifier():
    r=resolver('c@example.test',T2.isoformat())
    assert r.resolve('a@example.test',T0).emails=={'a@example.test'}
    for future in ['b@example.test','c@example.test']:
        with pytest.raises(IdentityError):r.resolve(future,T0)


def test_future_changes_do_not_override_an_eligible_snapshot():
    r=resolver('a@example.test',T0.isoformat())
    assert r.resolve('a@example.test',T0).emails=={'a@example.test'}


def index(observations=(),activities=()):
    scope=Coverage('scope',T0,T0,'account_service',frozenset(),'topology_table')
    return EvidenceIndex(list(observations),[scope],[],list(activities),[])


def test_already_absent_account_gets_evidence_before_request():
    o=index().state_at('account_1',T2,T1)
    assert o.state==State.ABSENT and o.evidence_id=='scope'


def test_creating_claim_invalidates_older_absence():
    claim=Activity('changed',T1,'SYNC_RECORD','worker','account_service','account_1','SUCCESS','claimed sync')
    assert index(activities=[claim]).state_at('account_1',T2,T2) is None


def test_newer_presence_prevents_using_an_older_absence():
    present=Observation('read',T1,T1,'account_service','account_1',Category.USER_PROFILE,State.PRESENT)
    assert index([present]).state_at('account_1',T2,T2) is None


def test_post_capture_observation_never_becomes_eligible_later():
    o=Observation('future',T0,T1,'account_service','account_1',Category.USER_PROFILE,State.PRESENT)
    assert not o.usable(T2)


def test_image_time_is_preserved_instead_of_clamped_to_capture():
    source=SimpleNamespace(file_id='image',captured_at=T0,path=Path('image.png'))
    o=_record_observation(source,dict(resource_id='account_1',category='USER_PROFILE',state='PRESENT',observed_at=T1.isoformat()))
    assert o.observed_at==T1 and not o.usable(T2)


def test_international_phone_codes_preserved_and_placeholders_rejected():
    assert norm_phone('+212 (6) 48-27-15-93')=='212648271593'
    assert norm_phone('212648271593')=='212648271593'
    assert norm_phone('123')==norm_phone('null')==''


def test_validator_rejects_uncited_complete(tmp_path):
    tables={
      'deletion_requests.csv':[['case_id','audit_at'],['case_1',T2.isoformat()]],
      'evidence_files.csv':[['file_id','captured_at']],
      'system_activity.csv':[['activity_id','event_time']],
      'user_audit_log.csv':[['audit_id','event_time']]}
    for name,records in tables.items():
        with (tmp_path/name).open('w',encoding='utf-8',newline='') as f:csv.writer(f).writerows(records)
    step=dict(step_no=1,phase='VERIFICATION',system_id='account_service',resource_id='account_1',operation='VERIFY_RECORD_ABSENT',state='ABSENT',evidence_id='')
    with (tmp_path/'output.csv').open('w',encoding='utf-8',newline='') as f:
        csv.writer(f).writerows([['case_id','deletion_status','steps_json'],['case_1','COMPLETE',json.dumps([step])]])
    errors,n=validate(tmp_path/'output.csv',tmp_path)
    assert n==1 and any('COMPLETE verification has no evidence' in e for e in errors)


def test_changed_image_cannot_reuse_stale_cached_facts(tmp_path):
    folder=tmp_path/'images';folder.mkdir();source=folder/'source.png';source.write_bytes(b'changed image')
    facts=tmp_path/'facts';facts.mkdir()
    (facts/'image.json').write_text(json.dumps(dict(source_sha256='0'*64,records=[])),encoding='utf-8')
    with pytest.raises(ValueError,match='SHA-256'):
        images.load([EvidenceFile('image',source,'test',T0)],facts)
