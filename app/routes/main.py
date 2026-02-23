from flask import Blueprint, render_template
from app.models import Site, ISP, Hardware, Firewall, VM, App, Storage, Network, ClientDevice, Misc, Connection

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    counts = {
        "sites":    Site.query.count(),
        "isps":     ISP.query.count(),
        "hardware": Hardware.query.count(),
        "firewalls": Firewall.query.count(),
        "vms":      VM.query.count(),
        "apps":     App.query.count(),
        "storage":  Storage.query.count(),
        "networks": Network.query.count(),
        "clients":  ClientDevice.query.count(),
        "misc":     Misc.query.count(),
        "connections": Connection.query.count(),
    }
    sites = Site.query.order_by(Site.name).all()
    return render_template("index.html", counts=counts, sites=sites)
