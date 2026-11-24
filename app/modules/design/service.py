from app.modules.loss.verdict import verdict
from app.modules.pairs.optimal import best_pairs


def reconcile(calibrated, joined, loss):
    points, measurements = calibrated['aligned']['design'], loss['rows']
    tolerance = calibrated['settings']['design_tol_mm']
    valid = [row for row in points if not row.get('code')]
    links = best_pairs([r['chain_mm']*2 for r in valid], [r['midpoint_half_mm'] for r in measurements], tolerance*2)
    mapped = {valid[i]['id']: measurements[j] for i,j in links}
    used = {j for _,j in links}
    rows = []
    for point in points:
        pair = mapped.get(point['id'])
        near_singles = [dict(id=r['id'], source=r['source'], line=r['line']) for r in joined['singles']
                        if abs(r['chain_mm']-point['chain_mm']) <= tolerance and not point.get('code')]
        if not pair:
            code = point.get('code') or ('SINGLE_SIDE_ONLY' if near_singles else 'NO_COUPLED_EVIDENCE')
        else:
            code = verdict(pair['net_double_mdb'], point['limit_mdb'])
        bucket = {'PASS':'passed','OVER_LIMIT':'over_limit'}.get(code,'missing')
        rows.append({'joint': point['id'], 'chain_mm': point['chain_mm'], 'design_line': point['line'],
                     'limit_mdb': point['limit_mdb'], 'pair': pair['pair'] if pair else None,
                     'net_db': pair['net_db'] if pair else None, 'code':code,'bucket':bucket, 'near_singles': near_singles,
                     'a_line': pair['a']['line'] if pair else None, 'b_line': pair['b']['line'] if pair else None,
                     'gain_ends': pair['gain_ends'] if pair else []})
    totals = {key: sum(r['bucket'] == key for r in rows) for key in ('passed','over_limit','missing')}
    orphans = [r for i,r in enumerate(measurements) if i not in used]
    measured = len(calibrated['aligned']['a']) + len(calibrated['aligned']['b'])
    return {'design_count':len(points), **totals, 'balanced':len(points)==sum(totals.values()), 'rows':rows,
            'orphans':orphans, 'orphan_pairs':len(orphans), 'singles': joined['singles'], 'single_count':joined['single_count'],
            'measurements':measured, 'measurements_balanced': measured == 2*(len(mapped)+len(orphans))+joined['single_count']}
