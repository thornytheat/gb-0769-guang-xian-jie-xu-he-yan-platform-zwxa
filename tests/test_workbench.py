from app.views import LABELS


def test_all_panes_render(client):
    home = client.get('/')
    assert '接头设计勾稽'.encode() in home.data and b'F-05' in home.data
    for path,label in LABELS.items():
        entry = client.get('/inspect/'+path)
        assert entry.status_code == 200 and label.encode() in entry.data


def test_loss_pane_includes_keyboard_targets_and_gain(client):
    response = client.get('/inspect/loss')
    assert b'id="event-next"' in response.data and b'data-event="P001"' in response.data
    assert 'A 端假增益'.encode() in response.data
