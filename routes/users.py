from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app_init import db
from models.user import User
from services.route_service import haversine_distance
from datetime import datetime

users_bp = Blueprint('users', __name__)


@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    users = User.query.all()
    return jsonify({'users': [u.to_dict() for u in users]}), 200


@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({'user': user.to_dict()}), 200


@users_bp.route('/guides', methods=['GET'])
@jwt_required()
def get_guides():
    guides = User.query.filter_by(role='guide').all()
    return jsonify({'guides': [g.to_dict() for g in guides]}), 200


@users_bp.route('/nearby', methods=['GET'])
@jwt_required()
def get_nearby():
    user_id = int(get_jwt_identity())
    current_user = User.query.get(user_id)
    if not current_user or not current_user.latitude:
        return jsonify({'error': 'Location not available'}), 400

    radius = float(request.args.get('radius', 50))
    role_filter = request.args.get('role', None)

    query = User.query.filter(User.id != user_id, User.latitude.isnot(None))
    if role_filter:
        query = query.filter_by(role=role_filter)

    all_users = query.all()
    nearby = []
    for u in all_users:
        dist = haversine_distance(
            current_user.latitude, current_user.longitude,
            u.latitude, u.longitude
        )
        if dist <= radius:
            user_dict = u.to_dict()
            user_dict['distance_km'] = round(dist, 2)
            nearby.append(user_dict)

    nearby.sort(key=lambda x: x['distance_km'])
    return jsonify({'nearby': nearby, 'count': len(nearby)}), 200


@users_bp.route('/update-location', methods=['POST'])
@jwt_required()
def update_location():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    lat = data.get('latitude')
    lng = data.get('longitude')

    if lat is None or lng is None:
        return jsonify({'error': 'Latitude and longitude required'}), 400

    old_lat, old_lng = user.latitude, user.longitude
    user.update_location(lat, lng)

    # Check for trip detection
    if old_lat and old_lng:
        from services.trip_monitor import TripMonitor
        TripMonitor.check_trip(user_id, old_lat, old_lng, lat, lng)

    return jsonify({'message': 'Location updated'}), 200


@users_bp.route('/online', methods=['GET'])
@jwt_required()
def get_online_users():
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(minutes=5)
    users = User.query.filter(User.last_seen >= cutoff).all()
    return jsonify({'users': [u.to_dict() for u in users], 'count': len(users)}), 200
