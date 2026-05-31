from datetime import datetime
from app_init import db


class Trip(db.Model):
    __tablename__ = 'trips'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_location = db.Column(db.String(300), nullable=False)
    destination = db.Column(db.String(300), nullable=True)
    start_lat = db.Column(db.Float, nullable=True)
    start_lng = db.Column(db.Float, nullable=True)
    end_lat = db.Column(db.Float, nullable=True)
    end_lng = db.Column(db.Float, nullable=True)
    distance = db.Column(db.Float, nullable=True)  # in km
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='active')  # active, completed, cancelled
    notes = db.Column(db.Text, nullable=True)
    route_data = db.Column(db.Text, nullable=True)  # JSON route data

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'start_location': self.start_location,
            'destination': self.destination,
            'start_lat': self.start_lat,
            'start_lng': self.start_lng,
            'end_lat': self.end_lat,
            'end_lng': self.end_lng,
            'distance': self.distance,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'notes': self.notes,
        }

    def __repr__(self):
        return f'<Trip {self.id} by user {self.user_id}>'
