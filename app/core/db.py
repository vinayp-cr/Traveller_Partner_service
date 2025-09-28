import os
import json
import time
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from fastapi import Depends
from app.core.logger import logger

def load_database_config():
    """Load database configuration from JSON file"""
    try:
        config_file = Path(__file__).parent.parent / "config" / "db.json"
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load database configuration: {str(e)}")
        # Return default config if file doesn't exist
        return {
            "database": {
                "default": {
                    "host": "localhost",
                    "port": 3306,
                    "user": "root",
                    "password": "password",
                    "name": "getmyhotels",
                    "driver": "mysql+pymysql"
                }
            },
            "connection_settings": {
                "max_retries": 5,
                "retry_delay_seconds": 5,
                "echo_queries": True
            }
        }

def get_database_url():
    """Build database URL from environment variables, JSON config, or fallback"""
    # Priority: Environment variables > JSON config > defaults
    
    # Check for full DATABASE_URL in environment
    if os.getenv("DATABASE_URL"):
        logger.info(f"Using DATABASE_URL from environment: {os.getenv('DATABASE_URL')}")
        return os.getenv("DATABASE_URL")
    
    # Load JSON configuration
    config = load_database_config()
    
    # Determine which database config to use
    environment = os.getenv("DB_ENVIRONMENT", "default")
    db_config = config["database"].get(environment, config["database"]["default"])
    
    # Override with environment variables if they exist
    db_host = os.getenv("DB_HOST", db_config["host"])
    db_user = os.getenv("DB_USER", db_config["user"])
    db_password = os.getenv("DB_PASSWORD", db_config["password"])
    db_name = os.getenv("DB_NAME", db_config["name"])
    db_port = os.getenv("DB_PORT", str(db_config["port"]))
    db_driver = os.getenv("DB_DRIVER", db_config["driver"])
    
    return f"{db_driver}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

DATABASE_URL = get_database_url()

def create_engine_with_retry(database_url, max_retries=None, retry_delay=None):
    """Create database engine with retry logic for connection issues"""
    # Load configuration settings
    config = load_database_config()
    connection_settings = config.get("connection_settings", {})
    
    # Use provided values or fall back to config
    max_retries = max_retries or connection_settings.get("max_retries", 5)
    retry_delay = retry_delay or connection_settings.get("retry_delay_seconds", 5)
    echo_queries = connection_settings.get("echo_queries", True)
    
    # Engine configuration
    engine_kwargs = {
        "echo": echo_queries,
        "future": True,
        "pool_size": connection_settings.get("pool_size", 10),
        "max_overflow": connection_settings.get("max_overflow", 20),
        "pool_timeout": connection_settings.get("pool_timeout", 30),
        "pool_recycle": connection_settings.get("pool_recycle", 3600)
    }
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Creating database engine with URL: {database_url}")
            engine = create_engine(database_url, **engine_kwargs)
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Database connection successful on attempt {attempt + 1}")
            return engine
        except OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection failed on attempt {attempt + 1}: {e}")
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Database connection failed after {max_retries} attempts: {e}")
                raise e
    return None

engine = create_engine_with_retry(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()