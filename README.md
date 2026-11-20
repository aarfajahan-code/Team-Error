# 🌱 FoodBridge – Smart Food Redistribution Platform

> A full-stack, responsive web application connecting restaurants, hotels, banquet organisers, and supermarkets with verified NGOs and volunteer drivers to eliminate food waste and nourish communities in real time.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-green.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-MySQL%20%7C%20SQLite-orange.svg)](https://www.mysql.com/)
[![Maps](https://img.shields.io/badge/Maps-Leaflet%20%2F%20OpenStreetMap-brightgreen.svg)](https://leafletjs.com/)
[![Analytics](https://img.shields.io/badge/Charts-Chart.js-red.svg)](https://www.chartjs.org/)
[![UN SDG](https://img.shields.io/badge/UN%20SDGs-SDG%202%20%26%2012-emerald.svg)](https://sdgs.un.org/)

---

## 🌟 Key Features

### 1. Multi-Role Authentication & Role-Based Access Control (RBAC)
- Dedicated registration and login workflows for:
  - **Donors**: Hotels, restaurants, wedding halls, caterers, supermarkets.
  - **NGOs / Shelters**: Food banks, orphanages, community kitchens, elder care shelters.
  - **Volunteers**: Delivery partners with motorbikes, cars, cargo vans, or bicycles.
  - **Administrators**: Verification officers, compliance monitors, and platform supervisors.
- Secure password hashing using PBKDF2/SHA256.
- **⚡ 1-Click Demo Persona Switcher**: Seamlessly switch between Donor, NGO, Volunteer, and Admin profiles directly from the navigation bar for instant hackathon demonstrations!

### 2. Food Donation Module
- Donors can post surplus food listings with:
  - Title, category (Cooked Meal, Bakery & Dairy, Fruits & Vegetables, Packaged Food).
  - Dietary restrictions (Vegetarian, Non-Vegetarian, Vegan, Jain).
  - Numerical quantity, units, and estimated people fed (servings).
  - Cooking timestamp and automated shelf-life countdown.
  - Storage conditions: Hot/Warm (>60°C), Refrigerated (0-4°C), Frozen (<-18°C), or Room Temperature.
  - Pickup address, contact details, special handling instructions, and photos.

### 3. Smart NGO Matching Algorithm
- **Scientific, multi-factor scoring (0–100%)**:
  1. **Haversine Distance (40%)**: Great-circle distance calculation prioritizing ultra-local NGOs.
  2. **Capacity Fit (25%)**: Compares donation servings with NGO's daily feeding capacity.
  3. **Dietary & Category Compatibility (20%)**: Ensures strictly vegetarian shelters only receive compatible foods.
  4. **Perishability & Cold Storage (15%)**: Perishable/refrigerated meals match with NGOs verified to have cold storage.
- Immediate recommendation modal showing ranked NGOs with distance, travel time, and match rationale.

### 4. Interactive Location-Based Map
- Powered by Leaflet.js and OpenStreetMap (100% free open tiles, no paid API keys required).
- Custom map pins:
  - 🟢 **Food Donors**: Pulsing red badges for critical urgency donations (<2 hours remaining).
  - 🔵 **Verified NGOs**: Displays daily capacity and cold storage facilities.
  - 🟠 **Active Volunteers**: Displays vehicle type and real-time availability.
- Dynamic filtering by food category, urgency, and layer toggles with interactive popup action buttons.

### 5. Food Safety Management
- FSSAI / WHO aligned redistribution safety checklists for donors and receiving shelters.
- Dynamic shelf-life progress bars and urgency warning banners:
  - ⚡ **Critical (<2 hrs)**: Triggers high-priority alerts to all nearby NGOs.
  - ⏳ **Moderate (2–4 hrs)**: Standard notification dispatch.
  - 🥗 **Extended (>4 hrs)**: Scheduled routine logistics.

### 6. Dual-Sided OTP Pickup & Delivery Verification
- **Pickup Verification Code**: Donor generates a 4-digit OTP. The volunteer/NGO enters this OTP to take custody and transition status to `in_transit`.
- **Delivery Verification Code**: Receiving NGO generates a 4-digit OTP. The driver enters this OTP upon arrival to verify delivery and log meals served.
- Prevents food diversion, ensures zero food waste, and creates an immutable chain of custody.

### 7. Volunteer Logistics Fleet Management
- Volunteers view live delivery missions in their vicinity with pickup/drop-off distances.
- Accept tasks, access route addresses and donor/shelter contact phone numbers.
- Track completed deliveries, total meals transported, and driver ratings.

### 8. Admin Compliance & Governance Console
- **NGO Verification Queue**: Review charity registration numbers and approve or reject applications.
- **User Management**: Search, filter by role, and toggle active/suspended account status.
- **Donation Surveillance**: Real-time platform-wide monitor of all donations and redistribution stages.
- **System Audit Trail**: Complete log of signups, claims, OTP handovers, and IP addresses.

### 9. Impact Dashboard & Analytics
- Live KPI Counters: Total food saved (kg), meals served, landfill CO2e emissions avoided, and completed deliveries.
- Visualizations powered by **Chart.js**:
  - Doughnut Chart: Surplus food category distribution.
  - Line Chart: Weekly food rescue trend (kg/day).
  - Bar Chart: Registered network stakeholder breakdown.
  - Alignment with UN SDGs 2 (Zero Hunger), 12 (Responsible Consumption), and 13 (Climate Action).

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3 (Custom Responsive Forest Green & Orange Palette), JavaScript (ES6+ Vanilla, No heavy frameworks) |
| **Backend** | Python Flask, Werkzeug Security, Flask-CORS |
| **Database** | MySQL 8.0 (Native PyMySQL engine) + Seamless automatic fallback to SQLite (`foodbridge.db`) |
| **Mapping** | Leaflet.js, OpenStreetMap tiles |
| **Charts** | Chart.js 4.4 |

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ installed
- (Optional) MySQL Server 8.0 running locally

### 2. Clone / Open Directory
```bash
cd FoodBridge
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup & Seeding
Run the automated initialization script:
```bash
python init_db.py
```
*Note: The platform is built with a dual-engine adapter. If MySQL credentials in `.env` are active, it connects to MySQL and creates `foodbridge`. Otherwise, it automatically and seamlessly operates on SQLite with zero configuration required!*

### 5. Launch Application
```bash
python app.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🗄️ MySQL Database Setup (Optional Native Mode)

If you prefer to run against your local MySQL server:

1. Open your MySQL client (MySQL CLI or MySQL Workbench) and run `schema.sql`:
   ```bash
   mysql -u root -p < schema.sql
   ```
2. Update your `.env` file:
   ```ini
   DB_TYPE=mysql
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DB=foodbridge
   ```
3. Run the seeder to populate sample data:
   ```bash
   python seed_data.py
   ```

---

## 👥 Hackathon Pre-Seeded Demo Accounts

You can test every role using the credentials below, or simply click the **"⚡ Demo Personas"** button in the navigation bar:

| Role | Persona / Organization | Email | Password | Key Demo Features |
|---|---|---|---|---|
| **Donor** | The Grand Palace Hotel (5-Star Luxury) | `grandpalace@donor.org` | `password123` | Post surplus buffet meals, view smart NGO matches, view pickup OTP |
| **NGO** | Hope Shelter & Food Bank (350 meals cap) | `hopeshelter@ngo.org` | `password123` | Urgent alerts, claim surplus food, view delivery OTP, verify food intake |
| **Volunteer** | Rahul Sharma (Motorbike Driver) | `rahul@volunteer.org` | `password123` | Browse nearby missions, accept task, enter pickup & delivery OTPs |
| **Admin** | Platform Administrator | `admin@foodbridge.org` | `admin123` | Approve pending NGOs (Elders Care), suspend users, view audit logs |

---

## 📡 Core API Reference

| Endpoint | Method | Role | Description |
|---|---|---|---|
| `/api/auth/register` | `POST` | Public | Multi-role user & organization registration |
| `/api/auth/login` | `POST` | Public | Secure email/password login |
| `/api/auth/logout` | `POST` | Authenticated | Clears user session |
| `/api/auth/switch-demo/<role>` | `GET/POST` | Public | 1-click persona switcher for evaluators |
| `/api/donations` | `GET` | Public | List food donations with category/urgency filters |
| `/api/donations` | `POST` | Donor | Create surplus food donation and notify nearby NGOs |
| `/api/donations/<id>/match-ngos` | `GET` | Authenticated | Runs Haversine distance & capacity matching algorithm |
| `/api/donations/<id>/claim` | `POST` | NGO | Claim food donation for community distribution |
| `/api/volunteer/tasks` | `GET` | Volunteer | Retrieve available delivery missions near driver |
| `/api/volunteer/accept-task/<id>` | `POST` | Volunteer | Accept delivery mission |
| `/api/donations/<id>/verify-pickup`| `POST` | Driver/Donor | Verify 4-digit pickup OTP to start transit |
| `/api/donations/<id>/verify-delivery`| `POST`| Driver/NGO | Verify 4-digit delivery OTP and record impact |
| `/api/map/data` | `GET` | Public | Real-time coordinates of donations, NGOs, and volunteers |
| `/api/impact/stats` | `GET` | Public | Aggregate food kg saved, meals served, CO2e prevented |
| `/api/admin/ngos/verify/<id>` | `POST` | Admin | Approve or reject NGO charity accreditation |
| `/api/admin/users/<id>/status` | `POST` | Admin | Activate or suspend user accounts |

---

## 🎨 Design System

- **Primary Forest Green**: `#155e39` (Represents freshness, sustainability, and trust)
- **Accent Warm Orange**: `#ea580c` (Represents warm food, urgency, and alert notifications)
- **Clean Surfaces**: `#ffffff` and `#f8fafc`
- **Typography**: Inter (Modern, readable, mobile-friendly)

---

## 📄 License
MIT License. Built for hackathons, community food rescues, and zero-waste initiatives. Dedicated to UN Sustainable Development Goals 2 and 12.
