/**
 * FoodBridge - Volunteer Dashboard JavaScript
 * Handles accepting delivery tasks, pickup OTP verification, and status updates
 */

document.addEventListener('DOMContentLoaded', () => {
  loadVolunteerDashboard();

  // Pickup OTP Modal Form
  const pickupForm = document.getElementById('pickup-otp-form');
  if (pickupForm) {
    pickupForm.addEventListener('submit', handleVerifyPickup);
  }

  // Delivery OTP Modal Form
  const deliveryForm = document.getElementById('volunteer-delivery-otp-form');
  if (deliveryForm) {
    deliveryForm.addEventListener('submit', handleVerifyVolunteerDelivery);
  }
});

async function loadVolunteerDashboard() {
  const availableContainer = document.getElementById('volunteer-tasks-grid');
  const activeContainer = document.getElementById('volunteer-active-grid');
  if (!availableContainer) return;

  try {
    const res = await fetch('/api/volunteer/tasks');
    const data = await res.json();
    if (!data.success) return;

    const tasks = data.tasks;
    // Split into available to accept (status: requested, no assigned volunteer) and active
    const available = tasks.filter(t => t.status === 'requested' && !t.assigned_volunteer_id);
    const active = tasks.filter(t => t.assigned_volunteer_id);

    renderAvailableTasks(available);
    renderActiveDeliveries(active);
    updateVolunteerStats(active);
  } catch (err) {
    console.error('Error loading volunteer tasks:', err);
  }
}

function updateVolunteerStats(activeDeliveries) {
  const elActive = document.getElementById('vol-stat-active');
  if (elActive) elActive.innerText = activeDeliveries.length;
}

function renderAvailableTasks(tasks) {
  const container = document.getElementById('volunteer-tasks-grid');
  if (!container) return;

  if (tasks.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 2.5rem; background: white; border-radius: var(--radius-lg); border: 1px dashed var(--border);">
        <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎉</div>
        <h4>All food deliveries are currently handled!</h4>
        <p style="color: var(--text-muted); font-size: 0.85rem;">Check back shortly as new restaurants and banquet halls post surplus donations.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = tasks.map(t => `
    <div class="card" style="display: flex; flex-direction: column;">
      <div class="card-body">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
          <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-main);">${t.title}</h3>
          <span class="badge ${t.urgency_level === 'critical' ? 'badge-critical' : 'badge-medium'}">
            ${t.urgency_level}
          </span>
        </div>

        <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.75rem;">
          Quantity: <strong>${t.quantity_value} ${t.quantity_unit}</strong> (~<strong>${t.servings}</strong> meals)
        </div>

        <div style="background: var(--surface-alt); padding: 0.75rem; border-radius: var(--radius-md); font-size: 0.8rem; margin-bottom: 1rem; display: flex; flex-direction: column; gap: 0.4rem;">
          <div>📍 <strong>Pickup:</strong> ${t.donor_name} (${t.dist_to_donor || '2.1'} km away)</div>
          <div>🏠 <strong>Delivery To:</strong> ${t.ngo_name || 'Community Shelter'} (~${t.dist_pickup_to_ngo || '4.5'} km)</div>
          <div>🌡️ <strong>Storage:</strong> ${t.storage_condition}</div>
        </div>

        <button class="btn btn-accent btn-block btn-sm" onclick="acceptTask(${t.id})">
          🛵 Accept Delivery Task
        </button>
      </div>
    </div>
  `).join('');
}

function renderActiveDeliveries(tasks) {
  const container = document.getElementById('volunteer-active-grid');
  if (!container) return;

  if (tasks.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 2rem; background: white; border-radius: var(--radius-lg); border: 1px dashed var(--border);">
        <p style="color: var(--text-muted); font-size: 0.9rem;">You have no active deliveries in progress. Accept an available mission above to get started!</p>
      </div>
    `;
    return;
  }

  container.innerHTML = tasks.map(t => {
    const isPickedUp = t.status === 'in_transit';

    return `
      <div class="card" style="border-left: 4px solid var(--accent);">
        <div class="card-body">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
            <h3 style="font-size: 1.1rem; font-weight: 700;">${t.title}</h3>
            <span class="badge badge-${t.status}">${t.status.replace('_', ' ')}</span>
          </div>

          <div class="stepper-container" style="margin: 1rem 0;">
            <div class="step-item completed">
              <div class="step-bubble">✓</div>
              <div class="step-label">Claimed</div>
            </div>
            <div class="step-item ${isPickedUp ? 'completed' : 'active'}">
              <div class="step-bubble">2</div>
              <div class="step-label">Pickup</div>
            </div>
            <div class="step-item ${isPickedUp ? 'active' : ''}">
              <div class="step-bubble">3</div>
              <div class="step-label">Delivering</div>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; font-size: 0.85rem; margin-bottom: 1rem;">
            <div style="background: var(--surface-alt); padding: 0.75rem; border-radius: var(--radius-md);">
              <div style="font-weight: 700; color: var(--primary); margin-bottom: 0.2rem;">📍 1. PICKUP AT</div>
              <div style="font-weight: 600;">${t.donor_name}</div>
              <div style="color: var(--text-muted); font-size: 0.75rem;">${t.pickup_address}</div>
              <div style="color: var(--text-muted); font-size: 0.75rem;">📞 ${t.donor_phone || 'N/A'}</div>
            </div>
            <div style="background: var(--surface-alt); padding: 0.75rem; border-radius: var(--radius-md);">
              <div style="font-weight: 700; color: var(--accent); margin-bottom: 0.2rem;">🏠 2. DELIVER TO</div>
              <div style="font-weight: 600;">${t.ngo_name}</div>
              <div style="color: var(--text-muted); font-size: 0.75rem;">${t.ngo_address || 'Shelter Facility'}</div>
              <div style="color: var(--text-muted); font-size: 0.75rem;">📞 ${t.ngo_phone || 'N/A'}</div>
            </div>
          </div>

          ${!isPickedUp ? `
            <button class="btn btn-primary btn-block" onclick="openPickupOtpModal(${t.id}, '${t.title}')">
              🔑 Enter Donor Pickup OTP & Start Transit
            </button>
          ` : `
            <button class="btn btn-accent btn-block" onclick="openVolunteerDeliveryModal(${t.id}, '${t.title}', ${t.servings})">
              🏁 Enter NGO Delivery OTP & Complete Delivery
            </button>
          `}
        </div>
      </div>
    `;
  }).join('');
}

async function acceptTask(donationId) {
  try {
    const res = await fetch(`/api/volunteer/accept-task/${donationId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await res.json();

    if (data.success) {
      showToast(data.message, 'success');
      loadVolunteerDashboard();
    } else {
      showToast(data.error || 'Failed to accept task', 'error');
    }
  } catch (err) {
    showToast('Network error while accepting delivery', 'error');
  }
}

// Pickup OTP Modal
function openPickupOtpModal(id, title) {
  const modal = document.getElementById('pickup-otp-modal');
  const titleEl = document.getElementById('pickup-modal-title');
  const idInput = document.getElementById('pickup-donation-id');

  if (titleEl) titleEl.innerText = title;
  if (idInput) idInput.value = id;
  if (modal) modal.classList.add('show');
}

function closePickupOtpModal() {
  const modal = document.getElementById('pickup-otp-modal');
  if (modal) modal.classList.remove('show');
}

async function handleVerifyPickup(e) {
  e.preventDefault();
  const donationId = document.getElementById('pickup-donation-id').value;
  const otp = document.getElementById('pickup-otp-input').value.trim();

  try {
    const res = await fetch(`/api/donations/${donationId}/verify-pickup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ otp })
    });
    const data = await res.json();

    if (data.success) {
      showToast(data.message, 'success');
      closePickupOtpModal();
      loadVolunteerDashboard();
    } else {
      showToast(data.error || 'Invalid OTP code from donor', 'error');
    }
  } catch (err) {
    showToast('Network error verifying pickup', 'error');
  }
}

// Delivery OTP Modal
function openVolunteerDeliveryModal(id, title, servings) {
  const modal = document.getElementById('volunteer-delivery-modal');
  const titleEl = document.getElementById('vol-delivery-modal-title');
  const idInput = document.getElementById('vol-delivery-id');
  const servingsInput = document.getElementById('vol-delivery-servings');

  if (titleEl) titleEl.innerText = title;
  if (idInput) idInput.value = id;
  if (servingsInput) servingsInput.value = servings;
  if (modal) modal.classList.add('show');
}

function closeVolunteerDeliveryModal() {
  const modal = document.getElementById('volunteer-delivery-modal');
  if (modal) modal.classList.remove('show');
}

async function handleVerifyVolunteerDelivery(e) {
  e.preventDefault();
  const donationId = document.getElementById('vol-delivery-id').value;
  const otp = document.getElementById('vol-delivery-otp-input').value.trim();
  const beneficiaries = parseInt(document.getElementById('vol-delivery-servings').value || '0');

  try {
    const res = await fetch(`/api/donations/${donationId}/verify-delivery`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        otp,
        beneficiaries_served: beneficiaries,
        delivery_notes: 'Delivered by volunteer driver in sealed clean containers.'
      })
    });
    const data = await res.json();

    if (data.success) {
      showToast(data.message, 'success');
      closeVolunteerDeliveryModal();
      loadVolunteerDashboard();
    } else {
      showToast(data.error || 'Invalid delivery code from NGO', 'error');
    }
  } catch (err) {
    showToast('Network error completing delivery', 'error');
  }
}
