import json
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


def create_user(db_session, username="tester", email="test@example.com", password="Secure1!"):
    user = User.fromStrings(username, email, password)
    db_session.add(user)
    db_session.commit()
    return user


def test_loginUser_returns_none_when_user_missing(db_session):
    assert loginUser(db_session, "missing", "password") is None


def test_loginUser_returns_user_for_valid_password(db_session):
    user = create_user(db_session, username="login-user", password="Valid1!")

    logged_in = loginUser(db_session, "login-user", "Valid1!")

    assert logged_in is not None
    assert logged_in.id == user.id


def test_loginUser_returns_none_for_invalid_password(db_session):
    create_user(db_session, username="wrong-password-user", password="Valid1!")

    assert loginUser(db_session, "wrong-password-user", "Invalid1!") is None


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


def test_fetchShopById_returns_none_for_missing_id(db_session):
    assert fetchShopById(db_session, "missing-shop-id") is None


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


def test_fetchItemById_returns_none_for_missing_id(db_session):
    assert fetchItemById(db_session, "missing-item-id") is None


def test_fetchFieldsFor_returns_matching_review_fields(db_session):
    user = create_user(db_session)
    shop = Shop.fromStrings("Biggby", "47.1217117", "-88.5635648")
    db_session.add(shop)
    db_session.commit()

    item = Item.fromStrings(shop.id, "Latte", "3.50")
    db_session.add(item)
    db_session.commit()

    review = Review(200.0, user.id, shop.id, item.id)
    other_review = Review(250.0, user.id, shop.id, item.id)
    db_session.add_all([review, other_review])
    db_session.commit()

    field = ReviewField.fromString(review.id, "bitterness", "0", "5", "4", "Nice")
    other_field = ReviewField.fromString(other_review.id, "sweetness", "0", "5", "3", "Fine")
    db_session.add_all([field, other_field])
    db_session.commit()

    reviews = fetchFieldsFor(db_session, shopId=shop.id, itemId=item.id, type="bitterness")

    assert len(reviews) == 1
    assert reviews[0].value == 4.0


def test_fetchFieldsFor_skips_old_reviews_and_missing_fields(db_session):
    user = create_user(db_session, username="reviewer")
    shop = Shop("Cafe", 42.0, -83.0, user.id)
    item = Item("Mocha", shop.id, 4.25, user.id)
    old_review = Review(100.0, user.id, shop.id, item.id)
    recent_review = Review(300.0, user.id, shop.id, item.id)
    db_session.add_all([shop, item, old_review, recent_review])
    db_session.commit()

    db_session.add(ReviewField(old_review.id, "body", 0, 5, 5.0, "Old"))
    db_session.commit()

    reviews = fetchFieldsFor(
        db_session,
        shopId=shop.id,
        itemId=item.id,
        type="body",
        afterDate=200.0,
    )

    assert reviews == []


def test_fetchShopsByDistance_respects_filters_and_sorting(db_session):
    shops = [
        Shop("Origin", 42.0, -83.0),
        Shop("Midpoint", 42.1, -83.0),
        Shop("Faraway", 42.2, -83.0),
    ]
    db_session.add_all(shops)
    db_session.commit()

    distance_shops = fetchShopsByDistance(db_session, 42.0, -83.0)
    within_ten = fetchShopsByDistance(db_session, 42.0, -83.0, maxDistance=10)
    at_least_five = fetchShopsByDistance(db_session, 42.0, -83.0, minDistance=5)
    between_five_and_ten = fetchShopsByDistance(
        db_session,
        42.0,
        -83.0,
        maxDistance=10,
        minDistance=5,
    )
    invalid_range = fetchShopsByDistance(db_session, 42.0, -83.0, maxDistance=1, minDistance=5)

    assert [shop.name for _, shop in distance_shops] == ["Origin", "Midpoint", "Faraway"]
    assert len(within_ten) == 2
    assert [shop.name for _, shop in at_least_five] == ["Midpoint", "Faraway"]
    assert [shop.name for _, shop in between_five_and_ten] == ["Midpoint"]
    assert invalid_range == []


def test_getReviewStatistics_returns_distribution_average_and_count():
    reviews = [
        ReviewField("review-1", "body", 0, 5, 1.2, "one"),
        ReviewField("review-2", "body", 0, 5, 3.4, "two"),
        ReviewField("review-3", "body", 0, 5, 3.6, "three"),
    ]

    distribution, average, total = getReviewStatistics(reviews)

    assert distribution == [0, 1, 0, 1, 1, 0]
    assert average == (1.2 + 3.4 + 3.6) / 3
    assert total == 3

def test_getReviewStatistics_with_non_zero_start():
    reviews = [
        ReviewField("review-1", "body", 5, 10, 5, "one"),
        ReviewField("review-2", "body", 5, 10, 6, "two"),
        ReviewField("review-3", "body", 5, 10, 10, "three")
    ]
    distribution, average, total = getReviewStatistics(reviews)
    assert distribution == [1, 1, 0, 0, 0, 1]
    assert average == (5 + 6 + 10) / 3
    assert total == 3

def test_getReviewStatistics_returns_none_tuple_for_empty_input():
    assert getReviewStatistics([]) == (None, None, None)


def test_encode_shops_by_dist_serializes_distances_and_shops(db_session):
    shops = seed_shops(db_session)
    encoded = encode_shops_by_dist([(1.25, shops[0])])

    assert json.loads(encoded) == [[1.25, shops[0].__json__()]]


def test_wipeShopAndItemPoster_clears_matching_posters_only(db_session):
    target_user = create_user(db_session, username="poster-a")
    other_user = create_user(db_session, username="poster-b")
    owned_shop = Shop("Owned Shop", 42.0, -83.0, target_user.id)
    kept_shop = Shop("Kept Shop", 42.1, -83.1, other_user.id)
    owned_item = Item("Owned Item", owned_shop.id, 4.5, target_user.id)
    kept_item = Item("Kept Item", kept_shop.id, 3.5, other_user.id)
    db_session.add_all([owned_shop, kept_shop, owned_item, kept_item])
    db_session.commit()

    wipeShopAndItemPoster(db_session, target_user.id)
    db_session.expire_all()

    assert db_session.get(Shop, owned_shop.id).posterID is None
    assert db_session.get(Item, owned_item.id).posterID is None
    assert db_session.get(Shop, kept_shop.id).posterID == other_user.id
    assert db_session.get(Item, kept_item.id).posterID == other_user.id


def test_anonymizeReviewFor_clears_matching_review_posters_only(db_session):
    target_user = create_user(db_session, username="reviewer-a")
    other_user = create_user(db_session, username="reviewer-b")
    shop = Shop("Cafe", 42.0, -83.0, target_user.id)
    item = Item("Latte", shop.id, 5.0, target_user.id)
    target_review = Review(100.0, target_user.id, shop.id, item.id)
    kept_review = Review(120.0, other_user.id, shop.id, item.id)
    db_session.add_all([shop, item, target_review, kept_review])
    db_session.commit()

    anonymizeReviewFor(db_session, target_user.id)
    db_session.expire_all()

    assert db_session.get(Review, target_review.id).posterID is None
    assert db_session.get(Review, target_review.id).attributedItemID is not None
    assert db_session.get(Review, target_review.id).attributedShopID is not None
    assert db_session.get(Review, kept_review.id).posterID == other_user.id


def test_deleteReviewFor_deletes_reviews_and_review_fields_for_matching_poster(db_session):
    target_user = create_user(db_session, username="delete-a")
    other_user = create_user(db_session, username="delete-b")
    shop = Shop("Cafe", 42.0, -83.0, target_user.id)
    item = Item("Latte", shop.id, 5.0, target_user.id)
    target_review = Review(100.0, target_user.id, shop.id, item.id)
    kept_review = Review(120.0, other_user.id, shop.id, item.id)
    db_session.add_all([shop, item, target_review, kept_review])
    db_session.commit()

    fields = [
        ReviewField(target_review.id, "body", 0, 5, 4.0, "delete me"),
        ReviewField(target_review.id, "sweetness", 0, 5, 3.0, "delete me too"),
        ReviewField(kept_review.id, "body", 0, 5, 5.0, "keep me"),
    ]
    db_session.add_all(fields)
    db_session.commit()

    deleteReviewFor(db_session, target_user.id)
    db_session.expire_all()

    assert db_session.get(Review, target_review.id) is None
    assert db_session.get(ReviewField, (target_review.id, "body")) is None
    assert db_session.get(ReviewField, (target_review.id, "sweetness")) is None
    assert db_session.get(Review, kept_review.id) is not None
    assert db_session.get(ReviewField, (kept_review.id, "body")) is not None


def test_getUserFromReviewFieldID_returns_user_for_review_parent(db_session):
    user = create_user(db_session, username="commenter")
    shop = Shop("Cafe", 42.0, -83.0, user.id)
    item = Item("Latte", shop.id, 5.0, user.id)
    review = Review(100.0, user.id, shop.id, item.id)
    db_session.add_all([shop, item, review])
    db_session.commit()

    fetched_user = getUserFromReviewFieldID(review.id)

    assert fetched_user is not None
    assert fetched_user.id == user.id


def test_getUsernameFromReviewFieldID_returns_username_and_handles_deleted_user(db_session):
    user = create_user(db_session, username="visible-name")
    shop = Shop("Cafe", 42.0, -83.0, user.id)
    item = Item("Latte", shop.id, 5.0, user.id)
    visible_review = Review(100.0, user.id, shop.id, item.id)
    deleted_review = Review(101.0, None, shop.id, item.id)
    db_session.add_all([shop, item, visible_review, deleted_review])
    db_session.commit()

    assert getUsernameFromReviewFieldID(visible_review.id) == "visible-name"
    assert getUsernameFromReviewFieldID(deleted_review.id) is None


def test_register_template_filters_adds_review_username_filter(app):
    register_template_filters(app)

    assert "usernameFromReviewFieldID" in app.jinja_env.filters
    assert "getUserFromReviewFieldID" in app.jinja_env.filters


def test_usernameIsTaken_detects_presence(db_session):
    create_user(db_session, username="taken-name")

    assert usernameIsTaken(db_session, "taken-name") is True
    assert usernameIsTaken(db_session, "available-name") is False


def test_passwordIsValid_accepts_and_rejects_expected_passwords():
    assert passwordIsValid("Valid1!")
    assert not passwordIsValid("short")
    assert not passwordIsValid("nouppercase1!")
    assert not passwordIsValid("NOLOWERCASE1!")
    assert not passwordIsValid("NoSpecial")
