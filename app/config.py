import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    SECRET_KEY             = os.environ.get("SECRET_KEY", "CHANGE-ME-IN-PRODUCTION")
    JWT_SECRET_KEY         = os.environ.get("JWT_SECRET_KEY", "CHANGE-JWT-SECRET")
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION     = ["headers"]
    JWT_HEADER_NAME        = "Authorization"
    JWT_HEADER_TYPE        = "Bearer"
    JWT_ERROR_MESSAGE_KEY  = "message"

    # MongoDB
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/campuseats")

    RESET_TOKEN_EXPIRY_SECONDS = 3600

    MAIL_SERVER          = os.environ.get("MAIL_SERVER",   "smtp.gmail.com")
    MAIL_PORT            = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS         = os.environ.get("MAIL_USE_TLS",  "true").lower() == "true"
    MAIL_USE_SSL         = os.environ.get("MAIL_USE_SSL",  "false").lower() == "true"
    MAIL_USERNAME        = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD        = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER  = os.environ.get("MAIL_DEFAULT_SENDER", "Chatline <noreply@chatline.com>")

    CORS_ORIGINS             = os.environ.get("CORS_ORIGINS", "http://localhost:4200").split(",")
    RATELIMIT_DEFAULT        = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URL    = os.environ.get("REDIS_URL", "memory://")
    RATELIMIT_HEADERS_ENABLED = True


class DevelopmentConfig(BaseConfig):
    DEBUG = True

class ProductionConfig(BaseConfig):
    DEBUG = False

class TestingConfig(BaseConfig):
    TESTING  = True
    MONGO_URI = "mongodb://localhost:27017/campuseats_test"

config_by_name = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
}