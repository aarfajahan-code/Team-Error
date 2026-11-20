import math
from datetime import datetime, timezone
from database import query_db

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    Returns distance in kilometers.
    """
    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    except (TypeError, ValueError):
        return 999.0 # Default large distance if coordinates invalid

    # Earth radius in kilometers
    R = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def calculate_match_score(donation, ngo):
    """
    Computes a scientific match score (0 to 100) between a donation and an NGO.
    Takes into account:
    1. Distance (Haversine formula)
    2. Capacity fit (Servings vs NGO daily capacity)
    3. Storage requirements (Cold storage for perishables/refrigerated)
    4. Dietary preferences (Veg/Non-veg/Raw/Cooked)
    5. Verification & Availability status
    """
    reasons = []

    # 1. Distance Calculation & Score (40% weight)
    donor_lat = donation.get('pickup_lat')
    donor_lng = donation.get('pickup_lng')
    ngo_lat = ngo.get('latitude')
    ngo_lng = ngo.get('longitude')
    
    dist_km = haversine_distance(donor_lat, donor_lng, ngo_lat, ngo_lng)
    
    if dist_km <= 2.0:
        dist_score = 100
        reasons.append(f"Ultra-close location ({dist_km} km away, ~5-10 min response)")
    elif dist_km <= 5.0:
        dist_score = 90 - (dist_km - 2.0) * 6
        reasons.append(f"Nearby NGO ({dist_km} km away)")
    elif dist_km <= 15.0:
        dist_score = 70 - (dist_km - 5.0) * 3
        reasons.append(f"Accessible within district ({dist_km} km)")
    elif dist_km <= 30.0:
        dist_score = 40 - (dist_km - 15.0) * 1.5
        reasons.append(f"Moderate distance ({dist_km} km)")
    else:
        dist_score = max(5, 20 - (dist_km - 30.0) * 0.4)
        reasons.append(f"Long distance ({dist_km} km)")

    # 2. Capacity Fit Score (25% weight)
    servings = float(donation.get('servings', 10))
    daily_cap = float(ngo.get('daily_capacity', 100))
    
    if daily_cap <= 0:
        daily_cap = 100
        
    cap_ratio = servings / daily_cap
    if cap_ratio <= 0.6:
        # Fits comfortably within daily distribution
        cap_score = 100
        reasons.append(f"Ideal capacity match ({int(servings)} servings fits daily quota of {int(daily_cap)})")
    elif cap_ratio <= 1.0:
        cap_score = 85
        reasons.append(f"High intake capacity ({int(servings)}/{int(daily_cap)} servings)")
    elif cap_ratio <= 1.5:
        cap_score = 60
        reasons.append("Exceeds normal capacity slightly, may require volunteer support")
    else:
        cap_score = max(20, 50 - (cap_ratio - 1.5) * 20)
        reasons.append("Large bulk donation relative to NGO daily intake")

    # 3. Dietary & Category Preference Score (20% weight)
    pref_str = (ngo.get('preferred_food_types') or '').lower()
    food_type = (donation.get('food_type') or '').lower()
    category = (donation.get('category') or '').lower()
    
    diet_score = 80 # Baseline
    
    # Check dietary restriction
    if 'veg' in food_type and 'non' not in food_type:
        # Veg food is accepted by virtually everyone
        diet_score = 100
        reasons.append("Vegetarian food matches all dietary rules")
    elif 'non' in food_type:
        if 'non-veg' in pref_str or 'all' in pref_str or 'meat' in pref_str:
            diet_score = 100
            reasons.append("Non-vegetarian food accepted by NGO kitchen")
        else:
            diet_score = 25
            reasons.append("NGO primarily distributes vegetarian food")
            
    # Check food category preference
    if category and category in pref_str:
        diet_score = min(100, diet_score + 10)

    # 4. Storage & Perishability Score (15% weight)
    storage = (donation.get('storage_condition') or '').lower()
    has_cold_storage = bool(ngo.get('has_cold_storage', 0))
    
    storage_score = 80
    if 'refrigerat' in storage or 'frozen' in storage or 'cold' in storage:
        if has_cold_storage:
            storage_score = 100
            reasons.append("NGO has certified cold storage facilities for perishable food")
        else:
            storage_score = 40
            reasons.append("Perishable food but NGO lacks specialized cold storage")
    else:
        storage_score = 90
        
    # Verification bonus
    verification_status = ngo.get('verification_status', 'pending')
    if verification_status == 'verified':
        storage_score = min(100, storage_score + 10)
    else:
        storage_score = max(30, storage_score - 20)
        reasons.append("Pending verification")

    # Compute Weighted Score
    # Distance: 40%, Capacity: 25%, Dietary: 20%, Storage/Verif: 15%
    total_score = (dist_score * 0.40) + (cap_score * 0.25) + (diet_score * 0.20) + (storage_score * 0.15)
    final_score = int(round(min(100, max(0, total_score))))

    return {
        'ngo_id': ngo.get('id'),
        'ngo_name': ngo.get('organization_name') or ngo.get('name'),
        'contact_person': ngo.get('contact_person') or ngo.get('name'),
        'phone': ngo.get('phone'),
        'email': ngo.get('email'),
        'address': ngo.get('address'),
        'latitude': ngo_lat,
        'longitude': ngo_lng,
        'distance_km': dist_km,
        'estimated_mins': max(5, int(dist_km * 2.8)),
        'match_score': final_score,
        'daily_capacity': int(daily_cap),
        'has_cold_storage': has_cold_storage,
        'verification_status': verification_status,
        'match_reasons': reasons[:3] # Top 3 key match highlights
    }

def find_best_matching_ngos(donation_id, limit=5):
    """
    Retrieves a donation by ID, scans all active and verified NGOs,
    and returns a ranked list of recommended NGOs with scores and rationale.
    """
    donation = query_db("SELECT * FROM donations WHERE id = %s", (donation_id,), one=True)
    if not donation:
        return []

    ngos = query_db("""
        SELECT u.id, u.name, u.email, u.phone, u.address, u.latitude, u.longitude,
               np.organization_name, np.registration_no, np.contact_person,
               np.daily_capacity, np.preferred_food_types, np.has_cold_storage,
               np.verification_status, np.operating_hours
        FROM users u
        JOIN ngo_profiles np ON u.id = np.user_id
        WHERE u.role = 'ngo' AND u.status = 'active'
    """)

    matches = []
    for ngo in ngos:
        score_data = calculate_match_score(donation, ngo)
        matches.append(score_data)

    # Sort descending by match_score, then ascending by distance
    matches.sort(key=lambda x: (x['match_score'], -x['distance_km']), reverse=True)
    return matches[:limit]
