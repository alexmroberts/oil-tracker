import logging
import os
import signal
import sys
import time
from logging.handlers import RotatingFileHandler

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.tracker.models import Base, OilPrice
from src.tracker.scraper import fetch_oil_prices

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
log_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

log_file = os.path.join(LOG_DIR, "oil_tracker.log")
file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=15)
file_handler.setFormatter(log_formatter)
# file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
# console_handler.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler],
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
        return
    scheduler = BlockingScheduler()

    run_scraper_and_save()
    scheduler.add_job(
        run_scraper_and_save,
        "cron",
        hour="4,8,12,16,20",
        minute=0,
        jitter=3600,
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


if __name__ == "__main__":
    main()
