from flask import Flask
from flask_sock import Sock
from .utils.db import ensure_db
from math import sin, cos, acos

def create_app():
    # Create app
    app = Flask(__name__,
                template_folder='./templates',
                static_folder='./static',
                instance_relative_config=True)

    # Load the default configuration
    app.config.from_object('config')

    # Load the instance configuration (if it exists)
    app.config.from_pyfile('config.py', silent=True)

    # Import sock and initialize it
    from .ws import sock
    sock.init_app(app)

    # Register blueprints
    from .main import main_bp
    from .auth import auth_bp
    from .replayer import replayer_bp
    from .statistics import statistics_bp
    from .rooms import rooms_bp

    app.register_blueprint(auth_bp, url_prefix='/')
    app.register_blueprint(replayer_bp, url_prefix='/replayer')
    app.register_blueprint(statistics_bp, url_prefix='/statistics')
    app.register_blueprint(rooms_bp, url_prefix='/')

    # Startup function
    with app.app_context():

        @app.context_processor
        def utility_processor():
            return dict(cos=cos, sin=sin, acos=acos)

        ensure_db()


    return app
