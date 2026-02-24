import subprocess
import re
from flask import Blueprint, jsonify, request
from app.models import Hardware, VM, Firewall, Storage, ClientDevice, Misc

bp = Blueprint("util", __name__, url_prefix="/util")

_IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


@bp.route("/ping")
def ping():
    ip = request.args.get("ip", "").strip()
    if not _IP_RE.match(ip):
        return jsonify({"error": "invalid IP"}), 400
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            capture_output=True, timeout=4
        )
        return jsonify({"ip": ip, "reachable": result.returncode == 0})
    except Exception:
        return jsonify({"ip": ip, "reachable": False})


@bp.route("/ip-conflicts")
def ip_conflicts():
    """Return a list of IP addresses that appear more than once across all entities."""
    seen = {}
    for h in Hardware.query.all():
        if h.ip_mgmt and h.ip_mgmt.strip():
            seen.setdefault(h.ip_mgmt.strip(), 0)
            seen[h.ip_mgmt.strip()] += 1
    for v in VM.query.all():
        if v.ip_address and v.ip_address.strip():
            seen.setdefault(v.ip_address.strip(), 0)
            seen[v.ip_address.strip()] += 1
    for f in Firewall.query.all():
        for ip in [f.public_ip, f.management_ip]:
            if ip and ip.strip():
                seen.setdefault(ip.strip(), 0)
                seen[ip.strip()] += 1
    for s in Storage.query.all():
        if s.ip_address and s.ip_address.strip():
            seen.setdefault(s.ip_address.strip(), 0)
            seen[s.ip_address.strip()] += 1
    for c in ClientDevice.query.all():
        if c.ip_address and c.ip_address.strip():
            seen.setdefault(c.ip_address.strip(), 0)
            seen[c.ip_address.strip()] += 1
    for m in Misc.query.all():
        if m.ip_address and m.ip_address.strip():
            seen.setdefault(m.ip_address.strip(), 0)
            seen[m.ip_address.strip()] += 1

    conflicts = [ip for ip, count in seen.items() if count > 1]
    return jsonify({"conflicts": conflicts})
