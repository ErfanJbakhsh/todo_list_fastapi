from fastapi import Depends, APIRouter, HTTPException, Path
import models
from database import SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status
from pydantic import BaseModel, Field
from .auth import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description : str = Field(min_length=0, max_length=100)
    priority: int = Field(gt=0 ,lt=11)
    complete: bool 

@router.get("/")
async def read_all(user: user_dependency, db: db_dependency):
    if user is None: 
        raise HTTPException(status_code=401, detail='Authentication failed')
    return db.query(models.Todos).filter(models.Todos.owner_id == user.get("id")).all()

@router.get("/todo/{todo_id}", status_code= status.HTTP_200_OK)
async def read_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None: 
        raise HTTPException(status_code=401, detail='Authentication failed')
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get("id")).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=404, detail='Item not found')

@router.post("/todo/create", status_code= status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=401, detail= "Authentication failed")
    todo_model = models.Todos(**todo_request.model_dump(), owner_id= user.get('id'))

    db.add(todo_model)
    db.commit()
    return todo_model

@router.put("/todo/update/{todo_id}")
async def update_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest, todo_id: int= Path(gt=0)):
    if user is None:
        raise HTTPException(status_code= 401, detail= "Authentication failed")
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get("id")).first()
    if todo_model is None: 
        raise HTTPException(status_code= 404, detail= "Item not found")
    
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.add(todo_model)
    db.commit()

@router.delete("/todo/delete/{todo_id}")
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int= Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail= "Authentication failed")
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get("id")).first()
    if todo_model is None:
        raise HTTPException(status_code= 404, detail = "Item not found")
    db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get("id")).delete()
    db.commit()
    return {"message": "Todo deleted successfully"}