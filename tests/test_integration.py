def test_archive_and_export_keep_isolation_and_net_loss(client):
    r = client.post('/api/inspections',json={'sample':'dirty'}).json
    pack = client.get('/api/export/'+r['inspection_id']).json
    assert pack['record']['computed']['trace']['reason_counts']['CONFLICTING_EVENT'] == 2
    assert pack['record']['computed']['loss']['rows'][0]['net_db'] == '0.1000'
    assert pack['record']['computed']['design']['design_count'] == 6
