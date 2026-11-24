from concurrent.futures import ThreadPoolExecutor

from app.main import create_app
from app.modules.archive.service import archive


def test_same_archive_request_is_idempotent(client):
    first = client.post('/api/inspections',json={'sample':'dirty'})
    later = client.post('/api/inspections',json={'sample':'dirty'})
    assert (first.status_code,later.status_code,later.json['created']) == (201,200,False)
    assert first.json['record'] == later.json['record']
    assert len(client.get('/api/inspections').json['inspections']) == 1


def test_failed_archive_keeps_store_empty(client):
    r = client.post('/api/inspections',json={'sample':'dirty','settings':{}})
    assert (r.status_code,r.json['code']) == (422,'SETTING_FIELDS')
    assert client.get('/api/inspections').json['inspections'] == []


def test_competing_workers_publish_once(tmp_path,dirty):
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda _: archive(tmp_path/'db',dirty),range(10)))
    assert sum(fresh for _,fresh in results) == 1
    assert len({r['inspection_id'] for r,_ in results}) == 1


def test_app_reopen_uses_persisted_snapshot(tmp_path,dirty):
    db = tmp_path/'db'
    r = create_app(db).test_client().post('/api/inspections',json=dirty).json
    restored = create_app(db).test_client().get('/api/inspections/'+r['inspection_id'])
    assert restored.json == r['record']


def test_calibration_changes_identity(client,dirty):
    first = client.post('/api/inspections',json=dirty).json['inspection_id']
    dirty['settings']['zero_a_m'] = 101
    second = client.post('/api/inspections',json=dirty).json['inspection_id']
    assert first != second


def test_unknown_inspection_returns_404(client):
    r = client.get('/api/inspections/unknown')
    assert (r.status_code,r.json['code']) == (404,'INSPECTION_NOT_FOUND')
