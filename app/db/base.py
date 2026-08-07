from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
'''
SQLALCHEMY_DATABASE_URL = (
    "postgresql+psycopg2://postgres:8211@Badal@localhost:5432/week2sample"
    
    #write url here 
)
'''

SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:8211%40Badal@localhost:5432/w2casestudy"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency – inject into your routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

 