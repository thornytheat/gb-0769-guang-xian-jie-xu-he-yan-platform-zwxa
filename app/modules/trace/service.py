from collections import Counter, defaultdict

from app.config import MAX_ROWS, SOURCES
from app.errors import InspectionError
from app.reasons import cell
from .reader import read_rows
from .units import distance, scaled


def normalize(source, fields):
    row = {key: cell(value) for key, value in fields.items()}
    position = distance(row['distance'], row['unit'])
    if source == 'design':
        return {'id': row['joint'], 'mm': position, 'limit_mdb': scaled(row['limit_db'], 1000, 0, 10000)}
    return {'id': row['event'], 'mm': position, 'loss_mdb': scaled(row['loss_db'], 1000, -10000, 10000)}


def receive_source(source, text):
    grouped, issues, counts = defaultdict(list), [], Counter()

    def mark(line, raw, code):
        issues.append({'source': source, 'line': line, 'code': code, 'raw': raw})

    for line, raw, values, reason in read_rows(source, text):
        counts['input'] += 1
        if counts['input'] > MAX_ROWS:
            raise InspectionError('ROW_LIMIT', source)
        if reason in {'BLANK','REPEATED_HEADER'}:
            counts[reason] += 1
            continue
        if reason:
            mark(line, raw, reason)
            continue
        try:
            row = normalize(source, values)
            grouped[row['id']].append((row, line, raw))
        except ValueError as exc:
            mark(line, raw, str(exc))
    data = []
    for group in grouped.values():
        first, *others = group
        if any(other[0] != first[0] for other in others):
            for _, line, raw in group:
                mark(line, raw, 'CONFLICTING_EVENT')
            continue
        row, line, raw = first
        data.append({**row, 'line': line, 'raw': raw, 'source': source})
        for _, line, raw in others:
            mark(line, raw, 'DUPLICATE_EVENT')
    meta = {'input': counts['input'], 'blank': counts['BLANK'], 'sections': counts['REPEATED_HEADER'] + 1,
            'accepted': len(data), 'isolated': len(issues), 'state': 'PROCESSED' if data or issues else 'HEADER_ONLY'}
    meta['balanced'] = meta['input'] == meta['blank'] + meta['sections'] - 1 + meta['accepted'] + meta['isolated']
    return data, meta, sorted(issues, key=lambda row: row['line'])


def ingest(sources):
    result = {key: receive_source(key, sources[key]) for key in SOURCES}
    isolated = [row for _, _, issues in result.values() for row in issues]
    return {'traces': {key: value[0] for key,value in result.items()},
            'counts': {key: value[1] for key,value in result.items()}, 'isolated': isolated,
            'reason_counts': dict(Counter(row['code'] for row in isolated))}
