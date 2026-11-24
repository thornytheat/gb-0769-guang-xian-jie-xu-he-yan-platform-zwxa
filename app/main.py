import os
from flask import Flask

from .api import api
from .console import console
from .errors import InspectionError


def create_app(database=None):
    app = Flask(__name__)
    app.config.update(DATABASE=database or os.getenv('FIBER_DB','instance/inspection.sqlite'), MAX_CONTENT_LENGTH=3000000)
    app.register_blueprint(api)
    app.register_blueprint(console)

    @app.errorhandler(InspectionError)
    def handle(error):
        return {'code':error.code, 'source':error.source}, error.status

    @app.get('/healthz')
    def health():
        return {'status':'ok'}

    return app
