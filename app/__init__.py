from flask import Flask
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_pymongo import PyMongo

jwt     = JWTManager()
bcrypt  = Bcrypt()
mail    = Mail()
mongo   = PyMongo()
limiter = Limiter(key_func=get_remote_address)


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)

    from .config import config_by_name
    app.config.from_object(config_by_name[config_name])

    jwt.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    mongo.init_app(app)
    limiter.init_app(app)

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
        max_age=600
    )

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"]     = "nosniff"
        response.headers["X-Frame-Options"]            = "DENY"
        response.headers["X-XSS-Protection"]           = "1; mode=block"
        response.headers["Referrer-Policy"]            = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"]  = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"]              = "no-store, no-cache, must-revalidate, max-age=0"
        return response

    from .utils.jwt_callbacks import register_jwt_callbacks
    register_jwt_callbacks(jwt)

    from .routes.auth import auth_bp
    from .routes.menu import menu_bp
    from .routes.order import orders_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(menu_bp, url_prefix="/api")
    app.register_blueprint(orders_bp, url_prefix="/api")

    # Create MongoDB indexes on startup
    with app.app_context():
        mongo.db.users.create_index("email", unique=True)
        mongo.db["Menu"].create_index("category")
        mongo.db["Category"].create_index("name", unique=True)
        # mongo.db["Orders"].create_index("orderId", unique=True)
        mongo.db["Orders"].create_index("email")

    return app