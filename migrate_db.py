from backend.database import engine
from sqlalchemy import text

def run_migrations():
    with engine.connect() as conn:
        print("Checking migrations...")
        try:
            # 1. Add is_fractioned to operation_allocations
            conn.execute(text("ALTER TABLE operation_allocations ADD COLUMN IF NOT EXISTS is_fractioned BOOLEAN DEFAULT FALSE"))
            print("Verified/Added is_fractioned to operation_allocations")
        except Exception as e:
            print(f"Error checking is_fractioned: {e}")

        try:
            # 2. Add columns to production_planning if missing
            conn.execute(text("ALTER TABLE production_planning ADD COLUMN IF NOT EXISTS batch_size INTEGER DEFAULT 0"))
            conn.execute(text("ALTER TABLE production_planning ADD COLUMN IF NOT EXISTS pulse_duration INTEGER DEFAULT 60"))
            conn.execute(text("ALTER TABLE production_planning ADD COLUMN IF NOT EXISTS total_operators INTEGER DEFAULT 0"))
            conn.execute(text("ALTER TABLE production_planning ADD COLUMN IF NOT EXISTS notes TEXT"))
            conn.execute(text("ALTER TABLE production_planning ADD COLUMN IF NOT EXISTS version_name VARCHAR"))
            print("Verified/Added columns to production_planning")
        except Exception as e:
            print(f"Error checking production_planning columns: {e}")

        conn.commit()
        print("Migration check complete.")

if __name__ == "__main__":
    run_migrations()
