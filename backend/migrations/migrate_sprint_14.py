from sqlalchemy import create_engine, text
from database import DATABASE_URL

def run_migrations():
    print("🔄 Running Sprint 14 Migrations (PSO Soft Delete)...")
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='pso' AND column_name='is_archived'"
            ))
            if result.fetchone():
                print("✅ Column 'is_archived' already exists in 'pso'. Skipping.")
            else:
                print("➕ Adding 'is_archived' column to 'pso' table...")
                conn.execute(text("ALTER TABLE pso ADD COLUMN is_archived BOOLEAN DEFAULT FALSE"))
                conn.commit()
                print("✅ Migration Applied Successfully.")
        except Exception as e:
            print(f"❌ Migration Failed: {e}")

if __name__ == "__main__":
    run_migrations()
