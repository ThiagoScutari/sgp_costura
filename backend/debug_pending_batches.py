from sqlalchemy.orm import Session
from database import SessionLocal
import models
from sqlalchemy import desc

def debug_state():
    db = SessionLocal()
    try:
        # 1. Find Active Planning
        planning = db.query(models.ProductionPlanning).filter(
            models.ProductionPlanning.is_active == True
        ).order_by(desc(models.ProductionPlanning.id)).first()

        if not planning:
            print("❌ No active planning found")
            return

        print(f"✅ Active Planning ID: {planning.id}")
        print(f"   PO ID: {planning.production_order_id}")
        print(f"   Batch Size: {planning.batch_size}")
        
        po = db.query(models.ProductionOrder).filter(models.ProductionOrder.id == planning.production_order_id).first()
        if not po:
            print(f"❌ Production Order {planning.production_order_id} not found")
            return
            
        print(f"✅ Production Order ID: {po.id}")
        print(f"   Reference: {po.product_reference}")
        print(f"   Quantity: {po.quantity}")

        # 2. Get Carts
        carts = db.query(models.CartLote).filter(
            models.CartLote.production_order_id == po.id
        ).order_by(models.CartLote.sequence_number).all()

        print(f"✅ Found {len(carts)} carts for this PO:")
        for c in carts:
            print(f"   - ID: {c.id}, Seq: {c.sequence_number}, Status: {c.status}, Qty: {c.quantity_pieces}")

        # 3. Get Tracking
        trackings = db.query(models.BatchTracking).filter(
            models.BatchTracking.planning_id == planning.id
        ).all()
        print(f"✅ Found {len(trackings)} tracking records for this planning session")

    finally:
        db.close()

if __name__ == "__main__":
    debug_state()
