"""外检报告复核：对已留档链路核验与外检报告做逐条对账并留档。

复核身份由链路核验编号与报告内容 SHA-256 共同决定，
同一份报告重复提交命中同一 review_id，不新增复核项。
"""
from app.modules.archive.identity import canonical, digest
from app.modules.archive.storage import get
from app.modules.report.reconcile import reconcile_report
from app.modules.report.service import receive_report
from .storage import publish


def build_review(record, report_text):
    bundle = receive_report(report_text)
    computed = record['computed']
    result = reconcile_report(bundle, computed['design'], computed['loss']['rows'])
    return bundle, result


def review(database, inspection_id, report_text):
    record = get(database, inspection_id)
    bundle, result = build_review(record, report_text)
    report_sha = digest(report_text.encode())
    review_id = digest(canonical(['review-1.0', inspection_id, report_sha]))
    document = {'review_id': review_id, 'inspection_id': inspection_id, 'report_sha256': report_sha,
                'handover_ready': result['handover_ready'], 'blockers': result['blockers'],
                'reconciliation': result, 'report_meta': bundle['meta']}
    stored, fresh = publish(database, inspection_id, report_sha, review_id, document)
    return stored, fresh
