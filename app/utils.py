# utils.py
from app.db.models import Comment

def update_place_rating(session, place):
    # Get all ratings for that place
    ratings = (
        session.query(Comment.rating)
        .filter(Comment.place_id == place.id)
        .all()
    )

    # No ratings?
    if not ratings:
        place.rating = 0.0
        place.num_ratings = 0
        return

    # Extract integers from tuples
    rating_values = [r[0] for r in ratings]

    # Update place values
    place.num_ratings = len(rating_values)
    place.rating = sum(rating_values) / place.num_ratings
