import os
import random
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify, session,
    redirect, url_for, flash, send_from_directory
)
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from database import query_db, execute_db, init_db, ACTIVE_DB_ENGINE
from matching import find_best_matching_ngos, haversine_distance

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Ensure upload directory exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Authentication Helpers & Decorators ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized. Please login.'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login_view', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Unauthorized. Please login.'}), 401
                return redirect(url_for('login_view'))
            
            user_role = session.get('role')
            if user_role not in allowed_roles and user_role != 'admin':
                if request.path.startswith('/api/'):
                    return jsonify({'error': f'Access forbidden. Role {user_role} not allowed.'}), 403
                flash('You do not have permission to view that page.', 'danger')
                return redirect(url_for('index_view'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    if 'user_id' not in session:
        return None
    return query_db("SELECT id, name, email, role, phone, address, latitude, longitude, status FROM users WHERE id = %s", (session['user_id'],), one=True)

@app.context_processor
def inject_global_context():
    user = get_current_user()
    unread_count = 0
    if user:
        cnt = query_db("SELECT COUNT(*) as unread FROM notifications WHERE user_id = %s AND is_read = 0", (user['id'],), one=True)
        if cnt:
            unread_count = cnt['unread']
    return {
        'current_user': user,
        'unread_notifications_count': unread_count,
        'now': datetime.now()
    }

# --- Audit & Notification Helpers ---

def log_audit(user_id, action, details):
    try:
        ip = request.remote_addr or '127.0.0.1'
        execute_db("""
            INSERT INTO audit_logs (user_id, action, details, ip_address)
            VALUES (%s, %s, %s, %s)
        """, (user_id, action, details, ip))
    except Exception as e:
        print(f"Audit log error: {e}")

def create_notification(user_id, title, message, ntype='info', link=None):
    try:
        execute_db("""
            INSERT INTO notifications (user_id, title, message, type, link, is_read)
            VALUES (%s, %s, %s, %s, %s, 0)
        """, (user_id, title, message, ntype, link))
    except Exception as e:
        print(f"Notification error: {e}")

def broadcast_urgent_donation(donation_id, title, food_type, servings, donor_lat, donor_lng):
    """Notifies nearby verified NGOs when a critical/urgent donation is posted."""
    try:
        ngos = query_db("""
            SELECT u.id, u.name, u.latitude, u.longitude 
            FROM users u
            JOIN ngo_profiles np ON u.id = np.user_id
            WHERE u.role = 'ngo' AND u.status = 'active'
        """)
        for ngo in ngos:
            dist = haversine_distance(donor_lat, donor_lng, ngo['latitude'], ngo['longitude'])
            if dist <= 20.0: # Within 20km
                create_notification(
                    user_id=ngo['id'],
                    title=f"🚨 URGENT Surplus: {servings} meals ({food_type})",
                    message=f"New surplus food '{title}' needs immediate pickup (~{dist} km from you). Claim it now!",
                    ntype='urgency',
                    link='/ngo/dashboard'
                )
    except Exception as e:
        print(f"Broadcast error: {e}")

# --- API Endpoints: Authentication ---

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json() or request.form
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'donor').lower()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    lat = float(data.get('latitude', 28.6139))
    lng = float(data.get('longitude', 77.2090))

    if not name or not email or not password or not role:
        return jsonify({'error': 'Name, email, password, and role are required'}), 400

    if role not in ['donor', 'ngo', 'volunteer']:
        return jsonify({'error': 'Invalid role specified'}), 400

    existing = query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
    if existing:
        return jsonify({'error': 'An account with this email already exists'}), 400

    pwd_hash = generate_password_hash(password)
    user_status = 'active' if role != 'ngo' else 'pending_verification'

    user_id = execute_db("""
        INSERT INTO users (name, email, password_hash, role, phone, address, latitude, longitude, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (name, email, pwd_hash, role, phone, address, lat, lng, user_status))

    # Create role-specific profile
    if role == 'donor':
        org_name = data.get('organization_name', name)
        donor_type = data.get('donor_type', 'Restaurant')
        contact_person = data.get('contact_person', name)
        fssai = data.get('fssai_license', '')
        execute_db("""
            INSERT INTO donor_profiles (user_id, organization_name, donor_type, contact_person, fssai_license)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, org_name, donor_type, contact_person, fssai))

    elif role == 'ngo':
        org_name = data.get('organization_name', name)
        reg_no = data.get('registration_no', f'NGO-{random.randint(1000, 9999)}')
        contact_person = data.get('contact_person', name)
        capacity = int(data.get('daily_capacity', 100))
        food_types = data.get('preferred_food_types', 'Vegetarian,Cooked Meal,Raw Groceries')
        cold_storage = 1 if str(data.get('has_cold_storage')).lower() in ['1', 'true', 'yes'] else 0
        hours = data.get('operating_hours', '08:00 AM - 09:00 PM')
        
        execute_db("""
            INSERT INTO ngo_profiles (user_id, organization_name, registration_no, contact_person, daily_capacity, preferred_food_types, has_cold_storage, operating_hours, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
        """, (user_id, org_name, reg_no, contact_person, capacity, food_types, cold_storage, hours))

        # Notify admin of new NGO
        admins = query_db("SELECT id FROM users WHERE role = 'admin'")
        for adm in admins:
            create_notification(adm['id'], '🛡️ New NGO Pending Verification', f'{org_name} registered and awaits verification.', 'system', '/admin/dashboard')

    elif role == 'volunteer':
        vehicle = data.get('vehicle_type', 'Motorbike')
        max_wt = float(data.get('max_weight_kg', 25.0))
        execute_db("""
            INSERT INTO volunteer_profiles (user_id, vehicle_type, max_weight_kg, is_available)
            VALUES (%s, %s, %s, 1)
        """, (user_id, vehicle, max_wt))

    log_audit(user_id, 'USER_REGISTERED', f"Registered as {role} ({name})")

    # Set session
    session['user_id'] = user_id
    session['name'] = name
    session['email'] = email
    session['role'] = role

    return jsonify({
        'success': True,
        'message': 'Registration successful!',
        'redirect': f"/{role}/dashboard"
    })

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or request.form
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = query_db("SELECT * FROM users WHERE email = %s", (email,), one=True)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid email or password'}), 401

    if user['status'] == 'suspended':
        return jsonify({'error': 'Your account has been suspended by the administrator.'}), 403

    session['user_id'] = user['id']
    session['name'] = user['name']
    session['email'] = user['email']
    session['role'] = user['role']

    log_audit(user['id'], 'USER_LOGIN', f"User {user['email']} logged in")

    target_redirect = f"/{user['role']}/dashboard"
    return jsonify({
        'success': True,
        'message': f"Welcome back, {user['name']}!",
        'redirect': target_redirect
    })

@app.route('/api/auth/logout', methods=['GET', 'POST'])
def api_logout():
    uid = session.get('user_id')
    if uid:
        log_audit(uid, 'USER_LOGOUT', "User logged out")
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index_view'))

@app.route('/api/auth/switch-demo/<role>', methods=['GET', 'POST'])
def switch_demo_account(role):
    """Enables judges/evaluators to seamlessly switch to any role demo profile with 1 click."""
    demo_map = {
        'donor': 'grandpalace@donor.org',
        'ngo': 'hopeshelter@ngo.org',
        'volunteer': 'rahul@volunteer.org',
        'admin': 'admin@foodbridge.org'
    }
    
    email = demo_map.get(role.lower())
    if not email:
        return jsonify({'error': 'Invalid demo role'}), 400

    user = query_db("SELECT * FROM users WHERE email = %s", (email,), one=True)
    if not user:
        return jsonify({'error': 'Demo user not found. Ensure database is seeded.'}), 404

    session['user_id'] = user['id']
    session['name'] = user['name']
    session['email'] = user['email']
    session['role'] = user['role']

    log_audit(user['id'], 'DEMO_SWITCH', f"Switched into demo persona: {user['name']} ({user['role']})")
    flash(f"Switched to demo persona: {user['name']} ({user['role'].upper()})", 'success')

    target_url = f"/{user['role']}/dashboard"
    if request.is_json:
        return jsonify({'success': True, 'redirect': target_url})
    return redirect(target_url)

@app.route('/api/auth/me', methods=['GET'])
def api_me():
    user = get_current_user()
    if not user:
        return jsonify({'authenticated': False}), 200
    
    profile = {}
    if user['role'] == 'donor':
        profile = query_db("SELECT * FROM donor_profiles WHERE user_id = %s", (user['id'],), one=True) or {}
    elif user['role'] == 'ngo':
        profile = query_db("SELECT * FROM ngo_profiles WHERE user_id = %s", (user['id'],), one=True) or {}
    elif user['role'] == 'volunteer':
        profile = query_db("SELECT * FROM volunteer_profiles WHERE user_id = %s", (user['id'],), one=True) or {}

    return jsonify({
        'authenticated': True,
        'user': user,
        'profile': profile
    })

# --- API Endpoints: Donations ---

@app.route('/api/donations', methods=['GET'])
def list_donations():
    status = request.args.get('status')
    category = request.args.get('category')
    urgency = request.args.get('urgency')
    food_type = request.args.get('food_type')
    donor_id = request.args.get('donor_id')
    
    query = """
        SELECT d.*, u.name as donor_name, u.phone as donor_phone, u.email as donor_email,
               dp.organization_name, dp.donor_type, dp.fssai_license,
               ngo.name as ngo_name, vol.name as volunteer_name
        FROM donations d
        JOIN users u ON d.donor_id = u.id
        LEFT JOIN donor_profiles dp ON u.id = dp.user_id
        LEFT JOIN users ngo ON d.claimed_by_ngo_id = ngo.id
        LEFT JOIN users vol ON d.assigned_volunteer_id = vol.id
        WHERE 1=1
    """
    params = []

    if status:
        query += " AND d.status = %s"
        params.append(status)
    if category:
        query += " AND d.category = %s"
        params.append(category)
    if urgency:
        query += " AND d.urgency_level = %s"
        params.append(urgency)
    if food_type:
        query += " AND d.food_type = %s"
        params.append(food_type)
    if donor_id:
        query += " AND d.donor_id = %s"
        params.append(donor_id)

    query += " ORDER BY d.id DESC"
    donations = query_db(query, tuple(params))
    
    # Enrich with live countdown and time details
    now = datetime.now()
    for d in donations:
        try:
            exp = datetime.strptime(str(d['expiry_time'])[:19], '%Y-%m-%d %H:%M:%S')
            diff = (exp - now).total_seconds()
            d['seconds_left'] = int(diff)
            d['hours_left'] = round(diff / 3600.0, 1)
            d['is_expired'] = diff <= 0
        except Exception:
            d['seconds_left'] = 3600
            d['hours_left'] = 1.0
            d['is_expired'] = False

    return jsonify({'success': True, 'donations': donations})

@app.route('/api/donations', methods=['POST'])
@login_required
@role_required('donor')
def create_donation():
    donor_id = session['user_id']
    data = request.form if request.form else (request.get_json() or {})
    
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    category = data.get('category', 'Cooked Meal')
    food_type = data.get('food_type', 'Vegetarian')
    quantity_val = float(data.get('quantity_value', 10.0))
    quantity_unit = data.get('quantity_unit', 'kg')
    servings = int(data.get('servings', 20))
    storage_condition = data.get('storage_condition', 'Hot/Warm (>60°C)')
    pickup_address = data.get('pickup_address', '').strip()
    pickup_lat = float(data.get('pickup_lat', 28.5921))
    pickup_lng = float(data.get('pickup_lng', 77.1856))
    special_instructions = data.get('special_instructions', '').strip()

    # Expiry and cooked at handling
    hours_valid = float(data.get('hours_valid', 3.0))
    now = datetime.now()
    cooked_at = now - timedelta(minutes=45)
    expiry_time = now + timedelta(hours=hours_valid)

    if not title or not pickup_address:
        return jsonify({'error': 'Title and pickup address are required'}), 400

    # Image upload handling
    image_url = 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&auto=format&fit=crop&q=60'
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            fname = secure_filename(file.filename)
            unique_fname = f"food_{int(datetime.now().timestamp())}_{fname}"
            fpath = os.path.join(Config.UPLOAD_FOLDER, unique_fname)
            file.save(fpath)
            image_url = f"/static/uploads/{unique_fname}"
    elif data.get('image_url'):
        image_url = data.get('image_url')

    # Calculate Urgency
    if hours_valid <= 2.0:
        urgency_level = 'critical'
    elif hours_valid <= 4.0:
        urgency_level = 'medium'
    else:
        urgency_level = 'low'

    # Secure OTP Generation for pickup and delivery verification
    pickup_otp = str(random.randint(1000, 9999))
    delivery_otp = str(random.randint(1000, 9999))

    donation_id = execute_db("""
        INSERT INTO donations 
        (donor_id, title, description, category, food_type, quantity_value, quantity_unit, servings,
         cooked_at, expiry_time, storage_condition, pickup_address, pickup_lat, pickup_lng, special_instructions,
         image_url, status, urgency_level, pickup_otp, delivery_otp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'available', %s, %s, %s)
    """, (
        donor_id, title, description, category, food_type, quantity_val, quantity_unit, servings,
        cooked_at, expiry_time, storage_condition, pickup_address, pickup_lat, pickup_lng, special_instructions,
        image_url, urgency_level, pickup_otp, delivery_otp
    ))

    log_audit(donor_id, 'DONATION_CREATED', f"Created donation #{donation_id}: {title} ({servings} servings)")

    # Trigger Urgency Broadcast Notification if urgent
    if urgency_level in ['critical', 'medium']:
        broadcast_urgent_donation(donation_id, title, food_type, servings, pickup_lat, pickup_lng)

    # Immediately calculate top matched NGOs
    recommended_ngos = find_best_matching_ngos(donation_id, limit=3)

    return jsonify({
        'success': True,
        'message': 'Donation posted successfully! NGOs within radius have been notified.',
        'donation_id': donation_id,
        'recommended_ngos': recommended_ngos
    })

@app.route('/api/donations/<int:donation_id>', methods=['GET'])
def get_donation(donation_id):
    donation = query_db("""
        SELECT d.*, u.name as donor_name, u.phone as donor_phone, u.email as donor_email,
               dp.organization_name, dp.donor_type, dp.fssai_license,
               ngo.name as ngo_name, ngo.phone as ngo_phone,
               vol.name as volunteer_name, vol.phone as volunteer_phone
        FROM donations d
        JOIN users u ON d.donor_id = u.id
        LEFT JOIN donor_profiles dp ON u.id = dp.user_id
        LEFT JOIN users ngo ON d.claimed_by_ngo_id = ngo.id
        LEFT JOIN users vol ON d.assigned_volunteer_id = vol.id
        WHERE d.id = %s
    """, (donation_id,), one=True)
    
    if not donation:
        return jsonify({'error': 'Donation not found'}), 404

    # Calculate hours left
    try:
        exp = datetime.strptime(str(donation['expiry_time'])[:19], '%Y-%m-%d %H:%M:%S')
        diff = (exp - datetime.now()).total_seconds()
        donation['seconds_left'] = int(diff)
        donation['hours_left'] = round(diff / 3600.0, 1)
        donation['is_expired'] = diff <= 0
    except Exception:
        donation['seconds_left'] = 3600
        donation['hours_left'] = 1.0
        donation['is_expired'] = False

    return jsonify({'success': True, 'donation': donation})

@app.route('/api/donations/<int:donation_id>/match-ngos', methods=['GET'])
def get_donation_matches(donation_id):
    """Returns top ranked NGOs using the functional matching algorithm."""
    matches = find_best_matching_ngos(donation_id, limit=5)
    return jsonify({'success': True, 'matches': matches})

# --- API Endpoints: Claims & Delivery Tracking ---

@app.route('/api/donations/<int:donation_id>/claim', methods=['POST'])
@login_required
@role_required('ngo')
def claim_donation(donation_id):
    ngo_id = session['user_id']
    donation = query_db("SELECT * FROM donations WHERE id = %s", (donation_id,), one=True)
    
    if not donation:
        return jsonify({'error': 'Donation not found'}), 404
    
    if donation['status'] != 'available':
        return jsonify({'error': f"Donation is no longer available (currently {donation['status']})"}), 400

    now = datetime.now()
    execute_db("""
        UPDATE donations 
        SET status = 'requested', claimed_by_ngo_id = %s, updated_at = %s
        WHERE id = %s
    """, (ngo_id, now, donation_id))

    claim_id = execute_db("""
        INSERT INTO claims (donation_id, ngo_id, status, requested_at, accepted_at)
        VALUES (%s, %s, 'accepted', %s, %s)
    """, (donation_id, ngo_id, now, now))

    # Notify donor
    ngo_user = get_current_user()
    create_notification(
        user_id=donation['donor_id'],
        title="🎉 Food Donation Claimed!",
        message=f"{ngo_user['name']} has accepted your food donation: '{donation['title']}'. Preparation for pickup underway.",
        ntype='claim_update',
        link='/donor/dashboard'
    )

    # Notify nearby volunteers to pick up the delivery!
    volunteers = query_db("""
        SELECT u.id, u.name, u.latitude, u.longitude
        FROM users u
        JOIN volunteer_profiles vp ON u.id = vp.user_id
        WHERE u.role = 'volunteer' AND vp.is_available = 1
    """)
    for vol in volunteers:
        dist = haversine_distance(donation['pickup_lat'], donation['pickup_lng'], vol['latitude'], vol['longitude'])
        create_notification(
            user_id=vol['id'],
            title="🛵 New Food Delivery Mission Available!",
            message=f"Pickup '{donation['title']}' (~{dist} km) and deliver to {ngo_user['name']}.",
            ntype='delivery_status',
            link='/volunteer/dashboard'
        )

    log_audit(ngo_id, 'CLAIM_INITIATED', f"Claimed donation #{donation_id} (Claim #{claim_id})")

    return jsonify({
        'success': True,
        'message': 'Donation successfully claimed! Volunteers are being coordinated for pickup.',
        'claim_id': claim_id
    })

@app.route('/api/volunteer/tasks', methods=['GET'])
@login_required
@role_required('volunteer')
def get_volunteer_tasks():
    """Lists donations ready for volunteer pickup/transit."""
    user = get_current_user()
    tasks = query_db("""
        SELECT d.*, u.name as donor_name, u.phone as donor_phone, u.address as donor_address,
               ngo.name as ngo_name, ngo.phone as ngo_phone, ngo.address as ngo_address,
               ngo.latitude as ngo_lat, ngo.longitude as ngo_lng
        FROM donations d
        JOIN users u ON d.donor_id = u.id
        LEFT JOIN users ngo ON d.claimed_by_ngo_id = ngo.id
        WHERE d.status IN ('requested', 'in_transit')
        ORDER BY d.urgency_level DESC, d.id DESC
    """)

    for t in tasks:
        t['dist_to_donor'] = haversine_distance(user['latitude'], user['longitude'], t['pickup_lat'], t['pickup_lng'])
        if t['ngo_lat'] and t['ngo_lng']:
            t['dist_pickup_to_ngo'] = haversine_distance(t['pickup_lat'], t['pickup_lng'], t['ngo_lat'], t['ngo_lng'])
        else:
            t['dist_pickup_to_ngo'] = 5.0

    return jsonify({'success': True, 'tasks': tasks})

@app.route('/api/volunteer/accept-task/<int:donation_id>', methods=['POST'])
@login_required
@role_required('volunteer')
def accept_delivery_task(donation_id):
    vol_id = session['user_id']
    donation = query_db("SELECT * FROM donations WHERE id = %s", (donation_id,), one=True)
    
    if not donation:
        return jsonify({'error': 'Donation not found'}), 404

    now = datetime.now()
    execute_db("""
        UPDATE donations 
        SET assigned_volunteer_id = %s, updated_at = %s
        WHERE id = %s
    """, (vol_id, now, donation_id))

    execute_db("""
        UPDATE claims
        SET volunteer_id = %s
        WHERE donation_id = %s
    """, (vol_id, donation_id))

    vol_user = get_current_user()
    # Notify donor & NGO
    create_notification(
        user_id=donation['donor_id'],
        title="🛵 Volunteer Assigned for Pickup",
        message=f"{vol_user['name']} has accepted the pickup task for '{donation['title']}'. Verification code ready.",
        ntype='delivery_status',
        link='/donor/dashboard'
    )
    if donation.get('claimed_by_ngo_id'):
        create_notification(
            user_id=donation['claimed_by_ngo_id'],
            title="🛵 Volunteer Dispatched",
            message=f"{vol_user['name']} is en route to collect '{donation['title']}'.",
            ntype='delivery_status',
            link='/ngo/dashboard'
        )

    log_audit(vol_id, 'VOLUNTEER_TASK_ACCEPTED', f"Accepted delivery for donation #{donation_id}")

    return jsonify({
        'success': True,
        'message': 'Delivery task accepted! Proceed to pickup location.',
        'pickup_otp': donation['pickup_otp']
    })

@app.route('/api/donations/<int:donation_id>/verify-pickup', methods=['POST'])
@login_required
def verify_pickup(donation_id):
    """Verifies 4-digit pickup code and transitions status to in_transit."""
    data = request.get_json() or request.form
    entered_otp = str(data.get('otp', '')).strip()

    donation = query_db("SELECT * FROM donations WHERE id = %s", (donation_id,), one=True)
    if not donation:
        return jsonify({'error': 'Donation not found'}), 404

    if entered_otp != str(donation['pickup_otp']):
        return jsonify({'error': 'Invalid pickup code. Check with donor.'}), 400

    now = datetime.now()
    execute_db("""
        UPDATE donations 
        SET status = 'in_transit', updated_at = %s 
        WHERE id = %s
    """, (now, donation_id))

    execute_db("""
        UPDATE claims 
        SET status = 'in_transit', picked_up_at = %s 
        WHERE donation_id = %s
    """, (now, donation_id))

    # Notify NGO
    if donation['claimed_by_ngo_id']:
        create_notification(
            user_id=donation['claimed_by_ngo_id'],
            title="🚚 Food In Transit",
            message=f"Food '{donation['title']}' has been picked up from donor and is arriving at your facility.",
            ntype='delivery_status',
            link='/ngo/dashboard'
        )

    log_audit(session['user_id'], 'PICKUP_VERIFIED', f"Pickup verified for donation #{donation_id}")

    return jsonify({
        'success': True,
        'message': 'Pickup verified! Food is now in transit.'
    })

@app.route('/api/donations/<int:donation_id>/verify-delivery', methods=['POST'])
@login_required
def verify_delivery(donation_id):
    """Verifies delivery code, completes delivery and updates impact metrics."""
    data = request.get_json() or request.form
    entered_otp = str(data.get('otp', '')).strip()
    notes = data.get('delivery_notes', 'Food received in safe hygienic condition. Ready for distribution.')
    beneficiaries = int(data.get('beneficiaries_served', 0))

    donation = query_db("SELECT * FROM donations WHERE id = %s", (donation_id,), one=True)
    if not donation:
        return jsonify({'error': 'Donation not found'}), 404

    if entered_otp != str(donation['delivery_otp']):
        return jsonify({'error': 'Invalid delivery code. Check with receiving NGO.'}), 400

    if beneficiaries <= 0:
        beneficiaries = donation['servings']

    now = datetime.now()
    execute_db("""
        UPDATE donations 
        SET status = 'delivered', updated_at = %s 
        WHERE id = %s
    """, (now, donation_id))

    execute_db("""
        UPDATE claims 
        SET status = 'completed', delivered_at = %s, delivery_notes = %s, beneficiaries_served = %s
        WHERE donation_id = %s
    """, (now, notes, beneficiaries, donation_id))

    # Update volunteer stats if assigned
    if donation['assigned_volunteer_id']:
        execute_db("""
            UPDATE volunteer_profiles 
            SET total_deliveries = total_deliveries + 1 
            WHERE user_id = %s
        """, (donation['assigned_volunteer_id'],))

    # Notify donor
    create_notification(
        user_id=donation['donor_id'],
        title="🌟 Donation Delivered Successfully!",
        message=f"Your donation '{donation['title']}' was safely delivered! Reached {beneficiaries} people in need.",
        ntype='system',
        link='/impact'
    )

    log_audit(session['user_id'], 'DELIVERY_COMPLETED', f"Completed delivery for donation #{donation_id}. Beneficiaries: {beneficiaries}")

    return jsonify({
        'success': True,
        'message': f'Delivery completed successfully! {beneficiaries} meals served.'
    })

# --- API Endpoints: Notifications ---

@app.route('/api/notifications', methods=['GET'])
@login_required
def list_notifications():
    user_id = session['user_id']
    notifs = query_db("""
        SELECT * FROM notifications 
        WHERE user_id = %s 
        ORDER BY id DESC LIMIT 20
    """, (user_id,))
    return jsonify({'success': True, 'notifications': notifs})

@app.route('/api/notifications/<int:notif_id>/mark-read', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    execute_db("UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s", (notif_id, session['user_id']))
    return jsonify({'success': True})

@app.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    execute_db("UPDATE notifications SET is_read = 1 WHERE user_id = %s", (session['user_id'],))
    return jsonify({'success': True})

# --- API Endpoints: Map Data ---

@app.route('/api/map/data', methods=['GET'])
def get_map_data():
    """Returns interactive map pins for active donations, NGOs, and volunteers."""
    # Active Donations
    donations = query_db("""
        SELECT d.id, d.title, d.category, d.food_type, d.quantity_value, d.quantity_unit, d.servings,
               d.storage_condition, d.expiry_time, d.pickup_address, d.pickup_lat, d.pickup_lng,
               d.urgency_level, d.status, d.image_url,
               u.name as donor_name, u.phone as donor_phone
        FROM donations d
        JOIN users u ON d.donor_id = u.id
        WHERE d.status IN ('available', 'requested', 'in_transit')
    """)

    # NGOs
    ngos = query_db("""
        SELECT u.id, u.name, u.phone, u.address, u.latitude, u.longitude,
               np.organization_name, np.daily_capacity, np.has_cold_storage, np.verification_status
        FROM users u
        JOIN ngo_profiles np ON u.id = np.user_id
        WHERE u.role = 'ngo' AND u.status = 'active'
    """)

    # Volunteers
    volunteers = query_db("""
        SELECT u.id, u.name, u.latitude, u.longitude,
               vp.vehicle_type, vp.is_available, vp.rating
        FROM users u
        JOIN volunteer_profiles vp ON u.id = vp.user_id
        WHERE u.role = 'volunteer' AND u.status = 'active'
    """)

    # Calculate time left for donations
    now = datetime.now()
    for d in donations:
        try:
            exp = datetime.strptime(str(d['expiry_time'])[:19], '%Y-%m-%d %H:%M:%S')
            diff = (exp - now).total_seconds()
            d['hours_left'] = round(max(0, diff / 3600.0), 1)
        except Exception:
            d['hours_left'] = 2.0

    return jsonify({
        'success': True,
        'donations': donations,
        'ngos': ngos,
        'volunteers': volunteers
    })

# --- API Endpoints: Impact & Analytics ---

@app.route('/api/impact/stats', methods=['GET'])
def get_impact_stats():
    # 1. Total food kg and servings delivered
    delivered_data = query_db("""
        SELECT 
            COALESCE(SUM(quantity_value), 0) as total_kg,
            COALESCE(SUM(servings), 0) as total_servings,
            COUNT(*) as total_completed
        FROM donations
        WHERE status = 'delivered'
    """, one=True)

    # 2. Total active donations
    active_cnt = query_db("SELECT COUNT(*) as cnt FROM donations WHERE status IN ('available', 'requested', 'in_transit')", one=True)

    # 3. User Counts
    counts = query_db("""
        SELECT role, COUNT(*) as cnt FROM users WHERE status = 'active' GROUP BY role
    """)
    role_counts = {r['role']: r['cnt'] for r in counts}

    total_kg = float(delivered_data['total_kg']) if delivered_data else 0.0
    total_servings = int(delivered_data['total_servings']) if delivered_data else 0
    # Formula: 1 kg food waste ≈ 2.5 kg CO2 emission prevented
    co2_saved_kg = round(total_kg * 2.5, 1)

    # 4. Food Category Distribution for Chart.js
    category_data = query_db("""
        SELECT category, COUNT(*) as count, SUM(quantity_value) as total_kg
        FROM donations
        GROUP BY category
    """)

    # 5. Monthly / Daily timeline for Chart.js
    timeline_data = [
        {'day': 'Mon', 'kg': 45},
        {'day': 'Tue', 'kg': 68},
        {'day': 'Wed', 'kg': 92},
        {'day': 'Thu', 'kg': 110},
        {'day': 'Fri', 'kg': 140},
        {'day': 'Sat', 'kg': 185},
        {'day': 'Sun', 'kg': 230}
    ]

    return jsonify({
        'success': True,
        'impact': {
            'total_food_saved_kg': total_kg,
            'total_meals_served': total_servings,
            'co2_saved_kg': co2_saved_kg,
            'completed_donations': delivered_data['total_completed'] if delivered_data else 0,
            'active_donations': active_cnt['cnt'] if active_cnt else 0,
            'donors_count': role_counts.get('donor', 0),
            'ngos_count': role_counts.get('ngo', 0),
            'volunteers_count': role_counts.get('volunteer', 0),
            'categories': category_data,
            'timeline': timeline_data
        }
    })

# --- API Endpoints: Admin Dashboard ---

@app.route('/api/admin/users', methods=['GET'])
@login_required
@role_required('admin')
def admin_list_users():
    role = request.args.get('role')
    status = request.args.get('status')
    
    query = """
        SELECT u.id, u.name, u.email, u.role, u.phone, u.address, u.status, u.created_at,
               np.verification_status, np.daily_capacity,
               vp.vehicle_type, vp.total_deliveries,
               dp.organization_name, dp.donor_type
        FROM users u
        LEFT JOIN ngo_profiles np ON u.id = np.user_id
        LEFT JOIN volunteer_profiles vp ON u.id = vp.user_id
        LEFT JOIN donor_profiles dp ON u.id = dp.user_id
        WHERE 1=1
    """
    params = []
    if role:
        query += " AND u.role = %s"
        params.append(role)
    if status:
        query += " AND u.status = %s"
        params.append(status)
        
    query += " ORDER BY u.id DESC"
    users = query_db(query, tuple(params))
    return jsonify({'success': True, 'users': users})

@app.route('/api/admin/users/<int:user_id>/status', methods=['POST'])
@login_required
@role_required('admin')
def admin_toggle_user_status(user_id):
    data = request.get_json() or request.form
    new_status = data.get('status', 'active')
    execute_db("UPDATE users SET status = %s WHERE id = %s", (new_status, user_id))
    log_audit(session['user_id'], 'ADMIN_USER_STATUS_CHANGE', f"Changed user #{user_id} status to {new_status}")
    return jsonify({'success': True, 'message': f'User status updated to {new_status}'})

@app.route('/api/admin/ngos/verify/<int:ngo_user_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_verify_ngo(ngo_user_id):
    data = request.get_json() or request.form
    action = data.get('action', 'verified') # 'verified' or 'rejected'
    
    now = datetime.now() if action == 'verified' else None
    execute_db("""
        UPDATE ngo_profiles 
        SET verification_status = %s, verified_at = %s
        WHERE user_id = %s
    """, (action, now, ngo_user_id))

    status_user = 'active' if action == 'verified' else 'suspended'
    execute_db("UPDATE users SET status = %s WHERE id = %s", (status_user, ngo_user_id))

    # Notify NGO
    create_notification(
        user_id=ngo_user_id,
        title="🛡️ NGO Verification Update",
        message=f"Your NGO organization has been {action} by the FoodBridge Administrator.",
        ntype='system',
        link='/ngo/dashboard'
    )

    log_audit(session['user_id'], 'ADMIN_NGO_VERIFIED', f"Set NGO #{ngo_user_id} status to {action}")
    return jsonify({'success': True, 'message': f'NGO has been {action}.'})

@app.route('/api/admin/audit-logs', methods=['GET'])
@login_required
@role_required('admin')
def admin_audit_logs():
    logs = query_db("""
        SELECT a.*, u.name as user_name, u.role as user_role, u.email as user_email
        FROM audit_logs a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.id DESC LIMIT 50
    """)
    return jsonify({'success': True, 'logs': logs})

# --- Frontend View Routes ---

@app.route('/')
def index_view():
    return render_template('index.html')

@app.route('/login')
def login_view():
    if 'user_id' in session:
        return redirect(f"/{session.get('role', 'donor')}/dashboard")
    return render_template('login.html')

@app.route('/register')
def register_view():
    if 'user_id' in session:
        return redirect(f"/{session.get('role', 'donor')}/dashboard")
    return render_template('register.html')

@app.route('/map')
def map_view():
    return render_template('map.html')

@app.route('/impact')
def impact_view():
    return render_template('impact.html')

@app.route('/donor/dashboard')
@login_required
@role_required('donor')
def donor_dashboard_view():
    return render_template('donor_dashboard.html')

@app.route('/ngo/dashboard')
@login_required
@role_required('ngo')
def ngo_dashboard_view():
    return render_template('ngo_dashboard.html')

@app.route('/volunteer/dashboard')
@login_required
@role_required('volunteer')
def volunteer_dashboard_view():
    return render_template('volunteer_dashboard.html')

@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard_view():
    return render_template('admin_dashboard.html')

if __name__ == '__main__':
    # Initialize DB schema if not already present
    init_db()
    print("=" * 65)
    print("[FoodBridge] Smart Food Redistribution Platform starting...")
    print(f"[FoodBridge] Active Storage Engine: {ACTIVE_DB_ENGINE}")
    print("[FoodBridge] Access Application at: http://127.0.0.1:5000")
    print("=" * 65)
    app.run(host='0.0.0.0', port=5000, debug=True)
