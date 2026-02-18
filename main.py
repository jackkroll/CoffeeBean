from models import *
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from extensions import db
from sqlalchemy.orm import DeclarativeBase
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)

with app.app_context():
    db.create_all()
@app.route("/")
def landing_page():
    return "Landing Page!"

if __name__ == "__main__":
    app.run(debug=True)