from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.user import User


SECRET_KEY = (
    "a3070824bd0bada02d3c05f35489f3c69bc6afb3011fd673ed9c065e007fed1f"
)

ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 20


login_router = APIRouter(
    tags=["Login"]
)


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


OAuth2_schema = OAuth2PasswordBearer(
    tokenUrl="/auth/login" #from here it extracts the token
)


def hash_password(password: str) -> str: #hasing a plain text password
    return pwd_context.hash(password)


def verify_password(plain_password: str,hashed_password: str) -> bool:
    #verify the plain password
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def generate_token(data: dict) -> str:
    #generates JWT token
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


@login_router.post("/login")
def login(request: OAuth2PasswordRequestForm = Depends(),db: Session = Depends(get_db)):
    #login using form data
    db_user = (
        db.query(User)
        .filter(User.email == request.username)
        .first()
    )

    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not verify_password(
        request.password,
        db_user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
            headers={"WWW-Authenticate": "Bearer"} #bearer token authentication is used
        )

    access_token = generate_token(
        data={"sub": db_user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


def get_current_user(token: str = Depends(OAuth2_schema),db: Session = Depends(get_db)):
    #validate the token 
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")

        if not email:
            raise credential_exception

    except JWTError:
        raise credential_exception

    db_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if db_user is None:
        raise credential_exception

    return db_user

def require_roles(*allowed_roles: str):
    #authorization
    def role_dependency(
        current_user: User = Depends(get_current_user)
    ):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions"
            )

        return current_user

    return role_dependency