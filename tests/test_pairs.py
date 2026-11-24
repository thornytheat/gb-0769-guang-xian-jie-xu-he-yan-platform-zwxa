from app.modules.pairs.optimal import best_pairs
from app.pipeline import run


def paired(data):
    return run(data, 'pairs')['pairs']


def test_global_pairing_beats_greedy_and_keeps_competition(dirty):  # TRAP-19
    r = paired(dirty)
    first, second = r['pairs'][:2]
    assert (first['b']['id'], second['b']['id'], first['possible_b'], r['pair_count']) == ('B-01','B-02',['B-01','B-02'],5)


def test_tolerance_inclusive(dirty):
    assert paired(dirty)['pairs'][1]['span_mm'] == 4000
    dirty['settings']['pair_tol_m'] = '3.999'
    assert paired(dirty)['pair_count'] == 4


def test_opposite_ends_missing_in_both_directions(dirty):  # TRAP-21
    r = paired(dirty)
    assert [(s['id'],s['code']) for s in r['singles']] == [('A-05','NO_B_NEARBY'),('B-05','NO_A_NEARBY')]
    assert r['balanced'] is True


def test_exact_tie_deterministic_under_shuffled_input(dirty):
    dirty['traces']['b'] += 'B-000,943,m,0.29\n'
    before = paired(dirty)
    header, *rows = dirty['traces']['b'].splitlines()
    dirty['traces']['b'] = '\n'.join([header,*reversed(rows)])
    after = paired(dirty)
    assert before['pairs'][0]['b']['id'] == after['pairs'][0]['b']['id'] == 'B-000'
    assert next(r for r in after['singles'] if r['id']=='B-01')['code'] == 'PAIR_COMPETITION'


def test_total_distance_resolves_equal_cardinality():
    assert best_pairs([100],[96,101],5) == [(0,1)]


def test_one_empty_direction_keeps_every_single(clean):
    clean['traces']['b'] = clean['traces']['b'].splitlines()[0] + '\n'
    r = paired(clean)
    assert (r['pair_count'],r['single_count'],r['balanced']) == (0,3,True)
