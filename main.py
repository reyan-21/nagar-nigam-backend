from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String
from pydantic import BaseModel
from passlib.context import CryptContext
import cloudinary
import cloudinary.uploader

import models, schemas
from database import Base, engine, SessionLocal

# 1. FastAPI App Initialization
app = FastAPI(title="Nagar Nigam API")

# 2. CORS Middleware (Netlify block hatane ke liye)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# 3. Security & Hashing Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 4. Database Models for Auth
class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255))
    role = Column(String(20)) # 'user', 'worker', ya 'admin'

# Tables auto-create karna
Base.metadata.create_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

# 5. Pydantic Schemas
class AccountCreate(BaseModel):
    email: str
    password: str
    role: str

class LoginRequest(BaseModel):
    email: str
    password: str

# 6. Database Dependency & Cloudinary Config
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

cloudinary.config(
  cloud_name = "hjdp8uik",
  api_key = "393357517292495",
  api_secret = "t2ZN4gZh9HXjf2e4drc7nVd7ofk",
  secure = True
)

# --- 🚀 APIs SHURU HOTE HAIN ---

# Signup API
@app.post("/api/signup")
def signup(account: AccountCreate, db: Session = Depends(get_db)):
    existing = db.query(Account).filter(Account.email == account.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ye Email pehle se registered hai!")
    
    hashed_pw = pwd_context.hash(account.password)
    new_acc = Account(email=account.email, password_hash=hashed_pw, role=account.role)
    db.add(new_acc)
    db.commit()
    return {"message": f"{account.role} account successfully ban gaya!"}

# Strict Role-Based Login API
@app.post("/api/login/{portal_role}")
def login(portal_role: str, req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Account).filter(Account.email == req.email).first()
    
    if not user or not pwd_context.verify(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ya Password galat hai!")
    
    if user.role != portal_role:
        raise HTTPException(status_code=403, detail=f"Access Denied! Aap ek {user.role} hain. Aap {portal_role} portal se login nahi kar sakte.")
        
    return {"message": "Login Success", "user_id": user.id, "role": user.role, "email": user.email}

# Admin Authority API
@app.get("/api/admin/all-users")
def get_all_users(admin_id: int, db: Session = Depends(get_db)):
    admin = db.query(Account).filter(Account.id == admin_id, Account.role == "admin").first()
    if not admin:
        raise HTTPException(status_code=403, detail="Restricted Area: Sirf Admin ko ye data dekhne ki permission hai!")
        
    users = db.query(Account).all()
    result = [{"id": u.id, "email": u.email, "role": u.role} for u in users]
    return result

# Complaint Darj Karna
@app.post("/api/complaints")
def register_complaint(complaint: schemas.ComplaintCreate, db: Session = Depends(get_db)):
    new_complaint = models.Complaint(
        user_id=complaint.user_id,
        category=complaint.category,
        latitude=complaint.latitude,
        longitude=complaint.longitude,
        user_image_url=complaint.user_image_url
    )
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)
    return {"message": "Aapki complaint successfully darj ho gayi hai!", "complaint_id": new_complaint.complaint_id}

# Image Upload (Cloudinary)
@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        result = cloudinary.uploader.upload(file.file)
        return {"message": "Image successfully upload ho gayi!", "url": result.get("secure_url")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

# Admin: Pending Complaints Dekhna
@app.get("/api/admin/complaints/pending")
def get_pending_complaints(db: Session = Depends(get_db)):
    return db.query(models.Complaint).filter(models.Complaint.status == models.StatusEnum.PENDING).all()

# Admin: Free Workers Dekhna
@app.get("/api/admin/employees/available")
def get_available_employees(db: Session = Depends(get_db)):
    return db.query(models.Employee).filter(models.Employee.is_available == True).all()

# Admin: Task Assign Karna
@app.put("/api/admin/complaints/{complaint_id}/assign")
def assign_complaint(complaint_id: int, assign_data: schemas.ComplaintAssign, db: Session = Depends(get_db)):
    complaint = db.query(models.Complaint).filter(models.Complaint.complaint_id == complaint_id).first()
    employee = db.query(models.Employee).filter(models.Employee.emp_id == assign_data.emp_id).first()
    
    if not complaint or not employee:
        raise HTTPException(status_code=404, detail="Complaint ya Employee nahi mila")
        
    complaint.emp_id = assign_data.emp_id
    complaint.status = models.StatusEnum.ASSIGNED
    employee.is_available = False 
    
    db.commit()
    return {"message": f"Complaint worker {assign_data.emp_id} ko assign ho gayi hai"}

# Worker: Kaam Complete Karna
@app.put("/api/employees/complaints/{complaint_id}/complete")
def complete_complaint(complaint_id: int, complete_data: schemas.ComplaintComplete, db: Session = Depends(get_db)):
    complaint = db.query(models.Complaint).filter(models.Complaint.complaint_id == complaint_id).first()
    
    if not complaint or complaint.status != models.StatusEnum.ASSIGNED:
        raise HTTPException(status_code=400, detail="Invalid Action")
        
    complaint.status = models.StatusEnum.WORKER_COMPLETED
    complaint.emp_image_url = complete_data.emp_image_url
    
    if complaint.emp_id:
        employee = db.query(models.Employee).filter(models.Employee.emp_id == complaint.emp_id).first()
        if employee:
            employee.is_available = True
            
    db.commit()
    return {"message": "Kaam successfully complete ho gaya!"}

# Admin: Kaam Verify Karna
@app.put("/api/admin/complaints/{complaint_id}/verify")
def verify_complaint(complaint_id: int, verify_data: schemas.ComplaintVerify, db: Session = Depends(get_db)):
    complaint = db.query(models.Complaint).filter(models.Complaint.complaint_id == complaint_id).first()
    
    if not complaint or complaint.status != models.StatusEnum.WORKER_COMPLETED:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    if verify_data.is_approved:
        complaint.status = models.StatusEnum.VERIFIED_CLOSED
        message = "Case VERIFIED_CLOSED mark ho gaya!"
    else:
        complaint.status = models.StatusEnum.REJECTED
        message = "Kaam reject kar diya gaya hai."
        if complaint.emp_id:
            employee = db.query(models.Employee).filter(models.Employee.emp_id == complaint.emp_id).first()
            if employee:
                employee.warning_count += 1

    complaint.admin_remark = verify_data.admin_remark
    db.commit()
    return {"message": message}