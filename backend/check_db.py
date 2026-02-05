from sqlalchemy import create_engine, text
from database import DATABASE_URL

def check_schema():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='pso' AND column_name='is_archived'"
        ))
        row = result.fetchone()
        if row:
            print("✅ Column 'is_archived' FOUND.")
        else:
            print("❌ Column 'is_archived' MISSING.")

if __name__ == "__main__":
    check_schema()
