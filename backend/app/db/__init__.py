from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from backend.app.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


def make_engine(url):
    engine = create_engine(url, pool_pre_ping=True, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def enable_fk(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
    return engine


engine = make_engine(DATABASE_URL)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_session():
    with SessionLocal() as session:
        yield session

