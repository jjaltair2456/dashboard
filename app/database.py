import os
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

ROOT_DIR = Path(__file__).resolve().parent.parent

TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

if TURSO_DATABASE_URL and TURSO_AUTH_TOKEN:
    url_conexion = TURSO_DATABASE_URL.replace("libsql://", "sqlite+libsql://")
    if "?secure=true" not in url_conexion:
        url_conexion += "?secure=true"
    engine = create_engine(
        url_conexion,
        connect_args={"auth_token": TURSO_AUTH_TOKEN}
    )
else:
    if os.getenv("VERCEL"):
        db_path = "/tmp/dashboard.db"
        local_db = ROOT_DIR / "dashboard.db"
        
        if local_db.exists() and not os.path.exists(db_path):
            shutil.copy(local_db, db_path)
            
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(
            f"sqlite:///{ROOT_DIR / 'dashboard.db'}",
            connect_args={"check_same_thread": False}
        )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()