
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from uuid import UUID

from core.config import Settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthService:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.settings.jwt_expire_minutes)
        to_encode.update({"exp": expire, "sub": "access"})
        encoded_jwt = jwt.encode(to_encode, self.settings.jwt_secret_key, algorithm=self.settings.jwt_algorithm)
        return encoded_jwt
    
    def decode_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            decoded_token = jwt.decode(token, self.settings.jwt_secret_key, algorithms=[self.settings.jwt_algorithm])
            return decoded_token
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def get_current_user(self, token: str = Security(oauth2_scheme)) -> Dict[str, Any]:
        payload = self.decode_access_token(token)
        if not payload or "user_id" not in payload:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        # In a real application, you would fetch the user from the database here
        # For now, we'll return a mock user
        return {"id": UUID(payload["user_id"]), "email": payload["email"], "role": payload["role"]}


