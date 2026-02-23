from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.database import db
from app.models import App, VM, Hardware, Site

bp = Blueprint("apps", __name__, url_prefix="/apps")


@bp.route("/")
def index():
    items = App.query.order_by(App.name).all()
    vms = VM.query.order_by(VM.name).all()
    hardware = Hardware.query.order_by(Hardware.name).all()
    return render_template("table.html",
        title="Apps & Services",
        entity="app",
        blueprint="apps",
        items=items,
        vms=vms,
        hardware_list=hardware,
        columns=["Name", "Version", "Host", "Port", "Protocol", "Public", "URL", "Notes"],
        row_attrs=lambda a: [
            a.name,
            a.version or "",
            (a.vm.name if a.vm else "") or (a.hardware.name if a.hardware else "") or "",
            str(a.port) if a.port else "",
            a.protocol or "",
            "Yes" if a.public_exposed else "No",
            a.url or "",
            a.notes or "",
        ],
    )


@bp.route("/create", methods=["POST"])
def create():
    a = App(
        vm_id=int(request.form.get("vm_id")) if request.form.get("vm_id") else None,
        hardware_id=int(request.form.get("hardware_id")) if request.form.get("hardware_id") else None,
        name=request.form.get("name", "").strip(),
        version=request.form.get("version", "").strip(),
        port=int(request.form.get("port") or 0) or None,
        protocol=request.form.get("protocol", "tcp").strip(),
        public_exposed=bool(request.form.get("public_exposed")),
        url=request.form.get("url", "").strip(),
        notes=request.form.get("notes", "").strip(),
    )
    db.session.add(a)
    db.session.commit()
    flash("App added.", "success")
    return redirect(url_for("apps.index"))


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    a = App.query.get_or_404(id)
    if request.method == "POST":
        a.vm_id        = int(request.form.get("vm_id")) if request.form.get("vm_id") else None
        a.hardware_id  = int(request.form.get("hardware_id")) if request.form.get("hardware_id") else None
        a.name         = request.form.get("name", "").strip()
        a.version      = request.form.get("version", "").strip()
        a.port         = int(request.form.get("port") or 0) or None
        a.protocol     = request.form.get("protocol", "tcp").strip()
        a.public_exposed = bool(request.form.get("public_exposed"))
        a.url          = request.form.get("url", "").strip()
        a.notes        = request.form.get("notes", "").strip()
        db.session.commit()
        flash("App updated.", "success")
        return redirect(url_for("apps.index"))
    return jsonify(a.to_dict())


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    a = App.query.get_or_404(id)
    db.session.delete(a)
    db.session.commit()
    flash("App deleted.", "success")
    return redirect(url_for("apps.index"))
