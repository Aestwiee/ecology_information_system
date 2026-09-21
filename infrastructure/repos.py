import sqlite3 
from datetime import datetime
from domain.models import EcoPoint, Review

class EcoPointsRepo():
    def get_points(self):
        conn = sqlite3.connect('ecology.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM eco_points")
        db_points = cursor.fetchall()

        points_list = []

        for p in db_points:
            cursor.execute("SELECT status, created_at FROM reviews WHERE point_id = ?", (p['id'],))
            db_reviews = cursor.fetchall()

            reviews_list = []
            for rev in db_reviews:
                time_obj = datetime.fromisoformat(rev['created_at'])
                new_review = Review(status=rev['status'], created_at=time_obj)
                reviews_list.append(new_review)

            point_obj = EcoPoint(p['id'], p['name'], p['address'], p['latitude'], p['longitude'], p['wastes'].split(","), reviews_list)
            points_list.append(point_obj)
        conn.close()
        return points_list