from app.input import sample
from app.modules.review.service import review


def archive_inspection(client, kind='dirty'):
    return client.post('/api/inspections', json=sample(kind)).json['inspection_id']


def test_review_api_idempotent_for_same_report(client):
    inspection_id = archive_inspection(client)
    report = sample('dirty')['report']
    first = client.post(f'/api/inspections/{inspection_id}/reviews', json={'report': report})
    second = client.post(f'/api/inspections/{inspection_id}/reviews', json={'report': report})
    assert first.status_code == 201 and second.status_code == 200
    assert first.json['created'] is True and second.json['created'] is False
    assert first.json['review_id'] == second.json['review_id']
    listing = client.get(f'/api/inspections/{inspection_id}/reviews').json['reviews']
    assert len(listing) == 1


def test_different_report_creates_distinct_review(client):
    inspection_id = archive_inspection(client)
    r1 = client.post(f'/api/inspections/{inspection_id}/reviews',
                     json={'report': 'joint,loss_db,verdict\nF-01,0.100,合格\n'}).json
    r2 = client.post(f'/api/inspections/{inspection_id}/reviews',
                     json={'report': 'joint,loss_db,verdict\nF-01,0.101,合格\n'}).json
    assert r1['review_id'] != r2['review_id']
    listing = client.get(f'/api/inspections/{inspection_id}/reviews').json['reviews']
    assert len(listing) == 2


def test_review_detail_fetch_and_404(client):
    inspection_id = archive_inspection(client)
    created = client.post(f'/api/inspections/{inspection_id}/reviews',
                          json={'report': sample('dirty')['report']}).json
    fetched = client.get('/api/reviews/' + created['review_id']).json
    assert fetched['review_id'] == created['review_id']
    assert client.get('/api/reviews/missing').status_code == 404


def test_review_requires_report_text(client):
    inspection_id = archive_inspection(client)
    response = client.post(f'/api/inspections/{inspection_id}/reviews', json={})
    assert response.status_code == 400 and response.json['code'] == 'REPORT_TEXT_REQUIRED'


def test_review_on_unknown_inspection_404(client):
    response = client.post('/api/inspections/missing/reviews',
                           json={'report': 'joint,loss_db,verdict\n'})
    assert response.status_code == 404 and response.json['code'] == 'INSPECTION_NOT_FOUND'


def test_clean_report_review_is_handover_ready(client):
    inspection_id = archive_inspection(client, 'clean')
    response = client.post(f'/api/inspections/{inspection_id}/reviews',
                           json={'report': sample('clean')['report']}).json
    assert response['review']['handover_ready'] is True


def test_service_retry_does_not_duplicate(tmp_path, dirty):
    db = tmp_path / 'db'
    from app.modules.archive.service import archive
    record, _ = archive(db, dirty)
    first, fresh_first = review(db, record['inspection_id'], dirty['report'])
    second, fresh_second = review(db, record['inspection_id'], dirty['report'])
    assert fresh_first is True and fresh_second is False
    assert first['review_id'] == second['review_id']
