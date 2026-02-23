from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.database import db
from app.models import ClientDevice, Site, Network

bp = Blueprint("clients", __name__, url_prefix="/clients")


@bp.route("/")
def index():
    items = ClientDevice.query.join(Site).order_by(Site.name, ClientDevice.name).all()
    sites = Site.query.order_by(Site.name).all()
    networks = Network.query.order_by(Network.name).all()
    return render_template("table.html",
        title="Client Devices",
        entity="client",
        blueprint="clients",
        fields=[],
        items=items,
        sites=sites,
        networks=networks,
        columns=["Site", "Name", "Owner", "Type", "IP", "MAC", "OS", "Network", "Notes"],
        row_attrs=lambda c: [
            c.site.name, c.name, c.owner or "", c.device_type or "",
            c.ip_address or "", c.mac_address or "", c.os or "",
            (c.network.name if c.network else ""), c.notes or "",
        ],
    )


@bp.route("/create", methods=["POST"])
def create():
    c = ClientDevice(
        site_id=int(request.form.get("site_id")),
        network_id=int(request.form.get("network_id")) if request.form.get("network_id") else None,
        name=request.form.get("name", "").strip(),
        owner=request.form.get("owner", "").strip(),
        device_type=request.form.get("device_type", "laptop").strip(),
        ip_address=request.form.get("ip_address", "").strip(),
        mac_address=request.form.get("mac_address", "").strip(),
        os=request.form.get("os", "").strip(),
        notes=request.form.get("notes", "").strip(),
    )
    db.session.add(c)
    db.session.commit()
    flash("Client device added.", "success")
    return redirect(url_for("clients.index"))


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    c = ClientDevice.query.get_or_404(id)
    if request.method == "POST":
        c.site_id    = int(request.form.get("site_id"))
        c.network_id = int(request.form.get("network_id")) if request.form.get("network_id") else None
        c.name       = request.form.get("name", "").strip()
        c.owner      = request.form.get("owner", "").strip()
        c.device_type= request.form.get("device_type", "laptop").strip()
        c.ip_address = request.form.get("ip_address", "").strip()
        c.mac_address= request.form.get("mac_address", "").strip()
        c.os         = request.form.get("os", "").strip()
        c.notes      = request.form.get("notes", "").strip()
        db.session.commit()
        flash("Client device updated.", "success")
        return redirect(url_for("clients.index"))
    return jsonify(c.to_dict())


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    c = ClientDevice.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    flash("Client device deleted.", "success")
    return redirect(url_for("clients.index"))
