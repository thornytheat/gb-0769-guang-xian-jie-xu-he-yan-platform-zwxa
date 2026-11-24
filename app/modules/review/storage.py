import json
import sqlite3
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.errors import InspectionError


@contextmanager
def session(database):
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database, timeout=15)) as connection, connection:
        connection.execute(
            'CREATE TABLE IF NOT EXISTS reviews ('
            'review_id TEXT UNIQUE NOT NULL, inspection_id TEXT NOT NULL, report_sha256 TEXT, '
            'handover_ready INTEGER NOT NULL, created_at TEXT NOT NULL, document BLOB NOT NULL)')
        yield connection


def publish(database, inspection_id, report_sha, review_id, bundle):
    created_at = datetime.now(timezone.utc).isoformat(timespec='seconds')
    document = json.dumps(bundle, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    with session(database) as db:
        changed = db.execute(
            'INSERT INTO reviews VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(review_id) DO NOTHING',
            (review_id, inspection_id, report_sha, int(bundle['handover_ready']), created_at, document)).rowcount
        raw = db.execute('SELECT document FROM reviews WHERE review_id=?', (review_id,)).fetchone()[0]
        return json.loads(raw), changed == 1


def list_reviews(database, inspection_id=None):
    with session(database) as db:
        if inspection_id:
            rows = db.execute(
                'SELECT document FROM reviews WHERE inspection_id=? ORDER BY rowid DESC LIMIT 50',
                (inspection_id,))
        else:
            rows = db.execute('SELECT document FROM reviews ORDER BY rowid DESC LIMIT 50')
        return [json.loads(data) for data, in rows]


def get_review(database, review_id):
    with session(database) as db:
        row = db.execute('SELECT document FROM reviews WHERE review_id=?', (review_id,)).fetchone()
        if not row:
            raise InspectionError('REVIEW_NOT_FOUND', status=404)
        return json.loads(row[0])
