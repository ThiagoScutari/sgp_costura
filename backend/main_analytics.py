from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

# Import local modules
from database import engine, get_db, Base
import models
import extractor

# Re-create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SGP Costura Analytics API - v1.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seed Seamstresses
def seed_seamstresses(db: Session):
    if db.query(models.Seamstress).count() == 0:
        names = ["Maria Silva", "Joana Santos", "Elizandra", "Débora", "Lúcia", "Fernanda"]
        for name in names:
            db.add(models.Seamstress(name=name))
        db.commit()

@app.on_event("startup")
def startup_event():
    db = next(get_db())
    seed_seamstresses(db)

@app.get("/api/analytics/dashboard")
def get_analytics_dashboard(hours: int = 8, db: Session = Depends(get_db)):
    """
    Returns comprehensive performance metrics for BI dashboard.
    """
    current_time = datetime.utcnow()
    start_time = current_time - timedelta(hours=hours)
    
    completed_batches = db.query(models.BatchTracking).filter(
        models.BatchTracking.checkout_time >= start_time
    ).all()
    
    if not completed_batches:
        return {
            "efficiency": {"current": 0, "target": 80.0, "status": "no_data"},
            "delay_rate": {"delayed_count": 0, "total_count": 0, "percentage": 0},
            "production_volume": {"total_pieces": 0, "total_batches": 0, "avg_pieces_per_hour": 0},
            "hourly_breakdown": []
        }
    
    total_batches = len(completed_batches)
    delayed_count = sum(1 for b in completed_batches if b.is_delayed)
    delay_percentage = (delayed_count / total_batches * 100) if total_batches > 0 else 0
    
    total_pieces = 0
    batch_ids = [b.batch_id for b in completed_batches]
    carts = db.query(models.CartLote).filter(models.CartLote.id.in_(batch_ids)).all()
    total_pieces = sum(c.quantity_pieces for c in carts if c.quantity_pieces)
    
    avg_pieces_per_hour = total_pieces / hours if hours > 0 else 0
    
    # Calculate efficiency (Total Standard Time vs Actual Clock Time)
    total_standard_minutes = 0.0
    
    # Pre-cache planning TPs to avoid redundant calculations
    planning_tp_cache = {}
    
    for tracking in completed_batches:
        p_id = tracking.planning_id
        if p_id:
            if p_id not in planning_tp_cache:
                p = db.query(models.ProductionPlanning).filter(models.ProductionPlanning.id == p_id).first()
                if p:
                    tp = sum(oa.operation.final_time for a in p.allocations for oa in a.op_allocations if oa.operation)
                    planning_tp_cache[p_id] = tp
                else:
                    planning_tp_cache[p_id] = 0.0
            total_standard_minutes += planning_tp_cache.get(p_id, 0.0)
        else:
            # Fallback for legacy data/unknown session: use current active planning TP if available
            # Otherwise assume 0 standard minutes
            active_p = db.query(models.ProductionPlanning).filter(models.ProductionPlanning.is_active == True).first()
            if active_p:
                tp = sum(oa.operation.final_time for a in active_p.allocations for oa in a.op_allocations if oa.operation)
                total_standard_minutes += tp
    
    efficiency_current = 0.0
    actual_minutes = hours * 60
    if actual_minutes > 0:
        efficiency_current = (total_standard_minutes / actual_minutes) * 100
    
    efficiency_status = "good" if efficiency_current >= 80 else "warning" if efficiency_current >= 60 else "critical"
    
    hourly_data = {}
    for batch in completed_batches:
        hour_key = batch.checkout_time.strftime("%H:00")
        if hour_key not in hourly_data:
            hourly_data[hour_key] = {"pieces": 0, "batches": 0}
        
        cart = db.query(models.CartLote).filter(models.CartLote.id == batch.batch_id).first()
        if cart:
            hourly_data[hour_key]["pieces"] += cart.quantity_pieces or 0
            hourly_data[hour_key]["batches"] += 1
    
    hourly_breakdown = [
        {"hour": hour, "pieces": data["pieces"], "batches": data["batches"]}
        for hour, data in sorted(hourly_data.items())
    ]
    
    # Get target metrics from the active or latest planning
    target_volume = 0
    target_batches = 0
    active_planning = db.query(models.ProductionPlanning).filter(
        models.ProductionPlanning.is_active == True
    ).order_by(desc(models.ProductionPlanning.id)).first()
    
    if active_planning:
        target_batches = db.query(models.CartLote).filter(
            models.CartLote.planning_id == active_planning.id
        ).count()
        po = db.query(models.ProductionOrder).filter(models.ProductionOrder.id == active_planning.production_order_id).first()
        if po:
            target_volume = po.quantity or 0

    # Calculate detailed delay stats (Early, OnTime, Delayed)
    # For now, let's treat "not delayed" as OnTime for the chart
    early_count = 0 # Future logic: track checkouts < 80% pulse
    on_time_count = total_batches - delayed_count
    
    return {
        "efficiency": {
            "current": round(efficiency_current, 1),
            "target": 80.0,
            "status": efficiency_status
        },
        "delay_rate": {
            "early_count": early_count,
            "on_time_count": on_time_count,
            "delayed_count": delayed_count,
            "total_count": total_batches,
            "percentage": round(delay_percentage, 1)
        },
        "production_volume": {
            "total_pieces": total_pieces,
            "total_batches": total_batches,
            "target_volume": target_volume,
            "target_batches": target_batches,
            "avg_pieces_per_hour": round(avg_pieces_per_hour, 1)
        },
        "hourly_breakdown": hourly_breakdown
    }

@app.get("/api/analytics/pso/{pso_id}")
def get_pso_analytics(pso_id: int, db: Session = Depends(get_db)):
    """
    Returns analytics for a specific PSO (Product Sequence Order).
    Used by Page 07 (BI Dashboard) to show production history and metrics.
    """
    try:
        pso = db.query(models.PSO).filter(models.PSO.id == pso_id).first()
        if not pso:
            raise HTTPException(status_code=404, detail="PSO not found")
        
        plannings = db.query(models.ProductionPlanning).filter(
            models.ProductionPlanning.pso_id == pso_id
        ).all()
        
        if not plannings:
            return {
                "pso_id": pso_id,
                "product_reference": pso.product.reference if pso.product else "N/A",
                "product_description": pso.product.description if pso.product else "N/A",
                "target_volume": 0,
                "target_batches": 0,
                "produced_volume": 0,
                "produced_batches": 0,
                "efficiency": 0.0,
                "hourly_production": []
            }
        
        latest_planning = max(plannings, key=lambda p: p.created_at)
        
        po = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.id == latest_planning.production_order_id
        ).first()
        
        target_volume = po.quantity if po and po.quantity else 0
        target_batches = db.query(models.CartLote).filter(
            models.CartLote.production_order_id == po.id
        ).count() if po else 0
        
        completed_trackings = []
        if po:
            completed_trackings = db.query(models.BatchTracking).filter(
                models.BatchTracking.planning_id == latest_planning.id
            ).order_by(models.BatchTracking.checkout_time).all()
        
        produced_batches = len(completed_trackings)
        
        produced_volume = 0
        if completed_trackings:
            batch_ids = [t.batch_id for t in completed_trackings]
            carts = db.query(models.CartLote).filter(
                models.CartLote.id.in_(batch_ids)
            ).all()
            produced_volume = sum(c.quantity_pieces or 0 for c in carts)
        
        efficiency = 0.0
        if produced_batches > 0 and latest_planning:
            total_tp_per_batch = 0.0
            for alloc in latest_planning.allocations:
                for op_alloc in alloc.op_allocations:
                    operation = db.query(models.Operation).filter(
                        models.Operation.id == op_alloc.operation_id
                    ).first()
                    if operation:
                        total_tp_per_batch += operation.final_time
            
            standard_minutes = total_tp_per_batch * produced_batches
            
            if completed_trackings:
                start_event = db.query(models.ProductionEvent).filter(
                    models.ProductionEvent.planning_id == latest_planning.id,
                    models.ProductionEvent.event_type == 'start'
                ).order_by(models.ProductionEvent.created_at).first()
                
                session_start = start_event.created_at if start_event else latest_planning.created_at
                last_checkout = completed_trackings[-1].checkout_time
                
                worked_minutes = (last_checkout - session_start).total_seconds() / 60
                
                if worked_minutes > 0:
                    efficiency = (standard_minutes / worked_minutes) * 100
                    efficiency = round(efficiency, 1)
        
        hourly_data = {}
        for tracking in completed_trackings:
            hour_key = tracking.checkout_time.strftime("%H:00")
            if hour_key not in hourly_data:
                hourly_data[hour_key] = {"pieces": 0, "batches": 0}
            
            cart = db.query(models.CartLote).filter(
                models.CartLote.id == tracking.batch_id
            ).first()
            if cart:
                hourly_data[hour_key]["pieces"] += cart.quantity_pieces or 0
                hourly_data[hour_key]["batches"] += 1
        
        hourly_production = [
            {"hour": hour, "pieces": data["pieces"], "batches": data["batches"]}
            for hour, data in sorted(hourly_data.items())
        ]
        
        return {
            "pso_id": pso_id,
            "product_reference": pso.product.reference if pso.product else "N/A",
            "product_description": pso.product.description if pso.product else "N/A",
            "target_volume": target_volume,
            "target_batches": target_batches,
            "produced_volume": produced_volume,
            "produced_batches": produced_batches,
            "efficiency": efficiency,
            "hourly_production": hourly_production
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_pso_analytics: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
