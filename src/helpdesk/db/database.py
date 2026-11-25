import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from helpdesk.core.config import settings

load_dotenv()

# 1. Read the URL from the environment, and fail loudly if it's missing.
DATABASE_URL = os.environ["DATABASE_URL"]

# 2. The engine: one per app. It manages a pool of connections to Postgres.
engine = create_engine(
    settings.DATABASE_URL, echo=True
)  # echo=True prints the SQL it runs (handy while learning)

# 3. A session factory. Each request gets its own short-lived Session from this.
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


# 4. A FastAPI dependency: opens a session per request and always closes it.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
