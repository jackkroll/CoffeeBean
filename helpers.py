from extensions import db
import bcrypt
import json
from models import *
from geopy.distance import geodesic
import re

def loginUser(db: db.session, username: str, password: str) -> User | None:
    password = bytes(password, "utf-8")
    user = db.query(User).where(User.username == username).first()
    if user is None:
        return None
    hash = user.passwordHash.encode("utf-8")
    if bcrypt.checkpw(password, hash):
        return user
    else:
        return None



def fetchAllShops(db : db.session) -> [Shop]:
    allShops = db.query(Shop).all()
    return allShops
def fetchShopById(db : db.session, shopId: str) -> Shop | None:
    shop = db.get(Shop, shopId)
    return shop if shop else None
def fetchItemById(db: db.session, itemId: str) -> Item | None:
    item = db.get(Item, itemId)
    return item if item else None

def fetchFieldsFor(db: db.session, shopId: str, itemId: str, type: str, afterDate: DateTime = None) -> [ReviewField]:
    fetchedFields = []
    reviews = db.query(Review).where(Review.attributedShopID == shopId, Review.attributedItemID == itemId).all()
    for review in reviews:
        # If post date is older than the cutoff
        if afterDate is not None and review.postDate < afterDate:
            continue
        field = db.get(ReviewField, (review.id, type))
        if field is not None:
            fetchedFields.append(field)
    return fetchedFields

def fetchShopsByDistance(db: db.session, lat: float, lon: float, maxDistance: float | None = None, minDistance: float | None = None) -> [(float,Shop)]:
    shops = db.query(Shop).all()
    distanceShops = []
    if maxDistance is not None and minDistance is not None and minDistance > maxDistance:
        return []
    for shop in shops:
        distance = geodesic((lat, lon), (shop.lat, shop.lon)).miles
        if maxDistance is not None and distance > maxDistance:
            continue
        if minDistance is not None and distance < minDistance:
            continue
        distanceShops.append((distance, shop))
    distanceShops.sort(key=lambda x: x[0])
    return distanceShops

def getReviewStatistics(shopReviews):
    total = 0
    if len(shopReviews) > 0:
        # - 1 because inclusive of lower range
        distribution = [0] * ((shopReviews[0].upperRange - (shopReviews[0].lowerRange - 1)))
    else:
        return None, None, None
    for review in shopReviews:
        total += review.value
        cur = round(review.value)
        distribution[cur] += 1
    avg = total / len(shopReviews)
    return distribution, avg, len(shopReviews)

def encode_shops_by_dist(distanceShops: [(float, Shop)]) -> str:
    return json.dumps(distanceShops, default=lambda o: o.__json__() if hasattr(o, '__json__') else None)

def wipeShopAndItemPoster(db: db.session, posterID: str):
    for shop in db.query(Shop).filter(Shop.posterID ==posterID):
        shop.posterID = None
    for item in db.query(Item).filter(Item.posterID ==posterID):
        item.posterID = None
    db.commit()

def anonymizeReviewFor(db: db.session, posterID: str):
    for review in db.query(Review).filter(Review.posterID == posterID):
        review.posterID = None
    db.commit()

def deleteReviewFor(db: db.session, posterID: str):
    for review in db.query(Review).filter(Review.posterID == posterID):
        for reviewField in review.fetchReviewFields(db):
            db.delete(reviewField)
        db.delete(review)
    db.commit()

def usernameIsTaken(db: db.session, username: str) -> bool:
    return len(db.query(User).filter(User.username == username).all()) >= 1

def passwordIsValid(password: str) -> bool:
    matches = re.findall(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[^A-Za-z]).{6,}$", password)
    return len(matches) > 0
