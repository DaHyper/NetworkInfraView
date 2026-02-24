/* map.js — NetworkInfraView Cytoscape.js network map */

let cy = null;
let pendingEdgeSource = null;

// ── Type appearance ──────────────────────────────────────────────
const TYPE_STYLES = {
  site:     { bg: '#1e3a8a', border: '#1e40af', shape: 'rectangle', textColor: '#fff', size: 50 },
  isp:      { bg: '#0891b2', border: '#0e7490', shape: 'ellipse',   textColor: '#fff', size: 40 },
  firewall: { bg: '#dc2626', border: '#b91c1c', shape: 'diamond',   textColor: '#fff', size: 44 },
  hardware: { bg: '#4b5563', border: '#374151', shape: 'rectangle', textColor: '#fff', size: 46 },
  vm:       { bg: '#16a34a', border: '#15803d', shape: 'round-rectangle', textColor: '#fff', size: 38 },
  network:  { bg: '#d97706', border: '#b45309', shape: 'hexagon',   textColor: '#fff', size: 44 },
  storage:  { bg: '#7c3aed', border: '#6d28d9', shape: 'barrel',    textColor: '#fff', size: 42 },
  client:   { bg: '#be185d', border: '#9d174d', shape: 'ellipse',   textColor: '#fff', size: 36 },
  misc:     { bg: '#64748b', border: '#475569', shape: 'pentagon',  textColor: '#fff', size: 36 },
};

function nodeStyle(type) {
  return TYPE_STYLES[type] || TYPE_STYLES.misc;
}

function buildStylesheet() {
  const baseNode = {
    'label': 'data(label)',
    'text-valign': 'center',
    'text-halign': 'center',
    'font-family': 'Arial, sans-serif',
    'font-size': '10px',
    'text-wrap': 'wrap',
    'text-max-width': '80px',
    'color': '#fff',
    'text-outline-width': 1,
    'text-outline-color': 'data(bgColor)',
    'width': 48,
    'height': 48,
    'border-width': 2,
    'cursor': 'pointer',
  };

  const styles = [
    { selector: 'node', style: baseNode },
    { selector: 'node:selected', style: { 'border-width': 3, 'border-color': '#f59e0b', 'border-style': 'solid' } },
    {
      selector: 'edge', style: {
        'width': 1.5,
        'line-color': 'data(color)',
        'target-arrow-color': 'data(color)',
        'target-arrow-shape': 'triangle',
        'arrow-scale': 0.8,
        'curve-style': 'bezier',
        'label': 'data(label)',
        'font-size': '9px',
        'text-background-color': '#fff',
        'text-background-opacity': 0.8,
        'text-background-padding': '2px',
        'color': '#555',
        'line-style': 'solid',
      }
    },
    // Dashed edges — uses lineStyle data field to avoid Cytoscape style key conflict
    { selector: 'edge[lineStyle="dashed"]', style: { 'line-style': 'dashed', 'line-dash-pattern': [6, 4] } },
  ];

  // Per-type node styles
  Object.entries(TYPE_STYLES).forEach(([type, s]) => {
    styles.push({
      selector: `.node-${type}`,
      style: {
        'background-color': s.bg,
        'border-color': s.border,
        'shape': s.shape,
        'width': s.size,
        'height': s.size,
        'text-outline-color': s.bg,
      }
    });
  });

  // Status tints
  styles.push({ selector: '.status-offline',     style: { 'opacity': 0.5 } });
  styles.push({ selector: '.status-maintenance', style: { 'border-style': 'dashed', 'border-width': 2 } });
  styles.push({ selector: '.node-public',        style: { 'border-color': '#f59e0b', 'border-width': 3 } });
  // Site nodes larger
  styles.push({ selector: '.node-site', style: { 'width': 70, 'height': 40, 'font-size': '12px', 'font-weight': 'bold' } });

  return styles;
}

// ── Init ──────────────────────────────────────────────────────────
function initCytoscape() {
  cy = cytoscape({
    container: document.getElementById('cy-container'),
    elements: [],
    style: buildStylesheet(),
    layout: { name: 'preset' },
    wheelSensitivity: 0.3,
    minZoom: 0.1,
    maxZoom: 5,
  });

  // Click node — if drawing a connection, handle that; otherwise show detail panel
  cy.on('tap', 'node', function(e) {
    const data = e.target.data();
    if (pendingEdgeSource) {
      if (data.id !== pendingEdgeSource.id) {
        openConnectionModal(pendingEdgeSource, data);
      }
      cancelConnectionMode();
      return;
    }
    showDetailPanel(data);
  });

  // Right-click edge → delete option
  cy.on('cxttap', 'edge', function(e) {
    const edge = e.target;
    if (edge.data('id').startsWith('conn-')) {
      if (confirm(`Delete connection "${edge.data('label') || edge.data('id')}"?`)) {
        const connId = edge.data('id').replace('conn-', '');
        fetch(`/map/api/connections/${connId}`, { method: 'DELETE' })
          .then(() => { cy.remove(edge); });
      }
    }
  });

  // Click background → clear selection / cancel connection mode
  cy.on('tap', function(e) {
    if (e.target === cy) {
      if (pendingEdgeSource) {
        cancelConnectionMode();
      } else {
        closeDetailPanel();
      }
    }
  });

  loadGraph();
}

// ── Load graph data ───────────────────────────────────────────────
function loadGraph() {
  const siteId = document.getElementById('site-filter')?.value || '';
  const url = `/map/api/graph${siteId ? '?site_id=' + siteId : ''}`;
  fetch(url)
    .then(r => r.json())
    .then(data => {
      cy.elements().remove();
      cy.add(data.nodes);
      cy.add(data.edges);
      applyLayout();
    });
}

// ── Layout ────────────────────────────────────────────────────────
function applyLayout() {
  const layoutName = document.getElementById('layout-select')?.value || 'cose';

  // If nodes have saved positions and user hasn't forced a re-layout, use them
  const hasPositions = cy.nodes().some(n => n.position().x !== 0 || n.position().y !== 0);

  if (layoutName === 'preset' || (hasPositions && layoutName !== 'cose' && layoutName !== 'grid' && layoutName !== 'breadthfirst' && layoutName !== 'dagre')) {
    cy.layout({ name: 'preset' }).run();
    cy.fit(undefined, 40);
    return;
  }

  const layoutConfig = {
    // Hierarchical top-down — auto-detects roots (nodes with no incoming edges = Sites)
    dagre: {
      name: 'breadthfirst',
      directed: true,
      spacingFactor: 2.0,
      padding: 60,
      animate: true,
      animationDuration: 500,
    },
    // Hierarchical top-down: Site → ISP → Firewall → Hardware → VM
    breadthfirst: {
      name: 'breadthfirst',
      directed: true,
      roots: '.node-site',
      spacingFactor: 2.0,
      padding: 60,
      animate: true,
      animationDuration: 400,
    },
    // Force-directed — best for mixed/disconnected graphs (default)
    cose: {
      name: 'cose',
      animate: true,
      animationDuration: 700,
      padding: 60,
      idealEdgeLength: 160,
      nodeRepulsion: 18000,
      gravity: 0.2,
      numIter: 1500,
      nodeOverlap: 30,
      componentSpacing: 80,
    },
    grid: {
      name: 'grid',
      padding: 40,
      animate: true,
      avoidOverlapPadding: 20,
    },
    preset: { name: 'preset' },
  };

  cy.layout(layoutConfig[layoutName] || layoutConfig.cose).run();
  cy.fit(undefined, 40);
}

// ── Detail panel ──────────────────────────────────────────────────
const DETAIL_LABELS = {
  type: 'Type',
  entity_id: null,   // hide
  bgColor: null,
  network_color: null,
  parent_site: null,
  isp_type: 'ISP Type',
  asn: 'ASN',
  public_ip_range: 'Public IP Range',
  device_type: 'Device Type',
  role: 'Role',
  ip_mgmt: 'Mgmt IP',
  make_model: 'Make / Model',
  status: 'Status',
  is_hypervisor: 'Hypervisor',
  hypervisor_type: 'Hypervisor Type',
  public_ip: 'Public IP',
  management_ip: 'Mgmt IP',
  model: 'Model',
  os: 'OS',
  ip_address: 'IP Address',
  public_exposed: 'Internet-Facing',
  network_name: 'Network',
  vlan_id: 'VLAN ID',
  subnet: 'Subnet',
  color: null,
  storage_type: 'Storage Type',
  capacity_tb: 'Capacity (TB)',
  protocol: 'Protocol',
  owner: 'Owner',
  location: 'Location',
  sublabel: null,
};

function showDetailPanel(data) {
  document.getElementById('detail-name').textContent = data.label || 'Node';
  const container = document.getElementById('detail-content');
  container.innerHTML = '';

  const typeStyle = TYPE_STYLES[data.type] || {};
  const badge = document.createElement('div');
  badge.style.cssText = `display:inline-block;padding:2px 8px;border-radius:3px;font-size:10px;font-weight:bold;background:${typeStyle.bg || '#888'};color:#fff;margin-bottom:10px;`;
  badge.textContent = (data.type || 'unknown').toUpperCase();
  container.appendChild(badge);

  Object.entries(data).forEach(([key, val]) => {
    if (key === 'id' || key === 'label') return;
    const label = DETAIL_LABELS[key];
    if (label === null) return;
    if (!val && val !== 0) return;

    const row = document.createElement('div');
    row.className = 'detail-row';
    const lbl = document.createElement('div');
    lbl.className = 'detail-label';
    lbl.textContent = label || key;
    const val_el = document.createElement('div');

    if (key === 'public_exposed' || key === 'is_hypervisor') {
      val_el.textContent = val ? 'Yes' : 'No';
      val_el.style.color = val ? '#dc2626' : '#6b7280';
    } else if (key === 'status') {
      val_el.innerHTML = `<span class="badge badge-${val}">${val}</span>`;
    } else {
      val_el.textContent = String(val);
    }
    row.appendChild(lbl);
    row.appendChild(val_el);
    container.appendChild(row);
  });

  // Add connection button
  const addConnBtn = document.createElement('button');
  addConnBtn.className = 'btn btn-sm mt-16';
  addConnBtn.style.width = '100%';
  addConnBtn.textContent = '+ Draw connection from this node';
  addConnBtn.onclick = () => startDrawConnection(data);
  container.appendChild(addConnBtn);

  document.getElementById('detail-panel').classList.add('open');
}

function closeDetailPanel() {
  document.getElementById('detail-panel').classList.remove('open');
  // Note: does NOT clear pendingEdgeSource — cancelConnectionMode() handles that
}

// ── Connection drawing ────────────────────────────────────────────
function startDrawConnection(sourceData) {
  pendingEdgeSource = sourceData;
  closeDetailPanel();
  // Show banner instead of highlighting every node gold
  const banner = document.getElementById('conn-banner');
  banner.querySelector('.conn-banner-label').textContent =
    `Drawing from "${sourceData.label}" — click the target node`;
  banner.classList.remove('hidden');
}

function cancelConnectionMode() {
  pendingEdgeSource = null;
  document.getElementById('conn-banner').classList.add('hidden');
}

function openConnectionModal(source, target) {
  document.getElementById('conn-from').value = source.label + ' (' + source.id + ')';
  document.getElementById('conn-to').value   = target.label + ' (' + target.id + ')';
  document.getElementById('conn-modal').dataset.sourceId = source.id;
  document.getElementById('conn-modal').dataset.targetId = target.id;
  document.getElementById('conn-modal').classList.remove('hidden');
}

function saveConnection() {
  const modal = document.getElementById('conn-modal');
  const srcId = modal.dataset.sourceId;
  const tgtId = modal.dataset.targetId;

  const parseNodeId = (id) => {
    const parts = id.split('-');
    return { type: parts.slice(0, -1).join('-'), id: parseInt(parts[parts.length - 1]) };
  };
  const src = parseNodeId(srcId);
  const tgt = parseNodeId(tgtId);

  const label    = document.getElementById('conn-label').value;
  const color    = document.getElementById('conn-color').value;
  const lineStyle = document.getElementById('conn-style').value;

  fetch('/map/api/connections', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from_type: src.type,
      from_id: src.id,
      to_type: tgt.type,
      to_id: tgt.id,
      label,
      color,
      style: lineStyle,   // server still stores it as "style" in DB column
    })
  })
  .then(r => r.json())
  .then(data => {
    cy.add({
      data: {
        id: `conn-${data.id}`,
        source: srcId,
        target: tgtId,
        label,
        color,
        lineStyle,  // use lineStyle so Cytoscape selector [lineStyle="dashed"] works
      }
    });
    modal.classList.add('hidden');
  });
}

// ── Save layout positions ─────────────────────────────────────────
function saveLayout(btn) {
  const positions = cy.nodes().map(n => ({
    id: n.data('id'),
    x: n.position('x'),
    y: n.position('y'),
  }));
  fetch('/map/api/layout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(positions),
  }).then(() => {
    btn.textContent = '✓ Saved';
    setTimeout(() => { btn.textContent = '💾 Save Positions'; }, 1500);
  });
}

// ── Export functions ──────────────────────────────────────────────
function exportPNG() {
  const png = cy.png({ output: 'blob', scale: 2, bg: '#ffffff' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(png);
  a.download = 'network-diagram.png';
  a.click();
}

function exportSVG() {
  const png64 = cy.png({ output: 'base64', scale: 2, bg: '#ffffff' });
  const bb = cy.extent();
  const w = Math.round((bb.x2 - bb.x1) * 2 + 80);
  const h = Math.round((bb.y2 - bb.y1) * 2 + 80);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">
  <image href="data:image/png;base64,${png64}" width="${w}" height="${h}"/>
</svg>`;
  const blob = new Blob([svg], { type: 'image/svg+xml' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'network-diagram.svg';
  a.click();
}

function exportHTML() {
  const png64 = cy.png({ output: 'base64', scale: 2, bg: '#ffffff' });
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Network Diagram — ${new Date().toLocaleDateString()}</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Arial, sans-serif; font-size: 11px; color: #111; background: #fff; padding: 24px; }
h1 { text-align: center; font-size: 14px; margin-bottom: 4px; }
.sub { text-align: center; font-size: 10px; color: #888; margin-bottom: 20px; }
img { max-width: 100%; border: 1px solid #ddd; border-radius: 4px; }
.footer { margin-top: 16px; text-align: center; font-size: 9px; color: #aaa; }
</style>
</head>
<body>
<h1>Network Diagram</h1>
<p class="sub">Exported from NetworkInfraView &middot; ${new Date().toLocaleString()}</p>
<img src="data:image/png;base64,${png64}" alt="Network Diagram">
<div class="footer">Generated by NetworkInfraView</div>
</body>
</html>`;
  const blob = new Blob([html], { type: 'text/html' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'network-diagram.html';
  a.click();
}

// ── Bootstrap ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  if (typeof cytoscape === 'undefined') {
    document.getElementById('cy-container').innerHTML =
      '<div style="padding:40px;text-align:center;color:#888;">Error: Cytoscape.js failed to load.</div>';
    return;
  }
  initCytoscape();
});
