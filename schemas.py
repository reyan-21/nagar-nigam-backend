from pydantic import BaseModel

class UserCreate(BaseModel):
    full_name: str
    phone_number: str
    password: str

    # schemas.py ke neeche ye add karo
class UserLogin(BaseModel):
    phone_number: str
    password: str

class ComplaintCreate(BaseModel):
    user_id: int
    category: str
    latitude: float
    longitude: float
    user_image_url: str = "" # URL format me aayega

class ComplaintAssign(BaseModel):
    emp_id: int

class ComplaintComplete(BaseModel):
    emp_image_url: str

from typing import Optional

class ComplaintVerify(BaseModel):
    is_approved: bool
    admin_remark: Optional[str] = ""