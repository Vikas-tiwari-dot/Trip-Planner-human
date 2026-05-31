from flask_socketio import emit, join_room, leave_room, disconnect
from flask_jwt_extended import decode_token
from app_init import db
from models.user import User
from datetime import datetime

connected_users = {}  # {user_id: sid}


def register_events(socketio):

    @socketio.on('connect')
    def handle_connect(auth):
        token = None
        if auth and isinstance(auth, dict):
            token = auth.get('token')
        if not token:
            return False  # Reject connection

        try:
            decoded = decode_token(token)
            user_id = int(decoded['sub'])
            user = User.query.get(user_id)
            if not user:
                return False

            # Join personal room
            join_room(f'user_{user_id}')
            connected_users[user_id] = user_id

            # Update online status
            user.is_online = True
            user.last_seen = datetime.utcnow()
            db.session.commit()

            # Notify others
            emit('user_online', {
                'user_id': user_id,
                'username': user.username,
                'is_online': True
            }, broadcast=True, include_self=False)

            emit('connected', {'status': 'ok', 'user_id': user_id})
            return True

        except Exception as e:
            print(f"Socket connect error: {e}")
            return False

    @socketio.on('disconnect')
    def handle_disconnect():
        from flask import request as flask_request
        # Find user by session
        for uid, sid in list(connected_users.items()):
            user = User.query.get(uid)
            if user:
                user.is_online = False
                user.last_seen = datetime.utcnow()
                db.session.commit()
                del connected_users[uid]
                emit('user_offline', {
                    'user_id': uid,
                    'username': user.username,
                    'is_online': False
                }, broadcast=True)
                break

    @socketio.on('update_location')
    def handle_location_update(data):
        token = data.get('token')
        lat = data.get('lat')
        lng = data.get('lng')

        if not token or lat is None or lng is None:
            return

        try:
            decoded = decode_token(token)
            user_id = int(decoded['sub'])
            user = User.query.get(user_id)
            if user:
                user.latitude = lat
                user.longitude = lng
                user.last_seen = datetime.utcnow()
                db.session.commit()

                # Broadcast location to all
                emit('location_update', {
                    'user_id': user_id,
                    'username': user.username,
                    'lat': lat,
                    'lng': lng,
                    'role': user.role,
                    'profile_image': user.profile_image,
                    'is_online': True
                }, broadcast=True)
        except Exception as e:
            print(f"Location update error: {e}")

    @socketio.on('typing')
    def handle_typing(data):
        token = data.get('token')
        receiver_id = data.get('receiver_id')
        is_typing = data.get('is_typing', False)

        if not token or not receiver_id:
            return

        try:
            decoded = decode_token(token)
            user_id = int(decoded['sub'])
            user = User.query.get(user_id)
            if user:
                emit('user_typing', {
                    'user_id': user_id,
                    'username': user.username,
                    'is_typing': is_typing
                }, room=f'user_{receiver_id}')
        except Exception as e:
            print(f"Typing event error: {e}")

    @socketio.on('send_message')
    def handle_message(data):
        token = data.get('token')
        receiver_id = data.get('receiver_id')
        content = data.get('content', '').strip()

        if not token or not receiver_id or not content:
            return

        try:
            decoded = decode_token(token)
            user_id = int(decoded['sub'])

            from models.message import Message
            message = Message(
                sender_id=user_id,
                receiver_id=receiver_id,
                content=content
            )
            db.session.add(message)
            db.session.commit()

            msg_data = message.to_dict()

            # Send to both sender and receiver rooms
            emit('new_message', msg_data, room=f'user_{receiver_id}')
            emit('new_message', msg_data, room=f'user_{user_id}')

        except Exception as e:
            print(f"Message error: {e}")

    @socketio.on('join_map_room')
    def handle_join_map(data):
        join_room('map_room')
        # Send all current user locations
        users = User.query.filter(User.latitude.isnot(None)).all()
        emit('all_locations', {
            'users': [u.to_dict() for u in users]
        })

    @socketio.on('leave_map_room')
    def handle_leave_map():
        leave_room('map_room')

    @socketio.on('ping_location')
    def handle_ping(data):
        """Periodic location ping from client."""
        token = data.get('token')
        if not token:
            return
        try:
            decoded = decode_token(token)
            user_id = int(decoded['sub'])
            user = User.query.get(user_id)
            if user:
                user.last_seen = datetime.utcnow()
                user.is_online = True
                db.session.commit()
        except Exception:
            pass
