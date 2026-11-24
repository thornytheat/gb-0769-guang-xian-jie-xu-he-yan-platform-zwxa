def test_inputs_require_three_sources(client):
    response = client.post('/api/trace',json={'traces':{'a':''}})
    assert (response.status_code,response.json['code']) == (400,'THREE_TRACES_REQUIRED')


def test_ingest_does_not_need_calibration(client):
    assert client.post('/api/trace', json={'sample': 'dirty', 'settings': None}).json['counts']['a']['isolated'] == 5
    assert client.post('/api/calibration', json={'sample': 'dirty', 'settings': None}).status_code == 422


def test_report_must_be_text(client, clean):
    clean['report'] = 123
    response = client.post('/api/design', json=clean)
    assert (response.status_code, response.json['code']) == (400, 'REPORT_TEXT_REQUIRED')


def test_report_runs_through_design_stage(client):
    response = client.post('/api/design', json={'sample': 'clean'})
    assert response.status_code == 200
