import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from database import get_connection, query_db, execute_db, init_db

def seed_database():
    print("[FoodBridge] Seeding comprehensive hackathon demonstration data...")
    init_db()
    
    # Check if data already exists
    existing = query_db("SELECT COUNT(*) as cnt FROM users", one=True)
    if existing and existing['cnt'] > 0:
        print("[FoodBridge] Database already seeded. Skipping re-seed.")
        return

    pwd_hash = generate_password_hash("password123")
    admin_pwd_hash = generate_password_hash("admin123")
    
    now = datetime.now()

    # 1. USERS: Admin, Donors, NGOs, Volunteers
    users_data = [
        # ADMIN
        {
            'name': 'Platform Administrator',
            'email': 'admin@foodbridge.org',
            'password_hash': admin_pwd_hash,
            'role': 'admin',
            'phone': '+91 98110 00001',
            'address': 'FoodBridge HQ, Connaught Place, New Delhi',
            'latitude': 28.6328,
            'longitude': 77.2197,
            'status': 'active'
        },
        # DONORS
        {
            'name': 'The Grand Palace Hotel',
            'email': 'grandpalace@donor.org',
            'password_hash': pwd_hash,
            'role': 'donor',
            'phone': '+91 98110 11001',
            'address': 'Chanakyapuri Diplomatic Enclave, New Delhi',
            'latitude': 28.5921,
            'longitude': 77.1856,
            'status': 'active'
        },
        {
            'name': 'Spice Route Fine Dining',
            'email': 'spiceroute@donor.org',
            'password_hash': pwd_hash,
            'role': 'donor',
            'phone': '+91 98110 11002',
            'address': 'Khan Market Commercial Center, New Delhi',
            'latitude': 28.6003,
            'longitude': 77.2270,
            'status': 'active'
        },
        {
            'name': 'Royal Celebrations Wedding Hall',
            'email': 'royalweddings@donor.org',
            'password_hash': pwd_hash,
            'role': 'donor',
            'phone': '+91 98110 11003',
            'address': 'Ring Road Banquet Row, Kirti Nagar, New Delhi',
            'latitude': 28.6517,
            'longitude': 77.1356,
            'status': 'active'
        },
        {
            'name': 'FreshMart Supermarket & Deli',
            'email': 'freshmart@donor.org',
            'password_hash': pwd_hash,
            'role': 'donor',
            'phone': '+91 98110 11004',
            'address': 'Sector 14 Market Complex, Gurugram',
            'latitude': 28.4732,
            'longitude': 77.0425,
            'status': 'active'
        },
        {
            'name': 'CyberHub Corporate Cafeteria',
            'email': 'cafeteria@donor.org',
            'password_hash': pwd_hash,
            'role': 'donor',
            'phone': '+91 98110 11005',
            'address': 'DLF Cyber City, Tower 8, Gurugram',
            'latitude': 28.4950,
            'longitude': 77.0895,
            'status': 'active'
        },
        # NGOs
        {
            'name': 'Hope Shelter & Food Bank',
            'email': 'hopeshelter@ngo.org',
            'password_hash': pwd_hash,
            'role': 'ngo',
            'phone': '+91 98110 22001',
            'address': 'Lodhi Road Community Center, New Delhi',
            'latitude': 28.5905,
            'longitude': 77.2245,
            'status': 'active'
        },
        {
            'name': 'Robin Community Kitchen',
            'email': 'robinkitchen@ngo.org',
            'password_hash': pwd_hash,
            'role': 'ngo',
            'phone': '+91 98110 22002',
            'address': 'Karol Bagh Market, New Delhi',
            'latitude': 28.6473,
            'longitude': 77.1906,
            'status': 'active'
        },
        {
            'name': 'Sunshine Children Orphanage',
            'email': 'sunshine@ngo.org',
            'password_hash': pwd_hash,
            'role': 'ngo',
            'phone': '+91 98110 22003',
            'address': 'Lajpat Nagar IV, New Delhi',
            'latitude': 28.5670,
            'longitude': 77.2435,
            'status': 'active'
        },
        {
            'name': 'Annapurna Relief Mission',
            'email': 'annapurna@ngo.org',
            'password_hash': pwd_hash,
            'role': 'ngo',
            'phone': '+91 98110 22004',
            'address': 'MG Road Sector 28, Gurugram',
            'latitude': 28.4812,
            'longitude': 77.0864,
            'status': 'active'
        },
        {
            'name': 'Elders Care Trust & Shelter',
            'email': 'elderscare@ngo.org',
            'password_hash': pwd_hash,
            'role': 'ngo',
            'phone': '+91 98110 22005',
            'address': 'Dwarka Sector 11 Community Hub, New Delhi',
            'latitude': 28.5912,
            'longitude': 77.0543,
            'status': 'active'
        },
        # VOLUNTEERS
        {
            'name': 'Rahul Sharma',
            'email': 'rahul@volunteer.org',
            'password_hash': pwd_hash,
            'role': 'volunteer',
            'phone': '+91 98110 33001',
            'address': 'Defence Colony, New Delhi',
            'latitude': 28.5726,
            'longitude': 77.2304,
            'status': 'active'
        },
        {
            'name': 'Priya Patel',
            'email': 'priya@volunteer.org',
            'password_hash': pwd_hash,
            'role': 'volunteer',
            'phone': '+91 98110 33002',
            'address': 'Hauz Khas Enclave, New Delhi',
            'latitude': 28.5494,
            'longitude': 77.2001,
            'status': 'active'
        },
        {
            'name': 'Amit Verma',
            'email': 'amit@volunteer.org',
            'password_hash': pwd_hash,
            'role': 'volunteer',
            'phone': '+91 98110 33003',
            'address': 'DLF Phase 2, Gurugram',
            'latitude': 28.4900,
            'longitude': 77.0800,
            'status': 'active'
        },
        {
            'name': 'Sarah Khan',
            'email': 'sarah@volunteer.org',
            'password_hash': pwd_hash,
            'role': 'volunteer',
            'phone': '+91 98110 33004',
            'address': 'Pusa Road, Rajendra Place, New Delhi',
            'latitude': 28.6430,
            'longitude': 77.1780,
            'status': 'active'
        }
    ]

    user_ids = {}
    for u in users_data:
        uid = execute_db("""
            INSERT INTO users (name, email, password_hash, role, phone, address, latitude, longitude, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (u['name'], u['email'], u['password_hash'], u['role'], u['phone'], u['address'], u['latitude'], u['longitude'], u['status']))
        user_ids[u['email']] = uid

    # 2. PROFILES
    # Donor profiles
    execute_db("""
        INSERT INTO donor_profiles (user_id, organization_name, donor_type, contact_person, fssai_license)
        VALUES 
        (%s, 'The Grand Palace Hotel', 'Hotel', 'Chef Rajesh Saxena', 'FSSAI-11520034001920'),
        (%s, 'Spice Route Fine Dining', 'Restaurant', 'Ananya Sen', 'FSSAI-11521034002811'),
        (%s, 'Royal Celebrations Wedding Hall', 'Wedding Hall', 'Vikram Malhotra', 'FSSAI-11522034003942'),
        (%s, 'FreshMart Supermarket & Deli', 'Supermarket', 'Neha Kapoor', 'FSSAI-11523034004123'),
        (%s, 'CyberHub Corporate Cafeteria', 'Catering', 'Sunil Rao', 'FSSAI-11524034005876')
    """, (
        user_ids['grandpalace@donor.org'],
        user_ids['spiceroute@donor.org'],
        user_ids['royalweddings@donor.org'],
        user_ids['freshmart@donor.org'],
        user_ids['cafeteria@donor.org']
    ))

    # NGO profiles
    execute_db("""
        INSERT INTO ngo_profiles (user_id, organization_name, registration_no, contact_person, daily_capacity, preferred_food_types, has_cold_storage, operating_hours, verification_status, verified_at)
        VALUES 
        (%s, 'Hope Shelter & Food Bank', 'NGO-DL-2018-8472', 'Dr. Aruna Mehta', 350, 'Vegetarian,Non-Vegetarian,Cooked Meal,Raw Groceries', 1, '07:00 AM - 11:00 PM', 'verified', %s),
        (%s, 'Robin Community Kitchen', 'NGO-DL-2020-5621', 'Karan Johar', 220, 'Vegetarian,Cooked Meal,Bakery & Dairy', 1, '08:00 AM - 10:00 PM', 'verified', %s),
        (%s, 'Sunshine Children Orphanage', 'NGO-DL-2019-9134', 'Sister Maria', 120, 'Vegetarian,Cooked Meal,Fruits & Vegetables,Bakery & Dairy', 0, '08:00 AM - 08:00 PM', 'verified', %s),
        (%s, 'Annapurna Relief Mission', 'NGO-HR-2017-3841', 'Ramesh Chandra', 500, 'Vegetarian,Non-Vegetarian,Cooked Meal,Packaged Food', 1, '06:00 AM - 11:30 PM', 'verified', %s),
        (%s, 'Elders Care Trust & Shelter', 'NGO-DL-2024-1109', 'Savita Deshmukh', 80, 'Vegetarian,Cooked Meal,Soft Food', 0, '09:00 AM - 07:00 PM', 'pending', NULL)
    """, (
        user_ids['hopeshelter@ngo.org'], now,
        user_ids['robinkitchen@ngo.org'], now,
        user_ids['sunshine@ngo.org'], now,
        user_ids['annapurna@ngo.org'], now,
        user_ids['elderscare@ngo.org']
    ))

    # Volunteer profiles
    execute_db("""
        INSERT INTO volunteer_profiles (user_id, vehicle_type, max_weight_kg, is_available, total_deliveries, rating)
        VALUES 
        (%s, 'Motorbike', 20.0, 1, 38, 4.95),
        (%s, 'Car', 60.0, 1, 24, 4.90),
        (%s, 'Van', 250.0, 1, 62, 5.00),
        (%s, 'Scooter', 25.0, 1, 19, 4.85)
    """, (
        user_ids['rahul@volunteer.org'],
        user_ids['priya@volunteer.org'],
        user_ids['amit@volunteer.org'],
        user_ids['sarah@volunteer.org']
    ))

    # 3. DONATIONS
    # Realistic times relative to 'now'
    donations_data = [
        # 1. High Urgency Available Donation (Expiring in 1.5 hours)
        {
            'donor_id': user_ids['grandpalace@donor.org'],
            'title': '65 Portions Shahi Biryani & Cucumber Raita',
            'description': 'Surplus hot buffet from diplomacy luncheon. Premium basmati rice, rich spices, sealed in insulated thermocol containers. Prepared under strict hygiene.',
            'category': 'Cooked Meal',
            'food_type': 'Vegetarian',
            'quantity_value': 28.0,
            'quantity_unit': 'kg',
            'servings': 65,
            'cooked_at': now - timedelta(hours=2),
            'expiry_time': now + timedelta(hours=1, minutes=45), # Urgent!
            'storage_condition': 'Hot/Warm (>60°C)',
            'pickup_address': 'The Grand Palace Hotel, Banquet Kitchen Gate 3, Chanakyapuri, New Delhi',
            'pickup_lat': 28.5921,
            'pickup_lng': 77.1856,
            'special_instructions': 'Security notified. Drive directly to Service Ramp Gate 3. Boxes are labeled.',
            'image_url': 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=800&auto=format&fit=crop&q=60',
            'status': 'available',
            'urgency_level': 'critical',
            'pickup_otp': '4821',
            'delivery_otp': '7912'
        },
        # 2. Medium Urgency Available Donation (Expiring in 3.5 hours)
        {
            'donor_id': user_ids['spiceroute@donor.org'],
            'title': '40 Portions Paneer Butter Masala & Butter Roti',
            'description': 'Surplus dinner preparation from evening private party. Packed in food-grade aluminum containers.',
            'category': 'Cooked Meal',
            'food_type': 'Vegetarian',
            'quantity_value': 18.0,
            'quantity_unit': 'kg',
            'servings': 40,
            'cooked_at': now - timedelta(hours=1),
            'expiry_time': now + timedelta(hours=3, minutes=30),
            'storage_condition': 'Hot/Warm (>60°C)',
            'pickup_address': 'Spice Route Fine Dining, Khan Market Middle Lane, New Delhi',
            'pickup_lat': 28.6003,
            'pickup_lng': 77.2270,
            'special_instructions': 'Collect from back kitchen dispatch door. Handover to Chef Ananya.',
            'image_url': 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=800&auto=format&fit=crop&q=60',
            'status': 'available',
            'urgency_level': 'medium',
            'pickup_otp': '3190',
            'delivery_otp': '6428'
        },
        # 3. Available Bakery Surplus (Expiring in 8 hours)
        {
            'donor_id': user_ids['freshmart@donor.org'],
            'title': '30 kg Fresh Bakery Assortment (Breads, Rolls, Buns)',
            'description': 'Fresh morning bakery production, packaged and sealed. High nutritional value, completely fresh.',
            'category': 'Bakery & Dairy',
            'food_type': 'Vegetarian',
            'quantity_value': 30.0,
            'quantity_unit': 'kg',
            'servings': 90,
            'cooked_at': now - timedelta(hours=4),
            'expiry_time': now + timedelta(hours=8),
            'storage_condition': 'Room Temperature',
            'pickup_address': 'FreshMart Supermarket, Loading Bay A, Sector 14, Gurugram',
            'pickup_lat': 28.4732,
            'pickup_lng': 77.0425,
            'special_instructions': 'Trolleys available for easy loading into car boot or bike crates.',
            'image_url': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=800&auto=format&fit=crop&q=60',
            'status': 'available',
            'urgency_level': 'low',
            'pickup_otp': '5512',
            'delivery_otp': '8841'
        },
        # 4. Large Raw Fresh Produce (Expiring in 24 hours)
        {
            'donor_id': user_ids['freshmart@donor.org'],
            'title': '75 kg Fresh Farm Vegetables & Seasonal Fruits',
            'description': 'Potatoes, tomatoes, carrots, spinach, and fresh apples in crates. Perfect for community kitchens.',
            'category': 'Fruits & Vegetables',
            'food_type': 'Vegetarian',
            'quantity_value': 75.0,
            'quantity_unit': 'kg',
            'servings': 180,
            'cooked_at': None,
            'expiry_time': now + timedelta(hours=22),
            'storage_condition': 'Refrigerated (0-4°C)',
            'pickup_address': 'FreshMart Supermarket, Cold Storage Dock, Sector 14, Gurugram',
            'pickup_lat': 28.4732,
            'pickup_lng': 77.0425,
            'special_instructions': 'Bring a van or car. Crates are stacked on pallets.',
            'image_url': 'https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=800&auto=format&fit=crop&q=60',
            'status': 'available',
            'urgency_level': 'low',
            'pickup_otp': '9012',
            'delivery_otp': '1452'
        },
        # 5. Non-Veg Cooked Meal (Expiring in 2.5 hours)
        {
            'donor_id': user_ids['cafeteria@donor.org'],
            'title': '50 Meal Trays Grilled Chicken & Herb Infused Rice',
            'description': 'Individual sealed meal trays from corporate executive dining. Balanced protein and nutrition.',
            'category': 'Cooked Meal',
            'food_type': 'Non-Vegetarian',
            'quantity_value': 22.0,
            'quantity_unit': 'kg',
            'servings': 50,
            'cooked_at': now - timedelta(hours=2),
            'expiry_time': now + timedelta(hours=2, minutes=30),
            'storage_condition': 'Hot/Warm (>60°C)',
            'pickup_address': 'DLF Cyber City, Tower 8 Service Entrance, Gurugram',
            'pickup_lat': 28.4950,
            'pickup_lng': 77.0895,
            'special_instructions': 'Pass required at security desk; registered under FoodBridge.',
            'image_url': 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&auto=format&fit=crop&q=60',
            'status': 'available',
            'urgency_level': 'medium',
            'pickup_otp': '7241',
            'delivery_otp': '9310'
        },
        # 6. Donation in Status 'requested' (Claimed by Hope Shelter, pending volunteer)
        {
            'donor_id': user_ids['royalweddings@donor.org'],
            'title': '120 Servings Wedding Feast (Dal Makhani, Pulao, Mix Veg)',
            'description': 'Massive wedding surplus. Hygienically transferred into food-grade steel containers and thermal casseroles.',
            'category': 'Cooked Meal',
            'food_type': 'Vegetarian',
            'quantity_value': 55.0,
            'quantity_unit': 'kg',
            'servings': 120,
            'cooked_at': now - timedelta(hours=3),
            'expiry_time': now + timedelta(hours=3),
            'storage_condition': 'Hot/Warm (>60°C)',
            'pickup_address': 'Royal Celebrations Banquet, Kirti Nagar Industrial Area, New Delhi',
            'pickup_lat': 28.6517,
            'pickup_lng': 77.1356,
            'special_instructions': 'Spacious parking right outside kitchen dispatch. Van recommended.',
            'image_url': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=800&auto=format&fit=crop&q=60',
            'status': 'requested',
            'urgency_level': 'medium',
            'claimed_by_ngo_id': user_ids['hopeshelter@ngo.org'],
            'pickup_otp': '8129',
            'delivery_otp': '4301'
        },
        # 7. Donation in Status 'in_transit' (Picked up by Volunteer Rahul, en route to Robin Community Kitchen)
        {
            'donor_id': user_ids['grandpalace@donor.org'],
            'title': '45 Packs Continental Pasta & Garlic Herb Bread',
            'description': 'Freshly prepared Italian buffet surplus, individually packed in heat-retaining containers.',
            'category': 'Cooked Meal',
            'food_type': 'Vegetarian',
            'quantity_value': 16.0,
            'quantity_unit': 'kg',
            'servings': 45,
            'cooked_at': now - timedelta(hours=2),
            'expiry_time': now + timedelta(hours=2),
            'storage_condition': 'Hot/Warm (>60°C)',
            'pickup_address': 'The Grand Palace Hotel, Chanakyapuri, New Delhi',
            'pickup_lat': 28.5921,
            'pickup_lng': 77.1856,
            'special_instructions': 'Picked up by volunteer. ETA 15 minutes to Robin Kitchen.',
            'image_url': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800&auto=format&fit=crop&q=60',
            'status': 'in_transit',
            'urgency_level': 'critical',
            'claimed_by_ngo_id': user_ids['robinkitchen@ngo.org'],
            'assigned_volunteer_id': user_ids['rahul@volunteer.org'],
            'pickup_otp': '6239',
            'delivery_otp': '1845'
        },
        # 8. Completed & Delivered Donation (For Impact Metrics & History)
        {
            'donor_id': user_ids['spiceroute@donor.org'],
            'title': '80 Portions Dal Tadka & Jeera Rice with Sweets',
            'description': 'Lunch banquet distribution successfully conducted.',
            'category': 'Cooked Meal',
            'food_type': 'Vegetarian',
            'quantity_value': 35.0,
            'quantity_unit': 'kg',
            'servings': 80,
            'cooked_at': now - timedelta(days=1, hours=4),
            'expiry_time': now - timedelta(days=1),
            'storage_condition': 'Hot/Warm (>60°C)',
            'pickup_address': 'Spice Route Fine Dining, Khan Market, New Delhi',
            'pickup_lat': 28.6003,
            'pickup_lng': 77.2270,
            'special_instructions': 'Completed delivery.',
            'image_url': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=800&auto=format&fit=crop&q=60',
            'status': 'delivered',
            'urgency_level': 'low',
            'claimed_by_ngo_id': user_ids['sunshine@ngo.org'],
            'assigned_volunteer_id': user_ids['priya@volunteer.org'],
            'pickup_otp': '9940',
            'delivery_otp': '2109'
        },
        # 9. Another Completed Delivered Donation
        {
            'donor_id': user_ids['cafeteria@donor.org'],
            'title': '110 Packaged Sandwiches & Fruit Juice Cartons',
            'description': 'Snack packs distributed to street children and daily wage workers.',
            'category': 'Packaged Food',
            'food_type': 'Vegetarian',
            'quantity_value': 42.0,
            'quantity_unit': 'kg',
            'servings': 110,
            'cooked_at': now - timedelta(days=2),
            'expiry_time': now - timedelta(days=1, hours=12),
            'storage_condition': 'Room Temperature',
            'pickup_address': 'DLF Cyber City, Tower 8, Gurugram',
            'pickup_lat': 28.4950,
            'pickup_lng': 77.0895,
            'special_instructions': 'Completed delivery.',
            'image_url': 'https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=800&auto=format&fit=crop&q=60',
            'status': 'delivered',
            'urgency_level': 'low',
            'claimed_by_ngo_id': user_ids['annapurna@ngo.org'],
            'assigned_volunteer_id': user_ids['amit@volunteer.org'],
            'pickup_otp': '4173',
            'delivery_otp': '8902'
        }
    ]

    donation_ids = []
    for d in donations_data:
        did = execute_db("""
            INSERT INTO donations 
            (donor_id, title, description, category, food_type, quantity_value, quantity_unit, servings,
             cooked_at, expiry_time, storage_condition, pickup_address, pickup_lat, pickup_lng, special_instructions,
             image_url, status, urgency_level, claimed_by_ngo_id, assigned_volunteer_id, pickup_otp, delivery_otp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            d['donor_id'], d['title'], d['description'], d['category'], d['food_type'], d['quantity_value'],
            d['quantity_unit'], d['servings'], d['cooked_at'], d['expiry_time'], d['storage_condition'],
            d['pickup_address'], d['pickup_lat'], d['pickup_lng'], d['special_instructions'], d['image_url'],
            d['status'], d['urgency_level'], d.get('claimed_by_ngo_id'), d.get('assigned_volunteer_id'),
            d['pickup_otp'], d['delivery_otp']
        ))
        donation_ids.append(did)

    # 4. CLAIMS
    # Claim for donation #6 (requested)
    execute_db("""
        INSERT INTO claims (donation_id, ngo_id, volunteer_id, status, requested_at, accepted_at)
        VALUES (%s, %s, NULL, 'pending', %s, %s)
    """, (donation_ids[5], user_ids['hopeshelter@ngo.org'], now - timedelta(minutes=45), now - timedelta(minutes=30)))

    # Claim for donation #7 (in_transit)
    execute_db("""
        INSERT INTO claims (donation_id, ngo_id, volunteer_id, status, requested_at, accepted_at, picked_up_at)
        VALUES (%s, %s, %s, 'in_transit', %s, %s, %s)
    """, (donation_ids[6], user_ids['robinkitchen@ngo.org'], user_ids['rahul@volunteer.org'],
          now - timedelta(hours=1, minutes=15), now - timedelta(minutes=50), now - timedelta(minutes=15)))

    # Claim for donation #8 (delivered)
    execute_db("""
        INSERT INTO claims (donation_id, ngo_id, volunteer_id, status, requested_at, accepted_at, picked_up_at, delivered_at, delivery_notes, beneficiaries_served)
        VALUES (%s, %s, %s, 'completed', %s, %s, %s, %s, 'Delivered fresh and hot. Distributed to children and residential staff.', 80)
    """, (donation_ids[7], user_ids['sunshine@ngo.org'], user_ids['priya@volunteer.org'],
          now - timedelta(days=1, hours=3), now - timedelta(days=1, hours=2, minutes=30),
          now - timedelta(days=1, hours=1, minutes=45), now - timedelta(days=1, hours=1),
          ))

    # Claim for donation #9 (delivered)
    execute_db("""
        INSERT INTO claims (donation_id, ngo_id, volunteer_id, status, requested_at, accepted_at, picked_up_at, delivered_at, delivery_notes, beneficiaries_served)
        VALUES (%s, %s, %s, 'completed', %s, %s, %s, %s, 'Distribution completed at community shelter site A. Zero wastage recorded.', 110)
    """, (donation_ids[8], user_ids['annapurna@ngo.org'], user_ids['amit@volunteer.org'],
          now - timedelta(days=2, hours=4), now - timedelta(days=2, hours=3, minutes=20),
          now - timedelta(days=2, hours=2, minutes=10), now - timedelta(days=2, hours=1, minutes=30),
          ))

    # 5. NOTIFICATIONS
    notifications_data = [
        # Urgency alert for Hope Shelter
        (user_ids['hopeshelter@ngo.org'], '🚨 URGENT: 65 Portions Shahi Biryani Expiring Soon', 'The Grand Palace Hotel posted 65 portions expiring in under 2 hours! 2.1 km away.', 'urgency', '/ngo/dashboard'),
        # Donation claimed alert for Grand Palace
        (user_ids['grandpalace@donor.org'], '📦 Food Claim Accepted', 'Robin Community Kitchen accepted your donation of 45 Packs Pasta.', 'claim_update', '/donor/dashboard'),
        # Volunteer dispatch alert for Rahul
        (user_ids['rahul@volunteer.org'], '🛵 Active Task: Pickup Confirmed', 'You are assigned to collect 45 packs pasta from The Grand Palace Hotel.', 'delivery_status', '/volunteer/dashboard'),
        # Admin pending verification notice
        (user_ids['admin@foodbridge.org'], '🛡️ New NGO Registration Awaiting Verification', 'Elders Care Trust & Shelter submitted credentials for review.', 'system', '/admin/dashboard'),
    ]

    for notif in notifications_data:
        execute_db("""
            INSERT INTO notifications (user_id, title, message, type, link, is_read, created_at)
            VALUES (%s, %s, %s, %s, %s, 0, %s)
        """, (notif[0], notif[1], notif[2], notif[3], notif[4], now - timedelta(minutes=20)))

    # 6. AUDIT LOGS
    execute_db("""
        INSERT INTO audit_logs (user_id, action, details, ip_address)
        VALUES 
        (%s, 'USER_REGISTERED', 'Elders Care Trust registered as NGO entity', '127.0.0.1'),
        (%s, 'DONATION_POSTED', 'The Grand Palace Hotel created donation #1 (65 portions biryani)', '127.0.0.1'),
        (%s, 'CLAIM_ACCEPTED', 'Hope Shelter initiated claim on wedding donation #6', '127.0.0.1'),
        (%s, 'PICKUP_VERIFIED', 'Volunteer Rahul verified OTP at Grand Palace Hotel gate', '127.0.0.1')
    """, (user_ids['elderscare@ngo.org'], user_ids['grandpalace@donor.org'], user_ids['hopeshelter@ngo.org'], user_ids['rahul@volunteer.org']))

    print("[FoodBridge] Hackathon database successfully populated with rich sample data!")

if __name__ == '__main__':
    seed_database()
