# backend/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(_env_path, override=True)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///C:/Users/Administrator/Desktop/pharmacrm/pharma_crm.db")

print(f"[DB] DATABASE_URL = {DATABASE_URL}")
print(f"[DB] CWD = {os.getcwd()}")
print(f"[DB] __file__ = {__file__}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    from backend.models import Base as ModelsBase
    ModelsBase.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
