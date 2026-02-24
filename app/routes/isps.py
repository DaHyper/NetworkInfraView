from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.database import db
from app.models import ISP, Site

bp = Blueprint("isps", __name__, url_prefix="/isps")


@bp.route("/")
def index():
    items = ISP.query.join(Site).order_by(Site.name, ISP.name).all()
    sites = Site.query.order_by(Site.name).all()
    return render_template("table.html",
        title="ISPs",
        entity="isp",
        blueprint="isps",
        items=items,
        sites=sites,
        columns=["Site", "Name", "Type", "ASN", "Public IP Range", "Notes"],
        row_attrs=lambda i: [i.site.name, i.name, i.type or "", i.asn or "", i.public_ip_range or "", i.notes or ""],
    )


@bp.route("/create", methods=["POST"])
def create():
    i = ISP(
        site_id=int(request.form.get("site_id")),
        name=request.form.get("name", "").strip(),
        type=request.form.get("type", "").strip(),
        asn=request.form.get("asn", "").strip(),
        public_ip_range=request.form.get("public_ip_range", "").strip(),
        notes=request.form.get("notes", "").strip(),
    )
    db.session.add(i)
    db.session.commit()
    flash("ISP created.", "success")
    return redirect(url_for("isps.index"))


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    i = ISP.query.get_or_404(id)
    if request.method == "POST":
        i.site_id        = int(request.form.get("site_id"))
        i.name           = request.form.get("name", "").strip()
        i.type           = request.form.get("type", "").strip()
        i.asn            = request.form.get("asn", "").strip()
        i.public_ip_range= request.form.get("public_ip_range", "").strip()
        i.notes          = request.form.get("notes", "").strip()
        db.session.commit()
        flash("ISP updated.", "success")
        return redirect(url_for("isps.index"))
    return jsonify(i.to_dict())


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    i = ISP.query.get_or_404(id)
    db.session.delete(i)
    db.session.commit()
    flash("ISP deleted.", "success")
    return redirect(url_for("isps.index"))


@bp.route("/<int:id>/clone", methods=["POST"])
def clone(id):
    i = ISP.query.get_or_404(id)
    copy = ISP(
        site_id=i.site_id,
        name="Copy of " + i.name,
        type=i.type,
        asn=i.asn,
        public_ip_range=None,
        notes=i.notes,
    )
    db.session.add(copy)
    db.session.commit()
    flash(f"Cloned '{i.name}'.", "success")
    return redirect(url_for("isps.index"))
