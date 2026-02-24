from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.database import db
from app.models import Firewall, Site

bp = Blueprint("firewalls", __name__, url_prefix="/firewalls")


@bp.route("/")
def index():
    items = Firewall.query.join(Site).order_by(Site.name, Firewall.name).all()
    sites = Site.query.order_by(Site.name).all()
    return render_template("table.html",
        title="Firewalls",
        entity="firewall",
        blueprint="firewalls",
        items=items,
        sites=sites,
        columns=["Site", "Name", "Public IP", "Mgmt IP", "Model", "Status", "Notes"],
        row_attrs=lambda f: [f.site.name, f.name, f.public_ip or "", f.management_ip or "",
                             f.model or "", f.status, f.notes or ""],
    )


@bp.route("/create", methods=["POST"])
def create():
    f = Firewall(
        site_id=int(request.form.get("site_id")),
        name=request.form.get("name", "").strip(),
        public_ip=request.form.get("public_ip", "").strip(),
        management_ip=request.form.get("management_ip", "").strip(),
        model=request.form.get("model", "").strip(),
        status=request.form.get("status", "active").strip(),
        notes=request.form.get("notes", "").strip(),
    )
    db.session.add(f)
    db.session.commit()
    flash("Firewall added.", "success")
    return redirect(url_for("firewalls.index"))


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    f = Firewall.query.get_or_404(id)
    if request.method == "POST":
        f.site_id       = int(request.form.get("site_id"))
        f.name          = request.form.get("name", "").strip()
        f.public_ip     = request.form.get("public_ip", "").strip()
        f.management_ip = request.form.get("management_ip", "").strip()
        f.model         = request.form.get("model", "").strip()
        f.status        = request.form.get("status", "active").strip()
        f.notes         = request.form.get("notes", "").strip()
        db.session.commit()
        flash("Firewall updated.", "success")
        return redirect(url_for("firewalls.index"))
    return jsonify(f.to_dict())


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    f = Firewall.query.get_or_404(id)
    db.session.delete(f)
    db.session.commit()
    flash("Firewall deleted.", "success")
    return redirect(url_for("firewalls.index"))


@bp.route("/<int:id>/clone", methods=["POST"])
def clone(id):
    f = Firewall.query.get_or_404(id)
    copy = Firewall(
        site_id=f.site_id,
        name="Copy of " + f.name,
        public_ip=None,
        management_ip=None,
        model=f.model,
        status=f.status,
        notes=f.notes,
    )
    db.session.add(copy)
    db.session.commit()
    flash(f"Cloned '{f.name}'.", "success")
    return redirect(url_for("firewalls.index"))
