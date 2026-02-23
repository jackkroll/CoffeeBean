import pytest
from flask import Flask

from extensions import db as _db
import models  # ensure models are registered before create_all


@pytest.fixture
def app(tmp_path):
    app = Flask(__name__, template_folder="doc")
    db_path = tmp_path / "test.db"
    app.config.update(
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    _db.init_app(app)

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def db_session(app):
    return _db.session
