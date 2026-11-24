SENTINELS = frozenset({'N/A','NULL','-','未知'})


def cell(raw):
    value = raw.strip()
    if not value:
        raise ValueError('EMPTY_CELL')
    if value in SENTINELS:
        raise ValueError('MISSING_SENTINEL')
    return value
