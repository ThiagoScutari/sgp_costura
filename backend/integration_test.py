import requests
from sqlalchemy import func
from database import SessionLocal
from models import PSO, Operation, Product, ProductionOrder, CartLote
from engine import calculate_tl
import sys

def run_integration_test():
    db = SessionLocal()
    try:
        print("--- 1. Validation of Extracted Data (PSO ID 2) ---")
        
        # 1. Total Time (TP)
        tp = db.query(func.sum(Operation.final_time)).filter(Operation.pso_id == 2).scalar()
        print(f"Total Peça (TP): {tp:.4f} minutes")
        
        if not tp:
            print("Error: TP is null or zero. Cannot proceed.")
            return

        # 2. Macro Machine Validation
        null_macros = db.query(Operation).filter(Operation.pso_id == 2, Operation.macro_machine == None).all()
        if null_macros:
            print(f"WARNING: Found {len(null_macros)} operations with NULL macro_machine!")
            for op in null_macros:
                print(f" - Seq {op.sequence}: {op.description}")
        else:
            print("Macro Machine Mapping: OK (No NULLs)")

        # 3. Load Distribution
        print("\n--- Load Distribution by Machine ---")
        dist = db.query(
            Operation.macro_machine, 
            func.sum(Operation.final_time)
        ).filter(
            Operation.pso_id == 2
        ).group_by(
            Operation.macro_machine
        ).order_by(
            func.sum(Operation.final_time).desc()
        ).all()
        
        for machine, load in dist:
            print(f"{machine:<15}: {load:.4f} min")

        print("\n--- 2. Production Simulation ---")
        
        # 4. Create Production Order
        # Ensure Product Exists
        product = db.query(Product).filter(Product.reference == 'J6686').first()
        if not product:
            print("Product J6686 not found!")
            return

        op = ProductionOrder(
            product_reference=product.reference,
            quantity=1000,
            pulse_duration=60,
            status="Ativa"
        )
        db.add(op)
        db.flush() # flush to get ID
        print(f"Created Production Order ID: {op.id} for {product.reference}")

        # 5. Calculate TL
        operators = 4
        pulse = 60
        tl = calculate_tl(operators, pulse, float(tp))
        print(f"Calculated TL (Operators={operators}, Pulse={pulse}, TP={tp:.4f}): {tl} pieces/cart")

        # 6. Create First Cart
        cart = CartLote(
            production_order_id=op.id,
            sequence_number=1,
            quantity_pieces=tl,
            status="Aguardando"
        )
        db.add(cart)
        db.commit()
        db.refresh(cart)
        print(f"Created CartLote ID: {cart.id} (Seq: {cart.sequence_number})")

        # 7. Execute Checkout
        print("\n--- 3. API Checkout Test ---")
        url = "http://localhost:8000/api/batches/checkout"
        payload = {"batch_id": cart.id}
        
        try:
            response = requests.post(url, json=payload)
            print(f"Status Code: {response.status_code}")
            print("Response JSON:")
            print(response.json())
        except Exception as req_e:
            print(f"API Request Failed: {req_e}")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_integration_test()
