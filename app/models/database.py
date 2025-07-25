from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, Integer, DateTime, CheckConstraint
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", None)

Base = declarative_base()

class DBMovement(Base):
    __tablename__ = "movements"

    movement_id = Column(String(36), primary_key=True)
    movement_type = Column(String(10), primary_key=True)
    warehouse_id = Column(String(36), nullable=False)
    product_id = Column(String(36), nullable=False)
    quantity = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    processed_at = Column(DateTime(timezone=True), default=datetime.now)
    source = Column(String(10), nullable=False)
    destination = Column(String(50), nullable=False)
    related_warehouse_id = Column(String(36), nullable=True)

    __table_args__ = (
        CheckConstraint("movement_type IN ('arrival', 'departure')", name="ck_movement_type"),
        CheckConstraint("quantity > 0", name="ck_positive_quantity"),
    )

class DBWarehouseStock(Base):
    __tablename__ = "warehouse_stocks"

    warehouse_id = Column(String(36), primary_key=True)
    product_id = Column(String(36), primary_key=True)
    quantity = Column(Integer, nullable=False, default=0)
    last_updated = Column(DateTime(timezone=True),
                      default=datetime.now,
                      onupdate=datetime.now)

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_non_negative_quantity"),
    )


engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
