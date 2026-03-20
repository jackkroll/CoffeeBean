import uuid

import bcrypt
import models
from models import Item, Review, ReviewField, Shop, User


def seed_shops_and_items(db_session):
    shops = [
        Shop.fromStrings("Biggby", "47.1217117", "-88.5635648"),
        Shop.fromStrings("Camp Coffee", "46.7449659", "-88.4358324"),
        Shop.fromStrings("Prickly Pine", "47.1219535", "-88.5672185"),
    ]
    db_session.add_all(shops)
    db_session.commit()

    items = [
        Item.fromStrings(shops[0].id, "Cookie", "3"),
        Item.fromStrings(shops[0].id, "Latte", "5"),
        Item.fromStrings(shops[1].id, "Water", "0"),
    ]
    db_session.add_all(items)
    db_session.commit()
    return shops, items


def test_user_init_sets_fields_and_uuid():
    user = User("name", "name@example.com", "hashed-password")

    assert user.username == "name"
    assert user.email == "name@example.com"
    assert user.passwordHash == "hashed-password"
    assert str(uuid.UUID(user.id)) == user.id


def test_user_changePassword_rehashes_and_validates_password():
    user = User("name", "name@example.com", "old-hash")

    user.changePassword("NewValid1!")

    assert user.passwordHash != "old-hash"
    assert bcrypt.checkpw(b"NewValid1!", user.passwordHash.encode("utf-8"))


def test_user_fromStrings_hashes_password():
    user = User.fromStrings("name", "name@example.com", "Valid1!")

    assert user.username == "name"
    assert user.email == "name@example.com"
    assert user.passwordHash != "Valid1!"
    assert bcrypt.checkpw(b"Valid1!", user.passwordHash.encode("utf-8"))


def test_shop_init_sets_fields_and_uuid():
    shop = Shop("Cafe", 45.0, -93.0, "poster-1")

    assert shop.name == "Cafe"
    assert shop.lat == 45.0
    assert shop.lon == -93.0
    assert shop.posterID == "poster-1"
    assert str(uuid.UUID(shop.id)) == shop.id


def test_shop_json_returns_public_fields():
    shop = Shop("Cafe", 45.0, -93.0)

    assert shop.__json__() == {
        "id": shop.id,
        "name": "Cafe",
        "lat": 45.0,
        "lon": -93.0,
    }


def test_shop_fromStrings_valid():
    shop = Shop.fromStrings("Cafe", "45.0", "-93.0", "poster-1")

    assert shop is not None
    assert shop.name == "Cafe"
    assert shop.lat == 45.0
    assert shop.lon == -93.0
    assert shop.posterID == "poster-1"


def test_shop_fromStrings_invalid_coordinates():
    assert Shop.fromStrings("Cafe", "95", "0") is None
    assert Shop.fromStrings("Cafe", "0", "190") is None


def test_shop_fromStrings_missing_fields():
    assert Shop.fromStrings("Cafe", "", "-93.0") is None
    assert Shop.fromStrings("Cafe", "45.0", "") is None


def test_item_init_sets_fields_and_uuid():
    item = Item("Latte", "shop-1", 4.5, "poster-1")

    assert item.name == "Latte"
    assert item.shopID == "shop-1"
    assert item.price == 4.5
    assert item.posterID == "poster-1"
    assert str(uuid.UUID(item.id)) == item.id


def test_item_fromStrings_valid():
    item = Item.fromStrings("shop-1", "Latte", "3.50", "poster-1")

    assert item is not None
    assert item.shopID == "shop-1"
    assert item.name == "Latte"
    assert item.price == 3.5
    assert item.posterID == "poster-1"


def test_item_fromStrings_optional_price():
    item = Item.fromStrings("shop-1", "Latte", "")

    assert item is not None
    assert item.price is None


def test_item_fromStrings_negative_price():
    assert Item.fromStrings("shop-1", "Latte", "-1") is None


def test_item_fromStrings_requires_shop_and_name():
    assert Item.fromStrings("", "Latte", "3") is None
    assert Item.fromStrings("shop-1", "", "3") is None


def test_review_init_sets_fields_and_uuid():
    review = Review(123.0, "poster-1", "shop-1", "item-1")

    assert review.postDate == 123.0
    assert review.posterID == "poster-1"
    assert review.attributedShopID == "shop-1"
    assert review.attributedItemID == "item-1"
    assert str(uuid.UUID(review.id)) == review.id


def test_review_fetchReviewFields_returns_linked_fields(db_session):
    shop = Shop("Cafe", 45.0, -93.0)
    item = Item("Latte", shop.id, 4.5)
    review = Review(123.0, None, shop.id, item.id)
    other_review = Review(124.0, None, shop.id, item.id)
    db_session.add_all([shop, item, review, other_review])
    db_session.commit()

    bitterness = ReviewField(review.id, "bitterness", 0, 5, 4.0, "good")
    sweetness = ReviewField(review.id, "sweetness", 0, 5, 3.0, "balanced")
    other = ReviewField(other_review.id, "other", 0, 5, 2.0, "other")
    db_session.add_all([bitterness, sweetness, other])
    db_session.commit()

    fetched = list(review.fetchReviewFields(db_session))

    assert {(field.parentID, field.fieldName) for field in fetched} == {
        (review.id, "bitterness"),
        (review.id, "sweetness"),
    }


def test_review_fromString_requires_fields():
    assert Review.fromString("", "shop-1", "item-1") is None
    assert Review.fromString("user-1", "", "item-1") is None
    assert Review.fromString("user-1", "shop-1", "") is None


def test_review_fromString_uses_current_timestamp(monkeypatch):
    class FrozenNow:
        @staticmethod
        def timestamp():
            return 987.654

    class FrozenDatetime:
        @staticmethod
        def now():
            return FrozenNow()

    monkeypatch.setattr(models, "datetime", FrozenDatetime)

    review = Review.fromString("user-1", "shop-1", "item-1")

    assert review is not None
    assert review.postDate == 987.654
    assert review.posterID == "user-1"
    assert review.attributedShopID == "shop-1"
    assert review.attributedItemID == "item-1"


def test_reviewfield_init_sets_fields():
    field = ReviewField("review-1", "name", 0, 5, 4.5, "good")

    assert field.parentID == "review-1"
    assert field.fieldName == "name"
    assert field.lowerRange == 0
    assert field.upperRange == 5
    assert field.value == 4.5
    assert field.comment == "good"


def test_reviewfield_fromString_casts_types():
    field = ReviewField.fromString("review-1", "bitterness", "0", "5", "3.5", "ok")

    assert field is not None
    assert field.lowerRange == 0
    assert field.upperRange == 5
    assert field.value == 3.5
    assert field.comment == "ok"


def test_reviewfield_fromString_rejects_missing_parent_or_name():
    assert ReviewField.fromString("", "name", "0", "5", "3", None) is None
    assert ReviewField.fromString("review-1", "", "0", "5", "3", None) is None


def test_reviewfield_fromString_rejects_non_integer_ranges():
    assert ReviewField.fromString("review-1", "name", "low", "5", "3", None) is None
    assert ReviewField.fromString("review-1", "name", "0", "high", "3", None) is None


def test_reviewField_fromString_range_values():
    field = ReviewField.fromString("parentShop", "bitterness", "10", "0", "3", "ok")
    assert field is None

    field = ReviewField.fromString("parentShop", "bitterness", "0", "10", "11", "ok")
    assert field is None


def test_fetchItems(db_session):
    shops, _items = seed_shops_and_items(db_session)
    biggby_items = shops[0].fetchItems(db_session)
    camp_coffee_items = shops[1].fetchItems(db_session)
    prickly_pine_items = shops[2].fetchItems(db_session)

    assert [item.name for item in biggby_items] == ["Cookie", "Latte"]
    assert [item.name for item in camp_coffee_items] == ["Water"]
    assert prickly_pine_items == []
