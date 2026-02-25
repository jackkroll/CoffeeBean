from helpers import *
from models import *


def seed_shops(db_session):
    shops = [
        Shop.fromStrings("Biggby", "47.1217117", "-88.5635648"),
        Shop.fromStrings("Camp Coffee", "46.7449659", "-88.4358324"),
        Shop.fromStrings("Prickly Pine", "47.1219535", "-88.5672185"),
    ]
    db_session.add_all(shops)
    db_session.commit()
    return shops


def test_fetchAllShops_returns_all(db_session):
    shops = seed_shops(db_session)
    fetched = fetchAllShops(db_session)
    assert len(fetched) == len(shops)


def test_fetchShopById_returns_shop(db_session):
    shops = seed_shops(db_session)
    target = shops[0]
    fetched = fetchShopById(db_session, target.id)
    assert fetched is not None
    assert fetched.id == target.id


def test_fetchItemById_returns_item(db_session):
    shop = Shop.fromStrings("Biggby", "47.1217117", "-88.5635648")
    db_session.add(shop)
    db_session.commit()

    item = Item.fromStrings(shop.id, "Latte", "3.50")
    db_session.add(item)
    db_session.commit()

    fetched = fetchItemById(db_session, item.id)
    assert fetched is not None
    assert fetched.name == "Latte"


def test_fetchReviews_returns_review_fields(db_session):
    user = User(id="user-1", username="tester", passwordHash="hash")
    shop = Shop.fromStrings("Biggby", "47.1217117", "-88.5635648")
    db_session.add_all([user, shop])
    db_session.commit()

    item = Item.fromStrings(shop.id, "Latte", "3.50")
    db_session.add(item)
    db_session.commit()

    review = Review.fromString(user.id, shop.id, item.id)
    db_session.add(review)
    db_session.commit()

    field = ReviewField.fromString(review.id, "bitterness", "0", "5", "4", "Nice")
    db_session.add(field)
    db_session.commit()

    reviews = fetchReviews(db_session, shopId=shop.id, itemId=item.id)
    assert len(reviews) == 1
    assert reviews[0].value == 4.0


def test_fetchShopsByDistance(db_session):
    shops = seed_shops(db_session)
    testLat = 47.118685
    testLon = -88.5467528
    distanceShops = fetchShopsByDistance(db_session, testLat, testLon)
    assert len(distanceShops) == len(shops)
    assert distanceShops[0][1] == shops[0]
    distanceShops = fetchShopsByDistance(db_session, testLat, testLon, maxDistance= 10)
    assert len(distanceShops) == (len(shops) - 1)
    distanceShops = fetchShopsByDistance(db_session, testLat, testLon, maxDistance=10, minDistance=9)
    assert len(distanceShops) == 0
    distanceShops = fetchShopsByDistance(db_session, testLat, testLon, maxDistance=0, minDistance=5)
    assert len(distanceShops) == 0

def test_serialization(db_session):
    shops = seed_shops(db_session)
    testLat = 47.118685
    testLon = -88.5467528
    distanceShops = fetchShopsByDistance(db_session, testLat, testLon)
    jsonReturn = encode_shops_by_dist(distanceShops)
    assert jsonReturn is not None
    assert json.loads(jsonReturn) == json.loads(jsonReturn)

