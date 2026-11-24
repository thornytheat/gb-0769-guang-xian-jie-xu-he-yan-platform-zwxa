from app.modules.archive.identity import canonical, digest

REPORT_BLOCKERS = {
    'VALUE_MISMATCH': 'REPORT_VALUE_MISMATCH',
    'VERDICT_CONFLICT': 'REPORT_VERDICT_CONFLICT',
    'EVIDENCE_MISSING': 'REPORT_EVIDENCE_MISSING',
    'REPORT_MISSING': 'REPORT_JOINT_MISSING',
    'REPORT_ROW_INVALID': 'REPORT_ROW_INVALID',
}


def certify(record):
    stages = record['computed']
    design = stages['design']
    blockers = []
    if design['missing']:
        blockers.append('MISSING_JOINTS')
    if design['over_limit']:
        blockers.append('LOSS_OVER_LIMIT')
    if not design['design_count']:
        blockers.append('EMPTY_DESIGN')
    if any(line['source'] == 'design' and line['code'] != 'DUPLICATE_EVENT' for line in stages['trace']['isolated']):
        blockers.append('UNVERIFIED_DESIGN_ROWS')
    review = stages.get('report_reconcile')
    if review is not None:
        for code in review['blockers']:
            blockers.append(REPORT_BLOCKERS[code])
    return {'inspection_id': record['inspection_id'], 'approved': not blockers,
            'blockers': blockers, 'integrity_sha256': digest(canonical(record)), 'record': record}
