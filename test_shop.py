import pytest
from flask import Flask, send_from_directory, request, Response, redirect, url_for, render_template, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from models import *
from helpers import *


@pytest.fixture
def client():
    app = Flask(__name__, template_folder='doc')
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///memory:"
    db.init_app(app)
    with app.app_context():
        db.create_all()
    testShops = [
    Shop.fromStrings("Biggby","47.1217117","-88.5635648"),
    Shop.fromStrings("Camp Coffee", "47.1219291","-88.566288"),
    Shop.fromStrings("Prickly Pine", "47.1219535","-88.5672185"),
    Shop.fromStrings("Dunkin", "47.1206833","-88.5788299"),
    Shop.fromStrings("Cruisin' Coffee", "47.2252707", "-88.4551763")
    ]
    db.session.add_all(testShops)
    yield app.test_client()

def shops_exist():
    shops = fetchAllShops(db.session)
    assert len(shops) == 5

