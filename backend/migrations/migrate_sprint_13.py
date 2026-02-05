from database import engine
from sqlalchemy import text

def run_migration():
    with engine.connect() as conn:
        print("Running Sprint 13 Migrations...")
        
        # 1. Add is_active to seamstresses if not exists
        try:
            conn.execute(text("ALTER TABLE seamstresses ADD COLUMN is_active BOOLEAN DEFAULT TRUE;"))
            print("✅ Added is_active to seamstresses")
        except Exception as e:
            print(f"ℹ️  Column 'is_active' likely exists on 'seamstresses': {e}")
            
        # 2. Add role to users if not exists (User model already has it, but good to ensure DB has it)
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'operator';"))
            print("✅ Added role to users")
        except Exception as e:
            print(f"ℹ️  Column 'role' likely exists on 'users': {e}")

        # 3. Add is_active to users if not exists
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;"))
            print("✅ Added is_active to users")
        except Exception as e:
            print(f"ℹ️  Column 'is_active' likely exists on 'users': {e}")
            
        conn.commit()
        print("Migration complete!")

if __name__ == "__main__":
    run_migration()
