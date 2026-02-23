from flask import Blueprint, render_template, jsonify, request
from app.database import db
from app.models import (Site, ISP, Hardware, Hypervisor, Firewall, VM,
                        App, Storage, Network, ClientDevice, Misc,
                        Connection, MapLayout)

bp = Blueprint("map", __name__, url_prefix="/map")


@bp.route("/")
def view():
    sites = Site.query.order_by(Site.name).all()
    networks = Network.query.order_by(Network.name).all()
    return render_template("map.html", sites=sites, networks=networks)


@bp.route("/api/graph")
def graph():
    """Return Cytoscape-compatible nodes and edges for the network map."""
    site_id = request.args.get("site_id", type=int)

    nodes = []
    edges = []

    # --- SITES (parent groups) ---
    site_q = Site.query
    if site_id:
        site_q = site_q.filter_by(id=site_id)
    for site in site_q.all():
        nodes.append({
            "data": {
                "id": f"site-{site.id}",
                "label": site.name,
                "type": "site",
                "entity_id": site.id,
                "location": site.location or "",
            },
            "classes": "node-site"
        })

    # --- ISPs ---
    isp_q = ISP.query
    if site_id:
        isp_q = isp_q.filter_by(site_id=site_id)
    for isp in isp_q.all():
        nodes.append({
            "data": {
                "id": f"isp-{isp.id}",
                "label": isp.name,
                "type": "isp",
                "entity_id": isp.id,
                "isp_type": isp.type or "",
                "asn": isp.asn or "",
                "public_ip_range": isp.public_ip_range or "",
                "parent_site": f"site-{isp.site_id}",
            },
            "classes": "node-isp"
        })
        edges.append({
            "data": {
                "id": f"edge-isp-site-{isp.id}",
                "source": f"isp-{isp.id}",
                "target": f"site-{isp.site_id}",
                "label": "uplink",
                "color": "#333",
                "style": "solid",
            }
        })

    # --- FIREWALLS ---
    fw_q = Firewall.query
    if site_id:
        fw_q = fw_q.filter_by(site_id=site_id)
    for fw in fw_q.all():
        nodes.append({
            "data": {
                "id": f"fw-{fw.id}",
                "label": fw.name,
                "type": "firewall",
                "entity_id": fw.id,
                "public_ip": fw.public_ip or "",
                "management_ip": fw.management_ip or "",
                "model": fw.model or "",
                "status": fw.status,
            },
            "classes": f"node-firewall status-{fw.status}"
        })
        # FW connects to each ISP in same site
        for isp in ISP.query.filter_by(site_id=fw.site_id).all():
            edges.append({
                "data": {
                    "id": f"edge-fw-isp-{fw.id}-{isp.id}",
                    "source": f"isp-{isp.id}",
                    "target": f"fw-{fw.id}",
                    "label": "",
                    "color": "#555",
                    "style": "solid",
                }
            })

    # --- HARDWARE ---
    hw_q = Hardware.query
    if site_id:
        hw_q = hw_q.filter_by(site_id=site_id)
    for hw in hw_q.all():
        nodes.append({
            "data": {
                "id": f"hw-{hw.id}",
                "label": hw.name,
                "type": "hardware",
                "entity_id": hw.id,
                "device_type": hw.device_type,
                "role": hw.role or "",
                "ip_mgmt": hw.ip_mgmt or "",
                "status": hw.status,
                "make_model": hw.make_model or "",
                "is_hypervisor": hw.hypervisor is not None,
                "hypervisor_type": hw.hypervisor.hypervisor_type if hw.hypervisor else "",
            },
            "classes": f"node-hardware node-{hw.device_type} status-{hw.status}"
        })
        # Connect hardware to firewalls in same site
        for fw in Firewall.query.filter_by(site_id=hw.site_id).all():
            edges.append({
                "data": {
                    "id": f"edge-hw-fw-{hw.id}-{fw.id}",
                    "source": f"fw-{fw.id}",
                    "target": f"hw-{hw.id}",
                    "color": "#555",
                    "style": "solid",
                }
            })

    # --- NETWORKS / VLANs ---
    net_q = Network.query
    if site_id:
        net_q = net_q.filter_by(site_id=site_id)
    for net in net_q.all():
        label = f"VLAN {net.vlan_id}" if net.vlan_id else net.name
        nodes.append({
            "data": {
                "id": f"net-{net.id}",
                "label": label,
                "sublabel": net.name if net.vlan_id else "",
                "type": "network",
                "entity_id": net.id,
                "vlan_id": net.vlan_id,
                "subnet": net.subnet or "",
                "color": net.color,
            },
            "classes": "node-network"
        })

    # --- VMs ---
    vm_q = VM.query
    if site_id:
        vm_q = vm_q.filter_by(site_id=site_id)
    for vm in vm_q.all():
        net_color = vm.network.color if vm.network else "#aaa"
        nodes.append({
            "data": {
                "id": f"vm-{vm.id}",
                "label": vm.name,
                "type": "vm",
                "entity_id": vm.id,
                "os": vm.os or "",
                "ip_address": vm.ip_address or "",
                "role": vm.role or "",
                "status": vm.status,
                "public_exposed": vm.public_exposed,
                "network_color": net_color,
                "network_name": (vm.network.name if vm.network else ""),
            },
            "classes": f"node-vm status-{vm.status}" + (" node-public" if vm.public_exposed else "")
        })
        # VM → Hypervisor/Hardware
        if vm.hypervisor:
            edges.append({
                "data": {
                    "id": f"edge-vm-hw-{vm.id}",
                    "source": f"hw-{vm.hypervisor.hardware_id}",
                    "target": f"vm-{vm.id}",
                    "color": "#888",
                    "style": "dashed",
                }
            })
        # VM → Network
        if vm.network_id:
            edges.append({
                "data": {
                    "id": f"edge-vm-net-{vm.id}",
                    "source": f"vm-{vm.id}",
                    "target": f"net-{vm.network_id}",
                    "color": net_color,
                    "style": "dashed",
                }
            })

    # --- STORAGE ---
    st_q = Storage.query
    if site_id:
        st_q = st_q.filter_by(site_id=site_id)
    for st in st_q.all():
        nodes.append({
            "data": {
                "id": f"storage-{st.id}",
                "label": st.name,
                "type": "storage",
                "entity_id": st.id,
                "storage_type": st.type or "",
                "capacity_tb": st.capacity_tb,
                "ip_address": st.ip_address or "",
            },
            "classes": "node-storage"
        })

    # --- CLIENT DEVICES ---
    cl_q = ClientDevice.query
    if site_id:
        cl_q = cl_q.filter_by(site_id=site_id)
    for cl in cl_q.all():
        nodes.append({
            "data": {
                "id": f"client-{cl.id}",
                "label": cl.name,
                "type": "client",
                "entity_id": cl.id,
                "device_type": cl.device_type or "",
                "owner": cl.owner or "",
                "ip_address": cl.ip_address or "",
            },
            "classes": f"node-client node-{cl.device_type}"
        })
        if cl.network_id:
            edges.append({
                "data": {
                    "id": f"edge-client-net-{cl.id}",
                    "source": f"client-{cl.id}",
                    "target": f"net-{cl.network_id}",
                    "color": "#aaa",
                    "style": "dashed",
                }
            })

    # --- MISC ---
    ms_q = Misc.query
    if site_id:
        ms_q = ms_q.filter_by(site_id=site_id)
    for ms in ms_q.all():
        nodes.append({
            "data": {
                "id": f"misc-{ms.id}",
                "label": ms.name,
                "type": "misc",
                "entity_id": ms.id,
                "category": ms.category or "",
            },
            "classes": "node-misc"
        })

    # --- Custom connections from DB ---
    conn_q = Connection.query
    for conn in conn_q.all():
        edges.append({
            "data": {
                "id": f"conn-{conn.id}",
                "source": f"{conn.from_type}-{conn.from_id}",
                "target": f"{conn.to_type}-{conn.to_id}",
                "label": conn.label or "",
                "color": conn.color,
                "style": conn.style,
            }
        })

    # --- Apply saved layout positions ---
    layouts = {f"{l.node_type}-{l.node_id}": (l.x, l.y)
               for l in MapLayout.query.all()}
    for node in nodes:
        nid = node["data"]["id"]
        if nid in layouts:
            node["position"] = {"x": layouts[nid][0], "y": layouts[nid][1]}

    return jsonify({"nodes": nodes, "edges": edges})


@bp.route("/api/layout", methods=["POST"])
def save_layout():
    """Save node positions from Cytoscape after user drag."""
    positions = request.json or []
    for pos in positions:
        nid = pos.get("id", "")
        parts = nid.rsplit("-", 1)
        if len(parts) != 2:
            continue
        ntype, nid_str = parts
        try:
            nid_int = int(nid_str)
        except ValueError:
            continue
        layout = MapLayout.query.filter_by(node_type=ntype, node_id=nid_int).first()
        if not layout:
            layout = MapLayout(node_type=ntype, node_id=nid_int)
            db.session.add(layout)
        layout.x = pos.get("x", 0)
        layout.y = pos.get("y", 0)
    db.session.commit()
    return jsonify({"status": "ok"})


@bp.route("/api/connections", methods=["POST"])
def add_connection():
    data = request.json or {}
    conn = Connection(
        from_type=data.get("from_type"),
        from_id=data.get("from_id"),
        to_type=data.get("to_type"),
        to_id=data.get("to_id"),
        label=data.get("label", ""),
        color=data.get("color", "#333"),
        style=data.get("style", "solid"),
        notes=data.get("notes", ""),
    )
    db.session.add(conn)
    db.session.commit()
    return jsonify({"id": conn.id})


@bp.route("/api/connections/<int:id>", methods=["DELETE"])
def delete_connection(id):
    conn = Connection.query.get_or_404(id)
    db.session.delete(conn)
    db.session.commit()
    return jsonify({"status": "ok"})
