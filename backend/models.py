from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, index=True)
    description = Column(String)
    psos = relationship("PSO", back_populates="product")

class PSO(Base):
    __tablename__ = "pso"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    version_name = Column(String)
    status = Column(String, default="Ativa")
    default_efficiency_factor = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product", back_populates="psos")
    operations = relationship("Operation", back_populates="pso")

class Operation(Base):
    __tablename__ = "operations"
    id = Column(Integer, primary_key=True, index=True)
    pso_id = Column(Integer, ForeignKey("pso.id"))
    sequence = Column(Integer)
    description = Column(String)
    original_machine = Column(String)
    macro_machine = Column(String)
    time_pdf = Column(Float)
    time_edited = Column(Float, nullable=True)
    final_time = Column(Float)
    is_active = Column(Boolean, default=True)  # Track if operation is active
    pso = relationship("PSO", back_populates="operations")

class Seamstress(Base):
    """
    Tabela: SEAMSTRESS (Costureiras/Operadoras)
    """
    __tablename__ = "seamstresses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    status = Column(String, default="Ativa")
    allocations = relationship("WorkstationAllocation", back_populates="seamstress")

class ProductionOrder(Base):
    __tablename__ = "production_orders"
    id = Column(Integer, primary_key=True, index=True)
    product_reference = Column(String, index=True)
    quantity = Column(Integer)
    status = Column(String, default="Pendente")
    created_at = Column(DateTime, default=datetime.utcnow)
    pulse_duration = Column(Integer, default=60)

class ProductionPlanning(Base):
    """
    Tabela: PRODUCTION_PLANNING (O Metrônomo do Planejamento)
    """
    __tablename__ = "production_planning"
    id = Column(Integer, primary_key=True, index=True)
    production_order_id = Column(Integer, ForeignKey("production_orders.id"))
    version_name = Column(String)
    notes = Column(String)
    pulse_duration = Column(Integer)
    batch_size = Column(Integer)
    total_operators = Column(Integer)
    efficiency_factor = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    allocations = relationship("WorkstationAllocation", back_populates="planning")

class WorkstationAllocation(Base):
    """
    Tabela: WORKSTATION_ALLOCATION (Estação de Trabalho / Costureira)
    """
    __tablename__ = "workstation_allocations"
    id = Column(Integer, primary_key=True, index=True)
    planning_id = Column(Integer, ForeignKey("production_planning.id"))
    seamstress_id = Column(Integer, ForeignKey("seamstresses.id"))
    position_sequence = Column(Integer) # 1 (First station), 2, 3...
    load_time_batch_min = Column(Float, default=0.0)
    
    planning = relationship("ProductionPlanning", back_populates="allocations")
    seamstress = relationship("Seamstress", back_populates="allocations")
    op_allocations = relationship("OperationAllocation", back_populates="workstation")

class OperationAllocation(Base):
    """
    Tabela: OPERATION_ALLOCATION (Operações alocadas na estação)
    """
    __tablename__ = "operation_allocations"
    id = Column(Integer, primary_key=True, index=True)
    allocation_id = Column(Integer, ForeignKey("workstation_allocations.id"))
    operation_id = Column(Integer, ForeignKey("operations.id"))
    executed_quantity = Column(Integer) # Full TL or fraction
    is_fractioned = Column(Boolean, default=False)
    
    workstation = relationship("WorkstationAllocation", back_populates="op_allocations")
    operation = relationship("Operation")

class CartLote(Base):
    __tablename__ = "cart_lote"
    id = Column(Integer, primary_key=True, index=True)
    production_order_id = Column(Integer, ForeignKey("production_orders.id"))
    sequence_number = Column(Integer)
    status = Column(String, default="Aguardando")
    quantity_pieces = Column(Integer)
    production_order = relationship("ProductionOrder")

class BatchTracking(Base):
    __tablename__ = "batch_tracking"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("cart_lote.id")) 
    workstation_id = Column(Integer, nullable=True)
    checkout_time = Column(DateTime, default=datetime.utcnow)
    is_delayed = Column(Boolean, default=False)
    batch = relationship("CartLote")

class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="operator")  # operator, supervisor, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
