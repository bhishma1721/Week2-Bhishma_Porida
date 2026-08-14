from pydantic import BaseModel,EmailStr,Field #data validation library

class UserRegister(BaseModel):
    name:str=Field(...,min_length=1,max_length=50)
    email:EmailStr
    password:str=Field(min_length=5)
    mobile:str=Field(...,min_length=10,max_length=10,pattern=r"^\d{10}$") #here pattern : r"^\d{10}$" its a regular expression (regex) ^ - start of value,\d- digits, {10}-exactly 10 numbers,$-endof value

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    mobile: str
    role: str

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password:str

class LoginResponse(BaseModel):
    message: str
    user: UserResponse

class Token(BaseModel):
    access_token: str
    token_type: str