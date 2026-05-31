from datetime import datetime
from app_init import db, bcrypt


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    profile_image = db.Column(db.String(256), default='default_avatar.png')
    role = db.Column(db.String(20), default='traveler')  # traveler or guide
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_online = db.Column(db.Boolean, default=False)
    bio = db.Column(db.Text, nullable=True)
    location_name = db.Column(db.String(200), nullable=True)

    # Guide-specific fields
    expertise = db.Column(db.String(300), nullable=True)
    languages = db.Column(db.String(200), nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    hourly_rate = db.Column(db.Float, nullable=True)

    # Relationships
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy='dynamic')
    trips = db.relationship('Trip', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def update_location(self, lat, lng):
        self.latitude = lat
        self.longitude = lng
        self.last_seen = datetime.utcnow()
        db.session.commit()

    def to_dict(self, include_private=False):
        data = {
            'id': self.id,
            'username': self.username,
            'profile_image': self.profile_image,
            'role': self.role,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_online': self.is_online,
            'bio': self.bio,
            'location_name': self.location_name,
            'expertise': self.expertise,
            'languages': self.languages,
            'is_available': self.is_available,
            'hourly_rate': self.hourly_rate,
        }
        if include_private:
            data['email'] = self.email
        return data

    def __repr__(self):
        return f'<User {self.username}>'
