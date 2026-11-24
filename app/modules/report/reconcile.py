"""外检报告 vs 现场双端复算的逐条对账。"""
from collections import Counter

from app.modules.report.reader import round3

# 现场复算结论 → 报告口径（合格 / 超限）；净增益无效按不可签认的不合格处理
FIELD_VERDICT = {'PASS': 'PASS', 'OVER_LIMIT': 'OVER_LIMIT', 'INVALID_NET_GAIN': 'OVER_LIMIT'}
FIELD_MISSING_CODES = {'SINGLE_SIDE_ONLY', 'NO_COUPLED_EVIDENCE', 'DESIGN_OUTSIDE_LINK'}
# 对账结论
CONSISTENT = 'CONSISTENT'              # 报告值=复算三位舍入且结论一致：差异仅舍入，采信
VALUE_MISMATCH = 'VALUE_MISMATCH'      # 舍入后损耗值仍对不上
VERDICT_CONFLICT = 'VERDICT_CONFLICT'  # 报告判合格、现场超限（或反之）：不能放行
EVIDENCE_MISSING = 'EVIDENCE_MISSING'  # 报告有、现场无双端证据：报告结论不可直接采信
REPORT_MISSING = 'REPORT_MISSING'      # 现场有结论、报告漏列
REPORT_ROW_INVALID = 'REPORT_ROW_INVALID'  # 报告该接头原行被隔离，无法对账
BLOCKING_CODES = (VALUE_MISMATCH, VERDICT_CONFLICT, EVIDENCE_MISSING, REPORT_MISSING, REPORT_ROW_INVALID)


def _field_views(design, loss_rows):
    """以设计接头为键生成现场复算视图。"""
    loss_by_pair = {row['pair']: row for row in loss_rows}
    views = {}
    for design_row in design['rows']:
        joint = design_row['joint']
        if design_row['code'] in FIELD_MISSING_CODES:
            views[joint] = {'available': False, 'code': design_row['code'],
                            'net_double_mdb': None, 'net_mdb': None, 'net_db': None, 'verdict': None}
            continue
        loss_row = loss_by_pair[design_row['pair']]
        double_mdb = loss_row['net_double_mdb']
        # net_double_mdb 为两倍毫 dB，先折成毫 dB 再按报告三位小数舍入
        net_mdb = round3(double_mdb / 2)
        views[joint] = {'available': True, 'code': design_row['code'],
                        'net_double_mdb': double_mdb, 'net_mdb': net_mdb,
                        'net_db': design_row['net_db'],
                        'verdict': FIELD_VERDICT[design_row['code']]}
    return views


def reconcile_report(report_bundle, design, loss_rows):
    report_rows = {row['id']: row for row in report_bundle['rows']}
    # 隔离行 raw 是原列值列表，首列为接头 ID
    invalid_ids = {item['raw'][0].strip() for item in report_bundle['isolated']
                   if isinstance(item['raw'], list) and item['raw']}
    field = _field_views(design, loss_rows)
    joints = sorted(set(field) | set(report_rows) | invalid_ids)

    rows = []
    for joint in joints:
        report = report_rows.get(joint)
        seen = field.get(joint)
        entry = {'joint': joint, 'report_line': report['line'] if report else None,
                 'report_loss_mdb': report['loss_mdb'] if report else None,
                 'report_verdict': report['verdict'] if report else None,
                 'field_available': bool(seen and seen['available']),
                 'field_code': seen['code'] if seen else None,
                 'field_net_db': seen['net_db'] if seen else None,
                 'field_net_mdb': seen['net_mdb'] if seen else None,
                 'reconcile_code': None, 'note': ''}
        if report is None and joint in invalid_ids:
            entry['reconcile_code'] = REPORT_ROW_INVALID
            entry['note'] = '报告该接头原行已隔离，无法对账'
        elif report is None:
            entry['reconcile_code'] = REPORT_MISSING
            entry['note'] = '现场有复算结论，报告漏列该接头'
        elif not seen or not seen['available']:
            entry['reconcile_code'] = EVIDENCE_MISSING
            entry['note'] = '报告列示但现场无双端耦合证据，报告结论不可直接采信，须补证后再判'
        elif report['loss_mdb'] == seen['net_mdb'] and report['verdict'] == seen['verdict']:
            entry['reconcile_code'] = CONSISTENT
            entry['note'] = '报告值与现场复算三位舍入一致，差异仅为小数舍入，报告结论采信'
        elif report['verdict'] != seen['verdict']:
            entry['reconcile_code'] = VERDICT_CONFLICT
            entry['note'] = '报告与现场复算合格性结论相反（如报告合格、现场超限），不得按报告放行'
        else:
            entry['reconcile_code'] = VALUE_MISMATCH
            entry['note'] = '三位舍入后损耗值仍不一致，报告数据不可采信'
        rows.append(entry)

    counts = Counter(row['reconcile_code'] for row in rows)
    totals = {code: counts.get(code, 0) for code in
              (CONSISTENT, VALUE_MISMATCH, VERDICT_CONFLICT, EVIDENCE_MISSING, REPORT_MISSING, REPORT_ROW_INVALID)}
    blockers = [code for code in BLOCKING_CODES if totals[code]]
    return {'report_meta': report_bundle['meta'], 'report_isolated': report_bundle['isolated'],
            'joint_count': len(rows), **totals, 'blockers': blockers,
            'handover_ready': not blockers, 'rows': rows}
