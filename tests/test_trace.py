import pytest

from app.errors import InspectionError
from app.modules.trace.service import ingest, receive_source


def test_bom_and_repeated_header(dirty):  # TRAP-02 TRAP-04
    totals = ingest(dirty['traces'])['counts']['a']
    assert totals == dict(input=14, blank=1, sections=2, accepted=7, isolated=5, state='PROCESSED', balanced=True)


def test_extra_fields_keep_raw_location(dirty):  # TRAP-05
    row = next(r for r in ingest(dirty['traces'])['isolated'] if r['code']=='COLUMN_COUNT')
    assert (row['line'], row['source'], row['raw'][-1]) == (14, 'a', 'extra')


def test_missing_sentinel_and_blank_are_isolated(dirty):  # TRAP-07
    rows = ingest(dirty['traces'])['isolated']
    assert [(r['source'], r['line'], r['raw'][-1]) for r in rows if r['code'] in {'MISSING_SENTINEL','EMPTY_CELL'}] == [('a',13,'N/A'),('b',8,'')]


def test_conflicting_records_both_withdrawn(dirty):  # TRAP-14
    r = ingest(dirty['traces'])
    assert 'A-C' not in [t['id'] for t in r['traces']['a']]
    assert [row['line'] for row in r['isolated'] if row['code']=='CONFLICTING_EVENT'] == [10,11]


def test_equivalent_units_dedupe(dirty):  # TRAP-15
    r = ingest(dirty['traces'])
    assert r['reason_counts']['DUPLICATE_EVENT'] == 1
    assert next(row for row in r['traces']['a'] if row['id']=='A-02')['mm'] == 205000


def test_three_empty_definitions(clean):
    assert receive_source('a', clean['traces']['a'].splitlines()[0])[1]['state'] == 'HEADER_ONLY'
    for text, code in (('', 'EMPTY_FILE'), ('\n ,,\n', 'BLANK_FILE')):
        with pytest.raises(InspectionError, match=code):
            receive_source('a', text)


def test_column_order_preserves_source_id():
    rows, _, _ = receive_source('a', 'unit,event,loss_db,distance\nm,00012,0.123,4\n')
    assert (rows[0]['id'], rows[0]['loss_mdb'], rows[0]['mm']) == ('00012', 123, 4000)
