from flask import Blueprint, abort, current_app, render_template, request

from .config import SOURCES, SPEC
from .errors import InspectionError
from .input import sample
from .modules.archive.service import archive
from .modules.archive.storage import get, recent
from .modules.certificate.service import certify
from .modules.review.service import review
from .modules.review.storage import list_reviews
from .pipeline import run
from .modules.calibration.contract import FIELDS
from .views import CODES, LABELS, half_mm_metres, metres, trace_frames

console = Blueprint('console', __name__)
console.add_app_template_filter(metres, 'metres')
console.add_app_template_filter(half_mm_metres, 'half_mm_metres')


def material(mode):
    if mode == 'custom':
        return {'traces': {key: request.form.get(key, '') for key in SOURCES},
                'settings': {key: request.form.get(key, '') for key in FIELDS},
                'report': request.form.get('report', '')}
    return sample(mode)


@console.route('/', methods=['GET', 'POST'])
@console.route('/inspect/<section>', methods=['GET', 'POST'])
def view(section='design'):
    if section not in LABELS:
        abort(404)
    mode = request.values.get('sample', 'dirty')
    database = current_app.config['DATABASE']
    evidence, frames, entries, data = None, {}, [], {}
    issued, fresh, error, sources = None, False, None, {}
    review_doc = review_fresh = None
    review_entries = []
    try:
        sources = material(mode)
        if section in ('archive', 'certificate', 'review'):
            if section == 'archive' and request.method == 'POST':
                issued, fresh = archive(database, sources)
            entries = recent(database)
            identifier = request.args.get('inspection') or (entries[0]['inspection_id'] if entries else None)
            if section == 'certificate' and identifier:
                evidence = certify(get(database, identifier))
            if section == 'review':
                if identifier:
                    review_entries = list_reviews(database, identifier)
                if request.method == 'POST' and identifier and sources.get('report'):
                    review_doc, review_fresh = review(database, identifier, sources['report'])
                    review_entries = list_reviews(database, identifier)
        else:
            data = run(sources, section)
            if 'calibration' in data:
                frames = trace_frames(data['calibration'])
    except InspectionError as exc:
        error = exc.code
    return render_template('console.html', section=section, labels=LABELS, codes=CODES, spec=SPEC, mode=mode,
                           data=data, frames=frames, error=error, materials=sources, entries=entries,
                           evidence=evidence, issued=issued, fresh=fresh, fields=FIELDS,
                           review_doc=review_doc, review_fresh=review_fresh, review_entries=review_entries)
