from models import Shop, Item, Review, ReviewField


def test_shop_fromStrings_valid():
    shop = Shop.fromStrings("Cafe", "45.0", "-93.0")
    assert shop is not None
    assert shop.name == "Cafe"
    assert shop.lat == 45.0
    assert shop.lon == -93.0


def test_shop_fromStrings_invalid_coordinates():
    assert Shop.fromStrings("Cafe", "95", "0") is None
    assert Shop.fromStrings("Cafe", "0", "190") is None


def test_shop_fromStrings_missing_fields():
    assert Shop.fromStrings("Cafe", "", "-93.0") is None
    assert Shop.fromStrings("Cafe", "45.0", "") is None


def test_item_fromStrings_optional_price():
    item = Item.fromStrings("shop-1", "Latte", "")
    assert item is not None
    assert item.price is None


def test_item_fromStrings_negative_price():
    assert Item.fromStrings("shop-1", "Latte", "-1") is None


def test_review_fromString_requires_fields():
    assert Review.fromString("", "shop-1", "item-1") is None
    assert Review.fromString("user-1", "", "item-1") is None
    assert Review.fromString("user-1", "shop-1", "") is None


def test_reviewfield_fromString_casts_types():
    field = ReviewField.fromString("review-1", "bitterness", "0", "5", "3.5", "ok")
    assert field is not None
    assert field.lowerRange == 0
    assert field.upperRange == 5
    assert field.value == 3.5


def test_reviewField_fromString_range_values():
    field = ReviewField.fromString("parentShop", "bitterness", "10", "0", "3", "ok")
    assert field is None
    field = ReviewField.fromString("parentShop", "bitterness", "0", "10", "11", "ok")
    assert field is None


