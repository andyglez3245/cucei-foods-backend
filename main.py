import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from sqlalchemy.orm import Session
from app.db.models import db, Place, MenuItem, Comment
from app.utils import update_place_rating
from flask import send_from_directory

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://postgres:{os.environ["DB_PASSWORD"]}@localhost:5432/cuceifoods'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db.init_app(app)

# -------------------
# Helpers
# -------------------

def get_session():
    return Session(db.engine)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------
# UPLOADS
# -------------------

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -------------------
# PLACES ENDPOINTS
# -------------------

@app.route("/api/places", methods=["GET"])
def get_places():
    session = get_session()
    try:
        category = request.args.get("category")

        query = session.query(Place)
        if category and category.lower() != "all":
            query = query.filter(Place.category == category)

        places = query.all()

        result = []
        for p in places:
            result.append({
                "id": p.id,
                "name": p.name,
                "schedule": p.schedule,
                "category": p.category,
                "image_url": p.image_url,
                "menu": [{"category": m.category, "dish_name": m.dish_name, "price": m.price} for m in p.menu_items],
                "rating": p.rating,
                "num_ratings": p.num_ratings,
                "latest_comment": p.comments[-1].text if p.comments else ""
            })

        return jsonify(result)
    finally:
        session.close()


@app.route("/api/places/<string:place_id>", methods=["GET"])
def get_place(place_id):
    session = get_session()
    try:
        p = session.get(Place, place_id)
        if not p:
            return jsonify({"error": "Place not found"}), 404

        return jsonify({
            "id": p.id,
            "name": p.name,
            "schedule": p.schedule,
            "category": p.category,
            "image_url": p.image_url,
            "menu": [{"category": m.category, "dish_name": m.dish_name, "price": m.price} for m in p.menu_items],
            "rating": p.rating,
            "num_ratings": p.num_ratings
        })
    finally:
        session.close()


@app.route("/api/places", methods=["POST"])
def create_place():
    session = get_session()
    try:
        name = request.form.get("name")
        category = request.form.get("category")

        schedule_raw = request.form.get("schedule", "{}")
        try:
            schedule = json.loads(schedule_raw)
        except:
            schedule = {}

        image_file = request.files.get("image")
        image_url = ""
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            image_url = f"/uploads/{filename}"

        new_place = Place(
            name=name,
            schedule=schedule,
            category=category,
            image_url=image_url
        )

        session.add(new_place)
        session.commit()

        # Menu items
        menu_json = request.form.get("menu", "[]")
        menu_items = json.loads(menu_json)
        for m in menu_items:
            menu_item = MenuItem(
                place_id=new_place.id,
                category=m.get("category"),
                dish_name=m.get("dish_name"),
                price=m.get("price")
            )
            session.add(menu_item)

        session.commit()
        return jsonify({"id": new_place.id}), 201
    finally:
        session.close()


@app.route("/api/places/<string:place_id>", methods=["PUT"])
def update_place(place_id):
    session = get_session()
    try:
        p = session.get(Place, place_id)
        if not p:
            return jsonify({"error": "Place not found"}), 404

        data = request.json
        p.name = data.get("name", p.name)
        p.category = data.get("category", p.category)
        p.image_url = data.get("image_url", p.image_url)

        if "schedule" in data:
            s = data["schedule"]
            if isinstance(s, str):
                try:
                    s = json.loads(s)
                except:
                    s = {}
            p.schedule = s

        # Delete old menu items
        session.query(MenuItem).filter(MenuItem.place_id == p.id).delete(synchronize_session=False)

        for m in data.get("menu", []):
            menu_item = MenuItem(
                place_id=p.id,
                category=m.get("category"),
                dish_name=m.get("dish_name"),
                price=m.get("price")
            )
            session.add(menu_item)

        session.commit()
        return jsonify({"message": "Updated"})
    finally:
        session.close()


@app.route("/api/places/<string:place_id>", methods=["DELETE"])
def delete_place(place_id):
    session = get_session()
    try:
        p = session.get(Place, place_id)
        if not p:
            return jsonify({"error": "Place not found"}), 404

        session.delete(p)
        session.commit()

        return jsonify({"message": "Deleted"})
    finally:
        session.close()


@app.route("/api/places/counts", methods=["GET"])
def get_place_counts():
    session = get_session()
    try:
        counts = {
            "all": session.query(Place).count(),
            "Desayunos y Comidas": session.query(Place).filter(Place.category == "Desayunos y Comidas").count(),
            "Bebidas y Cafetería": session.query(Place).filter(Place.category == "Bebidas y Cafetería").count(),
            "Snacks": session.query(Place).filter(Place.category == "Snacks").count()
        }
        return jsonify(counts)
    finally:
        session.close()


# -------------------
# COMMENTS
# -------------------

@app.route("/api/places/<string:place_id>/comments", methods=["GET"])
def get_comments(place_id):
    session = get_session()
    try:
        place = session.get(Place, place_id)
        if not place:
            return jsonify({"error": "Place not found"}), 404

        return jsonify([{
            "id": c.id,
            "place_id": c.place_id,
            "user_name": c.user_name,
            "user_image": c.user_image,
            "text": c.text,
            "rating": c.rating
        } for c in place.comments])
    finally:
        session.close()


@app.route("/api/places/<string:place_id>/comments", methods=["POST"])
def add_comment(place_id):
    session = get_session()
    try:
        place = session.get(Place, place_id)
        if not place:
            return jsonify({"error": "Place not found"}), 404

        data = request.form

        new_comment = Comment(
            place_id=place_id,
            user_name=data.get("user_name"),
            user_image=data.get("user_image", ""),
            text=data.get("text"),
            rating=int(data.get("rating", 0))
        )

        session.add(new_comment)
        session.commit()  # First commit comment

        # Now update rating
        update_place_rating(session, place)
        session.commit()

        return jsonify({"id": new_comment.id}), 201

    finally:
        session.close()


@app.route("/api/comments/<string:comment_id>", methods=["PUT"])
def update_comment(comment_id):
    session = get_session()
    try:
        c = session.get(Comment, comment_id)
        if not c:
            return jsonify({"error": "Comment not found"}), 404
        data = request.json

        c.text = data.get("text", c.text)
        c.rating = data.get("rating", c.rating)

        session.commit()
        update_place_rating(c.place)
        session.commit()

        return jsonify({"message": "Updated"})
    finally:
        session.close()


@app.route("/api/comments/<string:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    session = get_session()
    try:
        c = session.get(Comment, comment_id)
        if not c:
            return jsonify({"error": "Comment not found"}), 404

        place = c.place
        session.delete(c)
        session.commit()

        update_place_rating(place)
        session.commit()

        return jsonify({"message": "Deleted"})
    finally:
        session.close()


# -------------------
# RUN
# -------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
