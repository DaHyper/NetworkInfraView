from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.database import db
from app.models import Site

bp = Blueprint("sites", __name__, url_prefix="/sites")


@bp.route("/")
def index():
    items = Site.query.order_by(Site.name).all()
    return render_template("table.html",
        title="Sites",
        entity="site",
        blueprint="sites",
        items=items,
        columns=["Name", "Location", "Address", "Timezone", "Notes"],
        row_attrs=lambda s: [s.name, s.location or "", s.address or "", s.timezone or "", s.notes or ""],
    )


@bp.route("/create", methods=["POST"])
def create():
    s = Site(
        name=request.form.get("name", "").strip(),
        location=request.form.get("location", "").strip(),
        address=request.form.get("address", "").strip(),
        timezone=request.form.get("timezone", "").strip(),
        notes=request.form.get("notes", "").strip(),
    )
    db.session.add(s)
    db.session.commit()
    flash("Site created.", "success")
    return redirect(url_for("sites.index"))


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    s = Site.query.get_or_404(id)
    if request.method == "POST":
        s.name     = request.form.get("name", "").strip()
        s.location = request.form.get("location", "").strip()
        s.address  = request.form.get("address", "").strip()
        s.timezone = request.form.get("timezone", "").strip()
        s.notes    = request.form.get("notes", "").strip()
        db.session.commit()
        flash("Site updated.", "success")
        return redirect(url_for("sites.index"))
    return jsonify(s.to_dict())


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    s = Site.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    flash("Site deleted.", "success")
    return redirect(url_for("sites.index"))


@bp.route("/<int:id>/clone", methods=["POST"])
def clone(id):
    s = Site.query.get_or_404(id)
    copy = Site(
        name="Copy of " + s.name,
        location=s.location,
        address=s.address,
        timezone=s.timezone,
        notes=s.notes,
    )
    db.session.add(copy)
    db.session.commit()
    flash(f"Cloned '{s.name}'.", "success")
    return redirect(url_for("sites.index"))
