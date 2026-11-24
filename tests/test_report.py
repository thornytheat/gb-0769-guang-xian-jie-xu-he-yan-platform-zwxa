import pytest

from app.modules.report.reader import parse_loss, round3
from app.modules.report.service import receive_report


def test_report_keeps_three_decimals_as_milli_db():
    assert parse_loss('0.180') == 180
    assert parse_loss('0.181') == 181
    assert parse_loss('-0.050') == -50


def test_report_four_decimals_is_isolated():
    with pytest.raises(ValueError):
        parse_loss('0.1234')


def test_field_value_rounds_half_up_to_report_precision():
    # 现场 0.1805 dB（361 两倍毫 dB → 180.5 毫 dB）半进到 0.181
    assert round3(180.5) == 181
    assert round3(180.4) == 180
    assert round3(200) == 200


def test_report_bom_and_repeated_header():
    text = '﻿joint,loss_db,verdict\nF-1,0.100,合格\njoint,loss_db,verdict\nF-2,0.200,超限\n'
    bundle = receive_report(text)
    assert [r['id'] for r in bundle['rows']] == ['F-1', 'F-2']
    assert bundle['meta']['sections'] == 2 and bundle['meta']['balanced']


def test_bad_precision_and_verdict_are_isolated():
    text = ('joint,loss_db,verdict\n'
            'F-1,0.1234,合格\n'
            'F-2,0.100,未知\n'
            'F-3,0.200,合格\n')
    bundle = receive_report(text)
    codes = {row['code'] for row in bundle['isolated']}
    assert codes == {'REPORT_PRECISION_OVER_3', 'BAD_REPORT_VERDICT'}
    assert [r['id'] for r in bundle['rows']] == ['F-3']


def test_conflicting_report_joint_withdraws_whole_group():
    text = ('joint,loss_db,verdict\n'
            'F-1,0.100,合格\n'
            'F-1,0.110,合格\n')
    bundle = receive_report(text)
    assert bundle['rows'] == []
    assert {row['code'] for row in bundle['isolated']} == {'CONFLICTING_REPORT_JOINT'}


def test_duplicate_report_joint_keeps_first():
    text = ('joint,loss_db,verdict\n'
            'F-1,0.100,合格\n'
            'F-1,0.100,合格\n')
    bundle = receive_report(text)
    assert len(bundle['rows']) == 1
    assert {row['code'] for row in bundle['isolated']} == {'DUPLICATE_REPORT_JOINT'}


def test_english_and_chinese_verdict_tokens():
    text = 'joint,loss_db,verdict\nF-1,0.1,合格\nF-2,0.3,OVER_LIMIT\nF-3,0.3,不合格\n'
    bundle = receive_report(text)
    assert [r['verdict'] for r in bundle['rows']] == ['PASS', 'OVER_LIMIT', 'OVER_LIMIT']
