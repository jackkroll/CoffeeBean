from traceback import print_stack

from sqlalchemy.exc import IntegrityError
from helpers import *
from models import *
from flask import Flask, send_from_directory, request, Response, redirect, url_for, render_template, session
from flask_sqlalchemy import SQLAlchemy
from extensions import db
from sqlalchemy.orm import DeclarativeBase
from flask_cors import CORS
import os
from dotenv import load_dotenv
from flask_login import login_user, current_user, logout_user, login_required

load_dotenv()
app = Flask(__name__, template_folder='doc')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.secret_key = os.getenv("FLASK_SECRET")
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
db.init_app(app)
CORS(app); #fix later as this is bad practice

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

@login_manager.request_loader
def request_loader(request):
    id = request.form.get("id")
    if id is None:
        return None
    return db.session.get(User, id)
@app.route("/")
def landing_page():
    return render_template("landing.html")

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
        if shop is None:
            return Response("Shop does not exist", status=500, mimetype='application/json')
        else:
            shopItems = shop.fetchItems(db.session)
            avgList = dict()
            reviewType = "bitterness"
            for item in shopItems:
                avgList[item] = getItemAverageRating(item, reviewType)
            print(avgList)
            return render_template("viewshop.html", shop = shop, shopItems = shopItems, avgList = avgList)

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
    shopReviews = fetchFieldsFor(db.session, shopId = shop.id, itemId= item.id, type = "bitterness")
    distribution, avg, revCount = getReviewStatistics(shopReviews)
    return render_template("review.html", item = item, shop = shop, shopReviews = shopReviews, averageRating = avg, dist = distribution, revCount = revCount)

@app.route("/review", methods=["POST"])
@login_required
def add_review():
    posterID = current_user.id
    shopID = request.form.get("shopID")
    itemID = request.form.get("itemID")
    fieldName = "bitterness"
    lowerRange = 0
    upperRange = 5
    value = request.form.get("value")
    comment = request.form.get("comment")
    try:
        value = float(value)
    except ValueError:
        return Response("Value must be numerical", status=400, mimetype='application/json')
    if value < lowerRange or value > upperRange:
        return Response("Value out of range", status=400, mimetype='application/json')
    review = Review.fromString(posterID, shopID, itemID)
    reviewField = ReviewField.fromString(review.id, fieldName, str(lowerRange), str(upperRange), str(value), comment)
    try:
        db.session.add(review)
        db.session.add(reviewField)
        db.session.commit()
    except IntegrityError:
        return Response("Error Adding Review to DB", status=500, mimetype='application/json')
    return redirect(url_for("review", shopID = shopID, itemID = itemID,shopReviews = fetchFieldsFor(db.session, shopId = shopID, itemId= itemID, type = "bitterness")) )

@app.route("/shop/delete", methods = ["POST"])
@login_required
def delete_shop():
    try:
        shopID = request.form.get("shopID")
        shop = fetchShopById(db.session, shopID)
        db.session.delete(shop)
        db.session.commit()
    except IntegrityError:
        return Response("Error Deleting Shop from DB", status=500, mimetype='application/json')
    return redirect(url_for("shops"))
@app.route("/shop/add", methods=["GET", "POST"])
@login_required
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
            newShop = Shop.fromStrings(shopName, shopLatRaw, shopLonRaw, current_user.id)
            if newShop is None:
                return Response("Fields invalid", status=400, mimetype='application/json')
            try:
                db.session.add(newShop)
                db.session.commit()
                return redirect(url_for("shops"))
            except Exception as e:
                return Response("Error saving to database", status=500, mimetype='application/json')

@app.route("/shop/add-item", methods=["POST"])
@login_required
def add_item():
    shopID = request.form.get("shopID")
    itemName = request.form.get("itemName")
    itemPrice = request.form.get("itemPrice")
    if itemName == '' or shopID == '':
        return Response("Not all fields returned", status=400, mimetype='application/json')
    else:
        newItem = Item.fromStrings(shopID, itemName, itemPrice, current_user.id)
        if newItem is None:
            return Response("Fields invalid", status=400, mimetype='application/json')
        try:
            db.session.add(newItem)
            db.session.commit()
            return redirect(url_for("shops", shopID = newItem.shopID))
        except IntegrityError as e:
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

@app.route("/api/username-taken", methods=["GET"])
def username_taken():
    username = request.args.get("username")
    if username is None:
        return Response("No username provided", status=400, mimetype='application/json')
    else:
        isTaken = usernameIsTaken(db.session, username)
        return Response(str(isTaken), status=200, mimetype='application/json')

@app.route("/api/password-valid", methods=["GET"])
def password_valid():
    # Must have 6 characters, 1 uppercase, 1 lowercase, and one symbol/number
    password = request.args.get("password")
    if password is None:
        return Response("No password provided", status=400, mimetype='application/json')
    else:
        isValid = passwordIsValid(password)
        return Response(str(isValid), status=200, mimetype='application/json')

@app.route("/create-account", methods =["GET", "POST"])
def create_account():
    if request.method == "GET":
        returnTo = request.args.get("returnTo")
        if current_user.is_authenticated:
            if returnTo is None:
                return redirect(url_for("landing_page"))
            else:
                return redirect(returnTo)
        return render_template("create-account.html", returnTo = returnTo)
    else:
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        returnTo = request.form.get("returnTo")
        if username is None or email is None or password is None:
            return Response("Fields invalid", status=400, mimetype='application/json')
        if not passwordIsValid(password):
            return Response("Password must contain at least 6 characters, 1 uppercase, 1 lowercase, and one symbol/number", status=400, mimetype='application/json')
        user = User.fromStrings(username, email, password)
        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
        except IntegrityError as e:
            return Response("Username already taken", status=400, mimetype='application/json')
        if returnTo is None:
            return redirect(url_for("landing_page"))
        else:
            return redirect(returnTo)

@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "GET":
        returnTo = request.args.get("returnTo")
        if current_user.is_authenticated:
            if returnTo is None:
                return redirect(url_for("landing_page"))
            else:
                return redirect(returnTo)
        return render_template("login.html", returnTo = returnTo)
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        returnTo = request.form.get("returnTo")
        if username is None or password is None:
            return Response("Fields invalid", status=400, mimetype='application/json')
        user = loginUser(db.session, username, password)
        if user is None:
            return Response("Username or Password incorrect", status=400, mimetype='application/json')
        else:
            login_user(user)
            if returnTo is None:
                return redirect(url_for("landing_page"))
            else:
                return redirect(returnTo)
@app.route('/change-password', methods = ["GET", "POST"])
@login_required
def change_password():
    if request.method == "GET":
        return send_from_directory("doc", "change-password.html")
    else:
        oldPassword = request.form.get("oldPassword")
        newPassword = request.form.get("newPassword")
        newPasswordConf = request.form.get("newPasswordConf")
        print(oldPassword, newPassword, newPasswordConf)
        if oldPassword == None or newPassword == None or newPasswordConf == None:
            return Response("Fields invalid", status=400, mimetype='application/json')
        if newPassword != newPasswordConf:
            return Response("Passwords don't match", status=400, mimetype='application/json')
        if loginUser(db.session, current_user.username, oldPassword) == None:
            return Response("Incorrect old password", status=400, mimetype='application/json')
        else:
            current_user.changePassword(newPassword)
            db.session.commit()
            return redirect(url_for("landing_page"))

@app.route('/delete-account', methods = ["GET", "POST"])
@login_required
def delete_account():
    if request.method == "GET":
        return send_from_directory("doc", "delete-account.html")
    else:
        password = request.form.get("password")
        cleanupPref = request.form.get("contentCleanup")
        if password is None:
            return Response("Password not provided", status=400, mimetype='application/json')
        if cleanupPref is None:
            return Response("Post deletion content preference not provided", status=400, mimetype='application/json')
        if loginUser(db.session, current_user.username, password) == None:
            return Response("Password Incorrect", status=400, mimetype='application/json')
        db.session.delete(current_user)
        wipeShopAndItemPoster(db.session, current_user.id)
        if cleanupPref == "anonymize":
            anonymizeReviewFor(db.session, current_user.id)
        else:
            deleteReviewFor(db.session, current_user.id)
        return redirect(url_for("landing_page"))

@app.route("/logout", methods = ["GET"])
def logout():
    logout_user()
    return "ok!"
@app.route("/protected")
@login_required
def protected():
    return "logged in as:" + flask_login.current_user.id

@app.errorhandler(401)
def unauthorized_page(e):
    return (render_template("401.html",
                           loginURL = url_for("login", returnTo = request.url),
                           signupURL = url_for("create_account", returnTo = request.url)),
            401)



if __name__ == "__main__":
    app.run(debug=True)
