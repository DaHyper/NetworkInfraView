# NetworkInfraView — JSON/YAML Export Format

This document explains the structure of the JSON and YAML exports from NetworkInfraView.
Use this as a reference when feeding your inventory into an LLM (ChatGPT, Claude, etc.)
to generate network diagrams, documentation, or infrastructure analysis.

---

## Top-Level Structure

```json
{
  "export_version": "1.0",
  "exported_at": "2025-01-15T14:30:00Z",
  "app": "NetworkInfraView",
  "data": {
    "sites":       [...],
    "isps":        [...],
    "hardware":    [...],
    "hypervisors": [...],
    "firewalls":   [...],
    "vms":         [...],
    "apps":        [...],
    "storage":     [...],
    "networks":    [...],
    "clients":     [...],
    "misc":        [...],
    "connections": [...]
  }
}
```

All entity arrays live inside `data`. Foreign keys use numeric IDs that cross-reference
other records within the same export (e.g., `site_id` in a hardware record matches the
`id` of a site record).

---

## Entity Reference

### sites
Physical or logical locations. Everything else belongs to a site.

| Field      | Type   | Description                              |
|------------|--------|------------------------------------------|
| id         | int    | Unique identifier                        |
| name       | string | Site name (e.g. "HQ", "Lab-01")         |
| location   | string | City, region (e.g. "New York, NY")      |
| address    | string | Street address                           |
| timezone   | string | IANA timezone (e.g. "America/New_York") |
| notes      | string | Free-form notes                          |

```json
{ "id": 1, "name": "HQ", "location": "New York, NY", "address": "123 Main St",
  "timezone": "America/New_York", "notes": "" }
```

---

### isps
Internet service providers connected to a site.

| Field           | Type   | Description                               |
|-----------------|--------|-------------------------------------------|
| id              | int    | Unique identifier                         |
| site_id         | int    | Foreign key → sites.id                   |
| name            | string | ISP name (e.g. "Comcast Business")       |
| type            | string | fiber / cable / lte / satellite / other   |
| asn             | string | BGP Autonomous System Number              |
| public_ip_range | string | Public IP range or CIDR block             |
| notes           | string | Free-form notes                           |

```json
{ "id": 1, "site_id": 1, "name": "Comcast Business", "type": "fiber",
  "asn": "AS7922", "public_ip_range": "203.0.113.0/28", "notes": "" }
```

---

### hardware
Physical devices: servers, switches, routers, NAS units, etc.

| Field         | Type   | Description                                            |
|---------------|--------|--------------------------------------------------------|
| id            | int    | Unique identifier                                      |
| site_id       | int    | Foreign key → sites.id                                |
| name          | string | Device hostname/label (e.g. "PX-Node1")               |
| device_type   | string | server / switch / router / firewall / nas / other      |
| role          | string | Functional role (e.g. "Hypervisor", "Core Switch")    |
| status        | string | active / offline / maintenance                         |
| ip_mgmt       | string | Management IP address (IPv4 or IPv6)                   |
| cpu_cores     | int    | Number of CPU cores (null if unknown)                  |
| ram_gb        | int    | RAM in GB (null if unknown)                            |
| rack_position | string | Rack slot label (e.g. "U12")                          |
| make_model    | string | Manufacturer and model (e.g. "Dell PowerEdge R750")   |
| notes         | string | Free-form notes                                        |

```json
{ "id": 1, "site_id": 1, "name": "PX-Node1", "device_type": "server",
  "role": "Hypervisor", "status": "active", "ip_mgmt": "192.168.1.10",
  "cpu_cores": 32, "ram_gb": 256, "rack_position": "U4",
  "make_model": "Dell PowerEdge R750", "notes": "" }
```

---

### hypervisors
Virtualization hosts attached to a hardware record. A hardware item can have at most one hypervisor entry.

| Field           | Type   | Description                                      |
|-----------------|--------|--------------------------------------------------|
| id              | int    | Unique identifier                                |
| hardware_id     | int    | Foreign key → hardware.id                       |
| cluster_name    | string | Cluster or datacenter name (e.g. "proxmox-dc1") |
| hypervisor_type | string | proxmox / esxi / kvm / hyper-v / other          |
| notes           | string | Free-form notes                                  |

```json
{ "id": 1, "hardware_id": 1, "cluster_name": "proxmox-dc1",
  "hypervisor_type": "proxmox", "notes": "" }
```

---

### firewalls
Firewall appliances (may overlap with hardware; this captures firewall-specific attributes).

| Field         | Type   | Description                                       |
|---------------|--------|---------------------------------------------------|
| id            | int    | Unique identifier                                 |
| site_id       | int    | Foreign key → sites.id                           |
| name          | string | Firewall hostname/label                           |
| public_ip     | string | WAN-facing IP address                             |
| management_ip | string | Management/LAN IP address                         |
| model         | string | Appliance model (e.g. "pfSense", "FortiGate 60F")|
| status        | string | active / offline / maintenance                    |
| notes         | string | Free-form notes                                   |

```json
{ "id": 1, "site_id": 1, "name": "FW-HQ-01", "public_ip": "203.0.113.1",
  "management_ip": "192.168.1.1", "model": "pfSense 2.7",
  "status": "active", "notes": "" }
```

---

### networks
VLANs and subnets. Used for grouping VMs and clients in diagrams.

| Field       | Type   | Description                                        |
|-------------|--------|----------------------------------------------------|
| id          | int    | Unique identifier                                  |
| site_id     | int    | Foreign key → sites.id                            |
| vlan_id     | int    | 802.1Q VLAN tag (null if untagged)                |
| name        | string | Network name (e.g. "VLAN-10-Servers")             |
| subnet      | string | CIDR notation (e.g. "192.168.10.0/24")            |
| color       | string | Hex color for diagram display (e.g. "#6366f1")    |
| description | string | Purpose or notes                                   |

```json
{ "id": 1, "site_id": 1, "vlan_id": 10, "name": "VLAN-10-Servers",
  "subnet": "192.168.10.0/24", "color": "#6366f1",
  "description": "Production server VLAN" }
```

---

### vms
Virtual machines running on a hypervisor (or bare-metal if `hypervisor_id` is null).

| Field         | Type    | Description                                      |
|---------------|---------|--------------------------------------------------|
| id            | int     | Unique identifier                                |
| site_id       | int     | Foreign key → sites.id                          |
| hypervisor_id | int     | Foreign key → hypervisors.id (null = bare-metal)|
| network_id    | int     | Foreign key → networks.id (null = unassigned)   |
| name          | string  | VM hostname                                      |
| os            | string  | Operating system (e.g. "Ubuntu 22.04 LTS")      |
| ip_address    | string  | Primary IP address                               |
| cpu_cores     | int     | Allocated vCPUs                                  |
| ram_gb        | int     | Allocated RAM in GB                              |
| storage_gb    | int     | Allocated storage in GB                          |
| role          | string  | Functional role (e.g. "Web Server", "Database") |
| status        | string  | active / offline / maintenance                   |
| public_exposed| bool    | true if accessible from the internet             |
| notes         | string  | Free-form notes                                  |

```json
{ "id": 1, "site_id": 1, "hypervisor_id": 1, "network_id": 1,
  "name": "web-prod-01", "os": "Ubuntu 22.04 LTS",
  "ip_address": "192.168.10.11", "cpu_cores": 4, "ram_gb": 8,
  "storage_gb": 100, "role": "Web Server", "status": "active",
  "public_exposed": true, "notes": "" }
```

---

### apps
Applications and services running on a VM or directly on hardware.

| Field          | Type   | Description                                          |
|----------------|--------|------------------------------------------------------|
| id             | int    | Unique identifier                                    |
| vm_id          | int    | Foreign key → vms.id (null if on bare hardware)     |
| hardware_id    | int    | Foreign key → hardware.id (null if on a VM)         |
| name           | string | App/service name (e.g. "Nginx", "PostgreSQL")       |
| version        | string | Version string (e.g. "1.25.3")                     |
| port           | int    | Listening port number                               |
| protocol       | string | tcp / udp                                           |
| public_exposed | bool   | true if accessible from the internet                |
| url            | string | Access URL (e.g. "https://app.example.com")         |
| notes          | string | Free-form notes                                     |

> Either `vm_id` or `hardware_id` will be set; the other will be null.

```json
{ "id": 1, "vm_id": 1, "hardware_id": null, "name": "Nginx",
  "version": "1.25.3", "port": 443, "protocol": "tcp",
  "public_exposed": true, "url": "https://app.example.com", "notes": "" }
```

---

### storage
Storage devices and services (NAS, SAN, cloud buckets, etc.).

| Field       | Type   | Description                                              |
|-------------|--------|----------------------------------------------------------|
| id          | int    | Unique identifier                                        |
| site_id     | int    | Foreign key → sites.id                                  |
| name        | string | Storage unit name (e.g. "NAS-HQ-01")                   |
| type        | string | nas / san / cloud / local / tape                        |
| capacity_tb | float  | Total capacity in terabytes                             |
| ip_address  | string | Network address (null for local or cloud)               |
| protocol    | string | Access protocol(s) (e.g. "NFS, SMB", "iSCSI", "S3")   |
| make_model  | string | Hardware/software platform (e.g. "Synology DS923+")    |
| notes       | string | Free-form notes                                         |

```json
{ "id": 1, "site_id": 1, "name": "NAS-HQ-01", "type": "nas",
  "capacity_tb": 48.0, "ip_address": "192.168.1.20",
  "protocol": "NFS, SMB", "make_model": "Synology DS923+", "notes": "" }
```

---

### clients
End-user devices and IoT equipment on the network.

| Field       | Type   | Description                                          |
|-------------|--------|------------------------------------------------------|
| id          | int    | Unique identifier                                    |
| site_id     | int    | Foreign key → sites.id                              |
| network_id  | int    | Foreign key → networks.id (null = unassigned)       |
| name        | string | Device name/hostname                                 |
| owner       | string | Person or team responsible for the device           |
| device_type | string | laptop / desktop / phone / iot / printer / other    |
| ip_address  | string | IP address (may be DHCP-assigned)                   |
| mac_address | string | MAC address (e.g. "AA:BB:CC:DD:EE:FF")              |
| os          | string | Operating system                                    |
| notes       | string | Free-form notes                                     |

```json
{ "id": 1, "site_id": 1, "network_id": 2, "name": "jdoe-laptop",
  "owner": "Jane Doe", "device_type": "laptop",
  "ip_address": "192.168.20.55", "mac_address": "AA:BB:CC:11:22:33",
  "os": "macOS 14 Sonoma", "notes": "" }
```

---

### misc
Catch-all for infrastructure items that don't fit other categories (UPS units, KVMs, OOB managers, etc.).

| Field       | Type   | Description             |
|-------------|--------|-------------------------|
| id          | int    | Unique identifier       |
| site_id     | int    | Foreign key → sites.id |
| name        | string | Item name               |
| category    | string | Category label          |
| description | string | What it is/does         |
| ip_address  | string | IP address if any       |
| notes       | string | Free-form notes         |

```json
{ "id": 1, "site_id": 1, "name": "UPS-Rack-A", "category": "Power",
  "description": "APC Smart-UPS 3000VA for rack A",
  "ip_address": "192.168.1.250", "notes": "" }
```

---

### connections
Graph edges describing relationships between any two entities.
Used to draw lines on the network map.

| Field     | Type   | Description                                                      |
|-----------|--------|------------------------------------------------------------------|
| id        | int    | Unique identifier                                                |
| from_type | string | Source entity type: site / isp / hardware / firewall / vm / storage / network / client / misc |
| from_id   | int    | Source entity ID within its table                               |
| to_type   | string | Destination entity type (same options as from_type)             |
| to_id     | int    | Destination entity ID within its table                          |
| label     | string | Edge label shown on diagram (e.g. "1Gbps uplink")              |
| color     | string | Hex color for the edge (e.g. "#333333")                        |
| style     | string | solid / dashed                                                  |
| notes     | string | Free-form notes                                                 |

```json
{ "id": 1, "from_type": "isp", "from_id": 1, "to_type": "firewall", "to_id": 1,
  "label": "1Gbps fiber", "color": "#333333", "style": "solid", "notes": "" }
```

---

## Relationship Map

```
Site
├── ISP (site_id)
├── Hardware (site_id)
│   └── Hypervisor (hardware_id)
│       └── VM (hypervisor_id)  ← also has site_id, network_id
│           └── App (vm_id)
├── Firewall (site_id)
├── Storage (site_id)
├── Network / VLAN (site_id)
│   ├── VM (network_id)
│   └── ClientDevice (network_id)
├── ClientDevice (site_id)
└── Misc (site_id)

Connection → links any two entities by (type, id) pair
```

---

## Prompts for LLM Use

### Generate a network diagram description
> "Here is my network inventory in JSON format: [paste export]. Please describe my network topology in plain English, listing how traffic flows from the internet through the firewalls to the servers and VMs."

### Build a Mermaid diagram
> "Using the attached JSON export from NetworkInfraView, generate a Mermaid flowchart diagram showing the physical and logical topology. Group VMs under their hypervisors and color-code VLANs using the `color` field in the networks array."

### Identify risks or gaps
> "Review this network inventory JSON and identify any: (1) single points of failure, (2) devices with no redundancy, (3) VMs with `public_exposed: true` that have no firewall record at their site, (4) duplicate IP addresses."

### Generate documentation
> "Convert this YAML inventory into a structured Markdown document suitable for a runbook. Include a section per site, with tables for hardware, VMs, storage, and network segments."

### Create a Cytoscape.js node/edge dataset
> "Parse this NetworkInfraView JSON export and produce a Cytoscape.js `elements` array. Use the following node types: sites (rectangle), ISPs (diamond), firewalls (triangle), hardware (box), VMs (ellipse), networks (rounded rectangle). Use the `connections` array for edges, preserving `color` and `style` attributes."

---

## Notes on Import

- When re-importing a JSON/YAML file, **all existing data is replaced** (the importer clears tables first, then re-inserts in dependency order).
- IDs are remapped during import — old `id` values in the file do not need to match what gets stored; foreign key references within the file are resolved correctly.
- YAML exports contain the same data as JSON, just in YAML syntax. Both are always in sync.
- CSV imports are additive (they do not clear existing data) and are limited to: `sites`, `hardware`, `vms`, `networks`, `clients`.
