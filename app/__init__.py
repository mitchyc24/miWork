import os

from flask import Flask

from . import db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(base_dir, 'data', 'tracker.db'),
    )

    if test_config is not None:
        app.config.from_mapping(test_config)

    db.init_app(app)

    from .blueprints import views, api
    app.register_blueprint(views.bp)
    app.register_blueprint(api.bp)

    return app
