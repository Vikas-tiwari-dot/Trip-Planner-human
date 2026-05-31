from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app_init import db
from models.trip import Trip
from datetime import datetime

trips_bp = Blueprint('trips', __name__)


@trips_bp.route('/', methods=['GET'])
@jwt_required()
def get_trips():
    user_id = int(get_jwt_identity())
    trips = Trip.query.filter_by(user_id=user_id).order_by(Trip.start_time.desc()).all()
    return jsonify({'trips': [t.to_dict() for t in trips]}), 200


@trips_bp.route('/<int:trip_id>', methods=['GET'])
@jwt_required()
def get_trip(trip_id):
    user_id = int(get_jwt_identity())
    trip = Trip.query.filter_by(id=trip_id, user_id=user_id).first_or_404()
    return jsonify({'trip': trip.to_dict()}), 200


@trips_bp.route('/', methods=['POST'])
@jwt_required()
def create_trip():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    trip = Trip(
        user_id=user_id,
        start_location=data.get('start_location', 'Unknown'),
        destination=data.get('destination'),
        start_lat=data.get('start_lat'),
        start_lng=data.get('start_lng'),
        end_lat=data.get('end_lat'),
        end_lng=data.get('end_lng'),
        distance=data.get('distance'),
        notes=data.get('notes'),
    )
    db.session.add(trip)
    db.session.commit()
    return jsonify({'trip': trip.to_dict()}), 201


@trips_bp.route('/<int:trip_id>', methods=['PUT'])
@jwt_required()
def update_trip(trip_id):
    user_id = int(get_jwt_identity())
    trip = Trip.query.filter_by(id=trip_id, user_id=user_id).first_or_404()
    data = request.get_json()

    allowed = ['destination', 'end_lat', 'end_lng', 'distance', 'status', 'notes', 'route_data']
    for field in allowed:
        if field in data:
            setattr(trip, field, data[field])

    if data.get('status') == 'completed' and not trip.end_time:
        trip.end_time = datetime.utcnow()

    db.session.commit()
    return jsonify({'trip': trip.to_dict()}), 200


@trips_bp.route('/<int:trip_id>', methods=['DELETE'])
@jwt_required()
def delete_trip(trip_id):
    user_id = int(get_jwt_identity())
    trip = Trip.query.filter_by(id=trip_id, user_id=user_id).first_or_404()
    db.session.delete(trip)
    db.session.commit()
    return jsonify({'message': 'Trip deleted'}), 200


@trips_bp.route('/active', methods=['GET'])
@jwt_required()
def get_active_trip():
    user_id = int(get_jwt_identity())
    trip = Trip.query.filter_by(user_id=user_id, status='active').first()
    if trip:
        return jsonify({'trip': trip.to_dict()}), 200
    return jsonify({'trip': None}), 200
