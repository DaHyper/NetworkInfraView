from flask import Blueprint, render_template, request
from app.models import (Site, ISP, Hardware, Firewall, VM,
                        App, Storage, Network, ClientDevice, Misc)

bp = Blueprint("search", __name__, url_prefix="/search")


def _match(val, q):
    return q in str(val or "").lower()


@bp.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    if not q:
        return render_template("search.html", q="", results={}, total=0)

    results = {
        "sites":    [(s, "/sites/")    for s in Site.query.all()
                     if any(_match(v, q) for v in [s.name, s.location, s.address, s.notes])],
        "isps":     [(i, "/isps/")     for i in ISP.query.all()
                     if any(_match(v, q) for v in [i.name, i.type, i.asn, i.public_ip_range, i.notes])],
        "hardware": [(h, "/hardware/") for h in Hardware.query.all()
                     if any(_match(v, q) for v in [h.name, h.device_type, h.role, h.ip_mgmt, h.make_model, h.notes])],
        "firewalls":[(f, "/firewalls/")for f in Firewall.query.all()
                     if any(_match(v, q) for v in [f.name, f.public_ip, f.management_ip, f.model, f.notes])],
        "vms":      [(v, "/vms/")      for v in VM.query.all()
                     if any(_match(v2, q) for v2 in [v.name, v.os, v.ip_address, v.role, v.notes])],
        "apps":     [(a, "/apps/")     for a in App.query.all()
                     if any(_match(v, q) for v in [a.name, a.url, a.notes])],
        "storage":  [(s, "/storage/")  for s in Storage.query.all()
                     if any(_match(v, q) for v in [s.name, s.type, s.ip_address, s.make_model, s.notes])],
        "networks": [(n, "/networks/") for n in Network.query.all()
                     if any(_match(v, q) for v in [n.name, n.subnet, n.description])],
        "clients":  [(c, "/clients/")  for c in ClientDevice.query.all()
                     if any(_match(v, q) for v in [c.name, c.owner, c.ip_address, c.mac_address, c.os, c.notes])],
        "misc":     [(m, "/misc/")     for m in Misc.query.all()
                     if any(_match(v, q) for v in [m.name, m.category, m.ip_address, m.notes])],
    }

    # Remove empty categories
    results = {k: v for k, v in results.items() if v}
    total = sum(len(v) for v in results.values())

    return render_template("search.html", q=q, results=results, total=total)
