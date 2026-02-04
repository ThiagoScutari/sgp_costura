from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
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

# Re-create database tables (Note: In production this should be a migration)
# We drop all to apply schema changes effectively for dev/sprint 0
# models.Base.metadata.drop_all(bind=engine) # Keeping commented as per "no data loss"
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SGP Costura API - Sprint 7.0")

# Enable CORS for Frontend Development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shift Configuration
SHIFT_CONFIG = {
    "start_time": "07:00",
    "end_time": "17:00",
    "lunch_start": "12:00",
    "lunch_end": "13:00"
}

def calculate_working_minutes(start_dt: datetime, end_dt: datetime) -> float:
    """
    Calculate actual working minutes between two datetimes,
    excluding lunch breaks that fall within the period.
    """
    total_minutes = (end_dt - start_dt).total_seconds() / 60
    
    # Check if lunch period falls within the work period
    lunch_start = time(12, 0)  # 12:00
    lunch_end = time(13, 0)    # 13:00
    
    # If the work period crosses lunch time, subtract 60 minutes
    if start_dt.time() < lunch_end and end_dt.time() > lunch_start:
        # Check if lunch period is fully contained
        if start_dt.time() <= lunch_start and end_dt.time() >= lunch_end:
            total_minutes -= 60  # Full lunch break
        else:
            # Partial lunch overlap (calculate intersection)
            lunch_overlap_start = max(start_dt.time(), lunch_start)
            lunch_overlap_end = min(end_dt.time(), lunch_end)
            
            overlap_minutes = (
                datetime.combine(start_dt.date(), lunch_overlap_end) -
                datetime.combine(start_dt.date(), lunch_overlap_start)
            ).total_seconds() / 60
            
            total_minutes -= overlap_minutes
    
    return max(total_minutes, 0)  # Never return negative

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
    version_name: Optional[str] = None
    notes: Optional[str] = None
    pulse_duration: Optional[int] = 60
    batch_size: Optional[int] = None


@app.on_event("startup")
def startup_event():
    # Basic seeding
    db = next(get_db())
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
        for pso in product.psos:
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
    # 1. Get Seamstresses
    seamstresses = db.query(models.Seamstress).filter(models.Seamstress.status == "Ativa").all()
    
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
    
    return {
        "seamstresses": [{"id": s.id, "nome": s.name} for s in seamstresses],
        "pso": {
            "id": pso.id if pso else None,
            "product": pso.product.reference if pso else None,
            "product_reference": pso.product.reference if pso else None, # Ensure compatibility field
            "operations": operations
        } if pso else None
    }

@app.post("/api/planning/sync")
def sync_planning(data: PlanningSyncRequest, db: Session = Depends(get_db)):
    """
    Saves the current state of Kanban board.
    Creates a new ProductionPlanning version or updates existing active one.
    """
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
        
        new_planning = models.ProductionPlanning(
            production_order_id=po.id,
            version_name=data.version_name or f"Plan-{datetime.utcnow().strftime('%Y%m%d-%H%M')}",
            pulse_duration=data.pulse_duration or po.pulse_duration,
            batch_size=data.batch_size,
            notes=data.notes,
            total_operators=len({a.workstation_id for a in data.allocations if a.workstation_id is not None}),
            is_active=True
        )
        db.add(new_planning)
        db.flush()

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

                # Find the operation to get details if needed, or just link
                op_alloc = models.OperationAllocation(
                    allocation_id=ws_alloc.id,
                    operation_id=alloc_item.operation_id,
                    executed_quantity=alloc_item.quantity,
                    is_fractioned=True if alloc_item.quantity < po.quantity else False # Simple logic for now
                    # Note: "quantity" in frontend seems to be Batch Quantity (TL). 
                    # Use passed quantity.
                )
                db.add(op_alloc)

        db.commit()
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


@app.get("/api/planning/published")
def get_published_plannings(db: Session = Depends(get_db)):
    """
    Get all products that have published balancing plans.
    Used when clicking CARREGAR button.
    """
    try:
        # Get all production orders that have plannings
        orders_with_planning = db.query(models.ProductionOrder).join(
            models.ProductionPlanning,
            models.ProductionOrder.id == models.ProductionPlanning.production_order_id
        ).distinct().all()
        
        ops = []
        for po in orders_with_planning:
            # Get PSO for this product
            pso = db.query(models.PSO).join(models.Product).filter(
                models.Product.reference == po.product_reference
            ).order_by(desc(models.PSO.id)).first()
            
            if not pso:
                continue
            
            # Get all plannings for this PO
            plannings = db.query(models.ProductionPlanning).filter(
                models.ProductionPlanning.production_order_id == po.id
            ).order_by(desc(models.ProductionPlanning.created_at)).all()
            
            versions = []
            for idx, planning in enumerate(reversed(plannings)):
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
            
            ops.append({
                "pso_id": pso.id,
                "product_reference": pso.product.reference,
                "product_description": pso.product.description,
                "version_count": len(versions),
                "versions": list(reversed(versions))  # Newest first
            })
        
        return {"ops": ops}
        
    except Exception as e:
        print(f"Error getting published plannings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        
        # Get PSO
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
        
        return {
            "planning_id": planning.id,
            "pso_id": pso.id if pso else None,
            "version_number": version_number,
            "version_name": planning.version_name,
            "notes": planning.notes,
            "pulse_duration": planning.pulse_duration,
            "batch_size": planning.batch_size,
            "created_at": planning.created_at.isoformat() if planning.created_at else None,
            "allocations": allocations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting planning detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Existing Endpoints ---

@app.get("/api/dashboard/active-status")
def get_dashboard_active_status(db: Session = Depends(get_db)):
    """
    Returns real-time status for the Factory Dashboard (Monitor).
    Includes: Active Planning, Last Checkout Time, Pulse Status, Seamstress Allocations
    """
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
    
    # 2. Get Last Checkout (Pulse Reference)
    last_tracking = db.query(models.BatchTracking).join(models.CartLote).filter(
        models.CartLote.production_order_id == po.id
    ).order_by(desc(models.BatchTracking.checkout_time)).first()

    # Determine start time for the current cycle
    start_time = None
    carts_produced = 0
    
    if last_tracking:
        start_time = last_tracking.checkout_time
        carts_produced = db.query(models.BatchTracking).join(models.CartLote).filter(
             models.CartLote.production_order_id == po.id
        ).count()
    else:
        start_time = planning.created_at

    current_time = datetime.utcnow()
    elapsed_seconds = (current_time - start_time).total_seconds() if start_time else 0
    
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

    return {
        "status": "active",
        "product": po.product_reference if po else "Desconhecido",
        "planning_id": planning.id,
        "pulse_duration": planning.pulse_duration,
        "current_cycle_start": start_time,
        "now_server": current_time,
        "elapsed_seconds": elapsed_seconds,
        "is_delayed": elapsed_seconds > (planning.pulse_duration * 60),
        "carts_produced": carts_produced,
        "workstations": allocations
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
    """
    # 1. Busca a versão no banco
    pso_version = db.query(models.PSO).filter(models.PSO.id == pso_id).first()
    
    if not pso_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Versão de PSO não encontrada."
        )

    try:
        # 2. Exclui as operações vinculadas primeiro (evita erro de chave estrangeira)
        db.query(models.Operation).filter(models.Operation.pso_id == pso_id).delete()
        
        # 3. Exclui a versão do PSO
        db.delete(pso_version)
        
        # 4. Confirma a transação
        db.commit()
        
        return {"message": f"Versão '{pso_version.version_name}' excluída com sucesso."}
        
    except Exception as e:
        db.rollback()
        print(f"Erro ao excluir versão: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao excluir a versão do banco de dados."
        )

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
            models.CartLote.production_order_id == cart.production_order_id,
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
        workstation_id=item.workstation_id,
        checkout_time=current_time,
        is_delayed=is_delayed
    )
    
    cart.status = "Concluido" # Mark as Done
    db.add(cart)
    db.add(tracking_record)
    db.commit()
    db.refresh(tracking_record)
    
    return {
        "message": "Checkout registered successfully",
        "tracking_id": tracking_record.id,
        "batch_id": tracking_record.batch_id,
        "checkout_time": tracking_record.checkout_time,
        "is_delayed": tracking_record.is_delayed,
        "elapsed_seconds": (current_time - start_time).total_seconds() if start_time else None
    }

@app.get("/api/batches/pending")
def get_pending_batches(db: Session = Depends(get_db)):
    """
    Returns pending batches for the active Production Order.
    Used by the Checklist Screen (Page 05).
    """
    # 1. Find Active Planning/PO
    planning = db.query(models.ProductionPlanning).filter(
        models.ProductionPlanning.is_active == True
    ).order_by(desc(models.ProductionPlanning.id)).first()

    if not planning:
         return {"batches": []}

    po = db.query(models.ProductionOrder).filter(models.ProductionOrder.id == planning.production_order_id).first()
    
    # 2. Get Pending Carts
    carts = db.query(models.CartLote).filter(
        models.CartLote.production_order_id == po.id,
        models.CartLote.status != "Concluido"
    ).order_by(models.CartLote.sequence_number).all()

    # If no carts exist, create them? (For simulation purposes)
    if not carts and po:
        # Check if we should generate some?
        # Sprint 4 assumption: we might need to "generate" carts if none exist.
        pass

    return {
        "po_reference": po.product_reference,
        "batches": [
            {
                "id": c.id, 
                "sequence": c.sequence_number, 
                "status": c.status,
                "quantity": c.quantity_pieces
            } for c in carts
        ]
    }

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
    
    # Get target volume from active Production Order
    target_volume = 0
    if planning:
        # Get the production order associated with this planning
        po = db.query(models.ProductionOrder).filter(
            models.ProductionOrder.id == planning.production_order_id
        ).first()
        if po:
            target_volume = po.quantity or 0
    
    # Calculate efficiency (Standard Time vs Actual Time)
    # Get the active planning to find operation times
    planning = db.query(models.ProductionPlanning).filter(
        models.ProductionPlanning.is_active == True
    ).order_by(desc(models.ProductionPlanning.id)).first()
    
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
                elapsed_time = calculate_working_minutes(checkout_times[0], checkout_times[-1])
                
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
            "delayed_count": delayed_count,
            "total_count": total_batches,
            "percentage": round(delay_percentage, 1)
        },
        "production_volume": {
            "total_pieces": total_pieces,
            "total_batches": total_batches,
            "avg_pieces_per_hour": round(avg_pieces_per_hour, 1),
            "target_volume": target_volume
        },
        "hourly_breakdown": hourly_breakdown
    }

@app.get("/")
def health_check():
    return {"status": "ok", "service": "SGP Costura API"}
