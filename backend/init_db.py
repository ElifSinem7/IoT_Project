"""
Initialize database and add sample devices
Usage: python init_db.py
"""

import sys
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models import Base, Device
from datetime import datetime, timezone


def init_database():
    """Create all tables with latest schema"""
    print("🔧 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")
    print("   - devices")
    print("   - measurements")


def add_sample_devices():
    """Add sample devices to database"""
    db: Session = SessionLocal()
    
    try:
        # Check existing device count
        existing_count = db.query(Device).count()
        
        if existing_count > 0:
            print(f"\n⚠️  Database already contains {existing_count} devices.")
            response = input("Do you want to add more devices? (y/n): ")
            if response.lower() != 'y':
                print("❌ Cancelled.")
                return
        
        sample_devices = [
            Device(
                device_id="node-001",
                name="Kayseri Melikgazi - Ataturk Park",
                lat=38.7312,
                lon=35.4787,
                city="Kayseri",
                district="Melikgazi",
                created_at=datetime.now(timezone.utc)
            ),
            Device(
                device_id="node-002",
                name="Kayseri Kocasinan - Hospital Area",
                lat=38.7205,
                lon=35.4897,
                city="Kayseri",
                district="Kocasinan",
                created_at=datetime.now(timezone.utc)
            ),
            Device(
                device_id="node-003",
                name="Kayseri Talas - City Square",
                lat=38.6842,
                lon=35.5475,
                city="Kayseri",
                district="Talas",
                created_at=datetime.now(timezone.utc)
            ),
            Device(
                device_id="node-004",
                name="Istanbul Kadikoy - Moda Coast",
                lat=40.9875,
                lon=29.0290,
                city="Istanbul",
                district="Kadikoy",
                created_at=datetime.now(timezone.utc)
            ),
            Device(
                device_id="node-005",
                name="Istanbul Besiktas - Barbaros Square",
                lat=41.0429,
                lon=29.0082,
                city="Istanbul",
                district="Besiktas",
                created_at=datetime.now(timezone.utc)
            ),
            Device(
                device_id="node-006",
                name="Ankara Cankaya - Kizilay",
                lat=39.9208,
                lon=32.8541,
                city="Ankara",
                district="Cankaya",
                created_at=datetime.now(timezone.utc)
            ),
            Device(
                device_id="node-007",
                name="Izmir Karsiyaka - Coast",
                lat=38.4602,
                lon=27.1018,
                city="Izmir",
                district="Karsiyaka",
                created_at=datetime.now(timezone.utc)
            ),
        ]
        
        print(f"\n📝 Adding {len(sample_devices)} sample devices...")
        
        added_count = 0
        for device in sample_devices:
            # Check if device already exists
            existing = db.query(Device).filter(Device.device_id == device.device_id).first()
            
            if existing:
                print(f"⚠️  {device.device_id} already exists, skipping...")
                continue
            
            db.add(device)
            print(f"✅ {device.device_id}: {device.name} ({device.city}/{device.district})")
            added_count += 1
        
        db.commit()
        print(f"\n✅ Successfully added {added_count} new devices!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def show_devices():
    """Display all registered devices"""
    db: Session = SessionLocal()
    
    try:
        devices = db.query(Device).order_by(Device.city, Device.district).all()
        
        if not devices:
            print("\n❌ No devices found in database!")
            return
        
        print(f"\n📋 Registered Devices ({len(devices)} total):")
        print("=" * 90)
        
        current_city = None
        for device in devices:
            # Print city header if changed
            if device.city != current_city:
                if current_city is not None:
                    print("-" * 90)
                print(f"\n🏙️  {device.city.upper()}")
                print("-" * 90)
                current_city = device.city
            
            print(f"ID: {device.device_id:15} | {device.name}")
            print(f"{'':15}   Location: {device.district}")
            print(f"{'':15}   GPS: {device.lat:.4f}, {device.lon:.4f}")
            print(f"{'':15}   Created: {device.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        print("=" * 90)
        
    finally:
        db.close()


def delete_all_devices():
    """Delete all devices (use with caution!)"""
    db: Session = SessionLocal()
    
    try:
        count = db.query(Device).count()
        
        if count == 0:
            print("\n❌ No devices to delete!")
            return
        
        print(f"\n⚠️  WARNING: This will delete all {count} devices!")
        response = input("Are you sure? (yes/no): ")
        
        if response.lower() != 'yes':
            print("❌ Cancelled.")
            return
        
        db.query(Device).delete()
        db.commit()
        print(f"✅ Successfully deleted {count} devices!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    print("\n" + "=" * 90)
    print("Know The Air You Breeze In - Database Initialization")
    print("=" * 90 + "\n")
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "show":
            show_devices()
        elif command == "add":
            add_sample_devices()
        elif command == "delete":
            delete_all_devices()
        elif command == "reset":
            delete_all_devices()
            init_database()
            add_sample_devices()
            show_devices()
        else:
            print(f"❌ Unknown command: {command}")
            print("\nAvailable commands:")
            print("  python init_db.py          - Full initialization")
            print("  python init_db.py show     - Show all devices")
            print("  python init_db.py add      - Add sample devices")
            print("  python init_db.py delete   - Delete all devices")
            print("  python init_db.py reset    - Reset and reinitialize")
    else:
        # Default: Full initialization
        init_database()
        add_sample_devices()
        show_devices()
    
    print("\n✅ Operation completed!")
    print("\n📌 Next Steps:")
    print("   1. Start backend: uvicorn app.main:app --reload")
    print("   2. Test API: http://localhost:8000/docs")
    print("   3. Check devices: http://localhost:8000/api/devices")
    print("   4. Check map: http://localhost:8000/api/map/points")
    print("   5. Connect ESP32 and start sending data\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)