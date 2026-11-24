from time import perf_counter

from app.pipeline import run
from .identity import record
from .storage import publish


def archive(database, materials):
    start = perf_counter()
    results = run(materials)
    return publish(database, record(materials, results, start))
