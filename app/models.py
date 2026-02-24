from app.database import db
from datetime import datetime


class Site(db.Model):
    __tablename__ = "sites"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(200))
    address = db.Column(db.String(300))
    timezone = db.Column(db.String(60))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    isps = db.relationship("ISP", backref="site", lazy=True, cascade="all, delete-orphan")
    hardware = db.relationship("Hardware", backref="site", lazy=True, cascade="all, delete-orphan")
    firewalls = db.relationship("Firewall", backref="site", lazy=True, cascade="all, delete-orphan")
    vms = db.relationship("VM", backref="site", lazy=True, cascade="all, delete-orphan")
    storage = db.relationship("Storage", backref="site", lazy=True, cascade="all, delete-orphan")
    networks = db.relationship("Network", backref="site", lazy=True, cascade="all, delete-orphan")
    clients = db.relationship("ClientDevice", backref="site", lazy=True, cascade="all, delete-orphan")
    misc = db.relationship("Misc", backref="site", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "address": self.address,
            "timezone": self.timezone,
            "notes": self.notes,
        }


class ISP(db.Model):
    __tablename__ = "isps"
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey("sites.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(60))          # fiber, cable, lte, satellite
    asn = db.Column(db.String(20))
    public_ip_range = db.Column(db.String(200))
    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "name": self.name,
            "type": self.type,
            "asn": self.asn,
            "public_ip_range": self.public_ip_range,
            "notes": self.notes,
        }


class Hardware(db.Model):
    __tablename__ = "hardware"
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey("sites.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    device_type = db.Column(db.String(60), default="server")  # server, switch, router, nas, other
    role = db.Column(db.String(120))
    status = db.Column(db.String(30), default="active")       # active, offline, maintenance
    ip_mgmt = db.Column(db.String(60))
    cpu_cores = db.Column(db.Integer)
    ram_gb = db.Column(db.Integer)
    rack_position = db.Column(db.String(60))
    make_model = db.Column(db.String(120))
    notes = db.Column(db.Text)

    hypervisor = db.relationship("Hypervisor", backref="hardware", uselist=False, cascade="all, delete-orphan")
    apps = db.relationship("App", backref="hardware", lazy=True, cascade="all, delete-orphan",
                           primaryjoin="App.hardware_id == Hardware.id")

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "name": self.name,
            "device_type": self.device_type,
            "role": self.role,
            "status": self.status,
            "ip_mgmt": self.ip_mgmt,
            "cpu_cores": self.cpu_cores,
            "ram_gb": self.ram_gb,
            "rack_position": self.rack_position,
            "make_model": self.make_model,
            "notes": self.notes,
        }


class Hypervisor(db.Model):
    __tablename__ = "hypervisors"
    id = db.Column(db.Integer, primary_key=True)
    hardware_id = db.Column(db.Integer, db.ForeignKey("hardware.id"), nullable=False)
    cluster_name = db.Column(db.String(120))
    hypervisor_type = db.Column(db.String(60), default="proxmox")  # proxmox, esxi, kvm, hyper-v
    notes = db.Column(db.Text)

    vms = db.relationship("VM", backref="hypervisor", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "hardware_id": self.hardware_id,
            "cluster_name": self.cluster_name,
            "hypervisor_type": self.hypervisor_type,
            "notes": self.notes,
        }


class Firewall(db.Model):
    __tablename__ = "firewalls"
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey("sites.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    public_ip = db.Column(db.String(60))
    management_ip = db.Column(db.String(60))
    model = db.Column(db.String(120))
    status = db.Column(db.String(30), default="active")
    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "name": self.name,
            "public_ip": self.public_ip,
            "management_ip": self.management_ip,
            "model": self.model,
            "status": self.status,
            "notes": self.notes,
        }


class Network(db.Model):
    __tablename__ = "networks"
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey("sites.id"), nullable=False)
    vlan_id = db.Column(db.Integer)
    name = db.Column(db.String(120), nullable=False)
    subnet = db.Column(db.String(60))
    color = db.Column(db.String(10), default="#6366f1")  # hex color for diagram
    description = db.Column(db.Text)

    vms = db.relationship("VM", backref="network", lazy=True)
    clients = db.relationship("ClientDevice", backref="network", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "vlan_id": self.vlan_id,
            "name": self.name,
            "subnet": self.subnet,
            "color": self.color,
            "description": self.description,
        }


class VM(db.Model):
    __tablename__ = "vms"
    id = db.Column(db.Integer, primary_key=True)
    hypervisor_id = db.Column(db.Integer, db.ForeignKey("hypervisors.id"), nullable=True)
    site_id = db.Column(db.Integer, db.ForeignKey("sites.id"), nullable=False)
    network_id = db.Column(db.Integer, db.ForeignKey("networks.id"), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    os = db.Column(db.String(80))
    ip_address = db.Column(db.String(60))
    cpu_cores = db.Column(db.Integer)
    ram_gb = db.Column(db.Integer)
    storage_gb = db.Column(db.Integer)
    role = db.Column(db.String(120))
    status = db.Column(db.String(30), default="active")
    public_exposed = db.Column(db.Boolean, default=False)
    public_label = db.Column(db.String(60))   # e.g. "Cloudflare", "Direct", "VPN"
    notes = db.Column(db.Text)

    apps = db.relationship("App", backref="vm", lazy=True, cascade="all, delete-orphan",
                           primaryjoin="App.vm_id == VM.id")

    def to_dict(self):
        return {
            "id": self.id,
            "hypervisor_id": self.hypervisor_id,
            "site_id": self.site_id,
            "network_id": self.network_id,
            "name": self.name,
            "os": self.os,
            "ip_address": self.ip_address,
            "cpu_cores": self.cpu_cores,
            "ram_gb": self.ram_gb,
            "storage_gb": self.storage_gb,
            "role": self.role,
            "status": self.status,
            "public_exposed": self.public_exposed,
            "public_label": self.public_label or "",
            "notes": self.notes,
        }


class App(db.Model):
    __tablename__ = "apps"
    id = db.Column(db.Integer, primary_key=True)
    vm_id = db.Column(db.Integer, db.ForeignKey("vms.id"), nullable=True)
    hardware_id = db.Column(db.Integer, db.ForeignKey("hardware.id"), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    version = db.Column(db.String(40))
    port = db.Column(db.Integer)
    protocol = db.Column(db.String(10), default="tcp")
    public_exposed = db.Column(db.Boolean, default=False)
    url = db.Column(db.String(300))
    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "vm_id": self.vm_id,
            "hardware_id": self.hardware_id,
            "name": self.name,
            "version": self.version,
            "port": self.port,
            "protocol": self.protocol,
            "public_exposed": self.public_exposed,
            "url": self.url,
            "notes": self.notes,
        }


class Storage(db.Model):
    __tablename__ = "storage"
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey("sites.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(40), default="nas")  # nas, san, cloud, local, tape
    capacity_tb = db.Column(db.Float)
    ip_address = db.Column(db.String(60))
    protocol = db.Column(db.String(80))             # NFS, SMB, iSCSI, S3, etc.
    make_model = db.Column(db.String(120))
    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "name": self.name,
            "type": self.type,
            "capacity_tb": self.capacity_tb,
            "ip_address": self.ip_address,
            "protocol": self.protocol,
            "make_model": self.make_model,
            "notes": self.notes,
        }


class ClientDevice(db.Model):
    __tablename__ = "client_devices"
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey("sites.id"), nullable=False)
    network_id = db.Column(db.Integer, db.ForeignKey("networks.id"), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    owner = db.Column(db.String(120))
    device_type = db.Column(db.String(40), default="laptop")  # laptop, desktop, phone, iot, printer
    ip_address = db.Column(db.String(60))
    mac_address = db.Column(db.String(20))
    os = db.Column(db.String(80))
    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "network_id": self.network_id,
            "name": self.name,
            "owner": self.owner,
            "device_type": self.device_type,
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "os": self.os,
            "notes": self.notes,
        }


class Misc(db.Model):
    __tablename__ = "misc"
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey("sites.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80))
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(60))
    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "ip_address": self.ip_address,
            "notes": self.notes,
        }


class Connection(db.Model):
    """Graph edge between any two entities."""
    __tablename__ = "connections"
    id = db.Column(db.Integer, primary_key=True)
    from_type = db.Column(db.String(40), nullable=False)  # isp, hardware, firewall, vm, storage, network, etc.
    from_id = db.Column(db.Integer, nullable=False)
    to_type = db.Column(db.String(40), nullable=False)
    to_id = db.Column(db.Integer, nullable=False)
    label = db.Column(db.String(120))
    color = db.Column(db.String(10), default="#333333")
    style = db.Column(db.String(20), default="solid")   # solid, dashed
    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "from_type": self.from_type,
            "from_id": self.from_id,
            "to_type": self.to_type,
            "to_id": self.to_id,
            "label": self.label,
            "color": self.color,
            "style": self.style,
            "notes": self.notes,
        }


class MapLayout(db.Model):
    """Saved node positions for the network map."""
    __tablename__ = "map_layout"
    id = db.Column(db.Integer, primary_key=True)
    node_type = db.Column(db.String(40), nullable=False)
    node_id = db.Column(db.Integer, nullable=False)
    x = db.Column(db.Float, default=0)
    y = db.Column(db.Float, default=0)

    def to_dict(self):
        return {
            "node_type": self.node_type,
            "node_id": self.node_id,
            "x": self.x,
            "y": self.y,
        }
