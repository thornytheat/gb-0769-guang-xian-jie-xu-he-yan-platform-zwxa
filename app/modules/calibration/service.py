def calibrate(traces, settings):
    ends, outliers = {}, []
    for endpoint, sign in (('a', 1), ('b', -1), ('design', 0)):
        aligned = []
        for row in traces[endpoint]:
            reading = row['mm']
            if sign:
                from_head = reading - settings[f'zero_{endpoint}_mm']
                reading = from_head if sign == 1 else settings['length_mm'] - from_head
            evidence = {**row, 'chain_mm': reading}
            if not 0 <= reading <= settings['length_mm'] and endpoint != 'design':
                outliers.append({**evidence, 'code': 'OUTSIDE_LINK'})
            elif not 0 <= reading <= settings['length_mm']:
                aligned.append({**evidence, 'code': 'DESIGN_OUTSIDE_LINK'})
            else:
                aligned.append(evidence)
        ends[endpoint] = sorted(aligned, key=lambda item: (item['chain_mm'], item['id']))
    return {'settings': settings, 'aligned': ends, 'outliers': outliers}
