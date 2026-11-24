import json
from flask import request

from app.config import DATA, REPORT_KEY, SOURCES
from app.errors import InspectionError


def sample(kind):
    if kind not in ('clean', 'dirty'):
        raise InspectionError('UNKNOWN_TRACE_SET', status=404)
    folder = DATA / kind
    material = {'traces': {key: (folder / f'{key}.csv').read_text(encoding='utf-8') for key in SOURCES},
                'settings': json.loads((folder / 'link.json').read_text(encoding='utf-8'))}
    report_file = folder / 'report.csv'
    if report_file.exists():
        material[REPORT_KEY] = report_file.read_text(encoding='utf-8')
    return material


def request_material():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise InspectionError('JSON_OBJECT_REQUIRED', status=400)
    if set(body) <= {'sample', 'settings'} and 'sample' in body:
        data = sample(body['sample'])
        return {**data, 'settings': body.get('settings', data['settings'])}
    data = body.get('traces')
    allowed = {'traces', 'settings', REPORT_KEY}
    if set(body) - allowed or not isinstance(data, dict) or set(data) != set(SOURCES):
        raise InspectionError('THREE_TRACES_REQUIRED', status=400)
    if any(not isinstance(text, str) for text in data.values()):
        raise InspectionError('TRACE_TEXT_REQUIRED', status=400)
    if REPORT_KEY in body and not isinstance(body[REPORT_KEY], str):
        raise InspectionError('REPORT_TEXT_REQUIRED', status=400)
    return body
