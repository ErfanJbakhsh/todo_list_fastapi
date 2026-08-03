from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel, Field
import models
from database import SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
from .auth import get_current_user
from passlib.context import CryptContext

router = APIRouter(
    prefix= '/user',
    tags= ['user']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated= 'auto')

class UserVerification(BaseModel):
    password: str
    new_password: str = Field(min_length= 3)

@router.get("/")
async def get_user(user: user_dependency, db: db_dependency):
    if user is None: 
        raise HTTPException(status_code= 404, detail='User not found')
    return db.query(models.Users).filter(models.Users.id == user.get("id")).first()
 
@router.put("/password")
async def change_password(user: user_dependency, db: db_dependency, user_verification: UserVerification):
    if user is None: 
        raise HTTPException(status_code= 404, detail='User not found')
    user_model = db.query(models.Users).filter(models.Users.id == user.get("id")).first()
    if not bcrypt_context.verify(user_verification.password, user_model.hashed_password):
        raise HTTPException(status_code= 401, detail='Error on password change')
    user_model.hashed_password = bcrypt_context.hash(user_verification.new_password)
    db.add(user_model)
    db.commit()