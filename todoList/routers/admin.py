from fastapi import Depends, APIRouter, HTTPException
import models
from database import SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
from .auth import get_current_user

router = APIRouter(
    prefix= '/admin',
    tags= ['admin']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get("/todos")
async def get_todos_as_admin(user: user_dependency, db: db_dependency):
    if user is None or user.get("user_role") != "admin": 
        raise HTTPException(status_code= 401, detail= 'Authentication failed')
    return db.query(models.Todos).all()

@router.delete("/todos/{todo_id}")
async def delete_todos_as_admin(user: user_dependency, todo_id: int, db: db_dependency):
    if user is None or user.get("user_role") != "admin": 
        raise HTTPException(status_code= 401, detail= 'Authentication failed')
    chosen_todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if chosen_todo is None: 
        raise HTTPException(status_code=404, detail='Todo not found')
    db.query(models.Todos).filter(models.Todos.id == todo_id).delete()
    db.commit()