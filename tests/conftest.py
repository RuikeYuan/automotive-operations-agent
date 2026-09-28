import pytest
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from backend.app.db import Base, make_engine, get_session
from backend.app.db.seed import seed
from backend.app.main import app


@pytest.fixture
def session(tmp_path,monkeypatch):
    monkeypatch.setenv("DEMO_MODE","true")
    monkeypatch.setenv("MARKETPLACE_FAIL","false")
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine,expire_on_commit=False)
    with factory() as session:
        seed(session)
        yield session
    engine.dispose()


@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

