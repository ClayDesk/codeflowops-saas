#!/usr/bin/env python3
"""
Migration script to add subscription tables to existing CodeFlowOps database.
This script adds Customer, Subscription, and Payment tables to store Stripe subscription data.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Also add src directory 
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from src.models.enhanced_models import Base, Customer, Subscription, Payment
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_path():
    """Get the database file path"""
    # Check multiple possible locations
    possible_paths = [
        backend_dir.parent / "data" / "codeflowops.db",
        backend_dir / "data" / "codeflowops.db", 
        Path("data/codeflowops.db"),
        Path("../../data/codeflowops.db")
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path.resolve())
    
    # Default to the first path (will be created if needed)
    return str(possible_paths[0].resolve())

def run_migration():
    """Run the migration to add subscription tables"""
    try:
        # Get database path
        db_path = get_database_path()
        logger.info(f"Using database: {db_path}")
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create engine
        database_url = f"sqlite:///{db_path}"
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            echo=True  # Show SQL for debugging
        )
        
        # Create inspector to check existing tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        logger.info(f"Existing tables: {existing_tables}")
        
        # Check which subscription tables already exist
        subscription_tables = ['customers', 'subscriptions', 'payments']
        missing_tables = [table for table in subscription_tables if table not in existing_tables]
        
        if not missing_tables:
            logger.info("All subscription tables already exist. No migration needed.")
            return True
        
        logger.info(f"Creating missing tables: {missing_tables}")
        
        # Create only the new tables
        metadata = Base.metadata
        
        # Filter to only create the subscription tables
        tables_to_create = []
        for table_name in missing_tables:
            if table_name == 'customers':
                tables_to_create.append(Customer.__table__)
            elif table_name == 'subscriptions':
                tables_to_create.append(Subscription.__table__)
            elif table_name == 'payments':
                tables_to_create.append(Payment.__table__)
        
        # Create the tables
        for table in tables_to_create:
            logger.info(f"Creating table: {table.name}")
            table.create(engine, checkfirst=True)
        
        # Verify tables were created
        inspector = inspect(engine)
        new_tables = inspector.get_table_names()
        logger.info(f"Tables after migration: {new_tables}")
        
        # Verify all subscription tables now exist
        all_exist = all(table in new_tables for table in subscription_tables)
        
        if all_exist:
            logger.info("✅ Migration completed successfully!")
            logger.info("The following tables were created:")
            for table in subscription_tables:
                if table in missing_tables:
                    logger.info(f"  - {table} (new)")
                else:
                    logger.info(f"  - {table} (already existed)")
            return True
        else:
            logger.error("❌ Migration failed - not all tables were created")
            return False
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_migration_status():
    """Check if migration is needed"""
    try:
        db_path = get_database_path()
        if not os.path.exists(db_path):
            logger.info("Database file does not exist - migration will create it")
            return True
            
        database_url = f"sqlite:///{db_path}"
        engine = create_engine(database_url, connect_args={"check_same_thread": False})
        
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        subscription_tables = ['customers', 'subscriptions', 'payments']
        missing_tables = [table for table in subscription_tables if table not in existing_tables]
        
        if missing_tables:
            logger.info(f"Migration needed - missing tables: {missing_tables}")
            return True
        else:
            logger.info("No migration needed - all subscription tables exist")
            return False
            
    except Exception as e:
        logger.error(f"Error checking migration status: {str(e)}")
        return True  # Assume migration needed if we can't check

if __name__ == "__main__":
    logger.info("🚀 Starting subscription tables migration...")
    
    # Check if migration is needed
    if not check_migration_status():
        logger.info("No migration needed. Exiting.")
        sys.exit(0)
    
    # Run migration
    success = run_migration()
    
    if success:
        logger.info("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Migration failed!")
        sys.exit(1)