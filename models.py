from pydantic import BaseModel, EmailStr

class SignupModel(BaseModel):
    email: EmailStr
    password: str
    otp: str

class LoginModel(BaseModel):
    email: EmailStr
    password: str

class RequestOTPModel(BaseModel):
    email: EmailStr
