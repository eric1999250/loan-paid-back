from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import get_db, User
import secrets
import hashlib

# Security Configuration
SECRET_KEY = secrets.token_urlsafe(32)  # Generate a secure secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
RESET_TOKEN_EXPIRE_MINUTES = 60

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # Hash with SHA-256 first to handle any password length
    password_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return pwd_context.verify(password_hash, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Hash with SHA-256 first to handle any password length
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return pwd_context.hash(password_hash)

# Token utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_reset_token() -> str:
    """Create a password reset token"""
    return secrets.token_urlsafe(32)

def generate_reset_token() -> str:
    """Generate a password reset token (alias for create_reset_token)"""
    return secrets.token_urlsafe(32)

# User authentication
def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user by username/email and password"""
    # Try to find user by username first
    user = db.query(User).filter(User.username == username).first()
    
    # If not found, try to find by email
    if not user:
        user = db.query(User).filter(User.email == username).first()
    
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, email: str, username: str, password: str, full_name: Optional[str] = None) -> User:
    """Create a new user"""
    hashed_password = get_password_hash(password)
    db_user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
        is_active=True,
        is_verified=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Current user dependency
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Password reset utilities
def set_reset_token(db: Session, user: User) -> str:
    """Generate and set a password reset token for a user"""
    reset_token = create_reset_token()
    user.reset_token = reset_token
    user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    db.commit()
    return reset_token

def verify_reset_token(db: Session, token: str) -> Optional[User]:
    """Verify a password reset token and return the user"""
    user = db.query(User).filter(User.reset_token == token).first()
    
    if not user:
        return None
    
    if user.reset_token_expiry < datetime.utcnow():
        # Token expired
        user.reset_token = None
        user.reset_token_expiry = None
        db.commit()
        return None
    
    return user

def reset_password(db: Session, user: User, new_password: str) -> bool:
    """Reset a user's password"""
    user.hashed_password = get_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.commit()
    return True