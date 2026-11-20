/**
 * FoodBridge - Admin Dashboard JavaScript
 * Handles NGO verification approvals, user role management, system audit logs
 */

document.addEventListener('DOMContentLoaded', () => {
  loadAdminDashboard();

  // Admin Tab Navigation
  const tabBtns = document.querySelectorAll('.admin-tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const targetView = btn.getAttribute('data-view');
      document.querySelectorAll('.admin-view-panel').forEach(panel => {
        panel.style.display = (panel.id === targetView) ? 'block' : 'none';
      });
    });
  });

  // User Filter Select
  const roleFilter = document.getElementById('admin-role-filter');
  if (roleFilter) {
    roleFilter.addEventListener('change', () => loadUsers(roleFilter.value));
  }
});

async function loadAdminDashboard() {
  await Promise.all([
    loadPendingNgos(),
    loadUsers(''),
    loadDonationsSurveillance(),
    loadAuditLogs()
  ]);
}

// 1. Pending NGO Verification
async function loadPendingNgos() {
  const tbody = document.getElementById('admin-pending-ngos-tbody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/admin/users?role=ngo&status=pending_verification');
    const data = await res.json();
    if (!data.success) return;

    const ngos = data.users.filter(u => u.verification_status === 'pending');
    const badgeCount = document.getElementById('admin-pending-count');
    if (badgeCount) badgeCount.innerText = ngos.length;

    if (ngos.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">
            🛡️ All NGO partner organizations are currently verified.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = ngos.map(n => `
      <tr>
        <td><strong>${n.organization_name || n.name}</strong></td>
        <td><code>${n.registration_no || 'NGO-PENDING'}</code></td>
        <td>${n.daily_capacity || 100} meals/day</td>
        <td>${n.address || 'Address provided'}</td>
        <td><span class="badge badge-medium">Pending Review</span></td>
        <td>
          <div style="display: flex; gap: 0.4rem;">
            <button class="btn btn-primary btn-sm" onclick="verifyNgo(${n.id}, 'verified')">
              ✓ Approve
            </button>
            <button class="btn btn-outline btn-sm" style="color: var(--danger); border-color: #fecaca;" onclick="verifyNgo(${n.id}, 'rejected')">
              ✕ Reject
            </button>
          </div>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Error loading pending NGOs:', err);
  }
}

async function verifyNgo(userId, action) {
  try {
    const res = await fetch(`/api/admin/ngos/verify/${userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action })
    });
    const data = await res.json();

    if (data.success) {
      showToast(data.message, 'success');
      loadPendingNgos();
      loadUsers('');
    } else {
      showToast(data.error || 'Failed to update NGO status', 'error');
    }
  } catch (err) {
    showToast('Network error during NGO verification', 'error');
  }
}

// 2. User Management
async function loadUsers(role) {
  const tbody = document.getElementById('admin-users-tbody');
  if (!tbody) return;

  try {
    const url = role ? `/api/admin/users?role=${role}` : '/api/admin/users';
    const res = await fetch(url);
    const data = await res.json();
    if (!data.success) return;

    const users = data.users;
    tbody.innerHTML = users.map(u => {
      const isSuspended = u.status === 'suspended';
      const toggleAction = isSuspended ? 'active' : 'suspended';
      const toggleLabel = isSuspended ? 'Activate' : 'Suspend';
      const toggleBtnClass = isSuspended ? 'btn-primary' : 'btn-outline';

      return `
        <tr>
          <td>
            <div style="font-weight: 700;">${u.name}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${u.email}</div>
          </td>
          <td><span class="badge" style="background: var(--surface-alt); text-transform: uppercase;">${u.role}</span></td>
          <td>${u.phone || 'N/A'}</td>
          <td><span class="badge ${u.status === 'active' ? 'badge-low' : 'badge-critical'}">${u.status}</span></td>
          <td>${new Date(u.created_at).toLocaleDateString()}</td>
          <td>
            ${u.role !== 'admin' ? `
              <button class="btn ${toggleBtnClass} btn-sm" onclick="toggleUserStatus(${u.id}, '${toggleAction}')">
                ${toggleLabel}
              </button>
            ` : `<span style="font-size: 0.75rem; color: var(--text-muted);">Root Protected</span>`}
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('Error loading users:', err);
  }
}

async function toggleUserStatus(userId, newStatus) {
  try {
    const res = await fetch(`/api/admin/users/${userId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    const data = await res.json();

    if (data.success) {
      showToast(data.message, 'success');
      loadUsers('');
    } else {
      showToast(data.error || 'Action failed', 'error');
    }
  } catch (err) {
    showToast('Network error updating user', 'error');
  }
}

// 3. Donation Surveillance
async function loadDonationsSurveillance() {
  const tbody = document.getElementById('admin-donations-tbody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/donations');
    const data = await res.json();
    if (!data.success) return;

    tbody.innerHTML = data.donations.map(d => `
      <tr>
        <td><strong>#${d.id}</strong></td>
        <td>
          <div style="font-weight: 600;">${d.title}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${d.donor_name}</div>
        </td>
        <td>${d.servings} meals (${d.quantity_value} ${d.quantity_unit})</td>
        <td><span class="badge ${d.urgency_level === 'critical' ? 'badge-critical' : 'badge-medium'}">${d.urgency_level}</span></td>
        <td><span class="badge badge-${d.status}">${d.status.replace('_', ' ')}</span></td>
        <td>${d.ngo_name || '—'}</td>
        <td>${d.volunteer_name || '—'}</td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Error loading donations surveillance:', err);
  }
}

// 4. Audit Logs
async function loadAuditLogs() {
  const tbody = document.getElementById('admin-audit-tbody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/admin/audit-logs');
    const data = await res.json();
    if (!data.success) return;

    tbody.innerHTML = data.logs.map(l => `
      <tr>
        <td><code>${new Date(l.created_at).toLocaleTimeString()}</code></td>
        <td><strong>${l.action}</strong></td>
        <td>${l.user_name || 'System'} (${l.user_role || 'anon'})</td>
        <td style="font-size: 0.8rem; color: var(--text-muted);">${l.details}</td>
        <td><code style="font-size: 0.75rem;">${l.ip_address}</code></td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Error loading audit logs:', err);
  }
}
