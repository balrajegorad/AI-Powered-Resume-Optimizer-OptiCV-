from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
import random, string, os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 20
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "optimizecv"

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db["users"]

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# === MODELS ===
class SignupRequest(BaseModel):
    email: EmailStr
    password: str

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

class Token(BaseModel):
    access_token: str
    token_type: str

# === UTILS ===
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# === SIGNUP ===
@router.post("/signup")
async def signup(user: SignupRequest):
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    otp = ''.join(random.choices(string.digits, k=6))

    user_data = {
        "email": user.email,
        "password": get_password_hash(user.password),
        "is_verified": False,
        "otp": otp,
    }
    await users_collection.insert_one(user_data)

    print(f"[DEBUG] OTP sent to {user.email}: {otp}")  # Replace with email logic

    return {"message": "User created. Please verify OTP."}

# === OTP VERIFICATION ===
@router.post("/verify-otp")
async def verify_otp(data: OTPVerifyRequest):
    user = await users_collection.find_one({"email": data.email})
    if not user or user.get("otp") != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    await users_collection.update_one(
        {"email": data.email}, {"$set": {"is_verified": True}, "$unset": {"otp": ""}}
    )

    return {"message": "Email verified successfully"}

# === LOGIN ===
@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await users_collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not user.get("is_verified"):
        raise HTTPException(status_code=403, detail="Please verify your email first.")

    access_token = create_access_token(data={"sub": str(user["email"])})
    return {"access_token": access_token, "token_type": "bearer"}

# === CURRENT USER ===
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        user = await users_collection.find_one({"email": email})
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception
