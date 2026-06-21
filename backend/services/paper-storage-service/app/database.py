"""
Database configuration and connection helpers.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

MYSQL_USER = os.getenv("MYSQL_USER", "researchgo_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "researchgo123")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "researchgo")

SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    connect_args={"init_command": "SET time_zone = '+08:00'"},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_paper_status_columns()


def _ensure_paper_status_columns():
    inspector = inspect(engine)
    try:
        columns = {column["name"] for column in inspector.get_columns("papers")}
    except Exception:
        return

    statements = []
    if "processing_status" not in columns:
        statements.append(
            "ALTER TABLE papers "
            "ADD COLUMN processing_status VARCHAR(50) NOT NULL DEFAULT 'uploaded'"
        )
    if "processing_error" not in columns:
        statements.append("ALTER TABLE papers ADD COLUMN processing_error TEXT NULL")
    if "indexed_at" not in columns:
        statements.append("ALTER TABLE papers ADD COLUMN indexed_at DATETIME NULL")
    if "chunks_created" not in columns:
        statements.append(
            "ALTER TABLE papers ADD COLUMN chunks_created INT NOT NULL DEFAULT 0"
        )

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
