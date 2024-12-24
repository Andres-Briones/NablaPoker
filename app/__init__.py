from flask import Flask
from flask_sock import Sock

def create_app():

    # Create app
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static',
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
    app.register_blueprint(main_bp, url_prefix='/')

    return app
