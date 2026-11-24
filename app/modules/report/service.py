from collections import Counter, defaultdict

from .reader import VERDICT_TOKENS, parse_loss, read_rows


def receive_report(text):
    grouped, issues, counts = defaultdict(list), [], Counter()

    def mark(line, raw, code):
        issues.append({'source': 'report', 'line': line, 'code': code, 'raw': raw})

    for line, raw, values, reason in read_rows(text):
        counts['input'] += 1
        if reason in {'BLANK', 'REPEATED_HEADER'}:
            counts[reason] += 1
            continue
        if reason:
            mark(line, raw, reason)
            continue
        try:
            joint = values['joint'].strip()
            if not joint:
                raise ValueError('EMPTY_CELL')
            row = {'id': joint, 'loss_mdb': parse_loss(values['loss_db'].strip()),
                   'verdict': VERDICT_TOKENS[values['verdict'].strip()]}
        except KeyError:
            mark(line, raw, 'BAD_REPORT_VERDICT')
            continue
        except ValueError as exc:
            mark(line, raw, str(exc))
            continue
        grouped[row['id']].append((row, line, raw))

    rows = []
    for group in grouped.values():
        first, *others = group
        if any(other[0] != first[0] for other in others):
            for _, line, raw in group:
                mark(line, raw, 'CONFLICTING_REPORT_JOINT')
            continue
        row, line, raw = first
        rows.append({**row, 'line': line, 'raw': raw})
        for _, line, raw in others:
            mark(line, raw, 'DUPLICATE_REPORT_JOINT')

    meta = {'input': counts['input'], 'blank': counts['BLANK'],
            'sections': counts['REPEATED_HEADER'] + 1, 'accepted': len(rows), 'isolated': len(issues),
            'state': 'PROCESSED' if rows or issues else 'HEADER_ONLY'}
    meta['balanced'] = (meta['input'] == meta['blank'] + meta['sections'] - 1
                        + meta['accepted'] + meta['isolated'])
    return {'rows': sorted(rows, key=lambda item: item['id']),
            'meta': meta, 'isolated': sorted(issues, key=lambda item: item['line'])}
