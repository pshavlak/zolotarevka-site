"""Debug: check if tables actually exist after create_all."""
from sqlalchemy import create_engine, inspect
from app.database import Base
from app.models import MenuItem  # noqa: F401

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

# Before create_all
inspector = inspect(engine)
print("Tables before create_all:", inspector.get_table_names())

# After create_all
Base.metadata.create_all(bind=engine)
inspector = inspect(engine)
print("Tables after create_all:", inspector.get_table_names())

# Check if MenuItem is in metadata
print("Base metadata tables:", list(Base.metadata.tables.keys()))

# Try creating a session and inserting
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()
item = MenuItem(title="Test")
session.add(item)
session.commit()
print("Insert OK, id:", item.id)

# Verify read
from sqlalchemy import select
result = session.execute(select(MenuItem)).scalars().all()
print("Read OK, count:", len(result))
