import re
from decimal import Decimal

NUMBER = re.compile(r'[+-]?\d+(?:\.\d{1,6})?', re.ASCII)
DISTANCE = {'m': 1000, 'km': 1_000_000, 'mm': 1}


def scaled(text, factor, minimum, maximum):
    if len(text) > 24 or not NUMBER.fullmatch(text):
        raise ValueError('BAD_NUMERIC')
    value = Decimal(text) * factor
    if value != value.to_integral_value() or not minimum <= value <= maximum:
        raise ValueError('OUT_OF_SCALE')
    return int(value)


def distance(value, unit):
    if unit not in DISTANCE:
        raise ValueError('DISTANCE_UNIT')
    return scaled(value, DISTANCE[unit], 0, 500_000_000)
