import math
import requests
import folium
import json
from io import StringIO


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate geodesic distance between two points in km."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class RouteService:
    NOMINATIM_URL = 'https://nominatim.openstreetmap.org'
    OSRM_URL = 'https://router.project-osrm.org'
    OVERPASS_URL = 'https://overpass-api.de/api/interpreter'

    HEADERS = {
        'User-Agent': 'Pathick-TravelApp/1.0 (contact@pathick.app)'
    }

    @staticmethod
    def geocode(query):
        """Geocode an address to coordinates."""
        try:
            url = f"{RouteService.NOMINATIM_URL}/search"
            params = {
                'q': query,
                'format': 'json',
                'limit': 5,
                'addressdetails': 1
            }
            resp = requests.get(url, params=params, headers=RouteService.HEADERS, timeout=10)
            data = resp.json()
            if data:
                results = []
                for item in data:
                    results.append({
                        'lat': float(item['lat']),
                        'lng': float(item['lon']),
                        'display_name': item['display_name'],
                        'type': item.get('type', ''),
                        'importance': item.get('importance', 0)
                    })
                return {'results': results}
        except Exception as e:
            print(f"Geocode error: {e}")
        return None

    @staticmethod
    def reverse_geocode(lat, lng):
        """Reverse geocode coordinates to address."""
        try:
            url = f"{RouteService.NOMINATIM_URL}/reverse"
            params = {'lat': lat, 'lon': lng, 'format': 'json'}
            resp = requests.get(url, params=params, headers=RouteService.HEADERS, timeout=10)
            data = resp.json()
            return data.get('display_name', f'{lat}, {lng}')
        except Exception:
            return f'{lat}, {lng}'

    @staticmethod
    def get_route(start_lat, start_lng, end_lat, end_lng, profile='driving'):
        """Get route using OSRM."""
        profile_map = {'driving': 'car', 'walking': 'foot', 'cycling': 'bike'}
        osrm_profile = profile_map.get(profile, 'car')

        try:
            url = f"{RouteService.OSRM_URL}/route/v1/{osrm_profile}/{start_lng},{start_lat};{end_lng},{end_lat}"
            params = {
                'overview': 'full',
                'geometries': 'geojson',
                'steps': 'true',
                'annotations': 'false'
            }
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()

            if data.get('code') == 'Ok' and data.get('routes'):
                route = data['routes'][0]
                coords = route['geometry']['coordinates']
                # OSRM returns [lng, lat] - convert to [lat, lng]
                waypoints = [[c[1], c[0]] for c in coords]

                steps = []
                for leg in route.get('legs', []):
                    for step in leg.get('steps', []):
                        maneuver = step.get('maneuver', {})
                        steps.append({
                            'instruction': step.get('name', ''),
                            'maneuver_type': maneuver.get('type', ''),
                            'maneuver_modifier': maneuver.get('modifier', ''),
                            'distance': round(step.get('distance', 0) / 1000, 2),
                            'duration': round(step.get('duration', 0) / 60, 1)
                        })

                return {
                    'distance_km': round(route['distance'] / 1000, 2),
                    'duration_min': round(route['duration'] / 60, 1),
                    'waypoints': waypoints,
                    'steps': steps
                }
        except Exception as e:
            print(f"Route error: {e}")

        # Fallback: straight line
        dist = haversine_distance(start_lat, start_lng, end_lat, end_lng)
        return {
            'distance_km': round(dist, 2),
            'duration_min': round(dist * 2, 1),
            'waypoints': [[start_lat, start_lng], [end_lat, end_lng]],
            'steps': [{'instruction': 'Head to destination', 'distance': dist, 'duration': dist * 2}],
            'fallback': True
        }

    @staticmethod
    def generate_folium_map(center_lat, center_lng, markers=None, route_coords=None):
        """Generate a Folium map and return HTML string."""
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=12,
            tiles='OpenStreetMap'
        )

        if markers:
            for marker in markers:
                lat = marker.get('lat')
                lng = marker.get('lng')
                popup = marker.get('popup', '')
                icon_color = marker.get('color', 'blue')
                icon = marker.get('icon', 'user')

                folium.Marker(
                    location=[lat, lng],
                    popup=folium.Popup(popup, max_width=200),
                    icon=folium.Icon(color=icon_color, icon=icon, prefix='fa')
                ).add_to(m)

        if route_coords and len(route_coords) >= 2:
            folium.PolyLine(
                locations=route_coords,
                color='#3b82f6',
                weight=4,
                opacity=0.8,
                tooltip='Route'
            ).add_to(m)

            # Start and end markers
            folium.Marker(
                location=route_coords[0],
                popup='Start',
                icon=folium.Icon(color='green', icon='play', prefix='fa')
            ).add_to(m)
            folium.Marker(
                location=route_coords[-1],
                popup='End',
                icon=folium.Icon(color='red', icon='flag', prefix='fa')
            ).add_to(m)

        html_str = m._repr_html_()
        return html_str

    @staticmethod
    def nearby_places(lat, lng, category='tourism', radius=5000):
        """Search for nearby places using Overpass API."""
        try:
            category_map = {
                'tourism': 'tourism',
                'food': 'amenity',
                'hotel': 'tourism',
                'hospital': 'amenity',
                'atm': 'amenity',
            }
            tag = category_map.get(category, 'tourism')

            query = f"""
            [out:json][timeout:25];
            (
              node["{tag}"](around:{radius},{lat},{lng});
              way["{tag}"](around:{radius},{lat},{lng});
            );
            out body 20;
            """
            resp = requests.post(
                RouteService.OVERPASS_URL,
                data={'data': query},
                timeout=20
            )
            data = resp.json()
            places = []
            for el in data.get('elements', [])[:20]:
                tags = el.get('tags', {})
                place_lat = el.get('lat') or (el.get('center', {}) or {}).get('lat')
                place_lng = el.get('lon') or (el.get('center', {}) or {}).get('lon')
                name = tags.get('name', 'Unknown Place')
                if place_lat and place_lng and name != 'Unknown Place':
                    dist = haversine_distance(lat, lng, place_lat, place_lng)
                    places.append({
                        'name': name,
                        'lat': place_lat,
                        'lng': place_lng,
                        'type': tags.get(tag, category),
                        'distance_km': round(dist, 2),
                        'tags': {k: v for k, v in tags.items() if k in ['website', 'phone', 'opening_hours', 'description']}
                    })

            places.sort(key=lambda x: x['distance_km'])
            return places
        except Exception as e:
            print(f"Nearby places error: {e}")
            return []
