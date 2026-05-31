from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from services.route_service import RouteService
import io

maps_bp = Blueprint('maps', __name__)


@maps_bp.route('/users', methods=['GET'])
@jwt_required()
def get_map_users():
    """Get all users with location for map display."""
    users = User.query.filter(User.latitude.isnot(None)).all()
    return jsonify({
        'users': [u.to_dict() for u in users]
    }), 200


@maps_bp.route('/geocode', methods=['GET'])
@jwt_required()
def geocode():
    """Geocode an address using Nominatim."""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400

    result = RouteService.geocode(query)
    if result:
        return jsonify(result), 200
    return jsonify({'error': 'Location not found'}), 404


@maps_bp.route('/route', methods=['POST'])
@jwt_required()
def get_route():
    """Get route between two points using OSRM."""
    data = request.get_json()
    start_lat = data.get('start_lat')
    start_lng = data.get('start_lng')
    end_lat = data.get('end_lat')
    end_lng = data.get('end_lng')
    profile = data.get('profile', 'driving')

    if not all([start_lat, start_lng, end_lat, end_lng]):
        return jsonify({'error': 'All coordinates required'}), 400

    result = RouteService.get_route(start_lat, start_lng, end_lat, end_lng, profile)
    if result:
        return jsonify(result), 200
    return jsonify({'error': 'Could not calculate route'}), 500


@maps_bp.route('/folium', methods=['POST'])
@jwt_required()
def generate_folium_map():
    """Generate a Folium map and return as HTML."""
    data = request.get_json()
    center_lat = data.get('lat', 20.5937)
    center_lng = data.get('lng', 78.9629)
    markers = data.get('markers', [])
    route_coords = data.get('route', None)

    from services.route_service import RouteService
    map_html = RouteService.generate_folium_map(center_lat, center_lng, markers, route_coords)

    return jsonify({'map_html': map_html}), 200


@maps_bp.route('/nearby-places', methods=['GET'])
@jwt_required()
def nearby_places():
    """Search for nearby places using Nominatim."""
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    category = request.args.get('category', 'tourism')
    radius = request.args.get('radius', 5000, type=int)

    if not lat or not lng:
        return jsonify({'error': 'Coordinates required'}), 400

    places = RouteService.nearby_places(lat, lng, category, radius)
    return jsonify({'places': places}), 200
