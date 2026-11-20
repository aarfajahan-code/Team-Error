import sys
import os
from database import init_db
from seed_data import seed_database

def main():
    print("==================================================")
    print("🌱 FoodBridge Database Setup & Seeder")
    print("==================================================")
    
    init_db()
    seed_database()
    
    print("\n✅ Setup complete! You can now start the application with:")
    print("   python app.py")
    print("==================================================")

if __name__ == '__main__':
    main()
