import unittest
from app import app
from database import query_db

class FoodBridgeIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_public_views(self):
        endpoints = [
            ('/', 200),
            ('/login', 200),
            ('/register', 200),
            ('/map', 200),
            ('/impact', 200),
        ]
        for route, expected in endpoints:
            with self.subTest(route=route):
                res = self.client.get(route)
                self.assertEqual(res.status_code, expected)

    def test_api_endpoints(self):
        # 1. Donations
        res = self.client.get('/api/donations')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(len(data['donations']), 0)

        # 2. Map data
        res = self.client.get('/api/map/data')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('donations', data)
        self.assertIn('ngos', data)
        self.assertIn('volunteers', data)

        # 3. Impact stats
        res = self.client.get('/api/impact/stats')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('total_food_saved_kg', data['impact'])

        # 4. Smart matching algorithm
        res = self.client.get('/api/donations/1/match-ngos')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIsInstance(data['matches'], list)
        if len(data['matches']) > 0:
            top_match = data['matches'][0]
            self.assertIn('match_score', top_match)
            self.assertIn('distance_km', top_match)
            self.assertIn('match_reasons', top_match)

    def test_role_dashboards_with_demo_auth(self):
        roles = ['donor', 'ngo', 'volunteer', 'admin']
        for r in roles:
            with self.subTest(role=r):
                switch_res = self.client.get(f'/api/auth/switch-demo/{r}')
                self.assertIn(switch_res.status_code, [200, 302])
                
                dash_res = self.client.get(f'/{r}/dashboard')
                self.assertEqual(dash_res.status_code, 200)

    def test_full_redistribution_lifecycle(self):
        # 1. Donor posts food
        self.client.get('/api/auth/switch-demo/donor')
        post_res = self.client.post('/api/donations', data={
            'title': 'Test Wedding Banquet Surplus',
            'category': 'Cooked Meal',
            'food_type': 'Vegetarian',
            'quantity_value': '30.0',
            'quantity_unit': 'kg',
            'servings': '60',
            'storage_condition': 'Hot/Warm (>60°C)',
            'hours_valid': '2.0',
            'pickup_address': 'Grand Ballroom Gate 2, New Delhi'
        })
        self.assertEqual(post_res.status_code, 200)
        post_data = post_res.get_json()
        self.assertTrue(post_data['success'])
        donation_id = post_data['donation_id']

        # Verify donation created in database
        donation = query_db("SELECT * FROM donations WHERE id = %s", (donation_id,), one=True)
        self.assertIsNotNone(donation)
        self.assertEqual(donation['status'], 'available')
        pickup_otp = donation['pickup_otp']
        delivery_otp = donation['delivery_otp']

        # 2. NGO claims food
        self.client.get('/api/auth/switch-demo/ngo')
        claim_res = self.client.post(f'/api/donations/{donation_id}/claim')
        self.assertEqual(claim_res.status_code, 200)

        donation = query_db("SELECT * FROM donations WHERE id = %s", (donation_id,), one=True)
        self.assertEqual(donation['status'], 'requested')

        # 3. Volunteer accepts task
        self.client.get('/api/auth/switch-demo/volunteer')
        accept_res = self.client.post(f'/api/volunteer/accept-task/{donation_id}')
        self.assertEqual(accept_res.status_code, 200)

        # 4. Volunteer verifies pickup with OTP
        pickup_res = self.client.post(f'/api/donations/{donation_id}/verify-pickup', json={'otp': pickup_otp})
        self.assertEqual(pickup_res.status_code, 200)
        donation = query_db("SELECT * FROM donations WHERE id = %s", (donation_id,), one=True)
        self.assertEqual(donation['status'], 'in_transit')

        # 5. Volunteer/NGO verifies delivery with OTP
        delivery_res = self.client.post(f'/api/donations/{donation_id}/verify-delivery', json={
            'otp': delivery_otp,
            'beneficiaries_served': 60,
            'delivery_notes': 'Verified test handover complete'
        })
        self.assertEqual(delivery_res.status_code, 200)
        donation = query_db("SELECT * FROM donations WHERE id = %s", (donation_id,), one=True)
        self.assertEqual(donation['status'], 'delivered')

if __name__ == '__main__':
    unittest.main()
