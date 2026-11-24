import csv
from io import StringIO

from app.errors import InspectionError

TRACE = ('event', 'distance', 'unit', 'loss_db')
DESIGN = ('joint', 'distance', 'unit', 'limit_db')


def read_rows(source, text):
    text = text.removeprefix('\ufeff')
    if not text:
        raise InspectionError('EMPTY_FILE', source)
    reader = csv.reader(StringIO(text, newline=''), strict=True)
    required = DESIGN if source == 'design' else TRACE
    header = None
    try:
        while True:
            line = reader.line_num + 1
            row = next(reader, None)
            if row is None:
                if header is None:
                    raise InspectionError('BLANK_FILE', source)
                return
            if not any(value.strip() for value in row):
                if header is not None:
                    yield line, row, None, 'BLANK'
                continue
            if header is None:
                header = [value.strip() for value in row]
                if sorted(header) != sorted(required):
                    raise InspectionError('BAD_HEADER', source)
                continue
            if row == header:
                yield line, row, None, 'REPEATED_HEADER'
            elif len(row) != len(header):
                yield line, row, None, 'COLUMN_COUNT'
            else:
                yield line, row, dict(zip(header, row)), None
    except csv.Error:
        raise InspectionError('CSV_SYNTAX', source) from None
