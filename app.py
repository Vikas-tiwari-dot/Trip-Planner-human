import os
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_cors import CORS
from config import config
from app_init import db, bcrypt, jwt, socketio, limiter


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # Ensure database directory exists
    db_dir = os.path.join(os.path.dirname(__file__), 'database')
    os.makedirs(db_dir, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')
    limiter.init_app(app)
    CORS(app, supports_credentials=True)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.users import users_bp
    from routes.chat import chat_bp
    from routes.maps import maps_bp
    from routes.trips import trips_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(maps_bp, url_prefix='/api/maps')
    app.register_blueprint(trips_bp, url_prefix='/api/trips')

    # Register socket events
    from sockets.events import register_events
    register_events(socketio)

    # Frontend routes
    @app.route('/')
    def index():
        return render_template('landing.html')

    @app.route('/login')
    def login_page():
        return render_template('login.html')

    @app.route('/signup')
    def signup_page():
        return render_template('signup.html')

    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/map')
    def map_page():
        return render_template('map.html')

    @app.route('/chat')
    def chat_page():
        return render_template('chat.html')

    @app.route('/chat/<int:user_id>')
    def chat_with(user_id):
        return render_template('chat.html', chat_user_id=user_id)

    @app.route('/routes')
    def routes_page():
        return render_template('routes.html')

    @app.route('/profile')
    def profile_page():
        return render_template('profile.html')

    @app.route('/guides')
    def guides_page():
        return render_template('guides.html')

    # Create all tables
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
