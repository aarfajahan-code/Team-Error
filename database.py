import os
import sqlite3
import pymysql
import pymysql.cursors
from datetime import datetime
from config import Config

# Global database connection indicator
ACTIVE_DB_ENGINE = None

def get_connection():
    """
    Connect to MySQL if DB_TYPE is mysql or auto (and MySQL succeeds),
    otherwise fallback cleanly to SQLite.
    """
    global ACTIVE_DB_ENGINE
    
    # 1. If explicit SQLite requested
    if Config.DB_TYPE == 'sqlite':
        ACTIVE_DB_ENGINE = 'sqlite'
        conn = sqlite3.connect(Config.SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn, 'sqlite'
        
    # 2. Try MySQL if configured
    if Config.DB_TYPE in ['mysql', 'auto']:
        try:
            # First try connecting to server to ensure database exists
            server_conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=3
            )
            with server_conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            server_conn.close()

            # Now connect to the database
            conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            ACTIVE_DB_ENGINE = 'mysql'
            return conn, 'mysql'
        except Exception as e:
            if Config.DB_TYPE == 'mysql':
                print(f"[FoodBridge DB] MySQL connection error ({e}). Falling back to SQLite for seamless operation.")
            ACTIVE_DB_ENGINE = 'sqlite'
            conn = sqlite3.connect(Config.SQLITE_PATH)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn, 'sqlite'

    ACTIVE_DB_ENGINE = 'sqlite'
    conn = sqlite3.connect(Config.SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn, 'sqlite'

def adapt_sql_for_engine(sql, engine):
    """
    Normalizes query for MySQL vs SQLite:
    - Replaces %s with ? if SQLite
    - Replaces AUTO_INCREMENT with AUTOINCREMENT if SQLite
    - Replaces NOW() with datetime('now', 'localtime') if SQLite
    """
    if engine == 'sqlite':
        # Replace %s placeholders with ?
        # Be careful not to replace % inside string formats if any
        sql = sql.replace('%s', '?')
        sql = sql.replace('NOW()', "datetime('now', 'localtime')")
    return sql

def query_db(query, args=(), one=False):
    """Executes a SELECT query and returns list of dictionaries or single dictionary."""
    conn, engine = get_connection()
    adapted_query = adapt_sql_for_engine(query, engine)
    try:
        if engine == 'sqlite':
            cur = conn.cursor()
            cur.execute(adapted_query, args)
            rows = cur.fetchall()
            cur.close()
            conn.close()
            if not rows:
                return None if one else []
            res = [dict(row) for row in rows]
            return res[0] if one else res
        else:
            with conn.cursor() as cur:
                cur.execute(query, args)
                rows = cur.fetchall()
            conn.close()
            if not rows:
                return None if one else []
            return rows[0] if one else rows
    except Exception as e:
        try:
            conn.close()
        except:
            pass
        raise e

def execute_db(query, args=(), commit=True):
    """Executes an INSERT, UPDATE, DELETE query. Returns lastrowid or affected rows."""
    conn, engine = get_connection()
    adapted_query = adapt_sql_for_engine(query, engine)
    last_id = None
    rowcount = 0
    try:
        if engine == 'sqlite':
            cur = conn.cursor()
            cur.execute(adapted_query, args)
            if commit:
                conn.commit()
            last_id = cur.lastrowid
            rowcount = cur.rowcount
            cur.close()
        else:
            with conn.cursor() as cur:
                cur.execute(query, args)
                last_id = cur.lastrowid
                rowcount = cur.rowcount
            if commit:
                conn.commit()
        conn.close()
        return last_id if last_id else rowcount
    except Exception as e:
        try:
            if commit:
                conn.rollback()
            conn.close()
        except:
            pass
        raise e

def init_db(force_reinit=False):
    """Initializes tables in database."""
    conn, engine = get_connection()
    print(f"[FoodBridge DB] Initializing tables on engine: {engine.upper()}")
    
    if engine == 'mysql':
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                statements = f.read().split(';')
                with conn.cursor() as cur:
                    for stmt in statements:
                        stmt = stmt.strip()
                        if stmt:
                            try:
                                cur.execute(stmt)
                            except Exception as ex:
                                print(f"Notice executing SQL stmt: {ex}")
            conn.commit()
    else:
        # SQLite schema initialization
        cur = conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(150) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL CHECK(role IN ('donor', 'ngo', 'volunteer', 'admin')),
            phone VARCHAR(30),
            address TEXT,
            latitude REAL,
            longitude REAL,
            status VARCHAR(20) DEFAULT 'active',
            avatar_url VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS donor_profiles (
            user_id INTEGER PRIMARY KEY,
            organization_name VARCHAR(150),
            donor_type VARCHAR(50) DEFAULT 'Restaurant',
            contact_person VARCHAR(100),
            fssai_license VARCHAR(50),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ngo_profiles (
            user_id INTEGER PRIMARY KEY,
            organization_name VARCHAR(150),
            registration_no VARCHAR(100),
            contact_person VARCHAR(100),
            daily_capacity INTEGER DEFAULT 100,
            preferred_food_types VARCHAR(200) DEFAULT 'Vegetarian,Cooked Meal,Raw Groceries',
            has_cold_storage INTEGER DEFAULT 0,
            operating_hours VARCHAR(100) DEFAULT '08:00 AM - 10:00 PM',
            verification_status VARCHAR(20) DEFAULT 'pending',
            verified_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS volunteer_profiles (
            user_id INTEGER PRIMARY KEY,
            vehicle_type VARCHAR(50) DEFAULT 'Motorbike',
            max_weight_kg REAL DEFAULT 25.0,
            is_available INTEGER DEFAULT 1,
            total_deliveries INTEGER DEFAULT 0,
            rating REAL DEFAULT 5.0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_id INTEGER NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL,
            food_type VARCHAR(50) NOT NULL,
            quantity_value REAL NOT NULL,
            quantity_unit VARCHAR(20) NOT NULL,
            servings INTEGER NOT NULL,
            cooked_at TIMESTAMP,
            expiry_time TIMESTAMP NOT NULL,
            storage_condition VARCHAR(100) NOT NULL,
            pickup_address TEXT NOT NULL,
            pickup_lat REAL NOT NULL,
            pickup_lng REAL NOT NULL,
            special_instructions TEXT,
            image_url TEXT,
            status VARCHAR(30) DEFAULT 'available',
            urgency_level VARCHAR(20) DEFAULT 'medium',
            claimed_by_ngo_id INTEGER,
            assigned_volunteer_id INTEGER,
            pickup_otp VARCHAR(10),
            delivery_otp VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (donor_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (claimed_by_ngo_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (assigned_volunteer_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donation_id INTEGER NOT NULL,
            ngo_id INTEGER NOT NULL,
            volunteer_id INTEGER,
            status VARCHAR(30) DEFAULT 'accepted',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accepted_at TIMESTAMP,
            picked_up_at TIMESTAMP,
            delivered_at TIMESTAMP,
            delivery_notes TEXT,
            beneficiaries_served INTEGER DEFAULT 0,
            FOREIGN KEY (donation_id) REFERENCES donations(id) ON DELETE CASCADE,
            FOREIGN KEY (ngo_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (volunteer_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title VARCHAR(150) NOT NULL,
            message TEXT NOT NULL,
            type VARCHAR(30) DEFAULT 'info',
            link VARCHAR(255),
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action VARCHAR(100) NOT NULL,
            details TEXT,
            ip_address VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
    conn.close()
    print("[FoodBridge DB] Database schema successfully verified.")
