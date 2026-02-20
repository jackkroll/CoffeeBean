from extensions import db
from models import *

def fetchAllShops(db : db.session) -> [Shop]:
    allShops = db.query(Shop).all()
    return allShops

def fetchShopById(db : db.session, shopId: str) -> Shop | None:
    shop = db.query(Shop).get(shopId)
    return shop if shop else None
