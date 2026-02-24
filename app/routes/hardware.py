from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.database import db
from app.models import Hardware, Hypervisor, Site

bp = Blueprint("hardware", __name__, url_prefix="/hardware")


@bp.route("/")
def index():
    items = Hardware.query.join(Site).order_by(Site.name, Hardware.name).all()
    sites = Site.query.order_by(Site.name).all()
    return render_template("hardware.html", items=items, sites=sites)


@bp.route("/create", methods=["POST"])
def create():
    h = Hardware(
        site_id=int(request.form.get("site_id")),
        name=request.form.get("name", "").strip(),
        device_type=request.form.get("device_type", "server").strip(),
        role=request.form.get("role", "").strip(),
        status=request.form.get("status", "active").strip(),
        ip_mgmt=request.form.get("ip_mgmt", "").strip(),
        cpu_cores=int(request.form.get("cpu_cores") or 0) or None,
        ram_gb=int(request.form.get("ram_gb") or 0) or None,
        rack_position=request.form.get("rack_position", "").strip(),
        make_model=request.form.get("make_model", "").strip(),
        notes=request.form.get("notes", "").strip(),
    )
    db.session.add(h)
    db.session.flush()

    # Auto-create hypervisor record if device is a hypervisor type
    if request.form.get("is_hypervisor"):
        hyp = Hypervisor(
            hardware_id=h.id,
            cluster_name=request.form.get("cluster_name", "").strip(),
            hypervisor_type=request.form.get("hypervisor_type", "proxmox").strip(),
        )
        db.session.add(hyp)

    db.session.commit()
    flash("Hardware added.", "success")
    return redirect(url_for("hardware.index"))


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    h = Hardware.query.get_or_404(id)
    if request.method == "POST":
        h.site_id      = int(request.form.get("site_id"))
        h.name         = request.form.get("name", "").strip()
        h.device_type  = request.form.get("device_type", "server").strip()
        h.role         = request.form.get("role", "").strip()
        h.status       = request.form.get("status", "active").strip()
        h.ip_mgmt      = request.form.get("ip_mgmt", "").strip()
        h.cpu_cores    = int(request.form.get("cpu_cores") or 0) or None
        h.ram_gb       = int(request.form.get("ram_gb") or 0) or None
        h.rack_position= request.form.get("rack_position", "").strip()
        h.make_model   = request.form.get("make_model", "").strip()
        h.notes        = request.form.get("notes", "").strip()
        db.session.commit()
        flash("Hardware updated.", "success")
        return redirect(url_for("hardware.index"))
    data = h.to_dict()
    if h.hypervisor:
        data["is_hypervisor"] = True
        data["cluster_name"] = h.hypervisor.cluster_name
        data["hypervisor_type"] = h.hypervisor.hypervisor_type
    return jsonify(data)


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    h = Hardware.query.get_or_404(id)
    db.session.delete(h)
    db.session.commit()
    flash("Hardware deleted.", "success")
    return redirect(url_for("hardware.index"))


@bp.route("/<int:id>/clone", methods=["POST"])
def clone(id):
    h = Hardware.query.get_or_404(id)
    copy = Hardware(
        site_id=h.site_id,
        name="Copy of " + h.name,
        device_type=h.device_type,
        role=h.role,
        status=h.status,
        ip_mgmt=None,
        cpu_cores=h.cpu_cores,
        ram_gb=h.ram_gb,
        rack_position=h.rack_position,
        make_model=h.make_model,
        notes=h.notes,
    )
    db.session.add(copy)
    db.session.commit()
    flash(f"Cloned '{h.name}'.", "success")
    return redirect(url_for("hardware.index"))
