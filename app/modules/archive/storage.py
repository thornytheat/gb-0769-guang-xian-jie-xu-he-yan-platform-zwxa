import json
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path

from app.errors import InspectionError
from .identity import canonical


@contextmanager
def session(database):
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database, timeout=15)) as connection, connection:
        connection.execute('CREATE TABLE IF NOT EXISTS inspections (id TEXT UNIQUE NOT NULL, document BLOB NOT NULL)')
        yield connection


def publish(database, manifest):
    with session(database) as db:
        key = manifest['inspection_id']
        changed = db.execute('INSERT INTO inspections VALUES (?, ?) ON CONFLICT(id) DO NOTHING',
                             (key, canonical(manifest))).rowcount
        original = db.execute('SELECT document FROM inspections WHERE id=?',(key,)).fetchone()[0]
        return json.loads(original), changed == 1


def get(database, identifier):
    with session(database) as db:
        record = db.execute('SELECT document FROM inspections WHERE id=?',(identifier,)).fetchone()
        if not record:
            raise InspectionError('INSPECTION_NOT_FOUND', status=404)
        return json.loads(record[0])


def recent(database):
    with session(database) as db:
        rows = (json.loads(data) for data, in db.execute('SELECT document FROM inspections ORDER BY rowid DESC LIMIT 50'))
        return [{key: row[key] for key in ('inspection_id', 'generated_at', 'rule', 'duration_ms')} for row in rows]
