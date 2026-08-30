from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
import models, schemas
from database import engine, SessionLocal
import cloudinary
import cloudinary.uploader
from fastapi.middleware.cors import CORSMiddleware # Ye nayi line hai

from pydantic import BaseModel
from passlib.context import CryptContext
from fastapi import HTTPException, Depends

# Password Hashing Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 1. Database Model (Accounts Table)
class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255))
    role = Column(String(20)) # yahan 'user', 'worker', ya 'admin' save hoga

# Is line se nayi table automatically database me ban jayegi
Base.metadata.create_all(bind=engine)

# 2. Pydantic Schemas (Data aane ka format)
class AccountCreate(BaseModel):
    email: str
    password: str
    role: str

class LoginRequest(BaseModel):
    email: str
    password: str

# --- SECURITY APIs ---

# Signup API (Account banane ke liye)
@app.post("/api/signup")
def signup(account: AccountCreate, db: Session = Depends(get_db)):
    # Check karein ki email pehle se toh nahi hai
    existing = db.query(Account).filter(Account.email == account.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ye Email pehle se registered hai!")
    
    # Password ko encrypt (hash) karke save karna
    hashed_pw = pwd_context.hash(account.password)
    new_acc = Account(email=account.email, password_hash=hashed_pw, role=account.role)
    db.add(new_acc)
    db.commit()
    return {"message": f"{account.role} account successfully ban gaya!"}

# Strict Login API (Cross-portal login rokne ke liye)
@app.post("/api/login/{portal_role}")
def login(portal_role: str, req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Account).filter(Account.email == req.email).first()
    
    # Email ya Password galat hone par
    if not user or not pwd_context.verify(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ya Password galat hai!")
    
    # Strict Role Check (Ye rokega user ko admin panel me aane se)
    if user.role != portal_role:
        raise HTTPException(status_code=403, detail=f"Access Denied! Aap ek {user.role} hain. Aap {portal_role} portal se login nahi kar sakte.")
        
    return {"message": "Login Success", "user_id": user.id, "role": user.role, "email": user.email}

# Admin Authority API (Sirf Admin saare users dekh sakta hai)
@app.get("/api/admin/all-users")
def get_all_users(admin_id: int, db: Session = Depends(get_db)):
    # Security check: Pata karo ki maangne wala sach me admin hai ya nahi
    admin = db.query(Account).filter(Account.id == admin_id, Account.role == "admin").first()
    if not admin:
        raise HTTPException(status_code=403, detail="Restricted Area: Sirf Admin ko ye data dekhne ki permission hai!")
        
    users = db.query(Account).all()
    # Pura data return karne se pehle security ke liye password_hash hata do
    result = [{"id": u.id, "email": u.email, "role": u.role} for u in users]
    return result
# Tables auto-create karna
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nagar Nigam API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Har HTML file se request accept karega
    allow_credentials=True,
    allow_methods=["*"], # OPTIONS, POST, GET sab allow kar dega
    allow_headers=["*"],
)

# Database connection (Session) lene ka function
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Yahan apne asli credentials daalna
cloudinary.config(
  cloud_name = "hjdp8uik",
  api_key = "393357517292495",
  api_secret = "t2ZN4gZh9HXjf2e4drc7nVd7ofk",
  secure = True
)

@app.post("/api/users/register")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Check karo ki is phone number se pehle koi account toh nahi hai
    existing_user = db.query(models.User).filter(models.User.phone_number == user.phone_number).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Ye phone number pehle se registered hai!")

    # 2. Naya user database object banao
    new_user = models.User(
        full_name=user.full_name,
        phone_number=user.phone_number,
        password=user.password  # Aage chal kar hum is password ko encrypt (hash) karenge
    )

    # 3. Database me save karo
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User successfully register ho gaya!", "user_id": new_user.user_id}

@app.post("/api/users/login")
def login_user(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    # 1. Database mein phone number se user ko dhoondo
    user = db.query(models.User).filter(models.User.phone_number == user_credentials.phone_number).first()
    
    # 2. Agar us phone number se koi user nahi mila
    if not user:
        raise HTTPException(status_code=404, detail="Is phone number se koi account nahi mila!")
        
    # 3. Agar password match nahi karta hai
    if user.password != user_credentials.password:
        raise HTTPException(status_code=401, detail="Galat password! Kripya dobara try karein.")
        
    # 4. Agar sab sahi hai, toh login successful
    return {
        "message": "Login successful!", 
        "user_id": user.user_id, 
        "name": user.full_name
    }
@app.post("/api/complaints")
def register_complaint(complaint: schemas.ComplaintCreate, db: Session = Depends(get_db)):
    # Nayi complaint ka object banana
    new_complaint = models.Complaint(
        user_id=complaint.user_id,
        category=complaint.category,
        latitude=complaint.latitude,
        longitude=complaint.longitude,
        user_image_url=complaint.user_image_url
    )
    
    # Database me save karna
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)
    
    return {
        "message": "Aapki complaint successfully darj ho gayi hai!", 
        "complaint_id": new_complaint.complaint_id
    }
@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        # FastAPI se file lekar direct Cloudinary par upload karna
        result = cloudinary.uploader.upload(file.file)
        
        # Cloudinary se jo public URL mila, use nikalna
        image_url = result.get("secure_url")
        
        return {"message": "Image successfully upload ho gayi!", "url": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

    # 1. Saari PENDING complaints dekhne ke liye
@app.get("/api/admin/complaints/pending")
def get_pending_complaints(db: Session = Depends(get_db)):
    pending_complaints = db.query(models.Complaint).filter(models.Complaint.status == models.StatusEnum.PENDING).all()
    return pending_complaints

# 2. Jo workers abhi free hain (is_available = True), unki list dekhne ke liye
@app.get("/api/admin/employees/available")
def get_available_employees(db: Session = Depends(get_db)):
    free_employees = db.query(models.Employee).filter(models.Employee.is_available == True).all()
    return free_employees

# 3. Kisi specific complaint ko kisi worker ko assign karne ke liye
@app.put("/api/admin/complaints/{complaint_id}/assign")
def assign_complaint(complaint_id: int, assign_data: schemas.ComplaintAssign, db: Session = Depends(get_db)):
    # Complaint dhoondo
    complaint = db.query(models.Complaint).filter(models.Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint nahi mili")
    
    # Worker dhoondo
    employee = db.query(models.Employee).filter(models.Employee.emp_id == assign_data.emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee nahi mila")
        
    # Data update karo
    complaint.emp_id = assign_data.emp_id
    complaint.status = models.StatusEnum.ASSIGNED
    employee.is_available = False # Worker ab us kaam me busy ho gaya
    
    db.commit()
    return {"message": f"Complaint {complaint_id} worker {assign_data.emp_id} ko successfully assign ho gayi hai"}

@app.put("/api/employees/complaints/{complaint_id}/complete")
def complete_complaint(complaint_id: int, complete_data: schemas.ComplaintComplete, db: Session = Depends(get_db)):
    # 1. Complaint dhoondo
    complaint = db.query(models.Complaint).filter(models.Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint nahi mili")
    
    if complaint.status != models.StatusEnum.ASSIGNED:
        raise HTTPException(status_code=400, detail="Ye kaam abhi assign nahi hua hai ya pehle hi close ho chuka hai")
        
    # 2. Data aur Status update karo
    complaint.status = models.StatusEnum.WORKER_COMPLETED
    complaint.emp_image_url = complete_data.emp_image_url
    
    # 3. Worker ko wapas free (available) kar do taaki use naya kaam mil sake
    if complaint.emp_id:
        employee = db.query(models.Employee).filter(models.Employee.emp_id == complaint.emp_id).first()
        if employee:
            employee.is_available = True
            
    db.commit()
    return {"message": "Kaam successfully complete ho gaya aur photo upload ho gayi!"}

@app.put("/api/admin/complaints/{complaint_id}/verify")
def verify_complaint(complaint_id: int, verify_data: schemas.ComplaintVerify, db: Session = Depends(get_db)):
    # 1. Complaint dhoondo
    complaint = db.query(models.Complaint).filter(models.Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint nahi mili")
    
    # 2. Check karo ki worker ne photo upload ki hai ya nahi
    if complaint.status != models.StatusEnum.WORKER_COMPLETED:
        raise HTTPException(status_code=400, detail="Worker ne abhi tak kaam complete nahi kiya hai")
        
    # 3. Agar admin ne kaam accept kiya
    if verify_data.is_approved:
        complaint.status = models.StatusEnum.VERIFIED_CLOSED
        message = "Case successfully VERIFIED_CLOSED mark ho gaya hai!"
    
    # 4. Agar admin ne fake photo dekh kar reject kiya
    else:
        complaint.status = models.StatusEnum.REJECTED
        message = "Kaam reject kar diya gaya hai aur worker ko warning mil gayi hai."
        # Worker ko dhoond kar uska warning count badhao
        if complaint.emp_id:
            employee = db.query(models.Employee).filter(models.Employee.emp_id == complaint.emp_id).first()
            if employee:
                employee.warning_count += 1

    # Admin ka comment (remark) save karo
    complaint.admin_remark = verify_data.admin_remark
    db.commit()
    
    return {"message": message}