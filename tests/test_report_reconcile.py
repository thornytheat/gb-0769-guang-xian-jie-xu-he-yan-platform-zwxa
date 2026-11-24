from app.input import sample
from app.pipeline import run
from app.errors import InspectionError
import pytest


def reconcile(material, report):
    material = {**material, 'report': report}
    return run(material)['report_reconcile']


def by_joint(result):
    return {row['joint']: row for row in result['rows']}


def test_dirty_sample_spans_all_blocking_categories():
    result = reconcile(sample('dirty'), sample('dirty')['report'])
    assert (result['CONSISTENT'], result['VALUE_MISMATCH'], result['VERDICT_CONFLICT'],
            result['EVIDENCE_MISSING'], result['REPORT_ROW_INVALID']) == (2, 1, 1, 2, 1)
    assert result['handover_ready'] is False
    assert set(result['blockers']) == {'VALUE_MISMATCH', 'VERDICT_CONFLICT',
                                       'EVIDENCE_MISSING', 'REPORT_ROW_INVALID'}


def test_rounding_only_difference_is_accepted_not_fraud():
    """现场 0.1805 dB，报告保留三位写 0.181：仅舍入差异，应当采信。"""
    material = sample('dirty')
    material['traces']['a'] = material['traces']['a'].replace('A-02,205,m,0.160', 'A-02,205,m,0.161')
    material['traces']['a'] = material['traces']['a'].replace('A-02,0.205,km,0.16', 'A-02,0.205,km,0.161')
    report = 'joint,loss_db,verdict\nF-02,0.181,合格\n'
    row = by_joint(reconcile(material, report))['F-02']
    assert row['reconcile_code'] == 'CONSISTENT'
    assert row['field_net_db'] == '0.1805' and row['field_net_mdb'] == 181


def test_report_pass_but_field_over_limit_blocks_release():
    report = 'joint,loss_db,verdict\nF-03,0.320,合格\n'
    row = by_joint(reconcile(sample('dirty'), report))['F-03']
    assert row['reconcile_code'] == 'VERDICT_CONFLICT'
    assert row['report_verdict'] == 'PASS' and row['field_code'] == 'OVER_LIMIT'


def test_missing_field_evidence_cannot_trust_report_conclusion():
    report = 'joint,loss_db,verdict\nF-05,0.070,合格\nF-06,0.120,合格\n'
    rows = by_joint(reconcile(sample('dirty'), report))
    assert rows['F-05']['reconcile_code'] == 'EVIDENCE_MISSING'
    assert rows['F-06']['reconcile_code'] == 'EVIDENCE_MISSING'
    assert all('不可直接采信' in row['note'] for row in (rows['F-05'], rows['F-06']))


def test_value_mismatch_after_rounding_is_flagged():
    report = 'joint,loss_db,verdict\nF-04,0.198,合格\n'
    row = by_joint(reconcile(sample('dirty'), report))['F-04']
    assert row['reconcile_code'] == 'VALUE_MISMATCH'
    assert row['report_loss_mdb'] == 198 and row['field_net_mdb'] == 200


def test_joint_measured_but_omitted_from_report_is_report_missing():
    report = 'joint,loss_db,verdict\nF-01,0.100,合格\n'
    rows = by_joint(reconcile(sample('dirty'), report))
    assert rows['F-04']['reconcile_code'] == 'REPORT_MISSING'


def test_clean_sample_report_is_handover_ready():
    clean = sample('clean')
    result = reconcile(clean, clean['report'])
    assert result['handover_ready'] is True and result['blockers'] == []
    assert result['CONSISTENT'] == 3


def test_report_claiming_over_limit_when_field_passes_is_conflict():
    report = 'joint,loss_db,verdict\nF-01,0.100,超限\n'
    row = by_joint(reconcile(sample('dirty'), report))['F-01']
    assert row['reconcile_code'] == 'VERDICT_CONFLICT'


def test_invalid_net_gain_treated_as_non_passing():
    material = sample('dirty')
    material['traces']['a'] = material['traces']['a'].replace('0.200,km,-0.100', '0.200,km,-0.400')
    report = 'joint,loss_db,verdict\nF-01,-0.045,合格\n'
    row = by_joint(reconcile(material, report))['F-01']
    assert row['reconcile_code'] == 'VERDICT_CONFLICT'


def test_report_joint_without_any_field_evidence_is_missing():
    report = 'joint,loss_db,verdict\nF-99,0.100,合格\n'
    row = by_joint(reconcile(sample('dirty'), report))['F-99']
    assert row['reconcile_code'] == 'EVIDENCE_MISSING' and row['field_code'] is None


def test_malformed_report_raises_named_error():
    material = sample('dirty')
    material['report'] = 'wrong,header\nx,y\n'
    with pytest.raises(InspectionError) as exc:
        run(material)
    assert exc.value.code == 'BAD_REPORT_HEADER'


def test_empty_report_raises_named_error():
    material = sample('dirty')
    material['report'] = ''
    with pytest.raises(InspectionError) as exc:
        run(material)
    assert exc.value.code == 'EMPTY_REPORT'


def test_pipeline_without_report_has_no_reconcile_stage():
    material = {k: v for k, v in sample('clean').items() if k != 'report'}
    assert 'report_reconcile' not in run(material)
