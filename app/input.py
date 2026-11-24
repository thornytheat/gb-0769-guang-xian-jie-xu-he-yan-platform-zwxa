import json
from flask import request

from .config import DATA, SOURCES
from .errors import InspectionError


def sample(kind):
    if kind not in ('clean','dirty'):
        raise InspectionError('UNKNOWN_TRACE_SET', status=404)
    folder = DATA / kind
    return {'traces': {key:(folder / f'{key}.csv').read_text(encoding='utf-8') for key in SOURCES},
            'settings':json.loads((folder / 'link.json').read_text(encoding='utf-8'))}


def request_material():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise InspectionError('JSON_OBJECT_REQUIRED', status=400)
    if set(body) <= {'sample','settings'} and 'sample' in body:
        data = sample(body['sample'])
        return {**data, 'settings':body.get('settings', data['settings'])}
    data = body.get('traces')
    if set(body)-{'traces','settings'} or not isinstance(data,dict) or set(data)!=set(SOURCES):
        raise InspectionError('THREE_TRACES_REQUIRED', status=400)
    if any(not isinstance(text,str) for text in data.values()):
        raise InspectionError('TRACE_TEXT_REQUIRED', status=400)
    return body
