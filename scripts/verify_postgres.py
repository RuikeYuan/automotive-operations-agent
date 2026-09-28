"""Verify migrations and idempotent seed against the running local PostgreSQL service."""
import os
os.environ.setdefault("DATABASE_URL","postgresql+psycopg://automotive:local-demo-only@localhost:15432/automotive")
from alembic import command
from alembic.config import Config
from sqlalchemy import select,func,text
from backend.app.db import SessionLocal,engine
from backend.app.db.seed import seed
from backend.app.models import Vehicle,Part,InventoryItem,HistoricalSale,Order


def main():
    assert engine.dialect.name=="postgresql"
    command.upgrade(Config("alembic.ini"),"head")
    with SessionLocal() as session:
        seed(session)
        before = {m.__tablename__:session.scalar(select(func.count()).select_from(m)) for m in [Vehicle,Part,InventoryItem,HistoricalSale,Order]}
        seed(session)
        after = {m.__tablename__:session.scalar(select(func.count()).select_from(m)) for m in [Vehicle,Part,InventoryItem,HistoricalSale,Order]}
        assert before==after
        assert after["vehicles"]==5 and after["parts"]==41 and after["inventory_items"]>=41
        assert after["historical_sales"]==108 and after["orders"]==3
        print({"dialect":engine.dialect.name,"migration":session.scalar(text("SELECT version_num FROM alembic_version")),"seed_counts":after,"idempotent":True})
    command.check(Config("alembic.ini"))


if __name__=="__main__":
    main()

