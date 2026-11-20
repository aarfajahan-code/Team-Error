/**
 * FoodBridge - NGO Dashboard JavaScript
 * Handles browsing available donations, smart recommendations, claiming food, and delivery confirmation
 */

let availableDonations = [];
let myClaimedDonations = [];

document.addEventListener('DOMContentLoaded', () => {
  loadNgoDashboard();

  // Tab switching
  const tabAvailable = document.getElementById('tab-btn-available');
  const tabClaimed = document.getElementById('tab-btn-claimed');
  const viewAvailable = document.getElementById('view-available');
  const viewClaimed = document.getElementById('view-claimed');

  if (tabAvailable && tabClaimed) {
    tabAvailable.addEventListener('click', () => {
      tabAvailable.classList.add('active');
      tabClaimed.classList.remove('active');
      viewAvailable.style.display = 'block';
      viewClaimed.style.display = 'none';
    });

    tabClaimed.addEventListener('click', () => {
      tabClaimed.classList.add('active');
      tabAvailable.classList.remove('active');
      viewClaimed.style.display = 'block';
      viewAvailable.style.display = 'none';
    });
  }

  // Delivery Verification Form
  const verifyForm = document.getElementById('verify-delivery-form');
  if (verifyForm) {
    verifyForm.addEventListener('submit', handleVerifyDelivery);
  }
});

async function loadNgoDashboard() {
  try {
    const res = await fetch('/api/donations');
    const data = await res.json();
    if (!data.success) return;

    const all = data.donations;
    availableDonations = all.filter(d => d.status === 'available');
    myClaimedDonations = all.filter(d => ['requested', 'in_transit', 'delivered'].includes(d.status));

    renderUrgentAlerts(availableDonations);
    renderAvailableDonations(availableDonations);
    renderClaimedDonations(myClaimedDonations);
    updateNgoStats(all);
  } catch (err) {
    console.error('Error loading NGO dashboard:', err);
  }
}

function updateNgoStats(donations) {
  const activeAvailable = donations.filter(d => d.status === 'available').length;
  const inTransit = donations.filter(d => d.status === 'in_transit' || d.status === 'requested').length;
  const delivered = donations.filter(d => d.status === 'delivered').length;
  const totalMeals = donations.filter(d => d.status === 'delivered').reduce((acc, d) => acc + d.servings, 0);

  const elAvail = document.getElementById('ngo-stat-available');
  const elTransit = document.getElementById('ngo-stat-transit');
  const elDelivered = document.getElementById('ngo-stat-delivered');
  const elMeals = document.getElementById('ngo-stat-meals');

  if (elAvail) elAvail.innerText = activeAvailable;
  if (elTransit) elTransit.innerText = inTransit;
  if (elDelivered) elDelivered.innerText = delivered;
  if (elMeals) elMeals.innerText = totalMeals;
}

function renderUrgentAlerts(donations) {
  const alertContainer = document.getElementById('ngo-urgent-banner');
  if (!alertContainer) return;

  const urgentDonations = donations.filter(d => d.urgency_level === 'critical');
  if (urgentDonations.length === 0) {
    alertContainer.style.display = 'none';
    return;
  }

  const firstUrgent = urgentDonations[0];
  alertContainer.style.display = 'flex';
  alertContainer.innerHTML = `
    <div class="safety-alert-icon">⚡</div>
    <div class="safety-alert-content" style="flex: 1;">
      <h4>CRITICAL URGENCY: ${firstUrgent.title}</h4>
      <p>
        <strong>${firstUrgent.servings} meals</strong> prepared at ${firstUrgent.donor_name} will expire in <strong>${firstUrgent.hours_left} hours</strong>!
        Immediate pickup is necessary to prevent safe food from being wasted.
      </p>
    </div>
    <button class="btn btn-accent btn-sm" onclick="claimDonation(${firstUrgent.id})">
      🚨 Claim Immediately
    </button>
  `;
}

function renderAvailableDonations(donations) {
  const container = document.getElementById('ngo-available-grid');
  if (!container) return;

  if (donations.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3rem; background: white; border-radius: var(--radius-lg); border: 1px dashed var(--border);">
        <div style="font-size: 3rem; margin-bottom: 1rem;">🍲</div>
        <h3>No food donations waiting right now</h3>
        <p style="color: var(--text-muted);">Check back soon or explore the interactive map to see upcoming donor schedules.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = donations.map(d => {
    const isUrgent = d.urgency_level === 'critical';
    const urgencyClass = isUrgent ? 'badge-critical' : (d.urgency_level === 'medium' ? 'badge-medium' : 'badge-low');

    return `
      <div class="donation-card">
        <div class="card-img-wrap">
          <img src="${d.image_url || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800'}" alt="${d.title}">
          <div class="card-floating-badge">
            <span class="badge ${urgencyClass}">
              ${isUrgent ? '⚡ Critical (<2h)' : d.urgency_level + ' urgency'}
            </span>
          </div>
          <div class="card-category-badge">${d.category} • ${d.food_type}</div>
        </div>

        <div class="donation-card-content">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.4rem;">
            <h3 class="donation-card-title">${d.title}</h3>
            <span class="badge badge-available">Ready</span>
          </div>

          <div style="font-size: 0.8rem; color: var(--primary); font-weight: 700; margin-bottom: 0.5rem;">
            Donor: ${d.donor_name} (${d.donor_type || 'Restaurant'})
          </div>

          <p class="donation-card-desc">${d.description || 'Hygienic surplus meal ready for redistribution.'}</p>

          <div class="donation-meta-list">
            <div class="donation-meta-item">
              <span>⚖️</span>
              <div>Quantity: <strong>${d.quantity_value} ${d.quantity_unit}</strong> (~<strong>${d.servings}</strong> meals)</div>
            </div>
            <div class="donation-meta-item">
              <span>🌡️</span>
              <div>Storage: <strong>${d.storage_condition}</strong></div>
            </div>
            <div class="donation-meta-item">
              <span>📍</span>
              <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 250px;">
                ${d.pickup_address}
              </div>
            </div>
            <div class="donation-meta-item">
              <span>⏳</span>
              <div>Collection Deadline: <strong>${d.hours_left > 0 ? d.hours_left + ' hrs left' : 'Expired'}</strong></div>
            </div>
          </div>

          <div style="margin-top: auto;">
            <button class="btn btn-primary btn-block" onclick="claimDonation(${d.id})">
              🤝 Accept & Claim Donation
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function renderClaimedDonations(donations) {
  const container = document.getElementById('ngo-claimed-grid');
  if (!container) return;

  if (donations.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3rem; background: white; border-radius: var(--radius-lg); border: 1px dashed var(--border);">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📦</div>
        <h3>No active food claims</h3>
        <p style="color: var(--text-muted);">When you accept donations, tracking and volunteer coordination will appear here.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = donations.map(d => {
    let statusPill = `<span class="badge badge-${d.status}">${d.status.replace('_', ' ')}</span>`;
    const isDelivered = d.status === 'delivered';

    return `
      <div class="donation-card">
        <div class="donation-card-content">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
            <h3 class="donation-card-title">${d.title}</h3>
            ${statusPill}
          </div>

          <div style="font-size: 0.825rem; color: var(--text-muted); margin-bottom: 0.75rem;">
            Donor: <strong>${d.donor_name}</strong> • Phone: <strong>${d.donor_phone || 'N/A'}</strong>
          </div>

          <div class="donation-meta-list">
            <div class="donation-meta-item">
              <span>⚖️</span>
              <div>Servings: <strong>${d.servings} people</strong> (${d.quantity_value} ${d.quantity_unit})</div>
            </div>
            <div class="donation-meta-item">
              <span>🛵</span>
              <div>Volunteer: <strong>${d.volunteer_name || 'Dispatching nearby volunteer...'}</strong></div>
            </div>
            <div class="donation-meta-item">
              <span>📍</span>
              <div>Pickup From: <strong>${d.pickup_address}</strong></div>
            </div>
          </div>

          <!-- NGO Delivery Code Box -->
          <div style="background: var(--surface-alt); border: 1px dashed var(--border); border-radius: var(--radius-md); padding: 0.85rem; margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div>
                <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 700;">YOUR DELIVERY OTP</div>
                <div style="font-size: 1.35rem; font-weight: 800; letter-spacing: 2px; color: var(--accent);">${d.delivery_otp || '7912'}</div>
              </div>
              <div style="font-size: 0.75rem; color: var(--text-muted); text-align: right; max-width: 150px;">
                Share with driver when food safely arrives at your facility
              </div>
            </div>
          </div>

          ${!isDelivered ? `
            <button class="btn btn-outline-primary btn-block btn-sm" onclick="openVerifyModal(${d.id}, '${d.title}', ${d.servings})">
              ✅ Verify Received & Confirm Delivery
            </button>
          ` : `
            <div style="background: #ecfdf5; color: #047857; padding: 0.6rem; border-radius: var(--radius-md); text-align: center; font-size: 0.85rem; font-weight: 700;">
              ✨ Distribution Completed
            </div>
          `}
        </div>
      </div>
    `;
  }).join('');
}

async function claimDonation(donationId) {
  if (!confirm('Are you ready to claim this food donation and coordinate pickup?')) return;

  try {
    const res = await fetch(`/api/donations/${donationId}/claim`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await res.json();

    if (data.success) {
      showToast(data.message, 'success');
      loadNgoDashboard();
    } else {
      showToast(data.error || 'Failed to claim donation', 'error');
    }
  } catch (err) {
    showToast('Network error while claiming food', 'error');
  }
}

function openVerifyModal(donationId, title, servings) {
  const modal = document.getElementById('verify-delivery-modal');
  const titleEl = document.getElementById('modal-verify-title');
  const idInput = document.getElementById('verify-donation-id');
  const servingsInput = document.getElementById('verify-servings');

  if (titleEl) titleEl.innerText = title;
  if (idInput) idInput.value = donationId;
  if (servingsInput) servingsInput.value = servings;

  if (modal) modal.classList.add('show');
}

function closeVerifyModal() {
  const modal = document.getElementById('verify-delivery-modal');
  if (modal) modal.classList.remove('show');
}

async function handleVerifyDelivery(e) {
  e.preventDefault();
  const donationId = document.getElementById('verify-donation-id').value;
  const otp = document.getElementById('verify-otp').value.trim();
  const notes = document.getElementById('verify-notes').value.trim();
  const beneficiaries = parseInt(document.getElementById('verify-servings').value || '0');

  try {
    const res = await fetch(`/api/donations/${donationId}/verify-delivery`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        otp,
        delivery_notes: notes,
        beneficiaries_served: beneficiaries
      })
    });
    const data = await res.json();

    if (data.success) {
      showToast(data.message, 'success');
      closeVerifyModal();
      loadNgoDashboard();
    } else {
      showToast(data.error || 'Verification failed. Please check OTP code.', 'error');
    }
  } catch (err) {
    showToast('Network error during delivery verification', 'error');
  }
}
