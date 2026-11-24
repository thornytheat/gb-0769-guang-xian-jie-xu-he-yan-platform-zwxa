from app.pipeline import run


def losses(dirty):
    return run(dirty, 'loss')['loss']


def test_fake_gain_is_meaned_before_verdict(dirty):
    r = losses(dirty)['rows'][0]
    assert (r['a']['loss_mdb'],r['b']['loss_mdb'],r['net_db'],r['gain_ends'],r['code']) == (-100,300,'0.1000',['A'],'PASS')


def test_double_mdb_preserves_half_increment(dirty):  # TRAP-10
    dirty['traces']['b'] = dirty['traces']['b'].replace('538,m,0.23','538,m,0.231')
    r = losses(dirty)['rows'][3]
    assert (r['net_db'],r['net_double_mdb'],r['code']) == ('0.2005',401,'OVER_LIMIT')


def test_limit_equality_passes(dirty):
    r = losses(dirty)['rows'][3]
    assert r['net_db'] == '0.2000' and r['code'] == 'PASS'


def test_negative_combined_loss_invalid(dirty):
    dirty['traces']['b'] = dirty['traces']['b'].replace('943,m,0.30','943,m,0.01')
    r = losses(dirty)['rows'][0]
    assert (r['net_db'],r['code']) == ('-0.0450','INVALID_NET_GAIN')


def test_over_limit_directional_average(dirty):
    r = losses(dirty)
    assert r['over_count'] == 1 and r['rows'][2]['net_db'] == '0.3200'


def test_clean_no_false_gain(clean):
    r = losses(clean)
    assert (r['false_gain_count'],r['over_count'],r['invalid_count']) == (0,0,0)
