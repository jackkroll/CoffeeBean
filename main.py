from traceback import print_stack
from helpers import *
from models import *
from flask import Flask, send_from_directory, request, Response, redirect, url_for, render_template, session
from flask_sqlalchemy import SQLAlchemy
from extensions import db
from sqlalchemy.orm import DeclarativeBase
from flask_cors import CORS
app = Flask(__name__, template_folder='doc')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)
CORS(app); #fix later as this is bad practice

with app.app_context():
    db.create_all()
@app.route("/")
def landing_page():
    return "Landing Page!"

@app.route("/shop")
def shops():
    shopID = request.args.get("shopID")
    if not shopID:
        output = ""
        shops : [Shop] = fetchAllShops(db.session())
        for shop in shops:
            output += f"""<a href="{url_for("shops", shopID = shop.id)}">{shop.name}</a><br>"""
        return output
    else:
        shop = fetchShopById(db.session, shopID)
        return render_template("viewshop.html", shop = shop, shopItems = shop.fetchItems(db.session))

@app.route("/map")
def map():
    return render_template("map.html")

@app.route("/review/<shopID>")
def review(shopID):
    itemID = request.args.get("itemID")
    shop = fetchShopById(db.session, shopID)
    item = fetchItemById(db.session, itemID)
    if shop == None or item == None or item.shopID != shopID:
        return Response("Item and Shop Mismatch", status=400, mimetype='application/json')
    return render_template("review.html", item = item, shop = shop, shopReviews = fetchReviews(db.session, shopId = shop.id, itemId= item.id))

@app.route("/review", methods=["POST"])
def add_review():
    posterID = "0"
    shopID = request.form.get("shopID")
    itemID = request.form.get("itemID")
    fieldName = "bitterness"
    lowerRange = "0"
    upperRange = "5"
    value = request.form.get("value")
    comment = request.form.get("comment")

    review = Review.fromString(posterID, shopID, itemID)
    reviewField = ReviewField.fromString(review.id, fieldName, lowerRange, upperRange, value, comment)

    db.session.add(review)
    db.session.add(reviewField)
    db.session.commit()
    return redirect(url_for("review", shopID = shopID, itemID = itemID,shopReviews = fetchReviews(db.session, shopId = shopID, itemId= itemID)) )

@app.route("/shop/delete", methods = ["POST"])
def delete_shop():
    shopID = request.form.get("shopID")
    shop = fetchShopById(db.session, shopID)
    db.session.delete(shop)
    db.session.commit()
    return redirect(url_for("shops"))
@app.route("/shop/add", methods=["GET", "POST"])
def add_shop():
    if request.method == "GET":
        return send_from_directory("doc", "addshop.html")
    else:
        shopName = request.form.get("shopName")
        shopLatRaw = request.form.get("shopLat")
        shopLonRaw = request.form.get("shopLon")
        if shopName is None or shopLatRaw is None or shopLonRaw is None:
            return Response("Not all fields returned", status=400, mimetype='application/json')
        else:
            newShop = Shop.fromStrings(shopName, shopLatRaw, shopLonRaw)
            if newShop is None:
                return Response("Fields invalid", status=400, mimetype='application/json')
            try:
                db.session.add(newShop)
                db.session.commit()
                return redirect(url_for("shops"))
            except Exception as e:
                return Response("Error saving to database", status=500, mimetype='application/json')

@app.route("/shop/add-item", methods=["POST"])
def add_item():
    shopID = request.form.get("shopID")
    itemName = request.form.get("itemName")
    itemPrice = request.form.get("itemPrice")
    if itemName == '' or shopID == '':
        return Response("Not all fields returned", status=400, mimetype='application/json')
    else:
        newItem = Item.fromStrings(shopID, itemName, itemPrice)
        if newItem is None:
            return Response("Fields invalid", status=400, mimetype='application/json')
        try:
            db.session.add(newItem)
            db.session.commit()
            return redirect(url_for("shops", shopID = newItem.shopID))
        except Exception as e:
            print(e)
            return Response("Error saving to database", status=500, mimetype='application/json')

@app.route("/api/locationsearch", methods=["GET"])
def location_fetch():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
    except ValueError as e:
        return Response("Fields invalid", status=400, mimetype='application/json')
    maxDist = request.args.get("maxDist")
    minDist = request.args.get("minDist")
    if maxDist == '':
        maxDist = None
    else:
        maxDist = int(maxDist)
    if minDist == '':
        minDist = None
    if maxDist is not None and minDist is not None and maxDist < minDist:
        return Response("Fields invalid", status=400, mimetype='application/json')
    distanceShops = fetchShopsByDistance(db.session, lat, lon, maxDist, minDist)
    jsonText = encode_shops_by_dist(distanceShops)
    return Response(jsonText, status=200, mimetype='application/json')

if __name__ == "__main__":
    app.run(debug=True)
