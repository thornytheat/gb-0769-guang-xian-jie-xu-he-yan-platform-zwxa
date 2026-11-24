from .verdict import display, verdict


def judge(joined, settings):
    maximum = settings['reference_limit_mdb']
    rows = []
    for pair in joined['pairs']:
        a, b = pair['a']['loss_mdb'], pair['b']['loss_mdb']
        net = a + b
        gain = [name for name, value in (('A',a),('B',b)) if value < 0]
        rows.append({**pair, 'net_double_mdb': net, 'net_db': display(net), 'gain_ends': gain,
                     'reference_limit_mdb': maximum, 'code': verdict(net, maximum)})
    return {'rows': rows, 'reference_limit_mdb': maximum, 'false_gain_count': sum(bool(r['gain_ends']) for r in rows),
            'invalid_count': sum(r['code'] == 'INVALID_NET_GAIN' for r in rows),
            'over_count': sum(r['code'] == 'OVER_LIMIT' for r in rows)}
