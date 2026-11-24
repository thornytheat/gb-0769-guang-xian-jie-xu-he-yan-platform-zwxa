from app.pipeline import run


def table(data):
    return run(data)['design']


def test_design_and_measured_balances(dirty):
    r = table(dirty)
    assert (r['design_count'],r['passed'],r['over_limit'],r['missing'],r['balanced']) == (6,3,1,2,True)
    assert (r['orphan_pairs'],r['single_count'],r['measurements'],r['measurements_balanced']) == (1,2,12,True)


def test_one_side_and_no_readings_distinguished(dirty):
    r = table(dirty)['rows']
    assert (r[4]['code'],r[4]['near_singles']) == ('SINGLE_SIDE_ONLY',[{'id':'A-05','source':'a','line':2}])
    assert (r[5]['code'],r[5]['near_singles']) == ('NO_COUPLED_EVIDENCE',[])


def test_individual_design_limit_overrides_reference(dirty):
    dirty['traces']['design'] = dirty['traces']['design'].replace('F-03,0.300,km,0.2','F-03,0.300,km,0.32')
    r = table(dirty)
    assert r['passed'] == 4 and r['over_limit'] == 0


def test_out_of_bounds_design_stays_in_missing_total(dirty):
    dirty['traces']['design'] += 'F-90,1001,m,0.2\n'
    r = table(dirty)
    assert r['missing'] == 3 and r['rows'][-1]['code'] == 'DESIGN_OUTSIDE_LINK'


def test_orphan_has_two_original_evidence_rows(dirty):
    row, = table(dirty)['orphans']
    assert (row['pair'], row['a']['line'], row['b']['line']) == ('P005',8,2)


def test_net_gain_is_not_a_confirmed_joint(dirty):
    dirty['traces']['a'] = dirty['traces']['a'].replace('0.200,km,-0.100','0.200,km,-0.400')
    r = table(dirty)
    assert r['rows'][0]['code'] == 'INVALID_NET_GAIN' and r['missing'] == 3


def test_pair_cannot_cover_two_design_joints(clean):
    clean['traces']['design'] += 'C-X,101,m,0.2\n'
    r = table(clean)
    assert r['passed'] == 3 and r['missing'] == 1 and r['rows'][1]['pair'] is None
