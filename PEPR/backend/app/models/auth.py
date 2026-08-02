from sqlalchemy import Column, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import BaseModel

class Role(BaseModel):
    __tablename__ = "roles"
    
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255))
    
    users = relationship("User", back_populates="role")

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role_id = Column(ForeignKey("roles.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    role = relationship("Role", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    
    user_id = Column(ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_name = Column(String(100))
    entity_id = Column(String(100))
    details = Column(Text)
    ip_address = Column(String(50))
    
    user = relationship("User", back_populates="audit_logs")
