from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.database import db
from app.models import Storage, Site

bp = Blueprint("storage", __name__, url_prefix="/storage")


@bp.route("/")
def index():
    items = Storage.query.join(Site).order_by(Site.name, Storage.name).all()
    sites = Site.query.order_by(Site.name).all()
    return render_template("table.html",
        title="Storage",
        entity="storage",
        blueprint="storage",
        fields=[],
        items=items,
        sites=sites,
        columns=["Site", "Name", "Type", "Capacity (TB)", "IP", "Protocol", "Make/Model", "Notes"],
        row_attrs=lambda s: [s.site.name, s.name, s.type or "", str(s.capacity_tb or ""),
                             s.ip_address or "", s.protocol or "", s.make_model or "", s.notes or ""],
    )


@bp.route("/create", methods=["POST"])
def create():
    s = Storage(
        site_id=int(request.form.get("site_id")),
        name=request.form.get("name", "").strip(),
        type=request.form.get("type", "nas").strip(),
        capacity_tb=float(request.form.get("capacity_tb") or 0) or None,
        ip_address=request.form.get("ip_address", "").strip(),
        protocol=request.form.get("protocol", "").strip(),
        make_model=request.form.get("make_model", "").strip(),
        notes=request.form.get("notes", "").strip(),
    )
    db.session.add(s)
    db.session.commit()
    flash("Storage added.", "success")
    return redirect(url_for("storage.index"))


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    s = Storage.query.get_or_404(id)
    if request.method == "POST":
        s.site_id     = int(request.form.get("site_id"))
        s.name        = request.form.get("name", "").strip()
        s.type        = request.form.get("type", "nas").strip()
        s.capacity_tb = float(request.form.get("capacity_tb") or 0) or None
        s.ip_address  = request.form.get("ip_address", "").strip()
        s.protocol    = request.form.get("protocol", "").strip()
        s.make_model  = request.form.get("make_model", "").strip()
        s.notes       = request.form.get("notes", "").strip()
        db.session.commit()
        flash("Storage updated.", "success")
        return redirect(url_for("storage.index"))
    return jsonify(s.to_dict())


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    s = Storage.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    flash("Storage deleted.", "success")
    return redirect(url_for("storage.index"))
