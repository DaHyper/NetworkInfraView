from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.database import db
from app.models import Misc, Site

bp = Blueprint("misc", __name__, url_prefix="/misc")


@bp.route("/")
def index():
    items = Misc.query.join(Site).order_by(Site.name, Misc.name).all()
    sites = Site.query.order_by(Site.name).all()
    return render_template("table.html",
        title="Misc",
        entity="misc",
        blueprint="misc",
        fields=[],
        items=items,
        sites=sites,
        columns=["Site", "Name", "Category", "IP", "Description", "Notes"],
        row_attrs=lambda m: [m.site.name, m.name, m.category or "", m.ip_address or "",
                             m.description or "", m.notes or ""],
    )


@bp.route("/create", methods=["POST"])
def create():
    m = Misc(
        site_id=int(request.form.get("site_id")),
        name=request.form.get("name", "").strip(),
        category=request.form.get("category", "").strip(),
        description=request.form.get("description", "").strip(),
        ip_address=request.form.get("ip_address", "").strip(),
        notes=request.form.get("notes", "").strip(),
    )
    db.session.add(m)
    db.session.commit()
    flash("Misc item added.", "success")
    return redirect(url_for("misc.index"))


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    m = Misc.query.get_or_404(id)
    if request.method == "POST":
        m.site_id     = int(request.form.get("site_id"))
        m.name        = request.form.get("name", "").strip()
        m.category    = request.form.get("category", "").strip()
        m.description = request.form.get("description", "").strip()
        m.ip_address  = request.form.get("ip_address", "").strip()
        m.notes       = request.form.get("notes", "").strip()
        db.session.commit()
        flash("Misc item updated.", "success")
        return redirect(url_for("misc.index"))
    return jsonify(m.to_dict())


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    m = Misc.query.get_or_404(id)
    db.session.delete(m)
    db.session.commit()
    flash("Misc item deleted.", "success")
    return redirect(url_for("misc.index"))
