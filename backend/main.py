from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, time

# Import local modules
from database import engine, get_db, Base
import models
import extractor
import math
import logging

cart_logger = logging.getLogger("cart_lote")
if not cart_logger.handlers:
    logging.basicConfig(level=logging.INFO)
cart_logger.setLevel(logging.INFO)

# Re-create database tables (Note: In production this should be a migration)
# We drop all to apply schema changes effectively for dev/sprint 0
# models.Base.metadata.drop_all(bind=engine) # Keeping commented as per "no data loss"
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SGP Costura API - Sprint 7.0")

# Mount static files
app.mount("/telas", StaticFiles(directory="telas"), name="telas")

# Enable CORS for Frontend Development - MUST be before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

import json # Added import

# ... (Imports remain, just ensuring json is there)

# Shift Configuration Helper
def get_shift_config(db: Session):
    config_entry = db.query(models.SystemConfig).filter(models.SystemConfig.key == "SHIFT_CONFIG").first()
    if config_entry:
        return json.loads(config_entry.value)
    # Default Config
    return {
        "start_time": "07:00",
        "end_time": "17:00",
        "breaks": [
            {"start": "12:00", "end": "13:00"}
        ]
    }

def calculate_working_minutes(db: Session, start_dt: datetime, end_dt: datetime) -> float:
    """
    Calculate actual working minutes between two datetimes,
    using dynamic configuration from DB.
    """
    total_minutes = (end_dt - start_dt).total_seconds() / 60
    
    config = get_shift_config(db)
    breaks_config = config.get("breaks", [])
    
    # Parse dynamic breaks
    parsed_breaks = []
    for brk in breaks_config:
        try:
            b_start = datetime.strptime(brk["start"], "%H:%M").time()
            b_end = datetime.strptime(brk["end"], "%H:%M").time()
            parsed_breaks.append((b_start, b_end))
        except ValueError: 
            continue

    for b_start, b_end in parsed_breaks:
        # Check if work interval overlaps with this break
        if start_dt.time() < b_end and end_dt.time() > b_start:
            
            # CRITICAL FIX for "Production During Break":
            if start_dt.time() >= b_start:
                continue 

            # Calculate intersection
            overlap_start = max(start_dt.time(), b_start)
            overlap_end = min(end_dt.time(), b_end)
            
            overlap_minutes = (
                datetime.combine(start_dt.date(), overlap_end) -
                datetime.combine(start_dt.date(), overlap_start)
            ).total_seconds() / 60
            
            total_minutes -= overlap_minutes
    
    return max(total_minutes, 0)

def calculate_working_minutes_with_pauses(
    db: Session, 
    planning_id: int, 
    start_dt: datetime, 
    end_dt: datetime
) -> float:
    """
    Calcula os minutos trabalhados descontando almoço E pausas registradas.
    """
    # 1. Cálculo Bruto (incluindo lógica de almoço dinâmica)
    total_minutes = calculate_working_minutes(db, start_dt, end_dt) 
    
    # 2. Buscar eventos de pausa/retorno para este planejamento
    events = db.query(models.ProductionEvent).filter(
        models.ProductionEvent.planning_id == planning_id
    ).order_by(models.ProductionEvent.created_at).all()
    
    pause_minutes = 0.0
    pause_start = None
    
    # Filter only relevant events (optimization)
    relevant_events = [e for e in events if e.created_at >= start_dt and e.created_at <= end_dt]
    
    for event in relevant_events:
        if event.event_type == 'pause':
            if not pause_start: 
                pause_start = event.created_at
        elif event.event_type == 'resume' and pause_start:
            duration = (event.created_at - pause_start).total_seconds() / 60
            pause_minutes += duration
            pause_start = None
            
    if pause_start and pause_start < end_dt:
        duration = (end_dt - pause_start).total_seconds() / 60
        pause_minutes += duration

    return max(total_minutes - pause_minutes, 0)

# ... (Seeding remains the same)

# ==================== System Config Endpoints ====================

class ShiftConfigModel(BaseModel):
    start_time: str
    end_time: str
    breaks: List[dict] # [{"start": "12:00", "end": "13:00"}]

@app.post("/api/config/shift")
def save_shift_config(config: ShiftConfigModel, db: Session = Depends(get_db)):
    """Save shift configuration"""
    config_json = json.dumps(config.dict())
    
    existing = db.query(models.SystemConfig).filter(models.SystemConfig.key == "SHIFT_CONFIG").first()
    if existing:
        existing.value = config_json
    else:
        db.add(models.SystemConfig(key="SHIFT_CONFIG", value=config_json))
    
    db.commit()
    return {"message": "Configuration saved"}

@app.get("/api/config/shift")
def get_shift_config_endpoint(db: Session = Depends(get_db)):
    """Get shift configuration"""
    return get_shift_config(db)

# ==================== Seamstress Management Endpoints ====================

class SeamstressUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

@app.get("/api/seamstresses")
def get_seamstresses(db: Session = Depends(get_db)):
    """List all seamstresses with status"""
    seamstresses = db.query(models.Seamstress).all()
    return [{
        "id": s.id, 
        "name": s.name, 
        "is_active": s.is_active,
        "status": s.status 
    } for s in seamstresses]

@app.put("/api/seamstresses/{id}")
def update_seamstress(id: int, data: SeamstressUpdate, db: Session = Depends(get_db)):
    """Update seamstress active status"""
    s = db.query(models.Seamstress).filter(models.Seamstress.id == id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Seamstress not found")
    
    if data.name:
        s.name = data.name
    if data.is_active is not None:
        s.is_active = data.is_active
        s.status = "Ativa" if data.is_active else "Inativa" 
        
    db.commit()
    return {"message": "Seamstress updated"}

class SeamstressCreate(BaseModel):
    name: str

@app.post("/api/seamstresses")
def create_seamstress(data: SeamstressCreate, db: Session = Depends(get_db)):
    """Create a new seamstress"""
    s = models.Seamstress(name=data.name, is_active=True, status="Ativa")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

@app.delete("/api/seamstresses/{id}")
def delete_seamstress(id: int, db: Session = Depends(get_db)):
    """Delete a seamstress (Protected)"""
    s = db.query(models.Seamstress).filter(models.Seamstress.id == id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Seamstress not found")
    
    # Dependency Check: WorkstationAllocations
    active_allocations = db.query(models.WorkstationAllocation).filter(
        models.WorkstationAllocation.seamstress_id == id
    ).first()
    
    if active_allocations:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete: Seamstress has active allocations in production history."
        )

    db.delete(s)
    db.commit()
    return {"message": "Seamstress deleted"}

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
    is_fraction: Optional[bool] = False # True if this operation was split/fractioned

class PlanningSyncRequest(BaseModel):
    pso_id: int
    allocations: List[AllocationItem]
    version_name: Optional[str] = None
    notes: Optional[str] = None
    pulse_duration: Optional[int] = 60
    batch_size: Optional[int] = None
    total_quantity: Optional[int] = 1000 # Default if not provided


@app.on_event("startup")
def startup_event():
    # Basic seeding
    db = next(get_db())
    
    # ✅ Migration Sprint 13 (Run manually or here if lightweight)
    # Ensure schema is up to date BEFORE accessing models
    try:
        from migrate_db import run_migrations
        run_migrations()
    except Exception as e:
        print(f"⚠️ Error running migrations on startup: {e}")
        
    seed_seamstresses(db)
    seed_default_user(db)

def seed_default_user(db: Session):
    """Create default admin user if no users exist"""
    try:
        if db.query(models.User).count() == 0:
            from auth import get_password_hash
            
            # Create admin user with simple password
            admin_user = models.User(
                username="admin",
                email="admin@drx.com",
                hashed_password=get_password_hash("admin123"),
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            print("✅ Default admin user created: username='admin', password='admin123'")
    except Exception as e:
        print(f"⚠️  Error creating default user: {e}")
        db.rollback()

# ==================== Authentication Endpoints ====================

@app.post("/api/auth/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token"""
    from auth import verify_password, create_access_token
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password using SHA256
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role
    }

@app.post("/api/auth/register")
def register(username: str, email: str, password: str, db: Session = Depends(get_db)):
    """Register a new user"""
    from auth import get_password_hash
    
    # Check if user exists
    if db.query(models.User).filter(models.User.username == username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = get_password_hash(password)
    new_user = models.User(username=username, email=email, hashed_password=hashed_password, role="operator")
    db.add(new_user)
    db.commit()
    
    return {"message": "User created successfully", "username": username}

# ==================== User Management Endpoints (Sprint 13) ====================

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "operator"

class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

@app.get("/api/users")
def get_users(db: Session = Depends(get_db)):
    """List all users"""
    users = db.query(models.User).all()
    return [{"id": u.id, "username": u.username, "email": u.email, "role": u.role, "is_active": u.is_active} for u in users]

@app.post("/api/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create new user (Admin)"""
    from auth import get_password_hash
    
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username taken")
    
    hashed_password = get_password_hash(user.password)
    new_user = models.User(
        username=user.username, 
        email=user.email, 
        hashed_password=hashed_password, 
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username, "role": new_user.role}

@app.put("/api/users/{user_id}")
def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    """Update user role, active status or password"""
    from auth import get_password_hash
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_data.role:
        user.role = user_data.role
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.password:
        user.hashed_password = get_password_hash(user_data.password)
        
    db.commit()
    return {"message": "User updated successfully"}

# ==================== Seamstress Management Endpoints (Sprint 13) ====================

class SeamstressUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

@app.get("/api/seamstresses")
def get_seamstresses(db: Session = Depends(get_db)):
    """List all seamstresses with status"""
    # Return all, frontend decides how to show inactive ones
    seamstresses = db.query(models.Seamstress).all()
    return [{
        "id": s.id, 
        "name": s.name, 
        "is_active": s.is_active,
        "status": s.status # Backward compat
    } for s in seamstresses]

@app.put("/api/seamstresses/{id}")
def update_seamstress(id: int, data: SeamstressUpdate, db: Session = Depends(get_db)):
    """Update seamstress active status"""
    s = db.query(models.Seamstress).filter(models.Seamstress.id == id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Seamstress not found")
    
    if data.name:
        s.name = data.name
    if data.is_active is not None:
        s.is_active = data.is_active
        s.status = "Ativa" if data.is_active else "Inativa" # Sync legacy field
        
    db.commit()
    db.commit()
    return {"message": "Seamstress updated"}

class SeamstressCreate(BaseModel):
    name: str

@app.post("/api/seamstresses")
def create_seamstress(data: SeamstressCreate, db: Session = Depends(get_db)):
    """Create a new seamstress"""
    s = models.Seamstress(name=data.name, is_active=True, status="Ativa")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

@app.delete("/api/seamstresses/{id}")
def delete_seamstress(id: int, db: Session = Depends(get_db)):
    """Delete a seamstress"""
    s = db.query(models.Seamstress).filter(models.Seamstress.id == id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Seamstress not found")
    
    # Check for dependencies (allocations) - Optional: could block if has history
    # For now, we allow delete as requested.
    db.delete(s)
    db.commit()
    return {"message": "Seamstress deleted"}


# ==================== Product Endpoints ====================



@app.get("/api/products")
def get_products(db: Session = Depends(get_db)):
    """
    Returns list of all products with their PSO versions and calculated metrics.
    Used by Tela 03 (OP Management).
    """
    products = db.query(models.Product).all()
    
    result = []
    for product in products:
        # Filter PSOs: Exclude archived
        active_psos = [p for p in product.psos if not p.is_archived]
        
        for pso in active_psos:
            # Calculate total TP (sum of all operation times)
            operations = db.query(models.Operation).filter(models.Operation.pso_id == pso.id).all()
            # Check if this PSO has an active planning
            has_active_planning = db.query(models.ProductionPlanning).join(
                models.ProductionOrder
            ).filter(
                models.ProductionOrder.product_reference == product.reference,
                models.ProductionPlanning.is_active == True
            ).first() is not None

            # Count only ACTIVE operations
            active_ops = [op for op in operations if op.is_active]
            active_ops_count = len(active_ops)

            # Calculate total TP based on ACTIVE operations and EFFICIENCY factor
            # TP Real = TP Standard / Efficiency
            efficiency = pso.default_efficiency_factor or 1.0
            total_tp_minutes = sum(op.final_time for op in active_ops if op.final_time) / efficiency

            result.append({
                "product_reference": product.reference,
                "product_description": product.description,
                "pso_id": pso.id,
                "pso_version": pso.version_name,
                "status": pso.status,
                "total_tp_minutes": round(total_tp_minutes, 4),
                "operation_count": active_ops_count, # Return only active count
                "operation_count": active_ops_count, # Return only active count
                "created_at": pso.created_at,
                "has_active_planning": has_active_planning
            })
    
    # Sort by most recent first
    result.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {"products": result}

@app.get("/api/pso/{pso_id}/details")
def get_pso_details(pso_id: int, db: Session = Depends(get_db)):
    """
    Returns detailed operation list for a specific PSO.
    Used by Tela 03 operation details modal.
    """
    pso = db.query(models.PSO).filter(models.PSO.id == pso_id).first()
    if not pso:
        raise HTTPException(status_code=404, detail="PSO not found")
    
    operations = db.query(models.Operation).filter(
        models.Operation.pso_id == pso_id
    ).order_by(models.Operation.sequence).all()
    
    total_tp = sum(op.final_time for op in operations if op.final_time)
    
    return {
        "pso_id": pso.id,
        "product_reference": pso.product.reference,
        "product_description": pso.product.description,
        "version_name": pso.version_name,
        "status": pso.status,
        "total_tp_minutes": round(total_tp, 4),
        "default_efficiency_factor": pso.default_efficiency_factor, # Return saved efficiency
        "operations": [
            {
                "sequence": op.sequence,
                "description": op.description,
                "machine": op.macro_machine or "Indefinida",
                "time_minutes": round(op.final_time, 4) if op.final_time else 0,
                "time_seconds": round(op.final_time * 60, 2) if op.final_time else 0,
                "ativa": op.is_active  # Return active status
            } for op in operations
        ]
    }

@app.get("/api/planning/setup")
def get_planning_setup(pso_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Returns data to initialize the Cockpit:
    - Active Seamstresses
    - Operations from specified PSO (or latest if not specified)
    """
    # 1. Get Seamstresses (Sprint 13 - ONLY ACTIVE)
    seamstresses = db.query(models.Seamstress).filter(
        models.Seamstress.is_active == True
    ).all()
    
    # 2. Get PSO (specific or latest)
    pso = None
    if pso_id:
        pso = db.query(models.PSO).filter(models.PSO.id == pso_id).first()
        if not pso:
            raise HTTPException(status_code=404, detail=f"PSO with ID {pso_id} not found")
    
    # Defaults to None if no ID provided (prevents ghost data)
    
    operations = []
    
    if pso:
        # Filter for ACTIVE operations only
        ops = db.query(models.Operation).filter(
            models.Operation.pso_id == pso.id,
            models.Operation.is_active == True # Only active ops
        ).order_by(models.Operation.sequence).all()
        
        # Get efficiency factor
        eff_factor = pso.default_efficiency_factor or 1.0
        
        for op in ops:
            # Calculate Real Time: Standard Time / Efficiency
            # Then convert to seconds for the dashboard
            real_time_min = (op.final_time or 0.0) / eff_factor
            real_time_sec = real_time_min * 60
            
            operations.append({
                "seq": op.sequence,
                "id": op.id,
                "desc": op.description,
                "machine": op.macro_machine.lower().replace("overlock", "over") if op.macro_machine else "manual",
                "mName": op.macro_machine or "Indefinida",
                "time": float(f"{real_time_sec:.2f}")
            })
            
        # --- SPRINT 13: SHIELDING CODE (CAPACITY CALCULATION) ---
        num_active_operators = len(seamstresses)
        
        # Calculate total TP of the product (in minutes)
        total_tp_minutes = sum(op['time'] for op in operations) / 60.0

        if num_active_operators == 0:
            suggested_tl = 10 
            target_tact = 0
            print("⚠️ Warning: No active seamstresses found for calculation.")
        else:
            # 2. Total Capacity (528 min * operators)
            total_available_minutes = 528 * num_active_operators
            
            # 3. Suggested Batch Size (TL)
            if total_tp_minutes > 0:
                suggested_tl = math.floor(total_available_minutes / total_tp_minutes)
                suggested_tl = max(1, suggested_tl) 
            else:
                suggested_tl = 10
            
            # 4. Target Tact
            target_tact = total_tp_minutes / num_active_operators
    else:
        suggested_tl = 10
        num_active_operators = len(seamstresses)
        target_tact = 0

    
    return {
        "seamstresses": [{"id": s.id, "nome": s.name} for s in seamstresses],
        "pso": {
            "id": pso.id if pso else None,
            "product": pso.product.reference if pso else None,
            "product_reference": pso.product.reference if pso else None, # Ensure compatibility field
            "operations": operations
        } if pso else None,
        "suggested_metrics": {
            "suggested_tl": suggested_tl,
            "target_tact": target_tact if 'target_tact' in locals() else None,
            "active_operators": num_active_operators
        }
    }

@app.post("/api/planning/sync")
def sync_planning(data: PlanningSyncRequest, db: Session = Depends(get_db)):
    """
    Saves the current state of Kanban board.
    Creates a new ProductionPlanning version or updates existing active one.
    """
    cart_logger.info("[SYNC:start] pso_id=%s batch_size=%s total_quantity=%s allocations=%s", data.pso_id, data.batch_size, data.total_quantity, len(data.allocations))
    try:
        # 1. Validate PSO
        pso = db.query(models.PSO).filter(models.PSO.id == data.pso_id).first()
        if not pso:
            raise HTTPException(status_code=404, detail="PSO not found")

        # 2. Find or Create Production Order
        # Look for an active PO for this product
        po = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.product_reference == pso.product.reference,
            models.ProductionOrder.status == "Ativa"
        ).order_by(desc(models.ProductionOrder.id)).first()

        # If no active PO exists, create one automatically
        if not po:
            po = models.ProductionOrder(
                product_reference=pso.product.reference,
                quantity=1000,  # Default batch quantity
                status="Ativa",
                pulse_duration=60  # Default pulse
            )
            db.add(po)
            db.flush()

        # 3. Create/Reset Production Planning
        # We deactivate previous plannings for this PO
        db.query(models.ProductionPlanning).filter(
            models.ProductionPlanning.production_order_id == po.id
        ).update({"is_active": False})
        
        batch_size_val = data.batch_size if data.batch_size and data.batch_size > 0 else 50
        total_qty = data.total_quantity if data.total_quantity and data.total_quantity > 0 else 1000
        
        new_planning = models.ProductionPlanning(
            production_order_id=po.id,
            pso_id=data.pso_id,  # ✅ Save which PSO version was used
            version_name=data.version_name or f"Plan-{datetime.utcnow().strftime('%Y%m%d-%H%M')}",
            pulse_duration=data.pulse_duration or po.pulse_duration,
            batch_size=batch_size_val,
            total_quantity=total_qty,
            notes=data.notes,
            total_operators=len({a.workstation_id for a in data.allocations if a.workstation_id is not None}),
            is_active=False  # ✅ Default to inactive. Must be started manually in Monitor (Page 01)
        )
        db.add(new_planning)
        db.flush()
        print(f"[SYNC] Created planning id={new_planning.id} batch_size={batch_size_val} total_qty={total_qty} po_id={po.id}")

        # Ensure total_quantity and batch_size persist on the ProductionOrder for analytics/history
        if total_qty:
            po.quantity = total_qty
        if new_planning.pulse_duration:
            po.pulse_duration = new_planning.pulse_duration
        db.add(po)
        db.flush()
        print(f"[SYNC] PO {po.id} updated quantity={po.quantity} pulse={po.pulse_duration}")

        # 4. Process Allocations
        # Group allocations by workstation to create WorkstationAllocation first
        grouped_allocations = {}
        for item in data.allocations:
            if item.workstation_id is None: continue # Skip unallocated (bank)
            
            if item.workstation_id not in grouped_allocations:
                grouped_allocations[item.workstation_id] = []
            grouped_allocations[item.workstation_id].append(item)

        # Get valid OP IDs for this PSO to prevent FK error
        valid_op_ids = {row[0] for row in db.query(models.Operation.id).filter(models.Operation.pso_id == pso.id).all()}

        for ws_id, items in grouped_allocations.items():
            # Create Workstation Allocation (The "Seat" at the table)
            ws_alloc = models.WorkstationAllocation(
                planning_id=new_planning.id,
                seamstress_id=ws_id,
                position_sequence=1, # Logic for sorting workstations not implemented yet, default 1
                load_time_batch_min=0 # Calculated later if needed
            )
            db.add(ws_alloc)
            db.flush()

            # Add Operations to this Workstation
            for alloc_item in items:
                # Validation: Skip operations that don't belong to this PSO (Stale IDs from frontend)
                if alloc_item.operation_id not in valid_op_ids:
                    print(f"⚠️ Warning: Skipping stale/invalid operation ID {alloc_item.operation_id} (Not in PSO {pso.id})")
                    continue

                # Create operation allocation
                # Use frontend's is_fraction flag instead of comparing with po.quantity
                op_alloc = models.OperationAllocation(
                    allocation_id=ws_alloc.id,
                    operation_id=alloc_item.operation_id,
                    executed_quantity=alloc_item.quantity,
                    is_fractioned=alloc_item.is_fraction  # ✅ Use frontend's flag
                )
                db.add(op_alloc)

        # 5. Generate Batches (CartLote) for THIS planning session
        # Update PO quantity to match current planning metadata
        if data.total_quantity:
            po.quantity = data.total_quantity
            db.add(po)
            
        # ✅ NO LONGER DELETING: We keep history. New batches are tied to new_planning.id
        # db.query(models.CartLote).filter(models.CartLote.production_order_id == po.id).delete()
        db.flush()

        # Generate new batches based on total quantity and batch size
        num_lotes = math.ceil(total_qty / batch_size_val)
        cart_logger.info("[SYNC:batches] planning_id=%s num=%s batch_size=%s", new_planning.id, num_lotes, batch_size_val)
        
        for i in range(num_lotes):
            # Calculate quantity for this specific batch
            current_qty = batch_size_val
            # If it's the last batch, check if it's partial
            if (i + 1) * batch_size_val > total_qty:
                current_qty = total_qty % batch_size_val
                if current_qty == 0:
                    current_qty = batch_size_val
            
            new_lote = models.CartLote(
                production_order_id=po.id,
                planning_id=new_planning.id,  # ✅ Link to this specific session
                sequence_number=i + 1,
                quantity_pieces=current_qty,
                status="Aguardando"
            )
            db.add(new_lote)
            cart_logger.info("[SYNC:cart] seq=%s qty=%s planning_id=%s", i + 1, current_qty, new_planning.id)

        db.commit()
        cart_logger.info("[SYNC:done] planning_id=%s num_lotes=%s", new_planning.id, num_lotes)
        return {"status": "synced", "message": "Balanceamento publicado com sucesso!", "planning_id": new_planning.id}

    except Exception as e:
        db.rollback()
        print(f"Error syncing planning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/planning/versions")
def get_planning_versions(pso_id: int, db: Session = Depends(get_db)):
    """
    Get all planning versions for a specific PSO.
    Used when clicking PUBLICAR to show existing versions.
    """
    try:
        # Get the product reference for this PSO
        pso = db.query(models.PSO).filter(models.PSO.id == pso_id).first()
        if not pso:
            return {"versions": []}
        
        # Find production order for this product
        po = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.product_reference == pso.product.reference
        ).order_by(desc(models.ProductionOrder.id)).first()
        
        if not po:
            return {"versions": []}
        
        # Get all plannings for this PO
        plannings = db.query(models.ProductionPlanning).filter(
            models.ProductionPlanning.production_order_id == po.id
        ).order_by(desc(models.ProductionPlanning.created_at)).all()
        
        versions = []
        for idx, planning in enumerate(reversed(plannings)):  # Reverse to get correct version numbers
            # Count unique seamstresses in this planning
            seamstress_count = db.query(models.WorkstationAllocation.seamstress_id).filter(
                models.WorkstationAllocation.planning_id == planning.id
            ).distinct().count()
            
            versions.append({
                "planning_id": planning.id,
                "version_number": idx + 1,
                "version_name": planning.version_name,
                "notes": planning.notes,
                "created_at": planning.created_at.isoformat() if planning.created_at else None,
                "seamstress_count": seamstress_count,
                "batch_size": planning.batch_size,
                "pulse_duration": planning.pulse_duration
            })
        
        # Return in reverse order (newest first)
        return {"versions": list(reversed(versions))}
        
    except Exception as e:
        print(f"Error getting versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/planning/{planning_id}/allocations")
def get_planning_allocations(planning_id: int, db: Session = Depends(get_db)):
    """
    Returns the allocations for a specific planning ID.
    Used to restore the Cockpit state during Rebalancing.
    """
    planning = db.query(models.ProductionPlanning).filter(
        models.ProductionPlanning.id == planning_id
    ).first()
    
    if not planning:
        raise HTTPException(status_code=404, detail="Planning not found")
        
    result = []
    
    # Sort workstations by their original id or position if available
    sorted_allocations = sorted(planning.allocations, key=lambda x: x.id)
    
    for seat in sorted_allocations:
        # Sort operations by ID to respect original insertion order (UI order)
        ops = sorted(seat.op_allocations, key=lambda x: x.id)
        
        for i, op_alloc in enumerate(ops):
            # Fetch operation details to get sequence
            operation = db.query(models.Operation).filter(models.Operation.id == op_alloc.operation_id).first()
            op_sequence = operation.sequence if operation else 0

            result.append({
                "operation_id": op_alloc.operation_id,
                "operation_sequence": op_sequence,
                "workstation_id": seat.seamstress_id, # Seamstress ID
                "quantity": op_alloc.executed_quantity,
                "is_fraction": op_alloc.is_fractioned,
                "position": i + 1
            })
            
    return {"allocations": result, "pso_id": planning.pso_id}


@app.get("/api/planning/published")
def get_published_plannings(db: Session = Depends(get_db)):
    orders = db.query(models.ProductionOrder).join(models.ProductionPlanning).distinct().all()
    ops = []
    for po in orders:
        versions = []
        plannings = db.query(models.ProductionPlanning).filter(models.ProductionPlanning.production_order_id == po.id).all()
        for planning in plannings:
            pso = db.query(models.PSO).filter(models.PSO.id == planning.pso_id).first()
            if not pso:
                continue
            if pso and pso.is_archived:
                continue
            planning_timestamp = planning.created_at or getattr(planning, "updated_at", None) or datetime.utcnow()
            versions.append({
                "planning_id": planning.id,
                "version_name": planning.version_name,
                "batch_size": planning.batch_size,
                "created_at": planning_timestamp.isoformat()
            })
        if versions:
            ops.append({"product_reference": po.product_reference, "versions": versions})
    return {"ops": ops}


@app.get("/api/planning/{planning_id}")
def get_planning_detail(planning_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific planning version.
    Used when loading a published balance.
    """
    try:
        # Get the planning
        planning = db.query(models.ProductionPlanning).filter(
            models.ProductionPlanning.id == planning_id
        ).first()
        
        if not planning:
            raise HTTPException(status_code=404, detail="Planning not found")
        
        # Get production order to find PSO
        po = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.id == planning.production_order_id
        ).first()
        
        if not po:
            raise HTTPException(status_code=404, detail="Production order not found")
        
        # ✅ Use the PSO that was saved in the planning (instead of latest PSO)
        pso = None
        if planning.pso_id:
            pso = db.query(models.PSO).filter(models.PSO.id == planning.pso_id).first()
        
        # Fallback: If pso_id is not set (old data), try to find by product reference
        if not pso:
            pso = db.query(models.PSO).join(models.Product).filter(
                models.Product.reference == po.product_reference
            ).order_by(desc(models.PSO.id)).first()
        
        # Calculate version number
        all_plannings = db.query(models.ProductionPlanning).filter(
            models.ProductionPlanning.production_order_id == po.id
        ).order_by(models.ProductionPlanning.created_at).all()
        
        version_number = next((idx + 1 for idx, p in enumerate(all_plannings) if p.id == planning_id), 1)
        
        # Get allocations
        workstation_allocs = db.query(models.WorkstationAllocation).filter(
            models.WorkstationAllocation.planning_id == planning_id
        ).all()
        
        allocations = []
        for ws_alloc in workstation_allocs:
            # Get operation allocations for this workstation
            op_allocs = db.query(models.OperationAllocation).filter(
                models.OperationAllocation.allocation_id == ws_alloc.id
            ).all()
            
            for op_alloc in op_allocs:
                allocations.append({
                    "seamstress_id": ws_alloc.seamstress_id,
                    "operation_seq": op_alloc.operation.sequence,
                    "position": ws_alloc.position_sequence,
                    "quantity": op_alloc.executed_quantity,
                    "is_fraction": op_alloc.is_fractioned
                })

        # --- SPRINT 14.1: CAPACITY RECALCULATION VALIDATION ---
        
        # 1. Count CURRENT active seamstresses
        active_ops_count = db.query(models.Seamstress).filter(models.Seamstress.is_active == True).count()
        
        # 2. Get ORIGINAL operators count (fallback to allocation count if field is missing/zero)
        original_ops_count = planning.total_operators
        if not original_ops_count or original_ops_count == 0:
             # Fallback: Count unique seamstresses in the saved plan
             original_ops_count = len({alloc["seamstress_id"] for alloc in allocations}) or 1

        recalculated_batch_size = None
        capacity_warning = False
        
        # 3. Detect Capacity Drop
        # Only recalculate if we have FEWER operators than before
        if active_ops_count < original_ops_count and active_ops_count > 0:
            capacity_factor = active_ops_count / original_ops_count
            suggested_tl = math.floor(planning.batch_size * capacity_factor)
            recalculated_batch_size = max(1, suggested_tl) # Ensure at least 1
            capacity_warning = True
            
            print(f"⚠️ CAPACITY DROP: {original_ops_count} -> {active_ops_count}. Recalculating TL: {planning.batch_size} -> {recalculated_batch_size}")
        
        return {
            "planning_id": planning.id,
            "pso_id": pso.id if pso else None,
            "version_number": version_number,
            "version_name": planning.version_name,
            "notes": planning.notes,
            "pulse_duration": planning.pulse_duration,
            "batch_size": planning.batch_size,
            "created_at": planning.created_at.isoformat() if planning.created_at else None,
            "allocations": allocations,
            # New fields for frontend guardrails
            "active_operators_current": active_ops_count,
            "original_operators": original_ops_count,
            "recalculated_batch_size": recalculated_batch_size,
            "capacity_warning": capacity_warning
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting planning detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/planning/{planning_id}")
def delete_planning(planning_id: int, db: Session = Depends(get_db)):
    """
    Delete a specific planning version and all its allocations.
    Used when user wants to remove a published balancing.
    """
    try:
        # Get the planning
        planning = db.query(models.ProductionPlanning).filter(
            models.ProductionPlanning.id == planning_id
        ).first()
        
        if not planning:
            raise HTTPException(status_code=404, detail="Planning not found")
        
        # Store info for response
        version_name = planning.version_name
        
        # Delete operation allocations first (cascade from workstation allocations)
        workstation_allocs = db.query(models.WorkstationAllocation).filter(
            models.WorkstationAllocation.planning_id == planning_id
        ).all()
        
        for ws_alloc in workstation_allocs:
            # Delete operation allocations for this workstation
            db.query(models.OperationAllocation).filter(
                models.OperationAllocation.allocation_id == ws_alloc.id
            ).delete()
        
        # Delete workstation allocations
        db.query(models.WorkstationAllocation).filter(
            models.WorkstationAllocation.planning_id == planning_id
        ).delete()
        
        # Finally delete the planning itself
        db.delete(planning)
        db.commit()
        
        return {
            "status": "deleted",
            "message": f"Balanceamento '{version_name}' excluído com sucesso",
            "planning_id": planning_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting planning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/production/start")
def start_production(data: dict, db: Session = Depends(get_db)):
    """
    Activate a specific production planning and deactivate all others.
    This marks the start of a production batch.
    """
    try:
        planning_id = data.get("planning_id")
        if not planning_id:
            raise HTTPException(status_code=400, detail="planning_id is required")
        
        # Deactivate all current active plannings
        db.query(models.ProductionPlanning).update({"is_active": False})
        
        # Activate the selected planning
        planning = db.query(models.ProductionPlanning).filter(
            models.ProductionPlanning.id == planning_id
        ).first()
        
        if not planning:
            raise HTTPException(status_code=404, detail="Planning not found")
        
        # Activate
        planning.is_active = True
        cart_logger.info("[START] Activating planning=%s po=%s batch_size=%s total_qty=%s", planning.id, planning.production_order_id, planning.batch_size, planning.total_quantity)

        # Log Start Event
        db.add(models.ProductionEvent(
            planning_id=planning.id,
            event_type="start"
        ))
        db.commit()
        cart_logger.info("[START:done] planning=%s active=%s", planning.id, planning.is_active)
        
        return {
            "status": "started",
            "message": f"Produção iniciada: {planning.version_name}",
            "planning_id": planning_id,
            "pso_id": planning.pso_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        cart_logger.error("[START:error] planning_id=%s err=%s", data.get("planning_id"), e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/production/pause")
def pause_production(data: dict, db: Session = Depends(get_db)):
    """Pause the current active production"""
    try:
        planning_id = data.get("planning_id")
        planning = db.query(models.ProductionPlanning).filter(models.ProductionPlanning.id == planning_id).first()
        
        if not planning or not planning.is_active:
            raise HTTPException(status_code=400, detail="Planning not found or not active")
            
        db.add(models.ProductionEvent(planning_id=planning.id, event_type="pause"))
        db.commit()
        return {"status": "paused", "message": "Produção pausada"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/production/resume")
def resume_production(data: dict, db: Session = Depends(get_db)):
    """Resume the current active production"""
    try:
        planning_id = data.get("planning_id")
        planning = db.query(models.ProductionPlanning).filter(models.ProductionPlanning.id == planning_id).first()
        
        if not planning or not planning.is_active:
            raise HTTPException(status_code=400, detail="Planning not found or not active")
            
        db.add(models.ProductionEvent(planning_id=planning.id, event_type="resume"))
        db.commit()
        return {"status": "resumed", "message": "Produção retomada"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/production/stop")
def stop_production(data: dict, db: Session = Depends(get_db)):
    """Stop/Finish the current active production"""
    try:
        planning_id = data.get("planning_id")
        planning = db.query(models.ProductionPlanning).filter(models.ProductionPlanning.id == planning_id).first()
        
        if not planning:
            raise HTTPException(status_code=404, detail="Planning not found")
            
        # Log event and deactivate
        db.add(models.ProductionEvent(planning_id=planning.id, event_type="stop"))
        
        # Deactivate
        planning.is_active = False
        db.commit()
        
        return {"status": "stopped", "message": "Produção finalizada"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/production/rebalance")
def rebalance_production(data: dict, db: Session = Depends(get_db)):
    """
    Logic for Rebalancing (Trocar pneu com carro andando):
    1. Calculate remaining qty
    2. Clone PSO
    3. Return info for Cockpit
    """
    try:
        planning_id = data.get("planning_id")
        planning = db.query(models.ProductionPlanning).filter(models.ProductionPlanning.id == planning_id).first()
        
        if not planning:
            raise HTTPException(status_code=404, detail="Planning not found")

        # 1. Start Rebalancing Logic
        po_id = planning.production_order_id
        
        # Calculate Completed Quantity
        completed_batches = db.query(models.CartLote).filter(
            models.CartLote.production_order_id == po_id,
            models.CartLote.status == "Concluído"
        ).all()
        
        completed_qty = sum(b.quantity_pieces for b in completed_batches if b.quantity_pieces)
        total_original = planning.total_quantity or 0
        remaining_qty = max(0, total_original - completed_qty)
        
        # 2. Clone PSO
        original_pso = db.query(models.PSO).filter(models.PSO.id == planning.pso_id).first()
        if not original_pso:
             raise HTTPException(status_code=404, detail="Original PSO not found")
             
        new_version_name = f"{original_pso.version_name} (Rebal)"
        new_pso = models.PSO(
            product_id=original_pso.product_id,
            version_name=new_version_name,
            status="Em Criação", # Temporary
            default_efficiency_factor=original_pso.default_efficiency_factor
        )
        db.add(new_pso)
        db.flush()
        
        # Clone Operations (keeping original properties)
        original_ops = db.query(models.Operation).filter(models.Operation.pso_id == original_pso.id).all()
        for op in original_ops:
            new_op = models.Operation(
                pso_id=new_pso.id,
                sequence=op.sequence,
                description=op.description,
                original_machine=op.original_machine,
                macro_machine=op.macro_machine,
                time_pdf=op.time_pdf,
                time_edited=op.time_edited,
                final_time=op.final_time,
                is_active=op.is_active # Crucial: Keep same active/inactive state
            )
            db.add(new_op)
            
        db.commit()
        
        return {
            "status": "rebalancing_prepared",
            "new_pso_id": new_pso.id,
            "original_planning_id": planning.id,
            "remaining_quantity": remaining_qty,
            "message": "Rebalanceamento preparado"
        }

    except Exception as e:
        db.rollback()
        print(f"Error rebalancing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/production/active")
def get_active_production(db: Session = Depends(get_db)):
    """
    Get the currently active production planning.
    Returns null if no production is running.
    """
    try:
        active_planning = db.query(models.ProductionPlanning).filter(
            models.ProductionPlanning.is_active == True
        ).first()
        
        if not active_planning:
            return {"active": False, "planning": None}
        
        # Get PSO info
        pso = None
        if active_planning.pso_id:
            pso = db.query(models.PSO).filter(
                models.PSO.id == active_planning.pso_id
            ).first()
        
        product_reference = None
        if pso and pso.product:
            product_reference = pso.product.reference
        
        return {
            "active": True,
            "planning": {
                "id": active_planning.id,
                "version_name": active_planning.version_name,
                "pso_id": active_planning.pso_id,
                "pso_version": pso.version_name if pso else None,
                "product_reference": product_reference,
                "pulse_duration": active_planning.pulse_duration,
                "batch_size": active_planning.batch_size
            }
        }
        
    except Exception as e:
        print(f"Error getting active production: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Existing Endpoints ---

@app.get("/api/dashboard/active-status")
def get_dashboard_active_status(db: Session = Depends(get_db)):
    """
    Returns real-time status for the Factory Dashboard (Monitor).
    Includes: Active Planning, Last Checkout Time, Pulse Status, Seamstress Allocations
    """
    try:
        # 1. Get Latest Active Planning
        planning = db.query(models.ProductionPlanning).filter(
            models.ProductionPlanning.is_active == True
        ).order_by(desc(models.ProductionPlanning.id)).first()

        if not planning:
            return {
                "status": "idle", 
                "message": "Nenhum planejamento ativo.",
                "pulse_duration": 60,
                "elapsed_seconds": 0,
                "carts_produced": 0,
                "workstations": []
            }

        po = db.query(models.ProductionOrder).filter(models.ProductionOrder.id == planning.production_order_id).first()
        
        if not po:
            return {
                "status": "idle", 
                "message": "Ordem de Produção não encontrada.",
                "pulse_duration": 60,
                "elapsed_seconds": 0,
                "carts_produced": 0,
                "workstations": []
            }
        
        # 2. Get Last Checkout for THIS SPECIFIC PLANNING (Pulse Reference)
        last_tracking = db.query(models.BatchTracking).filter(
            models.BatchTracking.planning_id == planning.id
        ).order_by(desc(models.BatchTracking.checkout_time)).first()

        # Determine start time for the current cycle with Session Awareness
        # Find the latest START event for this planning
        latest_start_event = db.query(models.ProductionEvent).filter(
            models.ProductionEvent.planning_id == planning.id, 
            models.ProductionEvent.event_type == 'start'
        ).order_by(desc(models.ProductionEvent.created_at)).first()

        # Base reference is the start of this session (or planning creation as fallback)
        session_start_time = latest_start_event.created_at if latest_start_event else planning.created_at

        carts_produced = 0
        start_time = session_start_time

        if last_tracking:
            # ✅ CRITICAL: Only count batches from THIS planning session
            carts_produced = db.query(models.BatchTracking).filter(
                models.BatchTracking.planning_id == planning.id
            ).count()
            
            # If the last batch was completed, the current cycle starts from that checkout time
            if last_tracking.checkout_time > session_start_time:
                start_time = last_tracking.checkout_time
            else:
                # If the last checkout was BEFORE this session (e.g. yesterday), 
                # we start counting from the session start (08:00 today).
                start_time = session_start_time

        
        # Calculate elapsed time with pauses (New Logic)
        current_time = datetime.utcnow()
        elapsed_minutes = calculate_working_minutes_with_pauses(
            db, planning.id, start_time, current_time
        )
        elapsed_seconds = max(0, elapsed_minutes * 60)
        
        # Determine current status based on last event
        latest_event = db.query(models.ProductionEvent).filter(
            models.ProductionEvent.planning_id == planning.id
        ).order_by(desc(models.ProductionEvent.created_at)).first()
        
        is_paused = latest_event and latest_event.event_type == 'pause'
        
        # 3. Get Active Seamstresses and Loads
        allocations = []
        for seat in planning.allocations:
            active_ops_count = len(seat.op_allocations)
            allocations.append({
                "seamstress_name": seat.seamstress.name,
                "position": seat.seamstress_id, # Simplify for now
                "load_count": active_ops_count,
                "status": "Produzindo" if active_ops_count > 0 else "Ociosa"
            })

        allocations.sort(key=lambda x: x["position"])

        # Calculate total batches for THIS session
        total_batches = db.query(models.CartLote).filter(
            models.CartLote.planning_id == planning.id
        ).count()
        
        # ✅ REAL-TIME EFFICIENCY CALCULATION
        efficiency = 0.0
        
        if carts_produced > 0:
            # Calculate Standard Minutes (TP × Completed Batches)
            total_tp_per_batch = 0.0
            for alloc in planning.allocations:
                for op_alloc in alloc.op_allocations:
                    operation = db.query(models.Operation).filter(
                        models.Operation.id == op_alloc.operation_id
                    ).first()
                    if operation:
                        total_tp_per_batch += operation.final_time
            
            standard_minutes = total_tp_per_batch * carts_produced
            
            # Calculate Actual Worked Minutes (Session Start to Now, minus pauses)
            worked_minutes = calculate_working_minutes_with_pauses(
                db, planning.id, session_start_time, current_time
            )
            
            # Efficiency = (Standard Minutes / Worked Minutes) × 100
            if worked_minutes > 0:
                efficiency = (standard_minutes / worked_minutes) * 100
                efficiency = round(efficiency, 1)

        # Determine status
        final_status = "paused" if is_paused else "active"

        return {
            "status": final_status,
            "product": po.product_reference if po else "Desconhecido",
            "planning_id": planning.id,
            "pulse_duration": planning.pulse_duration,
            "total_batches": total_batches,
            "current_cycle_start": start_time,
            "now_server": current_time,
            "elapsed_seconds": elapsed_seconds,
            "is_delayed": elapsed_seconds > (planning.pulse_duration * 60),
            "carts_produced": carts_produced,
            "efficiency": efficiency,
            "workstations": allocations
        }
    except Exception as e:
        print(f"Error in get_dashboard_active_status: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Erro ao buscar status: {str(e)}",
            "pulse_duration": 60,
            "elapsed_seconds": 0,
            "carts_produced": 0,
            "workstations": []
        }

@app.post("/api/pso/import", status_code=status.HTTP_201_CREATED)
async def import_pso(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read()
        extracted_data = extractor.process_pdf_with_gpt4(content)
        
        if not extracted_data:
            raise HTTPException(status_code=500, detail="Failed to extract data or no data returned.")
        
        reference = extracted_data.get("referencia")
        product_name = extracted_data.get("produto")
        operations = extracted_data.get("operacoes", [])
        
        if not reference or not operations:
             raise HTTPException(status_code=422, detail="Missing required data (reference or operations) in extraction.")

        product = db.query(models.Product).filter(models.Product.reference == reference).first()
        if not product:
            product = models.Product(
                reference=reference,
                description=product_name
            )
            db.add(product)
            db.commit()
            db.refresh(product)

        existing_psos_count = db.query(models.PSO).filter(models.PSO.product_id == product.id).count()
        version_name = f"V{existing_psos_count + 1}"
        
        pso = models.PSO(
            product_id=product.id,
            version_name=version_name,
            status="Ativa",
            default_efficiency_factor=1.0
        )
        db.add(pso)
        db.commit()
        db.refresh(pso)
        
        for op in operations:
            raw_time_min = op.get("minutos_decimais", 0.0) # Correct key now
            
            new_op = models.Operation(
                pso_id=pso.id,
                sequence=op.get("ordem"),
                description=op.get("descricao"),
                original_machine=op.get("maquina_original"),
                macro_machine=op.get("maquina_macro"),
                time_pdf=raw_time_min,
                time_edited=None,
                final_time=raw_time_min,
                is_active=True  # All imported operations are active by default
            )
            db.add(new_op)
        
        db.commit()
        
        # Calculate total TP for response
        total_tp = sum(op.get("minutos_decimais", 0.0) for op in operations)
        
        return {
            "message": "PSO Importado com sucesso",
            "pso_id": pso.id,
            "product_reference": product.reference,
            "version": pso.version_name,
            "operation_count": len(operations),
            "total_tp_minutes": round(total_tp, 4)
        }

    except Exception as e:
        print(f"Error importing PSO: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pso/save-version", status_code=status.HTTP_201_CREATED)
async def save_pso_version(payload: dict, db: Session = Depends(get_db)):
    """
    Save a new PSO version with edited operations.
    Used by Tela 03 when user edits and saves a PSO version.
    """
    try:
        reference = payload.get("referencia")
        product_name = payload.get("produto")
        version_name = payload.get("version_name")
        efficiency_factor = payload.get("default_efficiency_factor", 1.0) # Get efficiency from payload
        operations = payload.get("operacoes", [])
        
        if not reference or not version_name or not operations:
            raise HTTPException(status_code=422, detail="Missing required data (reference, version_name, or operations).")

        # Get or create product
        product = db.query(models.Product).filter(models.Product.reference == reference).first()
        if not product:
            product = models.Product(
                reference=reference,
                description=product_name or reference
            )
            db.add(product)
            db.commit()
            db.refresh(product)

        # Create new PSO version
        pso = models.PSO(
            product_id=product.id,
            version_name=version_name,
            status="Ativa",
            default_efficiency_factor=efficiency_factor # Save efficiency
        )
        db.add(pso)
        db.commit()
        db.refresh(pso)
        
        # Add ALL operations (both active and inactive)
        total_tp = 0
        active_count = 0
        
        for op in operations:
            raw_time_min = op.get("minutos_decimais", 0.0)
            is_active = op.get("ativa")
            if is_active is None:
                is_active = True # Default to true only if explicitly missing
            
            # Save ALL operations to database
            new_op = models.Operation(
                pso_id=pso.id,
                sequence=op.get("ordem"),
                description=op.get("descricao"),
                original_machine=op.get("maquina_macro"),
                macro_machine=op.get("maquina_macro"),
                time_pdf=raw_time_min,
                time_edited=None,
                final_time=raw_time_min,
                is_active=is_active  # Store active/inactive status
            )
            db.add(new_op)
            
            # Only count active operations in TP total
            if is_active:
                total_tp += raw_time_min
                active_count += 1
        
        db.commit()
        
        return {
            "message": f"Versão '{version_name}' salva com sucesso",
            "pso_id": pso.id,
            "product_reference": product.reference,
            "version": pso.version_name,
            "operation_count": active_count,  # Only active operations
            "total_tp_minutes": round(total_tp, 4)  # Only sum active operations
        }

    except Exception as e:
        print(f"Error saving PSO version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/pso/{pso_id}", status_code=status.HTTP_200_OK)
def delete_pso_version(pso_id: int, db: Session = Depends(get_db)):
    """
    Exclui uma versão específica de PSO e todas as suas operações vinculadas.
    Legacy: Should be replaced by Archive in frontend for safety.
    """
    # 1. Busca a versão no banco
    pso_version = db.query(models.PSO).filter(models.PSO.id == pso_id).first()
    
    if not pso_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Versão de PSO não encontrada."
        )

    try:
        # HARD DELETE
        db.query(models.Operation).filter(models.Operation.pso_id == pso_id).delete()
        db.delete(pso_version)
        db.commit()
        return {"message": f"Versão '{pso_version.version_name}' excluída com sucesso."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ================= Sprint 14: Soft Delete Endpoints =================

@app.put("/api/pso/{pso_id}/archive")
def archive_pso(pso_id: int, db: Session = Depends(get_db)):
    """Soft delete a PSO"""
    pso = db.query(models.PSO).filter(models.PSO.id == pso_id).first()
    if not pso:
        raise HTTPException(404, "PSO not found")
        
    pso.is_archived = True
    pso.status = "Arquivada"
    db.commit()
    return {"message": "PSO arquivada com sucesso"}

@app.put("/api/pso/{pso_id}/restore")
def restore_pso(pso_id: int, db: Session = Depends(get_db)):
    """Restore an archived PSO"""
    pso = db.query(models.PSO).filter(models.PSO.id == pso_id).first()
    if not pso:
        raise HTTPException(404, "PSO not found")
        
    pso.is_archived = False
    pso.status = "Ativa"
    db.commit()
    return {"message": "PSO restaurada com sucesso"}

@app.get("/api/pso/archived")
def get_archived_psos(db: Session = Depends(get_db)):
    """List all archived PSOs"""
    psos = db.query(models.PSO).filter(models.PSO.is_archived == True).all()
    
    result = []
    for pso in psos:
        operations = db.query(models.Operation).filter(models.Operation.pso_id == pso.id).all()
        result.append({
            "pso_id": pso.id,
            "product_reference": pso.product.reference if pso.product else "N/A",
            "version_name": pso.version_name,
            "archived_at": pso.created_at, # Using created_at for sorting basically
            "operations_count": len(operations)
        })
    return result



@app.post("/api/batches/checkout", status_code=status.HTTP_201_CREATED)
def checkout_batch(item: CheckoutRequest, db: Session = Depends(get_db)):
    cart = db.query(models.CartLote).filter(models.CartLote.id == item.batch_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail=f"Cart (Carrinho) with ID {item.batch_id} not found")
    
    op = cart.production_order
    pulse_duration_minutes = op.pulse_duration if op and op.pulse_duration else 60
    
    previous_sequence = cart.sequence_number - 1
    start_time = None
    
    if previous_sequence > 0:
        prev_cart = db.query(models.CartLote).filter(
            models.CartLote.planning_id == cart.planning_id,
            models.CartLote.sequence_number == previous_sequence
        ).first()
        
        if prev_cart:
            prev_tracking = db.query(models.BatchTracking).filter(
                models.BatchTracking.batch_id == prev_cart.id
            ).order_by(desc(models.BatchTracking.checkout_time)).first()
            
            if prev_tracking:
                start_time = prev_tracking.checkout_time
    
    if not start_time and cart.sequence_number == 1 and op:
         start_time = op.created_at

    current_time = datetime.utcnow()
    is_delayed = False
    
    if start_time:
        elapsed = current_time - start_time
        if elapsed > timedelta(minutes=pulse_duration_minutes):
            is_delayed = True

    tracking_record = models.BatchTracking(
        batch_id=item.batch_id,
        planning_id=cart.planning_id,  # ✅ Link directly to session through the cart
        workstation_id=item.workstation_id,
        checkout_time=current_time,
        is_delayed=is_delayed
    )
    
    cart.status = "Concluido" # Mark as Done
    db.add(cart)
    db.add(tracking_record)
    db.commit()
    db.refresh(tracking_record)
    
    # ✅ AUTO-STOP LOGIC: Check if this was the last batch for THIS specific planning session
    remaining_batches = db.query(models.CartLote).filter(
        models.CartLote.planning_id == cart.planning_id,
        models.CartLote.status != "Concluido"
    ).count()
    
    is_last_batch = (remaining_batches == 0)
    
    if is_last_batch:
        # Find the active planning for this production order
        planning = db.query(models.ProductionPlanning).filter(
            models.ProductionPlanning.production_order_id == cart.production_order_id,
            models.ProductionPlanning.is_active == True
        ).first()
        
        if planning:
            # Deactivate the planning
            planning.is_active = False
            
            # Register STOP event
            stop_event = models.ProductionEvent(
                planning_id=planning.id,
                event_type='stop',
                created_at=current_time
            )
            db.add(stop_event)
            db.commit()
            
            print(f"✅ AUTO-STOP: Last batch completed for Planning {planning.id}. Production stopped automatically.")
    
    return {
        "message": "Checkout registered successfully",
        "tracking_id": tracking_record.id,
        "batch_id": tracking_record.batch_id,
        "checkout_time": tracking_record.checkout_time,
        "is_delayed": tracking_record.is_delayed,
        "elapsed_seconds": (current_time - start_time).total_seconds() if start_time else None,
        "is_last_batch": is_last_batch,
        "production_completed": is_last_batch
    }

@app.get("/api/batches/pending")
def get_pending_batches(db: Session = Depends(get_db)):
    """
    Returns pending batches for the active Production Order.
    Used by the Checklist Screen (Page 05).
    
    Returns:
    - po_reference: Product reference from ProductionOrder
    - po_description: Product description (if available)
    - op_code: OP code (from production_orders.code or formatted with ID)
    - batch_size: Batch size from ACTIVE planning (handles rebalancing)
    - batches: List of pending cart/batch objects
    """
    try:
        # 1. Find Active Planning/PO
        planning = db.query(models.ProductionPlanning).filter(
            models.ProductionPlanning.is_active == True
        ).order_by(desc(models.ProductionPlanning.id)).first()

        if not planning:
             return {"batches": [], "po_reference": "N/A", "op_code": "N/A", "batch_size": 0}

        po = db.query(models.ProductionOrder).filter(models.ProductionOrder.id == planning.production_order_id).first()
        
        if not po:
            return {"batches": [], "po_reference": "N/A", "op_code": "N/A", "batch_size": 0}
        
        # Get the PSO to find product description
        pso = None
        product_description = "N/A"
        if planning.pso_id:
            pso = db.query(models.PSO).filter(models.PSO.id == planning.pso_id).first()
            if pso and pso.product:
                product_description = pso.product.description
        
        # 2. Get Pending Carts for THIS planning session
        carts = db.query(models.CartLote).filter(
            models.CartLote.planning_id == planning.id,
            models.CartLote.status == "Aguardando"
        ).order_by(models.CartLote.sequence_number).all()

        return {
            "po_reference": po.product_reference or "N/A",
            "product_description": product_description,  # Description/name of the product
            "op_code": f"OP-{po.id}" if po.id else "OP-N/A",  # Format OP code with ID
            "batch_size": planning.batch_size or 0,  # Gets the batch size from the ACTIVE planning (handles rebalancing)
            "batches": [
                {
                    "id": c.id, 
                    "sequence": c.sequence_number, 
                    "status": c.status,
                    "quantity": c.quantity_pieces
                } for c in carts
            ]
        }
    except Exception as e:
        print(f"Error in get_pending_batches: {e}")
        import traceback
        traceback.print_exc()
        return {"batches": [], "po_reference": "N/A", "op_code": "N/A", "batch_size": 0}

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
    
    # Get the active planning to find operation times and specific targets
    planning = db.query(models.ProductionPlanning).filter(
        models.ProductionPlanning.is_active == True
    ).order_by(desc(models.ProductionPlanning.id)).first()

    # Get target volume from active planning session
    target_volume = 0
    target_batches = 0
    if planning:
        target_batches = db.query(models.CartLote).filter(
            models.CartLote.planning_id == planning.id
        ).count()
        # Get the production order associated with this planning
        po = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.id == planning.production_order_id
        ).first()
        if po:
            target_volume = po.quantity or 0
    
    # Efficiency calculated below using the planning session found above
    
    efficiency_current = 0
    if planning and len(completed_batches) > 1:
        # Get all workstation allocations for this planning
        # WorkstationAllocation uses 'planning_id' to link to ProductionPlanning
        ws_allocations = db.query(models.WorkstationAllocation).filter(
            models.WorkstationAllocation.planning_id == planning.id
        ).all()
        
        if not ws_allocations:
            # No workstation allocations found, efficiency remains 0
            pass
        else:
            # Get all operation allocations through workstation allocations
            ws_ids = [ws.id for ws in ws_allocations]
            op_allocations = db.query(models.OperationAllocation).filter(
                models.OperationAllocation.allocation_id.in_(ws_ids)
            ).all()
            
            # Calculate total standard time (sum of operation times * pieces produced)
            total_standard_minutes = 0
            for cart in carts:
                # Sum all operation times for one piece
                piece_time = 0
                for alloc in op_allocations:
                    operation = db.query(models.Operation).filter(
                        models.Operation.id == alloc.operation_id
                    ).first()
                    if operation and operation.final_time:
                        piece_time += operation.final_time
                
                total_standard_minutes += piece_time * (cart.quantity_pieces or 0)
            
            # Calculate actual elapsed time (first checkout to last checkout)
            # Use shift-aware calculation that excludes lunch breaks
            checkout_times = sorted([b.checkout_time for b in completed_batches])
            if len(checkout_times) >= 2:
                elapsed_time = calculate_working_minutes(db, checkout_times[0], checkout_times[-1])
                
                # Protection against division by zero
                if elapsed_time > 0 and total_standard_minutes > 0:
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
            "early_count": 0, # Future: check checkouts < 80% pulse
            "on_time_count": total_batches - delayed_count,
            "delayed_count": delayed_count,
            "total_count": total_batches,
            "percentage": round(delay_percentage, 1)
        },
        "production_volume": {
            "total_pieces": total_pieces,
            "total_batches": total_batches,
            "avg_pieces_per_hour": round(avg_pieces_per_hour, 1),
            "target_volume": target_volume,
            "target_batches": target_batches
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

@app.get("/")
def health_check():
    return {"status": "ok", "service": "SGP Costura API"}




