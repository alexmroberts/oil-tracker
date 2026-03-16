from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone


Base = declarative_base()

class OilPrice(Base):
    __tablename__ = 'oil_prices'

    id = Column(Integer, primary_key=True, index=True)

    supplier_name = Column(String, nullable=False, index=True)

    price_per_gallon = Column(Float, nullable=False)

    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


    def __repr__(self):
        return f"<OilPrice(supplier='{self.supplier_name}', price={self.price_per_gallon})>"