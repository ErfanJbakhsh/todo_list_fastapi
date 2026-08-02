from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from models import Users
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from dotenv import load_dotenv
import os

router = APIRouter(
    prefix= '/auth',
    tags= ['auth']
)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated= 'auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='/auth/token')

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

class CreateUserRequest(BaseModel):
    email : str
    username : str
    first_name : str
    last_name : str 
    password : str
    role : str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

def authenticate_user(username: str, password: str, db: db_dependency):
    user = db.query(Users).filter(Users.username == username).first()
    if not user: 
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode= {"sub": username, "id": user_id, "role": role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm= ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try: 
        payload = jwt.decode(token, SECRET_KEY, algorithms= [ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role : str = payload.get('role')
        if username is None or user_id is None or user_role is None:
            raise HTTPException(status_code= 401, detail= "Could not validate user")
        return {'username': username, 'id': user_id, 'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code= 401, detail= "Could not validate user")

@router.get("/users")
async def get_users(db: db_dependency):
    users = db.query(Users).all()
    return users

@router.post("/auth")
async def create_user(db: db_dependency, create_user_request: CreateUserRequest): 
    new_user = Users(
        email = create_user_request.email,
        username = create_user_request.username,
        first_name = create_user_request.first_name,
        last_name = create_user_request.last_name,
        hashed_password = bcrypt_context.hash(create_user_request.password),
        role = create_user_request.role
    )
    db.add(new_user)
    db.commit()

@router.post("/token")
async def login_for_access_token(db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user: 
        raise HTTPException(status_code= 401, detail= "Could not validate user")
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))
    return {"access_token": token, "token_type": "bearer"}