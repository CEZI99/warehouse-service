from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
import time
from sqlalchemy.exc import OperationalError
from sqlalchemy import event

DATABASE_URL = "postgresql+asyncpg://user:password@postgres:5432/warehouse_db"

Base = declarative_base()

class DBMovement(Base):
    __tablename__ = "movements"
    
    id = Column(String, primary_key=True)
    movement_type = Column(String)
    warehouse_id = Column(String)
    product_id = Column(String)
    quantity = Column(Integer)
    timestamp = Column(DateTime)
    related_movement_id = Column(String, nullable=True)

class DBWarehouseStock(Base):
    __tablename__ = "warehouse_stocks"
    
    warehouse_id = Column(String, primary_key=True)
    product_id = Column(String, primary_key=True)
    quantity = Column(Integer)
    last_updated = Column(DateTime)

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