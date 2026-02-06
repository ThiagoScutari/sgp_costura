import json
from datetime import datetime

from database import SessionLocal
import models


def create_planning_with_batches(session, pso_id, version_name="DEBUG_PLAN", total_quantity=200, batch_size=40):
    pso = session.query(models.PSO).filter(models.PSO.id == pso_id).first()
    if not pso:
        raise ValueError(f"PSO {pso} not found")
    po = session.query(models.ProductionOrder).filter(models.ProductionOrder.product_reference == pso.product.reference).order_by(models.ProductionOrder.id.desc()).first()
    if not po:
        po = models.ProductionOrder(product_reference=pso.product.reference, quantity=total_quantity, status="Ativa", pulse_duration=60)
        session.add(po)
        session.flush()
    session.query(models.ProductionPlanning).filter(models.ProductionPlanning.production_order_id == po.id).update({"is_active": False})
    planning = models.ProductionPlanning(
        production_order_id=po.id,
        pso_id=pso_id,
        version_name=version_name,
        pulse_duration=60,
        batch_size=batch_size,
        total_quantity=total_quantity,
        notes="debug",
        total_operators=0,
        is_active=False,
    )
    session.add(planning)
    session.flush()

    po.quantity = total_quantity
    po.pulse_duration = planning.pulse_duration
    session.add(po)
    session.flush()

    session.query(models.CartLote).filter(models.CartLote.planning_id == planning.id).delete()
    session.flush()

    print(f"[DEBUG] planning_id={planning.id} total_quantity={total_quantity} batch_size={batch_size}")
    num_lotes = -(-total_quantity // batch_size)
    for i in range(num_lotes):
        current_qty = batch_size
        if (i + 1) * batch_size > total_quantity:
            current_qty = total_quantity % batch_size
            if current_qty == 0:
                current_qty = batch_size
        cart = models.CartLote(
            production_order_id=po.id,
            planning_id=planning.id,
            sequence_number=i + 1,
            quantity_pieces=current_qty,
            status="Aguardando",
        )
        session.add(cart)
        print(f"  cart#{i+1} qty={current_qty}")
    session.commit()
    return planning.id


def main():
    session = SessionLocal()
    try:
        planning_id = create_planning_with_batches(session, pso_id=13)
        carts = session.query(models.CartLote).filter(models.CartLote.planning_id == planning_id).count()
        print(f"[DEBUG] planning {planning_id} has {carts} carts")
    finally:
        session.close()


if __name__ == "__main__":
    main()
