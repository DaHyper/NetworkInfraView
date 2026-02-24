from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.database import db
from app.models import VM, Site, Hypervisor, Network

bp = Blueprint("vms", __name__, url_prefix="/vms")


@bp.route("/")
def index():
    items = VM.query.join(Site).order_by(Site.name, VM.name).all()
    sites = Site.query.order_by(Site.name).all()
    hypervisors = Hypervisor.query.all()
    networks = Network.query.all()
    return render_template("vms.html", items=items, sites=sites,
                           hypervisors=hypervisors, networks=networks)


@bp.route("/create", methods=["POST"])
def create():
    v = VM(
        site_id=int(request.form.get("site_id")),
        hypervisor_id=int(request.form.get("hypervisor_id")) if request.form.get("hypervisor_id") else None,
        network_id=int(request.form.get("network_id")) if request.form.get("network_id") else None,
        name=request.form.get("name", "").strip(),
        os=request.form.get("os", "").strip(),
        ip_address=request.form.get("ip_address", "").strip(),
        cpu_cores=int(request.form.get("cpu_cores") or 0) or None,
        ram_gb=int(request.form.get("ram_gb") or 0) or None,
        storage_gb=int(request.form.get("storage_gb") or 0) or None,
        role=request.form.get("role", "").strip(),
        status=request.form.get("status", "active").strip(),
        public_exposed=bool(request.form.get("public_exposed")),
        notes=request.form.get("notes", "").strip(),
    )
    db.session.add(v)
    db.session.commit()
    flash("VM added.", "success")
    return redirect(url_for("vms.index"))


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    v = VM.query.get_or_404(id)
    if request.method == "POST":
        v.site_id       = int(request.form.get("site_id"))
        v.hypervisor_id = int(request.form.get("hypervisor_id")) if request.form.get("hypervisor_id") else None
        v.network_id    = int(request.form.get("network_id")) if request.form.get("network_id") else None
        v.name          = request.form.get("name", "").strip()
        v.os            = request.form.get("os", "").strip()
        v.ip_address    = request.form.get("ip_address", "").strip()
        v.cpu_cores     = int(request.form.get("cpu_cores") or 0) or None
        v.ram_gb        = int(request.form.get("ram_gb") or 0) or None
        v.storage_gb    = int(request.form.get("storage_gb") or 0) or None
        v.role          = request.form.get("role", "").strip()
        v.status        = request.form.get("status", "active").strip()
        v.public_exposed = bool(request.form.get("public_exposed"))
        v.notes         = request.form.get("notes", "").strip()
        db.session.commit()
        flash("VM updated.", "success")
        return redirect(url_for("vms.index"))
    return jsonify(v.to_dict())


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    v = VM.query.get_or_404(id)
    db.session.delete(v)
    db.session.commit()
    flash("VM deleted.", "success")
    return redirect(url_for("vms.index"))


@bp.route("/<int:id>/clone", methods=["POST"])
def clone(id):
    v = VM.query.get_or_404(id)
    copy = VM(
        site_id=v.site_id,
        hypervisor_id=v.hypervisor_id,
        network_id=v.network_id,
        name="Copy of " + v.name,
        os=v.os,
        ip_address=None,
        cpu_cores=v.cpu_cores,
        ram_gb=v.ram_gb,
        storage_gb=v.storage_gb,
        role=v.role,
        status=v.status,
        public_exposed=v.public_exposed,
        notes=v.notes,
    )
    db.session.add(copy)
    db.session.commit()
    flash(f"Cloned '{v.name}'.", "success")
    return redirect(url_for("vms.index"))
