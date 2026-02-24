from flask import Blueprint, render_template, request
from app.models import Site, ISP, Hardware, Firewall, VM, Network, Storage, Misc, Connection, ClientDevice

bp = Blueprint("diagram", __name__, url_prefix="/diagram")

# Misc categories shown in the external/internet row (above ISPs)
EXTERNAL_CATEGORIES = {"cloud", "internet", "external", "backup", "saas", "cdn", "vpn", "dns"}


def _vm_sort_key(v):
    """pfSense/firewall first, jumphosts second, everything else alpha."""
    n = v.name.lower()
    r = (v.role or "").lower()
    if "pfsense" in n or "pfsense" in r:
        return (0, n)
    if "firewall" in r or "router" in r or "gateway" in r:
        return (0, n)
    if "jump" in n or "jumphost" in r:
        return (1, n)
    return (2, n)


def _group_sort_key(g):
    """VLAN groups containing pfSense float to top, jumphost groups second."""
    has_pf   = any("pfsense" in v.name.lower() or "pfsense" in (v.role or "").lower()
                   for v in g["vms"])
    has_jump = any("jump" in v.name.lower() for v in g["vms"])
    if has_pf:   return (0, g["vlan_id"] or 0)
    if has_jump: return (1, g["vlan_id"] or 0)
    return (2 if g["vlan_id"] is not None else 3, g["vlan_id"] or 0)


@bp.route("/")
def view():
    sites = Site.query.order_by(Site.name).all()
    site_id = request.args.get("site_id", type=int)

    if not site_id and sites:
        site_id = sites[0].id

    site = Site.query.get(site_id) if site_id else None

    isps         = []
    firewalls    = []
    hardware     = []
    networks     = []
    storage_list = []
    misc_list    = []
    external_misc = []
    clients      = []
    connections  = []
    hw_vms       = {}   # hw.id → [{ network, name, vlan_id, color, vms }]
    hw_clusters  = {}   # cluster_name → [hw, ...]  (ordered insertion)

    if site:
        isps         = ISP.query.filter_by(site_id=site.id).order_by(ISP.name).all()
        firewalls    = Firewall.query.filter_by(site_id=site.id).order_by(Firewall.name).all()
        hardware     = Hardware.query.filter_by(site_id=site.id).order_by(Hardware.name).all()
        networks     = Network.query.filter_by(site_id=site.id).order_by(Network.vlan_id).all()
        storage_list = Storage.query.filter_by(site_id=site.id).order_by(Storage.name).all()
        clients      = ClientDevice.query.filter_by(site_id=site.id).order_by(ClientDevice.name).all()
        connections  = Connection.query.all()

        # Split Misc into external (internet-layer) and internal
        all_misc = Misc.query.filter_by(site_id=site.id).order_by(Misc.name).all()
        for m in all_misc:
            if m.category and m.category.lower() in EXTERNAL_CATEGORIES:
                external_misc.append(m)
            else:
                misc_list.append(m)

        net_map = {n.id: n for n in networks}

        for hw in hardware:
            # Group hardware by cluster name
            cluster = (
                hw.hypervisor.cluster_name
                if hw.hypervisor and hw.hypervisor.cluster_name
                else None
            )
            key = cluster or "_ungrouped"
            if key not in hw_clusters:
                hw_clusters[key] = []
            hw_clusters[key].append(hw)

            # Build VM groups per VLAN
            if not hw.hypervisor:
                continue
            vms = sorted(
                VM.query.filter_by(hypervisor_id=hw.hypervisor.id).all(),
                key=_vm_sort_key,
            )
            groups: dict = {}
            for vm in vms:
                nid = vm.network_id
                if nid not in groups:
                    net = net_map.get(nid) if nid else None
                    groups[nid] = {
                        "network": net,
                        "name": net.name if net else "Unassigned",
                        "vlan_id": net.vlan_id if net else None,
                        "color": net.color if net else "#888888",
                        "vms": [],
                    }
                groups[nid]["vms"].append(vm)

            hw_vms[hw.id] = sorted(groups.values(), key=_group_sort_key)

    return render_template(
        "diagram.html",
        sites=sites,
        site=site,
        isps=isps,
        firewalls=firewalls,
        hardware=hardware,
        hw_clusters=hw_clusters,
        networks=networks,
        storage_list=storage_list,
        misc_list=misc_list,
        external_misc=external_misc,
        clients=clients,
        connections=connections,
        hw_vms=hw_vms,
    )
