function openFormModal(title, formHtml, action, data) {
  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-body').innerHTML = formHtml;

  const form = document.getElementById('modal-form');
  if (!form) return;

  form.action = action;

  if (data) {
    populateForm(form, data);
  }

  document.getElementById('modal-overlay').classList.remove('hidden');
  setTimeout(() => {
    const first = form.querySelector('input:not([type=hidden]), select, textarea');
    if (first) first.focus();
  }, 50);
}

function populateForm(form, data) {
  Object.entries(data).forEach(([key, val]) => {
    const el = form.querySelector(`[name="${key}"]`);
    if (!el) return;
    if (el.type === 'checkbox') {
      el.checked = !!val;
      // trigger any onchange handlers (e.g. hypervisor toggle)
      el.dispatchEvent(new Event('change'));
    } else if (el.tagName === 'SELECT') {
      el.value = val != null ? String(val) : '';
    } else {
      el.value = val != null ? val : '';
    }
  });
}

function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
  document.getElementById('modal-body').innerHTML = '';
}

// Close modal on overlay click
document.getElementById('modal-overlay')?.addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});

// Close modal on Escape
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeModal();
});

// Sidebar toggle
document.getElementById('sidebar-toggle')?.addEventListener('click', function() {
  document.getElementById('sidebar').classList.toggle('collapsed');
});

// Auto-dismiss flash messages after 4s
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => el.style.opacity = '0', 3500);
  setTimeout(() => el.remove(), 4000);
  el.style.transition = 'opacity 0.5s';
});
