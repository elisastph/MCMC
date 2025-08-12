from __future__ import annotations
import os
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

def _normalize_db_url(url: str | None) -> str:
    """
    Akzeptiert:
      - postgres://... (wandelt um)
      - postgresql://...
      - postgresql+psycopg2://...
      - sqlite:///...
    Setzt sslmode=require, wenn Managed-DB üblich.
    """
    if not url:
        # Fallback: lokale SQLite-Datei (funktioniert überall)
        os.makedirs("var", exist_ok=True)
        return "sqlite:///var/app.db"

    # Heroku/Supabase liefern manchmal 'postgres://'
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

    # Falls bereits Query-Params da sind, sslmode nicht doppeln
    if url.startswith("postgresql+psycopg2://") and "sslmode=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"
    return url

def get_database_url() -> str:
    # 1) Streamlit Secrets (Cloud)
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            return _normalize_db_url(st.secrets["DATABASE_URL"])
    except Exception:
        pass
    # 2) ENV (lokal / CI)
    return _normalize_db_url(os.getenv("DATABASE_URL"))

def create_engine_for_env():
    url = get_database_url()
    # In Serverless-Umgebungen (Streamlit Cloud) besser NullPool (kurzlebige Verbindungen)
    use_null_pool = url.startswith("postgresql+psycopg2://")
    engine = create_engine(
        url,
        echo=os.getenv("SQL_ECHO", "0") == "1",
        future=True,
        pool_pre_ping=True,
        poolclass=NullPool if use_null_pool else None,
    )

    # SQLite: Foreign Keys aktivieren
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _fk_on_connect(dbapi_conn, _):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON;")
            cur.close()

    return engine

# Ein einzelner Engine pro Prozess (in Streamlit cachen!)
_engine = None
def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine_for_env()
    return _engine

SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def healthcheck() -> bool:
    from sqlalchemy import text
    try:
        with get_engine().connect() as c:
            c.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"[DB] Healthcheck failed: {e}")
        return False
