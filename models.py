import uuid
from datetime import datetime
from xmlrpc.client import DateTime

from flask_sqlalchemy import SQLAlchemy
from typing import Optional, Self
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

    def __init__(self, name: str, lat: float, lon: float):
        self.id = str(uuid.uuid4())
        self.name = name
        self.lat = lat
        self.lon = lon

    def __json__(self):
        return {'id': self.id, 'name': self.name, 'lat': self.lat, 'lon': self.lon}

    @classmethod
    def fromStrings(self, name: str, lat: str, lon: str) -> Self | None:
        if lat == "" or lon == "":
            return None
        lat = float(lat)
        lon = float(lon)

        # Impossible location
        if abs(lat) > 90:
            return None
        if abs(lon) > 180:
            return None

        return Shop(name=name, lat=lat, lon=lon)
    def fetchItems(self, db: db.session):
        items = db.query(Item).where(Shop.id == self.id)
        return items

class Review(db.Model):
    id: Mapped[str] = mapped_column(primary_key=True)
    postDate: Mapped[float]  #Unix timestamp
    posterID: Mapped[str] = mapped_column(ForeignKey('user.id'))
    attributedShopID: Mapped[str] = mapped_column(ForeignKey('shop.id'))
    attributedItemID: Mapped[str] = mapped_column(ForeignKey('item.id'))

    def __init__(self, postDate: float, posterID: str, attributedShopID: str, attributedItemID: str):
        self.id = str(uuid.uuid4())
        self.postDate = postDate
        self.posterID = posterID
        self.attributedShopID = attributedShopID
        self.attributedItemID = attributedItemID

    @classmethod
    def fromString(self, posterID: str, attributedShopID: str, attributedItemID: str) -> Self | None:
        if posterID == "" or attributedShopID == "" or attributedItemID == "":
            return None
        return Review(datetime.now().timestamp(), posterID, attributedShopID, attributedItemID)


class ReviewField(db.Model):
    parentID: Mapped[str] = mapped_column(ForeignKey('review.id'), primary_key=True)
    fieldName: Mapped[str] = mapped_column(primary_key=True)
    lowerRange: Mapped[int]
    upperRange: Mapped[int]
    value: Mapped[float]
    comment: Mapped[Optional[str]]

    def __init__(self, parentID: str, fieldName: str, lowerRange: int, upperRange: int, value: float, comment: str | None):
        self.parentID = parentID
        self.fieldName = fieldName
        self.lowerRange = lowerRange
        self.upperRange = upperRange
        self.value = value
        self.comment = comment

    @classmethod
    def fromString(self, parentID: str, fieldName: str, lowerRange: str, upperRange: str, value: str, comment: str | None):
        if parentID == "" or fieldName == "":
            return None
        lowerRange = int(lowerRange)
        upperRange = int(upperRange)
        value = float(value)
        return ReviewField(parentID, fieldName, lowerRange, upperRange, value, comment)

class Item(db.Model):
    id: Mapped[str] = mapped_column(primary_key=True)
    shopID: Mapped[str] = mapped_column(ForeignKey('shop.id'))
    name: Mapped[str]
    price: Mapped[Optional[float]]

    def __init__(self, name: str, shopID: str, price: float | None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.shopID = shopID
        self.price = price

    @classmethod
    def fromStrings(self, shopID: str, name: str, price: str) -> Self | None:
        if shopID == "" or name == "":
            return None
        if price == "":
            price = None
        else:
            price = float(price)
            if price < 0:
                return None
        return Item(shopID=shopID, name=name, price=price)