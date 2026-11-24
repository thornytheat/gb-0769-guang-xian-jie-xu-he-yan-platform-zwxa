import hashlib
import json

from app.input import sample


def package(client, data):
    run = client.post('/api/inspections', json=data).json['inspection_id']
    return client.get('/api/certificate/' + run).json


def material_without_report(kind):
    data = sample(kind)
    data.pop('report', None)
    return data


def test_dirty_blocks_approval(client):
    r = package(client, material_without_report('dirty'))
    assert r['approved'] is False and r['blockers'] == ['MISSING_JOINTS', 'LOSS_OVER_LIMIT']


def test_clean_is_approved(client):
    r = package(client, material_without_report('clean'))
    assert r['approved'] is True and r['blockers'] == []


def test_empty_design_fails_approval(client, clean):
    clean['traces']['design'] = clean['traces']['design'].splitlines()[0]
    clean.pop('report', None)
    assert package(client, clean)['blockers'] == ['EMPTY_DESIGN']


def test_quarantined_design_blocks_approval(client, clean):
    clean['traces']['design'] += 'C-4,250,m,\n'
    clean.pop('report', None)
    assert package(client, clean)['blockers'] == ['UNVERIFIED_DESIGN_ROWS']


def test_report_blockers_hold_up_certificate(client):
    r = package(client, {'sample': 'dirty'})
    assert r['approved'] is False
    assert 'REPORT_VERDICT_CONFLICT' in r['blockers']
    assert 'REPORT_EVIDENCE_MISSING' in r['blockers']
    assert 'REPORT_VALUE_MISMATCH' in r['blockers']
    assert 'REPORT_ROW_INVALID' in r['blockers']


def test_clean_report_keeps_approval(client):
    r = package(client, {'sample': 'clean'})
    assert r['approved'] is True and r['blockers'] == []


def test_download_verifies_checksum(client):
    r = package(client, material_without_report('dirty'))
    export = client.get('/api/export/' + r['inspection_id'])
    assert export.json == r and export.headers['Content-Disposition'].startswith('attachment;')
    raw = json.dumps(r['record'], sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    assert hashlib.sha256(raw).hexdigest() == r['integrity_sha256']


def test_unknown_export_has_no_attachment(client):
    r = client.get('/api/export/missing')
    assert r.status_code == 404 and 'Content-Disposition' not in r.headers
