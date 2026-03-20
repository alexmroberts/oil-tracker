import logging
import os
import signal
import sys
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from tracker.models import Base, OilPrice
from tracker.scraper import fetch_oil_prices

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
DATABASE_CONNECTION_ATTEMPTS = 5


def handle_sigterm(*args):
    """
    Catch the SIGTERM signal and raise SystemExit.
    """
    logger.info("Received SIGTERM. Triggering graceful shutdown...")
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)


def init_db():
    """Create tables if they do not exist"""
    max_retries = 5
    for i in range(max_retries):
        try:
            logger.info(
                f"Attempting to initialize database (Attempt {i + 1}/{max_retries})..."
            )
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
            return
        except Exception as e:
            if i < max_retries - 1:
                logger.warning("Database initialization failed. Retrying...")
                time.sleep(2)
            else:
                logger.error("Failed to initialize database: %s", e)
                raise e


def run_scraper_and_save():
    """Fetches the current price and stores it in the database."""
    logger.info("Starting scrape job for Vernon (06066)...")

    price = fetch_oil_prices()

    if price:
        try:
            with Session(engine) as session:
                for idx, entry in enumerate(price, 1):
                    new_record = OilPrice(
                        supplier_name=entry["supplier_id"],
                        price_type=entry["type"],
                        min_quantity=entry["quantity"],
                        price_per_gallon=entry["price"],
                    )
                    session.add(new_record)
                    logger.info(f"Loading entry {idx} out of {len(price)}")
                session.commit()
                logger.info(f"Saved dealer entry {len(price)} entries to DB")
        except Exception as e:
            logger.error(f"Database save failed: {e}")
            session.rollback()
    else:
        logger.warning("Scraper returned no data; nothing to save.")


def main():
    logger.info("Starting Phase 1: Environment check")

    init_db()

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("Health Check: Database connection verified")
    except Exception as e:
        logger.critical("Health Check: Database is unreachable. %s", e)


if __name__ == "__main__":
    main()

    scheduler = BlockingScheduler()

    run_scraper_and_save()
    scheduler.add_job(
        run_scraper_and_save,
        "cron",
        hour=8,
        minute=0,
        jitter=7200,
        timezone="America/New_York",
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopping Scheduler")
    finally:
        if scheduler.running:
            scheduler.shutdown()
        engine.dispose()
        logger.info("Database connection closed")
