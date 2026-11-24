from flask import Blueprint, current_app, jsonify, request

from .input import request_material
from .modules.archive.service import archive
from .modules.archive.storage import get, recent
from .modules.certificate.service import certify
from .modules.review.service import review
from .modules.review.storage import get_review, list_reviews
from .pipeline import run

api = Blueprint('fiber_api', __name__, url_prefix='/api')


def calculate(stage):
    return run(request_material(), stage)[stage]


@api.post('/trace')
def trace():
    return calculate('trace')


@api.post('/calibration')
def calibration():
    return calculate('calibration')


@api.post('/pairs')
def pairs():
    return calculate('pairs')


@api.post('/loss')
def loss():
    return calculate('loss')


@api.post('/design')
def design():
    return calculate('design')


@api.post('/inspections')
def submit():
    report, fresh = archive(current_app.config['DATABASE'], request_material())
    return {'inspection_id': report['inspection_id'], 'created': fresh, 'record': report}, 201 if fresh else 200


@api.get('/inspections')
def list_inspections():
    return {'inspections': recent(current_app.config['DATABASE'])}


@api.get('/inspections/<identifier>')
def inspection(identifier):
    return get(current_app.config['DATABASE'], identifier)


@api.post('/inspections/<identifier>/reviews')
def create_review(identifier):
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get('report'), str):
        return {'code': 'REPORT_TEXT_REQUIRED'}, 400
    stored, fresh = review(current_app.config['DATABASE'], identifier, body['report'])
    return {'review_id': stored['review_id'], 'created': fresh, 'review': stored}, 201 if fresh else 200


@api.get('/inspections/<identifier>/reviews')
def reviews_for_inspection(identifier):
    get(current_app.config['DATABASE'], identifier)
    return {'reviews': list_reviews(current_app.config['DATABASE'], identifier)}


@api.get('/reviews/<review_id>')
def review_detail(review_id):
    return get_review(current_app.config['DATABASE'], review_id)


@api.get('/certificate/<identifier>')
def certificate(identifier):
    return certify(inspection(identifier))


@api.get('/export/<identifier>')
def export(identifier):
    response = jsonify(certificate(identifier))
    response.headers['Content-Disposition'] = f'attachment; filename="splice-{identifier[:12]}.json"'
    return response
