from fastapi import FastAPI,HTTPException,APIRouter
from app.schemas.user_schema import UserRegister,UserResponse,UserLogin,LoginResponse

from app.db.base import get_db #provides db session for each request
from app.models.user import User

from fastapi.params import Depends #dependency injection
from sqlalchemy.orm import Session #communication with db

user_router=APIRouter()

@user_router.post('/register',response_model=UserResponse,tags=['Users'])
def add(request:UserRegister,db:Session=Depends(get_db)):
    existing_user=(
        db.query(User)
        .filter(User.email==request.email)
        .first()
    )
    if existing_user is not None:
        raise HTTPException(status_code=404,detail="Email is already registered")

    new_user=User(
        name=request.name,
        email=request.email,
        password=request.password,
        mobile=request.mobile
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@user_router.post('/login',response_model=LoginResponse,tags=['Users'])
def login_user(request:UserLogin,db:Session=Depends(get_db)):
    db_user=db.query(User).filter(User.email==request.email).first()

    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
 
    if db_user.password != request.password:
            raise HTTPException(
                status_code=401,
                detail="invalid Password"
            )
    return {
         "message": "Login Succesfully",
         "user" : db_user
    }