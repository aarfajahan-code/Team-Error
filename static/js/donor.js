/**
 * FoodBridge - Donor Dashboard JavaScript
 * Handles food donation creation, smart NGO match popups, and status tracking
 */

let donorDonations = [];

document.addEventListener('DOMContentLoaded', () => {
  loadDonorDashboard();

  // Create Donation Form Handler
  const donationForm = document.getElementById('create-donation-form');
  if (donationForm) {
    donationForm.addEventListener('submit', handleDonationSubmit);
  }

  // Preset Image Selector
  const presetSelectors = document.querySelectorAll('.food-preset-item');
  presetSelectors.forEach(item => {
    item.addEventListener('click', () => {
      presetSelectors.forEach(p => p.classList.remove('selected'));
      item.classList.add('selected');
      const url = item.getAttribute('data-url');
      const input = document.getElementById('donation-image-url');
      if (input) input.value = url;
    });
  });
});

async function loadDonorDashboard() {
  const container = document.getElementById('donor-donations-grid');
  if (!container) return;

  try {
    const res = await fetch('/api/donations');
    const data = await res.json();
    if (!data.success) return;

    // Filter to current donor's donations (or all if demo)
    donorDonations = data.donations;
    renderDonations(donorDonations);
    updateDonorStats(donorDonations);
  } catch (err) {
    console.error('Error loading donations:', err);
  }
}

function updateDonorStats(donations) {
  const activeCount = donations.filter(d => ['available', 'requested', 'in_transit'].includes(d.status)).length;
  const deliveredCount = donations.filter(d => d.status === 'delivered').length;
  const totalMeals = donations.reduce((sum, d) => sum + (d.status === 'delivered' ? d.servings : 0), 0);
  const totalKg = donations.reduce((sum, d) => sum + (d.status === 'delivered' ? d.quantity_value : 0), 0);

  const elActive = document.getElementById('donor-stat-active');
  const elDelivered = document.getElementById('donor-stat-delivered');
  const elMeals = document.getElementById('donor-stat-meals');
  const elCo2 = document.getElementById('donor-stat-co2');

  if (elActive) elActive.innerText = activeCount;
  if (elDelivered) elDelivered.innerText = deliveredCount;
  if (elMeals) elMeals.innerText = totalMeals;
  if (elCo2) elCo2.innerText = (totalKg * 2.5).toFixed(1) + ' kg';
}

function renderDonations(donations) {
  const container = document.getElementById('donor-donations-grid');
  if (!container) return;

  if (donations.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3rem; background: white; border-radius: var(--radius-lg); border: 1px dashed var(--border);">
        <div style="font-size: 3rem; margin-bottom: 1rem;">🍲</div>
        <h3>No food donations posted yet</h3>
        <p style="color: var(--text-muted); margin: 0.5rem 0 1.5rem;">Have surplus meals from banquet, buffet or kitchen? List them now to feed nearby people in need.</p>
        <button class="btn btn-primary" onclick="openCreateDonationModal()">+ Post Surplus Food</button>
      </div>
    `;
    return;
  }

  container.innerHTML = donations.map(d => {
    const isUrgent = d.urgency_level === 'critical';
    const urgencyClass = d.urgency_level === 'critical' ? 'badge-critical' : (d.urgency_level === 'medium' ? 'badge-medium' : 'badge-low');
    
    // Status text & color
    let statusBadge = `<span class="badge badge-${d.status}">${d.status.replace('_', ' ')}</span>`;

    // Stepper active step
    const steps = ['available', 'requested', 'in_transit', 'delivered'];
    const currentStepIndex = steps.indexOf(d.status);

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
            ${statusBadge}
          </div>

          <p class="donation-card-desc">${d.description || 'Hygienically packaged surplus food ready for immediate distribution.'}</p>

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
              <div>Deadline: <strong>${d.hours_left > 0 ? d.hours_left + ' hrs left' : 'Expired'}</strong></div>
            </div>
          </div>

          <!-- Stepper Flow -->
          <div style="font-size: 0.75rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.2rem;">Redistribution Lifecycle</div>
          <div class="stepper-container" style="margin: 0.75rem 0 1rem;">
            <div class="step-item ${currentStepIndex >= 0 ? 'completed' : ''}">
              <div class="step-bubble">1</div>
              <div class="step-label">Posted</div>
            </div>
            <div class="step-item ${currentStepIndex >= 1 ? 'completed' : (currentStepIndex === 0 ? 'active' : '')}">
              <div class="step-bubble">2</div>
              <div class="step-label">NGO Claim</div>
            </div>
            <div class="step-item ${currentStepIndex >= 2 ? 'completed' : (currentStepIndex === 1 ? 'active' : '')}">
              <div class="step-bubble">3</div>
              <div class="step-label">Transit</div>
            </div>
            <div class="step-item ${currentStepIndex >= 3 ? 'completed' : ''}">
              <div class="step-bubble">4</div>
              <div class="step-label">Delivered</div>
            </div>
          </div>

          <!-- Donor Pickup OTP -->
          ${d.status !== 'delivered' ? `
            <div style="background: var(--surface-alt); border: 1px dashed var(--border); border-radius: var(--radius-md); padding: 0.75rem; margin-bottom: 1rem; display: flex; align-items: center; justify-content: space-between;">
              <div>
                <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600;">DRIVER PICKUP OTP</div>
                <div style="font-size: 1.25rem; font-weight: 800; letter-spacing: 2px; color: var(--primary);">${d.pickup_otp || '4821'}</div>
              </div>
              <div style="font-size: 0.75rem; color: var(--text-muted); text-align: right; max-width: 140px;">
                Share with volunteer upon arrival to verify handover
              </div>
            </div>
          ` : `
            <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: var(--radius-md); padding: 0.75rem; margin-bottom: 1rem; text-align: center; color: #047857; font-weight: 600; font-size: 0.85rem;">
              ✅ Successfully Delivered & Distributed to Beneficiaries
            </div>
          `}

          <!-- Actions -->
          <div style="display: flex; gap: 0.5rem; margin-top: auto;">
            <button class="btn btn-outline-primary btn-sm btn-block" onclick="viewSmartMatches(${d.id})">
              🎯 View NGO Matches
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function openCreateDonationModal() {
  const modal = document.getElementById('create-donation-modal');
  if (modal) modal.classList.add('show');
}

function closeCreateDonationModal() {
  const modal = document.getElementById('create-donation-modal');
  if (modal) modal.classList.remove('show');
}

async function handleDonationSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalHtml = submitBtn.innerHTML;
  submitBtn.innerHTML = 'Posting Surplus & Matching NGOs...';
  submitBtn.disabled = true;

  const formData = new FormData(form);

  try {
    const res = await fetch('/api/donations', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();

    if (data.success) {
      showToast(data.message, 'success');
      closeCreateDonationModal();
      form.reset();
      loadDonorDashboard();

      // Show immediate smart match popup!
      if (data.recommended_ngos && data.recommended_ngos.length > 0) {
        showMatchModal(data.donation_id, data.recommended_ngos);
      }
    } else {
      showToast(data.error || 'Failed to post donation', 'error');
    }
  } catch (err) {
    showToast('Network error while posting donation', 'error');
  } finally {
    submitBtn.innerHTML = originalHtml;
    submitBtn.disabled = false;
  }
}

// Smart Matches Modal Trigger
async function viewSmartMatches(donationId) {
  try {
    const res = await fetch(`/api/donations/${donationId}/match-ngos`);
    const data = await res.json();
    if (data.success) {
      showMatchModal(donationId, data.matches);
    } else {
      showToast('Could not calculate matches at this time', 'error');
    }
  } catch (err) {
    showToast('Failed to load NGO matches', 'error');
  }
}

function showMatchModal(donationId, matches) {
  const modal = document.getElementById('smart-match-modal');
  const container = document.getElementById('matches-container');
  if (!modal || !container) return;

  if (!matches || matches.length === 0) {
    container.innerHTML = '<p style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No matching NGOs found within radius.</p>';
  } else {
    container.innerHTML = matches.map(m => `
      <div class="match-card">
        <div class="match-score-badge">
          <div class="match-score-number">${m.match_score}%</div>
          <div class="match-score-text">Match</div>
        </div>
        <div class="match-details">
          <div class="match-ngo-name">${m.ngo_name}</div>
          <div style="font-size: 0.8rem; color: var(--text-muted);">
            📍 ${m.distance_km} km away (~${m.estimated_mins} mins travel) • Daily Capacity: ${m.daily_capacity} meals
          </div>
          <div class="match-reasons-list">
            ${m.match_reasons.map(r => `<span class="match-reason-pill">✓ ${r}</span>`).join('')}
          </div>
        </div>
      </div>
    `).join('');
  }

  modal.classList.add('show');
}

function closeSmartMatchModal() {
  const modal = document.getElementById('smart-match-modal');
  if (modal) modal.classList.remove('show');
}
