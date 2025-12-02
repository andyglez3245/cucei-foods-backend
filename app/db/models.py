import uuid
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB

db = SQLAlchemy()

class Place(db.Model):
    __tablename__ = 'places'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)

    # JSON schedule instead of string
    schedule = db.Column(JSONB, nullable=False)

    category = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(300), default='')
    rating = db.Column(db.Float, default=0.0)
    num_ratings = db.Column(db.Integer, default=0)

    menu_items = db.relationship("MenuItem", backref="place", cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="place", cascade="all, delete-orphan")

class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    place_id = db.Column(db.String(36), db.ForeignKey('places.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    dish_name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    place_id = db.Column(db.String(36), db.ForeignKey('places.id'), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    user_image = db.Column(db.String(300), default='')
    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=0)
