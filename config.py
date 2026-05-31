import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-please-change')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-please-change')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    _db_url = os.environ.get('DATABASE_URL')
    SQLALCHEMY_DATABASE_URI = _db_url if _db_url else f'sqlite:///{os.path.join(BASE_DIR, "database", "pathick.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TRIP_THRESHOLD_KM = float(os.environ.get('TRIP_THRESHOLD_KM', 50))
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per day;50 per hour')
    CORS_HEADERS = 'Content-Type'

class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
