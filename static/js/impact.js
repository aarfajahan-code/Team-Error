/**
 * FoodBridge - Impact Dashboard & Chart.js Visualizations
 */

document.addEventListener('DOMContentLoaded', () => {
  loadImpactDashboard();
});

async function loadImpactDashboard() {
  try {
    const res = await fetch('/api/impact/stats');
    const data = await res.json();
    if (!data.success) return;

    const imp = data.impact;

    // Update KPI numbers
    const elKg = document.getElementById('impact-food-kg');
    const elMeals = document.getElementById('impact-meals-served');
    const elCo2 = document.getElementById('impact-co2-saved');
    const elMissions = document.getElementById('impact-missions');

    if (elKg) elKg.innerText = imp.total_food_saved_kg.toLocaleString() + ' kg';
    if (elMeals) elMeals.innerText = imp.total_meals_served.toLocaleString();
    if (elCo2) elCo2.innerText = imp.co2_saved_kg.toLocaleString() + ' kg';
    if (elMissions) elMissions.innerText = imp.completed_donations;

    // Initialize Charts
    initCategoryChart(imp.categories);
    initTrendChart(imp.timeline);
    initPartnerBarChart(imp.donors_count, imp.ngos_count, imp.volunteers_count);
  } catch (err) {
    console.error('Error loading impact stats:', err);
  }
}

// 1. Food Category Doughnut Chart
function initCategoryChart(categories) {
  const ctx = document.getElementById('categoryDoughnutChart');
  if (!ctx) return;

  const labels = categories && categories.length > 0 ? categories.map(c => c.category) : ['Cooked Meals', 'Bakery & Dairy', 'Fruits & Veg', 'Packaged Food'];
  const values = categories && categories.length > 0 ? categories.map(c => c.total_kg || c.count) : [145, 60, 110, 42];

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: [
          '#155e39', // Forest green
          '#ea580c', // Orange
          '#22c55e', // Light green
          '#0ea5e9', // Sky blue
          '#8b5cf6'  // Purple
        ],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            boxWidth: 12,
            font: { family: 'Inter', size: 12, weight: '600' }
          }
        }
      },
      cutout: '68%'
    }
  });
}

// 2. Weekly Redistribution Trend Line Chart
function initTrendChart(timeline) {
  const ctx = document.getElementById('trendLineChart');
  if (!ctx) return;

  const days = timeline ? timeline.map(t => t.day) : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const values = timeline ? timeline.map(t => t.kg) : [45, 68, 92, 110, 140, 185, 230];

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: days,
      datasets: [{
        label: 'Surplus Food Saved (kg)',
        data: values,
        borderColor: '#155e39',
        backgroundColor: 'rgba(21, 94, 57, 0.08)',
        fill: true,
        tension: 0.35,
        pointBackgroundColor: '#155e39',
        pointRadius: 5,
        pointHoverRadius: 7
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: '#f1f5f9' },
          ticks: { font: { family: 'Inter' } }
        },
        x: {
          grid: { display: false },
          ticks: { font: { family: 'Inter' } }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

// 3. Network Community Bar Chart
function initPartnerBarChart(donors, ngos, volunteers) {
  const ctx = document.getElementById('partnerBarChart');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Donors (Hotels/Restaurants)', 'NGOs & Shelters', 'Active Volunteer Drivers'],
      datasets: [{
        label: 'Registered Network Partners',
        data: [donors || 5, ngos || 5, volunteers || 4],
        backgroundColor: ['#155e39', '#2563eb', '#ea580c'],
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: '#f1f5f9' }
        },
        x: {
          grid: { display: false }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}
