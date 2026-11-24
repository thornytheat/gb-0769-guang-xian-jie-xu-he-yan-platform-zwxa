from decimal import Decimal


def verdict(double_mdb, maximum_mdb):
    if double_mdb < 0:
        return 'INVALID_NET_GAIN'
    return 'PASS' if double_mdb <= maximum_mdb * 2 else 'OVER_LIMIT'


def display(double_mdb):
    return f'{Decimal(double_mdb) / 2000:.4f}'
