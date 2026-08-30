from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, Float, Text
from sqlalchemy.orm import relationship
import datetime
import enum
from database import Base

# Status ke fixed options define karna
class StatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    WORKER_COMPLETED = "WORKER_COMPLETED"
    REJECTED = "REJECTED"
    VERIFIED_CLOSED = "VERIFIED_CLOSED"

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(50), nullable=False)
    phone_number = Column(String(15), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Connection with complaints hata diya gaya hai error rokne ke liye

class Employee(Base):
    __tablename__ = "employees"
    emp_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    phone_number = Column(String(15), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
    department = Column(String(50))
    warning_count = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)
    
    complaints = relationship("Complaint", back_populates="employee")

class Admin(Base):
    __tablename__ = "admins"
    admin_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)

class Complaint(Base):
    # Table ka naam change kar diya taaki fresh table ban jaye
    __tablename__ = "complaints_new" 
    
    complaint_id = Column(Integer, primary_key=True, index=True)
    
    # ForeignKey hata diya taaki crash na ho
    user_id = Column(Integer) 
    
    emp_id = Column(Integer, ForeignKey("employees.emp_id"), nullable=True)
    category = Column(String(50))
    user_image_url = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING)
    emp_image_url = Column(String(255), nullable=True)
    admin_remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Sirf employee relationship rakhi hai
    employee = relationship("Employee", back_populates="complaints")