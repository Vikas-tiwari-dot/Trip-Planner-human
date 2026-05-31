from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app_init import db
from models.message import Message
from models.user import User
from sqlalchemy import or_, and_

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/messages/<int:other_user_id>', methods=['GET'])
@jwt_required()
def get_messages(other_user_id):
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.receiver_id == user_id)
        )
    ).order_by(Message.timestamp.asc()).paginate(page=page, per_page=per_page, error_out=False)

    # Mark as read
    Message.query.filter(
        Message.sender_id == other_user_id,
        Message.receiver_id == user_id,
        Message.read_status == False
    ).update({'read_status': True})
    db.session.commit()

    return jsonify({
        'messages': [m.to_dict() for m in messages.items],
        'total': messages.total,
        'pages': messages.pages,
        'current_page': page
    }), 200


@chat_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    receiver_id = data.get('receiver_id')
    content = data.get('content', '').strip()

    if not receiver_id or not content:
        return jsonify({'error': 'receiver_id and content required'}), 400

    if len(content) > 2000:
        return jsonify({'error': 'Message too long (max 2000 chars)'}), 400

    receiver = User.query.get(receiver_id)
    if not receiver:
        return jsonify({'error': 'Receiver not found'}), 404

    message = Message(
        sender_id=user_id,
        receiver_id=receiver_id,
        content=content
    )
    db.session.add(message)
    db.session.commit()

    # Emit via socketio
    from app_init import socketio
    socketio.emit('new_message', message.to_dict(), room=f'user_{receiver_id}')
    socketio.emit('new_message', message.to_dict(), room=f'user_{user_id}')

    return jsonify({'message': message.to_dict()}), 201


@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    user_id = int(get_jwt_identity())

    # Get all unique conversations
    sent = db.session.query(Message.receiver_id).filter_by(sender_id=user_id).distinct()
    received = db.session.query(Message.sender_id).filter_by(receiver_id=user_id).distinct()

    user_ids = set()
    for r in sent:
        user_ids.add(r[0])
    for r in received:
        user_ids.add(r[0])

    conversations = []
    for uid in user_ids:
        other_user = User.query.get(uid)
        if not other_user:
            continue

        last_msg = Message.query.filter(
            or_(
                and_(Message.sender_id == user_id, Message.receiver_id == uid),
                and_(Message.sender_id == uid, Message.receiver_id == user_id)
            )
        ).order_by(Message.timestamp.desc()).first()

        unread_count = Message.query.filter_by(
            sender_id=uid, receiver_id=user_id, read_status=False
        ).count()

        conversations.append({
            'user': other_user.to_dict(),
            'last_message': last_msg.to_dict() if last_msg else None,
            'unread_count': unread_count
        })

    conversations.sort(
        key=lambda x: x['last_message']['timestamp'] if x['last_message'] else '',
        reverse=True
    )

    return jsonify({'conversations': conversations}), 200


@chat_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def unread_count():
    user_id = int(get_jwt_identity())
    count = Message.query.filter_by(receiver_id=user_id, read_status=False).count()
    return jsonify({'unread_count': count}), 200
