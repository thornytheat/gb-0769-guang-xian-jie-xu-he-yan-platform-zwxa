import pytest

from app.errors import InspectionError
from app.pipeline import run


def aligned(source):
    return run(source, 'calibration')['calibration']


def test_launch_zero_applies_to_a(dirty):
    assert aligned(dirty)['aligned']['a'][0]['chain_mm'] == 100000


def test_b_sign_and_order(dirty):
    r = aligned(dirty)['aligned']['b']
    assert (r[0]['id'], r[0]['chain_mm'], r[-1]['id'], r[-1]['chain_mm']) == ('B-01',97000,'B-06',900000)


def test_design_already_uses_a_coordinate(dirty):
    rows = aligned(dirty)['aligned']['design']
    assert [(r['id'], r['chain_mm']) for r in rows[:3]] == [('F-01',99000),('F-02',103000),('F-03',300000)]


def test_outside_span_keeps_signed_residual(dirty):
    row, = aligned(dirty)['outliers']
    assert (row['id'], row['code'], row['chain_mm'], row['line']) == ('A-X','OUTSIDE_LINK',-50000,12)


def test_zero_and_end_points_are_in_link(clean):
    clean['traces']['a'] += 'MIN,5,m,0.1\nMAX,505,m,0.1\n'
    rows = aligned(clean)['aligned']['a']
    assert (rows[0]['chain_mm'], rows[-1]['chain_mm']) == (0,500000)


def test_bad_link_rejects_before_pairing(dirty):
    dirty['settings']['length_m'] = 0
    with pytest.raises(InspectionError, match='BAD_LINK_RANGE'):
        aligned(dirty)
