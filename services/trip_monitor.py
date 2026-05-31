from services.route_service import haversine_distance, RouteService
from app_init import db
from models.trip import Trip
import os


class TripMonitor:
    THRESHOLD_KM = float(os.environ.get('TRIP_THRESHOLD_KM', 50))

    @staticmethod
    def check_trip(user_id, old_lat, old_lng, new_lat, new_lng):
        """Check if user has traveled beyond threshold and record trip."""
        distance = haversine_distance(old_lat, old_lng, new_lat, new_lng)

        if distance >= TripMonitor.THRESHOLD_KM:
            # Check if there's an active trip
            active_trip = Trip.query.filter_by(user_id=user_id, status='active').first()

            if active_trip:
                # Update existing trip
                active_trip.end_lat = new_lat
                active_trip.end_lng = new_lng
                if active_trip.distance:
                    active_trip.distance += distance
                else:
                    active_trip.distance = distance
                db.session.commit()
            else:
                # Create new trip
                start_name = RouteService.reverse_geocode(old_lat, old_lng)
                trip = Trip(
                    user_id=user_id,
                    start_location=start_name,
                    start_lat=old_lat,
                    start_lng=old_lng,
                    end_lat=new_lat,
                    end_lng=new_lng,
                    distance=distance,
                    status='active'
                )
                db.session.add(trip)
                db.session.commit()

                # Emit notification
                from app_init import socketio
                socketio.emit('trip_detected', {
                    'message': f'New trip detected! You have traveled {distance:.1f} km',
                    'trip_id': trip.id,
                    'distance': distance
                }, room=f'user_{user_id}')

                return trip

        return None

    @staticmethod
    def complete_trip(trip_id, user_id):
        """Mark a trip as completed."""
        from datetime import datetime
        trip = Trip.query.filter_by(id=trip_id, user_id=user_id).first()
        if trip:
            trip.status = 'completed'
            trip.end_time = datetime.utcnow()
            # Get destination name
            if trip.end_lat and trip.end_lng:
                trip.destination = RouteService.reverse_geocode(trip.end_lat, trip.end_lng)
            db.session.commit()
            return trip
        return None
