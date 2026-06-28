from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.models.base import Base

class AppUser(Base):
    __tablename__ = "app_users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), unique=True, index=True)
    role = Column(String(50), server_default="researcher", default="researcher")
    institution = Column(String(255))
    interest = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("app_users.id", ondelete="CASCADE"), nullable=False)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    key_prefix = Column(String(12), nullable=False)
    label = Column(String(100), default="Default")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))

class ApiUsageLog(Base):
    __tablename__ = "api_usage_log"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id", ondelete="SET NULL"))
    user_id = Column(Integer, ForeignKey("app_users.id", ondelete="SET NULL"))
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), default="GET")
    status_code = Column(Integer)
    response_time_ms = Column(Float)
    request_params = Column(JSONB)
    response_bytes = Column(Integer)
    ip_address = Column(String(45))
    user_agent = Column(String(512))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
