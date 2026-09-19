"""
Database Connection Manager for Employee Analytics.
Supports PostgreSQL (via psycopg2) with seamless automatic fallback to SQLite.
"""

import os
from pathlib import Path
from typing import Tuple
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE_PATH = BASE_DIR / "data" / "employee_analytics.db"

def get_database_url() -> Tuple[str, str]:
    """
    Determines Database URL from environment variables.
    Returns: (db_url, db_type)
    """
    # 1. Direct DATABASE_URL
    custom_url = os.getenv("DATABASE_URL")
    if custom_url and custom_url.strip():
        db_type = "postgresql" if "postgres" in custom_url else "other"
        return custom_url.strip(), db_type

    # 2. PostgreSQL structured credentials
    db_type = os.getenv("DB_TYPE", "").lower().strip()
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "employee_db")

    if db_type == "postgresql" and db_user and db_password:
        url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        return url, "postgresql"

    # 3. Default to SQLite
    DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    sqlite_url = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
    return sqlite_url, "sqlite"

def get_engine(custom_url: str = None) -> Tuple[Engine, str, str]:
    """
    Creates and validates an SQLAlchemy engine.
    If a requested PostgreSQL connection fails, it falls back to SQLite.
    
    Returns: (engine, db_type, status_message)
    """
    if custom_url:
        url = custom_url
        db_type = "postgresql" if "postgres" in url else "sqlite"
    else:
        url, db_type = get_database_url()

    # Try connecting to the specified DB
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine, db_type, f"Connected to {db_type.upper()} successfully."
    except Exception as exc:
        # Fallback to SQLite if PostgreSQL fails
        if db_type == "postgresql":
            fallback_path = DEFAULT_SQLITE_PATH
            fallback_path.parent.mkdir(parents=True, exist_ok=True)
            fallback_url = f"sqlite:///{fallback_path.as_posix()}"
            fallback_engine = create_engine(fallback_url)
            return fallback_engine, "sqlite", f"PostgreSQL unavailable ({exc.args[0] if exc.args else 'connection error'}). Fallback to local SQLite active."
        else:
            raise exc

def test_db_connection(url: str) -> Tuple[bool, str]:
    """Tests if a given database URL is reachable."""
    try:
        eng = create_engine(url, pool_pre_ping=True)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Connection successful!"
    except Exception as e:
        return False, str(e)
