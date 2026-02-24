from flask import Flask
from config import Config
from app.database import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    # Register blueprints
    from app.routes.main import bp as main_bp
    from app.routes.sites import bp as sites_bp
    from app.routes.isps import bp as isps_bp
    from app.routes.hardware import bp as hardware_bp
    from app.routes.firewalls import bp as firewalls_bp
    from app.routes.vms import bp as vms_bp
    from app.routes.apps import bp as apps_bp
    from app.routes.storage import bp as storage_bp
    from app.routes.networks import bp as networks_bp
    from app.routes.clients import bp as clients_bp
    from app.routes.misc import bp as misc_bp
    from app.routes.map import bp as map_bp
    from app.routes.data_io import bp as data_io_bp
    from app.routes.search import bp as search_bp
    from app.routes.util import bp as util_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(sites_bp)
    app.register_blueprint(isps_bp)
    app.register_blueprint(hardware_bp)
    app.register_blueprint(firewalls_bp)
    app.register_blueprint(vms_bp)
    app.register_blueprint(apps_bp)
    app.register_blueprint(storage_bp)
    app.register_blueprint(networks_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(misc_bp)
    app.register_blueprint(map_bp)
    app.register_blueprint(data_io_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(util_bp)

    with app.app_context():
        db.create_all()

    return app
