import os

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import Session, sessionmaker

from src.tracker.models import OilPrice

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Heating Oil Price API", root_path="/oiltracker/api")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def health_check():
    return {"status": "online", "location": "Vernon, CT"}


@app.get("/prices")
def get_prices(limit: int = 50, db: Session = Depends(get_db)):
    """Fetch the most recent oil prices."""
    return db.query(OilPrice).order_by(desc(OilPrice.scraped_at)).limit(limit).all()
