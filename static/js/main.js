/**
 * FoodBridge - Main Global JavaScript
 * Handles notifications, toasts, demo switcher, and helpers
 */

// Toast Notifications
function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let icon = '✅';
  if (type === 'error' || type === 'danger') icon = '❌';
  if (type === 'warning') icon = '⚠️';
  if (type === 'info') icon = 'ℹ️';

  toast.innerHTML = `
    <span style="font-size: 1.25rem;">${icon}</span>
    <div style="flex: 1; font-size: 0.9rem; font-weight: 500;">${message}</div>
    <button style="background: none; border: none; cursor: pointer; color: #94a3b8; font-size: 1rem;" onclick="this.parentElement.remove()">✕</button>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(50px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

// Notification Drawer Toggle
function toggleNotifDrawer(e) {
  if (e) e.stopPropagation();
  const drawer = document.getElementById('notif-drawer');
  if (!drawer) return;
  drawer.classList.toggle('show');
  if (drawer.classList.contains('show')) {
    loadNotifications();
  }
}

// Demo Dropdown Toggle
function toggleDemoDropdown(e) {
  if (e) e.stopPropagation();
  const dropdown = document.getElementById('demo-dropdown');
  if (!dropdown) return;
  dropdown.classList.toggle('show');
}

// Close dropdowns on outside click
document.addEventListener('click', (e) => {
  const notifDrawer = document.getElementById('notif-drawer');
  const demoDropdown = document.getElementById('demo-dropdown');
  
  if (notifDrawer && !e.target.closest('#notif-container')) {
    notifDrawer.classList.remove('show');
  }
  if (demoDropdown && !e.target.closest('#demo-container')) {
    demoDropdown.classList.remove('show');
  }
});

// Load Live Notifications
async function loadNotifications() {
  const listEl = document.getElementById('notif-list');
  if (!listEl) return;

  try {
    const res = await fetch('/api/notifications');
    const data = await res.json();
    if (!data.success) return;

    if (!data.notifications || data.notifications.length === 0) {
      listEl.innerHTML = '<li style="padding: 1.5rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">No notifications right now.</li>';
      return;
    }

    listEl.innerHTML = data.notifications.map(n => `
      <li class="notif-item ${n.is_read ? '' : 'unread'}" onclick="markNotifRead(${n.id}, '${n.link || '#'}')">
        <div class="notif-title">${n.title}</div>
        <div class="notif-msg">${n.message}</div>
        <div class="notif-time">${new Date(n.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
      </li>
    `).join('');
  } catch (err) {
    console.error('Error fetching notifications:', err);
  }
}

async function markNotifRead(id, link) {
  try {
    await fetch(`/api/notifications/${id}/mark-read`, { method: 'POST' });
    if (link && link !== '#') {
      window.location.href = link;
    } else {
      loadNotifications();
    }
  } catch (err) {
    console.error(err);
  }
}

async function markAllNotificationsRead() {
  try {
    await fetch('/api/notifications/mark-all-read', { method: 'POST' });
    const badge = document.getElementById('notif-badge');
    if (badge) badge.style.display = 'none';
    loadNotifications();
    showToast('All notifications marked as read', 'info');
  } catch (err) {
    console.error(err);
  }
}

// Quick 1-click Demo Persona Login
async function switchDemo(role) {
  try {
    const res = await fetch(`/api/auth/switch-demo/${role}`, {
      headers: { 'Accept': 'application/json' }
    });
    const data = await res.json();
    if (data.success) {
      window.location.href = data.redirect;
    } else {
      showToast(data.error || 'Failed to switch demo persona', 'error');
    }
  } catch (err) {
    window.location.href = `/api/auth/switch-demo/${role}`;
  }
}

// Format relative hours/minutes for countdowns
function formatTimeRemaining(seconds) {
  if (seconds <= 0) return 'Expired';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) {
    return `${hours}h ${minutes}m left`;
  }
  return `${minutes} mins left`;
}
