# models.py
import uuid

class Place:
    def __init__(self, name, category, image_url, menu=[]):
        self.id = str(uuid.uuid4())
        self.name = name
        self.category = category
        self.image_url = image_url
        self.menu = menu  # list of {"categoria": ..., "platillo": ..., "precio": ...}
        self.rating = 0.0       # average rating
        self.num_ratings = 0    # number of ratings

class Comment:
    def __init__(self, place_id, user_name, user_image, text, rating=0):
        self.id = str(uuid.uuid4())
        self.place_id = place_id
        self.user_name = user_name
        self.user_image = user_image
        self.text = text
        self.rating = rating
