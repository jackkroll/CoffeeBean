import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from extensions import db

class User(db.Model):
    id: Mapped[str] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    passwordHash: Mapped[str]

class Shop(db.Model):
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    lat: Mapped[float]
    lon: Mapped[float]

class Review(db.Model):
    id: Mapped[str] = mapped_column(primary_key=True)
    postDate: Mapped[int]  #Unix timestamp
    posterID: Mapped[str] = mapped_column(ForeignKey('user.id'))
    attributedShopID: Mapped[str] = mapped_column(ForeignKey('shop.id'))
    attributedItemID: Mapped[str] = mapped_column(ForeignKey('item.id'))

class ReviewField(db.Model):
    parentID: Mapped[str] = mapped_column(ForeignKey('review.id'), primary_key=True)
    fieldName: Mapped[str] = mapped_column(primary_key=True)
    lowerRange: Mapped[int]
    upperRange: Mapped[int]
    value: Mapped[float]
    comment: Mapped[Optional[str]]

class Item(db.Model):
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[float]
