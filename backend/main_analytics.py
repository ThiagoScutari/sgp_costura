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

# Re-create database tables (Note: In production this should be a migration)
# We drop all to apply schema changes effectively for dev/sprint 0
# models.Base.metadata.drop_all(bind=engine) # Keeping commented as per "no data loss"
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SGP Costura API - Sprint 6.0")

# Enable CORS for Frontend Development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seed Seamstresses if empty
def seed_seamstresses(db: Session):
    if db.query(models.Seamstress).count() == 0:
        names = ["Maria Silva", "Joana Santos", "Elizandra", "Débora", "Lúcia", "Fernanda"]
        for name in names:
            db.add(models.Seamstress(name=name))
        db.commit()

# Run seed on startup (hacky way, but works for dev)
# We will check this inside the setup endpoint lazily or just once.

class CheckoutRequest(BaseModel):
    batch_id: int
    workstation_id: Optional[int] = None

class AllocationItem(BaseModel):
    operation_id: int
    workstation_id: Optional[int] # None means "Bank" (unallocated)
    position: int
    quantity: int # Pieces allocated (for fractions)

class PlanningSyncRequest(BaseModel):
    pso_id: int
    allocations: List[AllocationItem]

# Startup event to seed data
@app.on_event("startup")
def startup_event():
    db = next(get_db())
    seed_seamstresses(db)

@app.get("/api/analytics/dashboard")
def get_analytics_dashboard(hours: int = 8, db: Session = Depends(get_db)):
    """
    Returns comprehensive performance metrics for BI dashboard.
    Calculates efficiency, delay rate, and production volume.
    """
    # Calculate time window
    current_time = datetime.utcnow()
    start_time = current_time - timedelta(hours=hours)
    
    # Get all completed batches in time window
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
    
    # Calculate metrics
    total_batches = len(completed_batches)
    delayed_count = sum(1 for b in completed_batches if b.is_delayed)
    delay_percentage = (delayed_count / total_batches * 100) if total_batches > 0 else 0
    
    # Calculate production volume
    total_pieces = 0
    batch_ids = [b.batch_id for b in completed_batches]
    carts = db.query(models.CartLote).filter(models.CartLote.id.in_(batch_ids)).all()
    total_pieces = sum(c.quantity_pieces for c in carts if c.quantity_pieces)
    
    avg_pieces_per_hour = total_pieces / hours if hours > 0 else 0
    
    # Calculate efficiency (Standard Time vs Actual Time)
    # Get the active planning to find operation times
    planning = db.query(models.ProductionPlanning).filter(
        models.ProductionPlanning.is_active == True
    ).order_by(desc(models.ProductionPlanning.id)).first()
    
    efficiency_current = 0
    if planning and len(completed_batches) > 1:
        # Get all operations for this planning
        allocations = db.query(models.OperationAllocation).filter(
            models.OperationAllocation.planning_id == planning.id
        ).all()
        
        # Calculate total standard time (sum of operation times * pieces produced)
        total_standard_minutes = 0
        for cart in carts:
            # Sum all operation times for one piece
            piece_time = sum(
                db.query(models.Operation).filter(
                    models.Operation.id == alloc.operation_id
                ).first().final_time or 0
                for alloc in allocations
            )
            total_standard_minutes += piece_time * (cart.quantity_pieces or 0)
        
        # Calculate actual elapsed time (first checkout to last checkout)
        checkout_times = sorted([b.checkout_time for b in completed_batches])
        if len(checkout_times) > 1:
            # Use shared logic from main.py to handle pauses/shift breaks
            from main import calculate_working_minutes_with_pauses
            elapsed_time = calculate_working_minutes_with_pauses(
                db, planning.id, checkout_times[0], checkout_times[-1]
            )
            
            if elapsed_time > 0:
                efficiency_current = (total_standard_minutes / elapsed_time) * 100
    
    efficiency_status = "above_target" if efficiency_current >= 80 else "below_target"
    
    # Hourly breakdown
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
    
    return {
        "efficiency": {
            "current": round(efficiency_current, 1),
            "target": 80.0,
            "status": efficiency_status
        },
        "delay_rate": {
            "delayed_count": delayed_count,
            "total_count": total_batches,
            "percentage": round(delay_percentage, 1)
        },
        "production_volume": {
            "total_pieces": total_pieces,
            "total_batches": total_batches,
            "avg_pieces_per_hour": round(avg_pieces_per_hour, 1)
        },
        "hourly_breakdown": hourly_breakdown
    }
