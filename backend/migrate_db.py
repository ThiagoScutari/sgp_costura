from database import engine
from sqlalchemy import text

def run_migrations():
    with engine.connect() as conn:
        print("Checking migrations...")
        try:
            # 1. Add is_fractioned to operation_allocations
            conn.execute(text("ALTER TABLE operation_allocations ADD COLUMN IF NOT EXISTS is_fractioned BOOLEAN DEFAULT FALSE"))
            print("Verified/Added is_fractioned to operation_allocations")
        except Exception as e:
            # Postgres throws error if column exists and we rely on IF NOT EXISTS? No, IF NOT EXISTS is safe.
            # But just in case
            print(f"Note on is_fractioned: {e}")

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

        # --- SPRINT 13 MIGRATIONS ---
        try:
            conn.execute(text("ALTER TABLE seamstresses ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
            print("Verified/Added is_active to seamstresses")
        except Exception as e:
            print(f"Error checking seamstresses columns: {e}")

        try:
            conn.execute(text("CREATE TABLE IF NOT EXISTS system_config (key VARCHAR PRIMARY KEY, value VARCHAR)"))
            print("Verified/Created system_config table")
        except Exception as e:
            print(f"Error checking system_config: {e}")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'operator'"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
            print("Verified/Added role/is_active to users")
        except Exception as e:
            print(f"Error checking users columns: {e}")
        # ---------------------------

        conn.commit()
        print("Migration check complete.")

if __name__ == "__main__":
    run_migrations()
