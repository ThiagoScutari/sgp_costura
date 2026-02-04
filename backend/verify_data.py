from database import SessionLocal
from models import PSO, Operation, Product
from sqlalchemy import desc

def verify():
    db = SessionLocal()
    output = []
    try:
        # Get the latest PSO
        latest_pso = db.query(PSO).order_by(desc(PSO.id)).first()
        
        if not latest_pso:
            output.append("No PSOs found.")
        else:
            product = db.query(Product).filter(Product.id == latest_pso.product_id).first()
            output.append(f"\n--- Latest Imported PSO ---")
            output.append(f"PSO ID: {latest_pso.id}")
            output.append(f"Product: {product.reference} - {product.description}")
            output.append(f"Version: {latest_pso.version_name}")
            output.append("-" * 100)
            output.append(f"{'Seq':<5} | {'Description':<50} | {'Macro Machine':<15} | {'PDF Time (min)':<10}")
            output.append("-" * 100)

            # Get operations for this PSO
            ops = db.query(Operation).filter(Operation.pso_id == latest_pso.id).order_by(Operation.sequence).all()
            
            for op in ops:
                output.append(f"{op.sequence:<5} | {op.description[:50]:<50} | {op.macro_machine:<15} | {op.time_pdf:<10}")

            output.append("-" * 100)
            output.append(f"Total Operations: {len(ops)}")
            
    except Exception as e:
        output.append(f"Error: {str(e)}")
    finally:
        db.close()
    
    final_output = "\n".join(output)
    print(final_output)
    
    with open("results.txt", "w", encoding="utf-8") as f:
        f.write(final_output)

if __name__ == "__main__":
    verify()
