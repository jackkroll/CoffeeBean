from extensions import db
import json
from models import *
from geopy.distance import geodesic

def fetchAllShops(db : db.session) -> [Shop]:
    allShops = db.query(Shop).all()
    return allShops
def fetchShopById(db : db.session, shopId: str) -> Shop | None:
    shop = db.get(Shop, shopId)
    return shop if shop else None
def fetchItemById(db: db.session, itemId: str) -> Item | None:
    item = db.get(Item, itemId)
    return item if item else None

def fetchReviews(db: db.session, shopId: str, itemId: str) -> [ReviewField]:
    fetchedReviews = []
    reviews = db.query(Review).where(Review.attributedShopID == shopId, Review.attributedItemID == itemId).all()
    for review in reviews:
        field = db.get(ReviewField, (review.id, "bitterness"))
        if field is not None:
            fetchedReviews.append(field)
    return fetchedReviews

def fetchShopsByDistance(db: db.session, lat: float, lon: float, maxDistance: float | None = None, minDistance: float | None = None) -> [(float,Shop)]:
    shops = db.query(Shop).all()
    distanceShops = []
    for shop in shops:
        distance = geodesic((lat, lon), (shop.lat, shop.lon)).miles
        if maxDistance is not None and distance > maxDistance:
            continue
        if minDistance is not None and distance < minDistance:
            continue
        distanceShops.append((distance, shop))
    distanceShops.sort(key=lambda x: x[0])
    return distanceShops

def encode_shops_by_dist(distanceShops: [(float, Shop)]) -> str:
    return json.dumps(distanceShops, default=lambda o: o.__json__() if hasattr(o, '__json__') else None)

