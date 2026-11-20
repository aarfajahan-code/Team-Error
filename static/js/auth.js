/**
 * FoodBridge - Authentication JavaScript
 * Handles login & role-based registration form tabs and validation
 */

document.addEventListener('DOMContentLoaded', () => {
  // Login Form Submission
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = loginForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = 'Signing in...';
      submitBtn.disabled = true;

      const email = document.getElementById('login-email').value.trim();
      const password = document.getElementById('login-password').value;

      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (data.success) {
          showToast(data.message, 'success');
          setTimeout(() => {
            window.location.href = data.redirect;
          }, 400);
        } else {
          showToast(data.error || 'Login failed', 'error');
          submitBtn.innerHTML = originalText;
          submitBtn.disabled = false;
        }
      } catch (err) {
        showToast('Network error during login. Please try again.', 'error');
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
      }
    });
  }

  // Registration Form Multi-Role Tab Switching
  const roleSelectInputs = document.querySelectorAll('input[name="reg-role"]');
  const roleSections = {
    donor: document.getElementById('role-fields-donor'),
    ngo: document.getElementById('role-fields-ngo'),
    volunteer: document.getElementById('role-fields-volunteer')
  };

  roleSelectInputs.forEach(input => {
    input.addEventListener('change', (e) => {
      const selectedRole = e.target.value;
      Object.keys(roleSections).forEach(role => {
        if (roleSections[role]) {
          roleSections[role].style.display = (role === selectedRole) ? 'block' : 'none';
        }
      });
    });
  });

  // Registration Form Submission
  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = registerForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = 'Creating account...';
      submitBtn.disabled = true;

      const role = document.querySelector('input[name="reg-role"]:checked')?.value || 'donor';
      const name = document.getElementById('reg-name').value.trim();
      const email = document.getElementById('reg-email').value.trim();
      const password = document.getElementById('reg-password').value;
      const phone = document.getElementById('reg-phone').value.trim();
      const address = document.getElementById('reg-address').value.trim();

      const payload = { role, name, email, password, phone, address };

      if (role === 'donor') {
        payload.organization_name = document.getElementById('donor-org-name')?.value.trim() || name;
        payload.donor_type = document.getElementById('donor-type')?.value || 'Restaurant';
        payload.fssai_license = document.getElementById('donor-fssai')?.value.trim() || '';
      } else if (role === 'ngo') {
        payload.organization_name = document.getElementById('ngo-org-name')?.value.trim() || name;
        payload.registration_no = document.getElementById('ngo-reg-no')?.value.trim() || '';
        payload.daily_capacity = parseInt(document.getElementById('ngo-capacity')?.value || '100');
        payload.has_cold_storage = document.getElementById('ngo-cold-storage')?.checked ? 1 : 0;
        payload.operating_hours = document.getElementById('ngo-hours')?.value || '08:00 AM - 09:00 PM';
      } else if (role === 'volunteer') {
        payload.vehicle_type = document.getElementById('vol-vehicle')?.value || 'Motorbike';
        payload.max_weight_kg = parseFloat(document.getElementById('vol-capacity')?.value || '25');
      }

      try {
        const res = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.success) {
          showToast(data.message, 'success');
          setTimeout(() => {
            window.location.href = data.redirect;
          }, 500);
        } else {
          showToast(data.error || 'Registration failed', 'error');
          submitBtn.innerHTML = originalText;
          submitBtn.disabled = false;
        }
      } catch (err) {
        showToast('Network error during registration.', 'error');
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
      }
    });
  }
});
