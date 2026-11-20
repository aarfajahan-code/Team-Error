/**
 * FoodBridge - Interactive Map Integration
 * Powered by Leaflet & OpenStreetMap (100% Free, No API key required)
 */

let map;
let markersLayer;
let allMapData = { donations: [], ngos: [], volunteers: [] };

document.addEventListener('DOMContentLoaded', () => {
  initMap();
  loadMapData();

  // Filter Listeners
  const categoryFilters = document.querySelectorAll('.filter-category');
  const urgencyFilters = document.querySelectorAll('.filter-urgency');
  const typeFilters = document.querySelectorAll('.filter-pin-type');

  const reFilter = () => applyFilters();

  categoryFilters.forEach(cb => cb.addEventListener('change', reFilter));
  urgencyFilters.forEach(cb => cb.addEventListener('change', reFilter));
  typeFilters.forEach(cb => cb.addEventListener('change', reFilter));
});

function initMap() {
  const mapElement = document.getElementById('foodbridge-map');
  if (!mapElement) return;

  // Default centered around Delhi NCR / Northern hub
  map = L.map('foodbridge-map', {
    zoomControl: false
  }).setView([28.6139, 77.2090], 12);

  // Add zoom control top right
  L.control.zoom({ position: 'topright' }).addTo(map);

  // OpenStreetMap Tile Layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | FoodBridge',
    maxZoom: 19
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);
}

async function loadMapData() {
  try {
    const res = await fetch('/api/map/data');
    const data = await res.json();
    if (!data.success) return;

    allMapData = data;
    applyFilters();
  } catch (err) {
    console.error('Error fetching map pins:', err);
  }
}

function applyFilters() {
  if (!markersLayer) return;
  markersLayer.clearLayers();

  // Read filter checkboxes
  const selectedCategories = Array.from(document.querySelectorAll('.filter-category:checked')).map(cb => cb.value);
  const selectedUrgencies = Array.from(document.querySelectorAll('.filter-urgency:checked')).map(cb => cb.value);
  const showDonations = document.getElementById('filter-show-donations')?.checked ?? true;
  const showNgos = document.getElementById('filter-show-ngos')?.checked ?? true;
  const showVolunteers = document.getElementById('filter-show-volunteers')?.checked ?? true;

  const bounds = [];

  // 1. Plot Donations
  if (showDonations && allMapData.donations) {
    allMapData.donations.forEach(d => {
      // Category filter
      if (selectedCategories.length > 0 && !selectedCategories.includes(d.category)) return;
      // Urgency filter
      if (selectedUrgencies.length > 0 && !selectedUrgencies.includes(d.urgency_level)) return;

      const isUrgent = d.urgency_level === 'critical';
      const iconHtml = `
        <div class="custom-pin ${isUrgent ? 'pin-urgent' : 'pin-donor'}">
          ${isUrgent ? '⚡' : '🍲'}
        </div>
      `;

      const customIcon = L.divIcon({
        html: iconHtml,
        className: 'custom-map-icon',
        iconSize: [36, 36],
        iconAnchor: [18, 18],
        popupAnchor: [0, -20]
      });

      const popupContent = `
        <div class="popup-card">
          <img src="${d.image_url || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800'}" class="popup-img" alt="${d.title}">
          <div class="popup-body">
            <span class="badge ${isUrgent ? 'badge-critical' : 'badge-low'}" style="margin-bottom: 0.35rem;">
              ${isUrgent ? '⚡ Critical: ' + d.hours_left + 'h left' : d.hours_left + 'h left'}
            </span>
            <div class="popup-title">${d.title}</div>
            <div class="popup-desc">By: <strong>${d.donor_name}</strong> • ${d.category}</div>
            <div class="popup-meta">
              <span>⚖️ ${d.quantity_value} ${d.quantity_unit}</span>
              <span>👥 ${d.servings} Servings</span>
            </div>
            <a href="/ngo/dashboard" class="btn btn-primary btn-sm btn-block">
              🤝 View & Claim Food
            </a>
          </div>
        </div>
      `;

      const marker = L.marker([d.pickup_lat, d.pickup_lng], { icon: customIcon })
        .bindPopup(popupContent);
      markersLayer.addLayer(marker);
      bounds.push([d.pickup_lat, d.pickup_lng]);
    });
  }

  // 2. Plot NGOs
  if (showNgos && allMapData.ngos) {
    allMapData.ngos.forEach(n => {
      const iconHtml = `
        <div class="custom-pin pin-ngo">
          🏠
        </div>
      `;

      const customIcon = L.divIcon({
        html: iconHtml,
        className: 'custom-map-icon',
        iconSize: [36, 36],
        iconAnchor: [18, 18],
        popupAnchor: [0, -20]
      });

      const popupContent = `
        <div class="popup-card">
          <div class="popup-body">
            <span class="badge" style="background: #eff6ff; color: #1d4ed8; margin-bottom: 0.35rem;">NGO Food Center</span>
            <div class="popup-title">${n.organization_name || n.name}</div>
            <div class="popup-desc">${n.address || 'Local community facility'}</div>
            <div class="popup-meta">
              <span>👥 Cap: ${n.daily_capacity} meals/day</span>
              <span>❄️ ${n.has_cold_storage ? 'Cold Storage: Yes' : 'Cold Storage: No'}</span>
            </div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">
              📞 Contact: <strong>${n.phone || 'Available to partners'}</strong>
            </div>
          </div>
        </div>
      `;

      const marker = L.marker([n.latitude, n.longitude], { icon: customIcon })
        .bindPopup(popupContent);
      markersLayer.addLayer(marker);
      bounds.push([n.latitude, n.longitude]);
    });
  }

  // 3. Plot Volunteers
  if (showVolunteers && allMapData.volunteers) {
    allMapData.volunteers.forEach(v => {
      const iconHtml = `
        <div class="custom-pin pin-volunteer">
          🛵
        </div>
      `;

      const customIcon = L.divIcon({
        html: iconHtml,
        className: 'custom-map-icon',
        iconSize: [32, 32],
        iconAnchor: [16, 16],
        popupAnchor: [0, -18]
      });

      const popupContent = `
        <div class="popup-card">
          <div class="popup-body">
            <span class="badge" style="background: #fff7ed; color: #c2410c; margin-bottom: 0.35rem;">Active Volunteer</span>
            <div class="popup-title">${v.name}</div>
            <div class="popup-desc">Vehicle: <strong>${v.vehicle_type}</strong></div>
            <div class="popup-meta">
              <span>⭐ Rating: ${v.rating || '5.0'}</span>
              <span>🟢 Status: Available</span>
            </div>
          </div>
        </div>
      `;

      const marker = L.marker([v.latitude, v.longitude], { icon: customIcon })
        .bindPopup(popupContent);
      markersLayer.addLayer(marker);
    });
  }

  // Fit bounds if markers exist
  if (bounds.length > 0 && map) {
    map.fitBounds(bounds, { padding: [50, 50], maxZoom: 13 });
  }
}
