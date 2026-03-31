import os
from datetime import date, datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import asc, create_engine, desc
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
def get_prices(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    supplier: str = None,
    start_date: date = Query(None),
    end_date: date = Query(None),
    sort_by: str = Query(default="scraped_at"),
    order: str = Query(default="desc"),
):
    query = db.query(OilPrice)
    column = getattr(OilPrice, sort_by, OilPrice.scraped_at)
    sort_opt = asc(column) if order.lower() == "asc" else desc(column)

    if supplier:
        query = query.filter(OilPrice.supplier_name == supplier)
    if start_date:
        query = query.filter(OilPrice.scraped_at >= start_date)
    if end_date:
        query = query.filter(OilPrice.scraped_at <= end_date + timedelta(days=1))
    total_count = query.count()
    prices = query.order_by(sort_opt).offset(offset).limit(limit).all()
    return {"total": total_count, "limit": limit, "offset": offset, "data": prices}
