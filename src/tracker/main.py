import logging
import os
from sqlalchemy import create_engine, text
from tracker.models import Base, OilPrice
import time


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("oil_tracker")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
DATABASE_CONNECTION_ATTEMPTS = 5



def init_db():
    """Create tables if they do not exist"""
    max_retries = 5
    for i in range(max_retries):
        try:
            logger.info(f"Attempting to initialize database (Attempt {i + 1}/{max_retries})...")
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