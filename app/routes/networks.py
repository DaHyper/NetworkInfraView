from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.database import db
from app.models import Network, Site

bp = Blueprint("networks", __name__, url_prefix="/networks")


@bp.route("/")
def index():
    items = Network.query.join(Site).order_by(Site.name, Network.vlan_id).all()
    sites = Site.query.order_by(Site.name).all()
    return render_template("table.html",
        title="Networks / VLANs",
        entity="network",
        blueprint="networks",
        fields=[],
        items=items,
        sites=sites,
        columns=["Site", "VLAN ID", "Name", "Subnet", "Color", "Description"],
        row_attrs=lambda n: [n.site.name, str(n.vlan_id or ""), n.name,
                             n.subnet or "", n.color or "", n.description or ""],
    )


@bp.route("/create", methods=["POST"])
def create():
    n = Network(
        site_id=int(request.form.get("site_id")),
        vlan_id=int(request.form.get("vlan_id") or 0) or None,
        name=request.form.get("name", "").strip(),
        subnet=request.form.get("subnet", "").strip(),
        color=request.form.get("color", "#6366f1").strip(),
        description=request.form.get("description", "").strip(),
    )
    db.session.add(n)
    db.session.commit()
    flash("Network added.", "success")
    return redirect(url_for("networks.index"))


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    n = Network.query.get_or_404(id)
    if request.method == "POST":
        n.site_id     = int(request.form.get("site_id"))
        n.vlan_id     = int(request.form.get("vlan_id") or 0) or None
        n.name        = request.form.get("name", "").strip()
        n.subnet      = request.form.get("subnet", "").strip()
        n.color       = request.form.get("color", "#6366f1").strip()
        n.description = request.form.get("description", "").strip()
        db.session.commit()
        flash("Network updated.", "success")
        return redirect(url_for("networks.index"))
    return jsonify(n.to_dict())


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    n = Network.query.get_or_404(id)
    db.session.delete(n)
    db.session.commit()
    flash("Network deleted.", "success")
    return redirect(url_for("networks.index"))


@bp.route("/api/list")
def api_list():
    """Used by other forms to populate network dropdowns."""
    nets = Network.query.order_by(Network.name).all()
    return jsonify([n.to_dict() for n in nets])
