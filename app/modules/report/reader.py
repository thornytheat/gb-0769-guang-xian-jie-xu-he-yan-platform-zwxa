import csv
import re
from decimal import Decimal, ROUND_HALF_UP
from io import StringIO

from app.errors import InspectionError

REPORT_HEADER = ('joint', 'loss_db', 'verdict')
NUMBER = re.compile(r'[+-]?\d+(?:\.\d+)?', re.ASCII)
VERDICT_TOKENS = {'PASS': 'PASS', '合格': 'PASS', 'OVER_LIMIT': 'OVER_LIMIT', '超限': 'OVER_LIMIT',
                  '不合格': 'OVER_LIMIT'}


def read_rows(text):
    text = text.removeprefix('\ufeff')
    if not text:
        raise InspectionError('EMPTY_REPORT')
    reader = csv.reader(StringIO(text, newline=''), strict=True)
    header = None
    try:
        while True:
            line = reader.line_num + 1
            row = next(reader, None)
            if row is None:
                if header is None:
                    raise InspectionError('BLANK_REPORT')
                return
            if not any(value.strip() for value in row):
                if header is not None:
                    yield line, row, None, 'BLANK'
                continue
            if header is None:
                header = [value.strip() for value in row]
                if sorted(header) != sorted(REPORT_HEADER):
                    raise InspectionError('BAD_REPORT_HEADER')
                continue
            if row == header:
                yield line, row, None, 'REPEATED_HEADER'
            elif len(row) != len(header):
                yield line, row, None, 'COLUMN_COUNT'
            else:
                yield line, row, dict(zip(header, row)), None
    except csv.Error:
        raise InspectionError('REPORT_CSV_SYNTAX') from None


def parse_loss(text):
    """外检报告只保留三位小数；多于三位无法由报告本身保证，按坏行隔离。"""
    if len(text) > 24 or not NUMBER.fullmatch(text):
        raise ValueError('BAD_REPORT_NUMERIC')
    value = Decimal(text)
    if abs(value.as_tuple().exponent) > 3:
        raise ValueError('REPORT_PRECISION_OVER_3')
    milli = value * 1000
    if milli != milli.to_integral_value() or not -10_000 <= milli <= 10_000:
        raise ValueError('REPORT_OUT_OF_SCALE')
    return int(milli)


def round3(milli):
    """现场复算值（毫 dB）按报告精度（半进）回到三位小数，单位仍为毫 dB。"""
    return int((Decimal(milli) / 1000).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP) * 1000)
