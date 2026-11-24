import hashlib
import json
from datetime import datetime, timezone
from time import perf_counter

from app.config import SPEC


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def record(material, computed, started):
    sources = {key: digest(value.encode()) for key, value in material['traces'].items()}
    settings = computed['calibration']['settings']
    report_sha = digest(material['report'].encode()) if material.get('report') else None
    identifier = digest(canonical([SPEC, sources, settings, report_sha]))
    return {'inspection_id': identifier, 'rule': SPEC, 'traces_sha256': sources,
            'report_sha256': report_sha, 'settings': settings,
            'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'duration_ms': round(1000 * (perf_counter() - started)), 'computed': computed}
