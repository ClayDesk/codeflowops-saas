# Phase 3: Migration Management System
# backend/core/migration_manager.py

"""
Database migration management with transaction safety
Enterprise-grade schema migration system with rollback capabilities
"""

import os
import re
import logging
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from enum import Enum

import boto3

logger = logging.getLogger(__name__)

class MigrationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class Migration:
    """Database migration representation"""
    filename: str
    version: str
    description: str
    sql_content: str
    checksum: str
    applied_at: Optional[datetime] = None
    status: MigrationStatus = MigrationStatus.PENDING
    execution_time_ms: Optional[int] = None
    rollback_sql: Optional[str] = None

@dataclass
class MigrationResult:
    """Result of migration execution"""
    migration: Migration
    success: bool
    error_message: Optional[str] = None
    execution_time_ms: int = 0
    rows_affected: int = 0

class MigrationManager:
    """
    ✅ Handle database schema migrations safely
    
    Features:
    - Transaction-safe migration execution
    - Automatic rollback on failure
    - Migration versioning and checksums
    - Cross-database engine support
    - Migration history tracking
    - Rollback capabilities
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.rds = boto3.client('rds', region_name=region)
        self.secrets_manager = boto3.client('secretsmanager', region_name=region)
        
        # Database connections will be established per migration run
        self.db_connections = {}
        
        logger.info("🔄 Migration manager initialized")
    
    def discover_migrations(self, migrations_path: str) -> List[Migration]:
        """
        Discover and parse migration files from directory
        
        Expected filename format: V{version}__{description}.sql
        Example: V001__create_users_table.sql
        """
        
        logger.info(f"🔍 Discovering migrations in: {migrations_path}")
        
        migrations_dir = Path(migrations_path)
        if not migrations_dir.exists():
            logger.warning(f"Migration directory not found: {migrations_path}")
            return []
        
        migrations = []
        migration_files = sorted(migrations_dir.glob("V*.sql"))
        
        for migration_file in migration_files:
            try:
                migration = self._parse_migration_file(migration_file)
                migrations.append(migration)
                logger.debug(f"📄 Found migration: {migration.filename}")
                
            except Exception as e:
                logger.error(f"❌ Failed to parse migration {migration_file.name}: {e}")
        
        logger.info(f"✅ Discovered {len(migrations)} migrations")
        return migrations
    
    def _parse_migration_file(self, migration_file: Path) -> Migration:
        """Parse a single migration file"""
        
        filename = migration_file.name
        
        # Extract version and description from filename
        # Format: V{version}__{description}.sql
        match = re.match(r'V(\d+(?:\.\d+)*)__(.+)\.sql$', filename)
        if not match:
            raise ValueError(f"Invalid migration filename format: {filename}")
        
        version = match.group(1)
        description = match.group(2).replace('_', ' ')
        
        # Read migration content
        sql_content = migration_file.read_text(encoding='utf-8')
        
        # Calculate checksum for integrity verification
        checksum = hashlib.sha256(sql_content.encode('utf-8')).hexdigest()
        
        # Extract rollback SQL if present (-- ROLLBACK section)
        rollback_sql = self._extract_rollback_sql(sql_content)
        
        return Migration(
            filename=filename,
            version=version,
            description=description,
            sql_content=sql_content,
            checksum=checksum,
            rollback_sql=rollback_sql
        )
    
    def _extract_rollback_sql(self, sql_content: str) -> Optional[str]:
        """Extract rollback SQL from migration content"""
        
        # Look for -- ROLLBACK section
        rollback_match = re.search(
            r'--\s*ROLLBACK\s*\n(.*?)(?=--\s*END\s*ROLLBACK|\Z)', 
            sql_content, 
            re.DOTALL | re.IGNORECASE
        )
        
        if rollback_match:
            rollback_sql = rollback_match.group(1).strip()
            if rollback_sql:
                return rollback_sql
        
        return None
    
    def get_applied_migrations(self, db_connection_info: Dict[str, str]) -> List[Migration]:
        """Get list of migrations that have already been applied"""
        
        logger.info("📋 Retrieving applied migrations")
        
        try:
            connection = self._get_database_connection(db_connection_info)
            
            # Create migration tracking table if it doesn't exist
            self._ensure_migration_table(connection, db_connection_info['engine'])
            
            # Query applied migrations
            cursor = connection.cursor()
            cursor.execute("""
                SELECT filename, version, description, checksum, applied_at, 
                       status, execution_time_ms
                FROM schema_migrations 
                ORDER BY version
            """)
            
            applied_migrations = []
            for row in cursor.fetchall():
                migration = Migration(
                    filename=row[0],
                    version=row[1], 
                    description=row[2],
                    sql_content="",  # Not stored in tracking table
                    checksum=row[3],
                    applied_at=row[4],
                    status=MigrationStatus(row[5]),
                    execution_time_ms=row[6]
                )
                applied_migrations.append(migration)
            
            logger.info(f"✅ Found {len(applied_migrations)} applied migrations")
            return applied_migrations
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve applied migrations: {e}")
            return []
    
    def _ensure_migration_table(self, connection: Any, engine: str):
        """Create migration tracking table if it doesn't exist"""
        
        cursor = connection.cursor()
        
        if engine.startswith('postgres'):
            create_table_sql = """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL UNIQUE,
                    version VARCHAR(50) NOT NULL,
                    description TEXT,
                    checksum VARCHAR(64) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'completed',
                    execution_time_ms INTEGER,
                    applied_by VARCHAR(100) DEFAULT 'codeflowops'
                )
            """
        elif engine.startswith('mysql'):
            create_table_sql = """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL UNIQUE,
                    version VARCHAR(50) NOT NULL,
                    description TEXT,
                    checksum VARCHAR(64) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'completed',
                    execution_time_ms INT,
                    applied_by VARCHAR(100) DEFAULT 'codeflowops'
                )
            """
        else:
            # MongoDB doesn't use SQL, handle separately if needed
            return
        
        cursor.execute(create_table_sql)
        connection.commit()
    
    def run_migrations(self, migrations_path: str, db_connection_info: Dict[str, str], 
                      target_version: Optional[str] = None, dry_run: bool = False) -> List[MigrationResult]:
        """
        Execute database migrations safely with transaction support
        
        Args:
            migrations_path: Path to migration files
            db_connection_info: Database connection details
            target_version: Run migrations up to this version (optional)
            dry_run: Preview migrations without executing
        """
        
        logger.info(f"🚀 Starting migration execution (dry_run={dry_run})")
        
        # Discover all migrations
        all_migrations = self.discover_migrations(migrations_path)
        
        # Get already applied migrations
        applied_migrations = self.get_applied_migrations(db_connection_info)
        applied_versions = {m.version for m in applied_migrations}
        
        # Determine which migrations to run
        pending_migrations = [
            m for m in all_migrations 
            if m.version not in applied_versions and 
            (target_version is None or m.version <= target_version)
        ]
        
        if not pending_migrations:
            logger.info("✅ No pending migrations to run")
            return []
        
        logger.info(f"📋 Found {len(pending_migrations)} pending migrations")
        
        if dry_run:
            for migration in pending_migrations:
                logger.info(f"🔍 Would apply: {migration.filename} - {migration.description}")
            return []
        
        # Execute migrations
        results = []
        connection = self._get_database_connection(db_connection_info)
        
        for migration in pending_migrations:
            try:
                logger.info(f"⚡ Applying migration: {migration.filename}")
                result = self._execute_migration(connection, migration, db_connection_info['engine'])
                results.append(result)
                
                if not result.success:
                    logger.error(f"❌ Migration failed, stopping execution: {result.error_message}")
                    break
                    
            except Exception as e:
                logger.error(f"❌ Migration execution failed: {e}")
                result = MigrationResult(
                    migration=migration,
                    success=False,
                    error_message=str(e)
                )
                results.append(result)
                break
        
        # Summary
        successful = sum(1 for r in results if r.success)
        logger.info(f"✅ Migration execution completed: {successful}/{len(results)} successful")
        
        return results
    
    def _execute_migration(self, connection: Any, migration: Migration, engine: str) -> MigrationResult:
        """Execute a single migration with transaction safety"""
        
        start_time = datetime.now()
        
        # Start transaction
        if hasattr(connection, 'begin'):
            connection.begin()
        else:
            connection.autocommit = False
        
        try:
            cursor = connection.cursor()
            
            # Update migration status to running
            self._update_migration_status(cursor, migration, MigrationStatus.RUNNING, engine)
            
            # Execute migration SQL
            statements = self._split_sql_statements(migration.sql_content)
            rows_affected = 0
            
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)
                    if hasattr(cursor, 'rowcount'):
                        rows_affected += cursor.rowcount
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Update migration status to completed
            migration.applied_at = datetime.now()
            migration.status = MigrationStatus.COMPLETED
            migration.execution_time_ms = int(execution_time)
            
            self._record_migration_completion(cursor, migration, execution_time, engine)
            
            # Commit transaction
            connection.commit()
            
            logger.info(f"✅ Migration applied successfully: {migration.filename} ({execution_time:.0f}ms)")
            
            return MigrationResult(
                migration=migration,
                success=True,
                execution_time_ms=int(execution_time),
                rows_affected=rows_affected
            )
            
        except Exception as e:
            # Rollback transaction
            connection.rollback()
            
            # Update migration status to failed
            try:
                cursor = connection.cursor()
                self._update_migration_status(cursor, migration, MigrationStatus.FAILED, engine)
                connection.commit()
            except:
                pass  # Don't let tracking failure mask the original error
            
            logger.error(f"❌ Migration failed: {migration.filename} - {e}")
            
            return MigrationResult(
                migration=migration,
                success=False,
                error_message=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
    
    def _split_sql_statements(self, sql_content: str) -> List[str]:
        """Split SQL content into individual statements"""
        
        # Remove comments and split by semicolon
        # This is a simplified approach - a real implementation would use a proper SQL parser
        statements = []
        
        for line in sql_content.split('\n'):
            line = line.strip()
            
            # Skip comments
            if line.startswith('--') or line.startswith('#'):
                continue
                
            if line:
                statements.append(line)
        
        # Join and split by semicolon
        full_sql = ' '.join(statements)
        statements = [stmt.strip() for stmt in full_sql.split(';') if stmt.strip()]
        
        return statements
    
    def _update_migration_status(self, cursor: Any, migration: Migration, status: MigrationStatus, engine: str):
        """Update migration status in tracking table"""
        
        if engine.startswith('postgres'):
            sql = """
                INSERT INTO schema_migrations (filename, version, description, checksum, status, applied_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (filename) 
                DO UPDATE SET status = EXCLUDED.status, applied_at = EXCLUDED.applied_at
            """
        elif engine.startswith('mysql'):
            sql = """
                INSERT INTO schema_migrations (filename, version, description, checksum, status, applied_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE status = VALUES(status), applied_at = VALUES(applied_at)
            """
        else:
            return  # MongoDB or other NoSQL
        
        cursor.execute(sql, (
            migration.filename,
            migration.version,
            migration.description,
            migration.checksum,
            status.value,
            datetime.now()
        ))
    
    def _record_migration_completion(self, cursor: Any, migration: Migration, execution_time: float, engine: str):
        """Record successful migration completion"""
        
        if engine.startswith('postgres'):
            sql = """
                UPDATE schema_migrations 
                SET status = %s, applied_at = %s, execution_time_ms = %s
                WHERE filename = %s
            """
        elif engine.startswith('mysql'):
            sql = """
                UPDATE schema_migrations 
                SET status = %s, applied_at = %s, execution_time_ms = %s
                WHERE filename = %s
            """
        else:
            return
        
        cursor.execute(sql, (
            MigrationStatus.COMPLETED.value,
            migration.applied_at,
            migration.execution_time_ms,
            migration.filename
        ))
    
    def rollback_migration(self, db_connection_info: Dict[str, str], target_version: str) -> List[MigrationResult]:
        """
        Rollback migrations to a specific version
        
        Args:
            db_connection_info: Database connection details
            target_version: Rollback to this version (exclusive)
        """
        
        logger.info(f"🔄 Starting rollback to version: {target_version}")
        
        # Get applied migrations that need to be rolled back
        applied_migrations = self.get_applied_migrations(db_connection_info)
        
        # Find migrations to rollback (versions > target_version)
        migrations_to_rollback = [
            m for m in applied_migrations 
            if m.version > target_version and m.status == MigrationStatus.COMPLETED
        ]
        
        # Sort in reverse order for rollback
        migrations_to_rollback.sort(key=lambda x: x.version, reverse=True)
        
        if not migrations_to_rollback:
            logger.info("✅ No migrations to rollback")
            return []
        
        logger.info(f"📋 Found {len(migrations_to_rollback)} migrations to rollback")
        
        results = []
        connection = self._get_database_connection(db_connection_info)
        
        for migration in migrations_to_rollback:
            try:
                logger.info(f"🔄 Rolling back migration: {migration.filename}")
                result = self._execute_rollback(connection, migration, db_connection_info['engine'])
                results.append(result)
                
                if not result.success:
                    logger.error(f"❌ Rollback failed, stopping: {result.error_message}")
                    break
                    
            except Exception as e:
                logger.error(f"❌ Rollback execution failed: {e}")
                result = MigrationResult(
                    migration=migration,
                    success=False,
                    error_message=str(e)
                )
                results.append(result)
                break
        
        # Summary
        successful = sum(1 for r in results if r.success)
        logger.info(f"✅ Rollback completed: {successful}/{len(results)} successful")
        
        return results
    
    def _execute_rollback(self, connection: Any, migration: Migration, engine: str) -> MigrationResult:
        """Execute rollback for a single migration"""
        
        if not migration.rollback_sql:
            return MigrationResult(
                migration=migration,
                success=False,
                error_message="No rollback SQL provided for this migration"
            )
        
        start_time = datetime.now()
        
        # Start transaction
        if hasattr(connection, 'begin'):
            connection.begin()
        else:
            connection.autocommit = False
        
        try:
            cursor = connection.cursor()
            
            # Execute rollback SQL
            statements = self._split_sql_statements(migration.rollback_sql)
            
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)
            
            # Remove migration record from tracking table
            if engine.startswith('postgres') or engine.startswith('mysql'):
                cursor.execute("DELETE FROM schema_migrations WHERE filename = %s", (migration.filename,))
            
            # Commit transaction
            connection.commit()
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"✅ Migration rolled back successfully: {migration.filename} ({execution_time:.0f}ms)")
            
            return MigrationResult(
                migration=migration,
                success=True,
                execution_time_ms=int(execution_time)
            )
            
        except Exception as e:
            # Rollback transaction
            connection.rollback()
            
            logger.error(f"❌ Migration rollback failed: {migration.filename} - {e}")
            
            return MigrationResult(
                migration=migration,
                success=False,
                error_message=str(e),
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
    
    def _get_database_connection(self, connection_info: Dict[str, str]) -> Any:
        """Get database connection based on engine type"""
        
        engine = connection_info['engine']
        
        if engine.startswith('postgres'):
            import psycopg2
            return psycopg2.connect(
                host=connection_info['host'],
                port=connection_info['port'],
                database=connection_info['database'],
                user=connection_info['username'],
                password=connection_info['password']
            )
        elif engine.startswith('mysql'):
            import pymysql
            return pymysql.connect(
                host=connection_info['host'],
                port=int(connection_info['port']),
                database=connection_info['database'],
                user=connection_info['username'],
                password=connection_info['password'],
                autocommit=False
            )
        else:
            raise ValueError(f"Unsupported database engine: {engine}")
    
    def generate_migration_template(self, version: str, description: str, 
                                  migrations_path: str, include_rollback: bool = True) -> str:
        """Generate a new migration file template"""
        
        filename = f"V{version}__{description.replace(' ', '_')}.sql"
        filepath = Path(migrations_path) / filename
        
        # Ensure migrations directory exists
        Path(migrations_path).mkdir(parents=True, exist_ok=True)
        
        template = f"""-- Migration: {description}
-- Version: {version}
-- Created: {datetime.now().isoformat()}

-- Add your migration SQL here
-- Example:
-- CREATE TABLE example_table (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(255) NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

"""
        
        if include_rollback:
            template += """
-- ROLLBACK
-- Add rollback SQL here (optional but recommended)
-- Example:
-- DROP TABLE IF EXISTS example_table;
-- END ROLLBACK
"""
        
        # Write template to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(template)
        
        logger.info(f"✅ Migration template created: {filepath}")
        return str(filepath)
    
    def get_migration_status(self, db_connection_info: Dict[str, str]) -> Dict[str, Any]:
        """Get comprehensive migration status and history"""
        
        applied_migrations = self.get_applied_migrations(db_connection_info)
        
        status = {
            'total_migrations': len(applied_migrations),
            'completed_migrations': len([m for m in applied_migrations if m.status == MigrationStatus.COMPLETED]),
            'failed_migrations': len([m for m in applied_migrations if m.status == MigrationStatus.FAILED]),
            'last_migration_version': applied_migrations[-1].version if applied_migrations else None,
            'last_migration_applied': applied_migrations[-1].applied_at if applied_migrations else None,
            'migrations': [
                {
                    'version': m.version,
                    'description': m.description,
                    'status': m.status.value,
                    'applied_at': m.applied_at.isoformat() if m.applied_at else None,
                    'execution_time_ms': m.execution_time_ms
                }
                for m in applied_migrations
            ]
        }
        
        return status


# CLI interface for migration management
if __name__ == "__main__":
    import sys
    import argparse
    
    def main():
        parser = argparse.ArgumentParser(description="Database Migration Manager")
        parser.add_argument('command', choices=['run', 'rollback', 'status', 'generate'])
        parser.add_argument('--migrations-path', required=True, help='Path to migrations directory')
        parser.add_argument('--db-host', required=True, help='Database host')
        parser.add_argument('--db-port', type=int, default=5432, help='Database port')
        parser.add_argument('--db-name', required=True, help='Database name')
        parser.add_argument('--db-user', required=True, help='Database username')
        parser.add_argument('--db-password', required=True, help='Database password')
        parser.add_argument('--db-engine', required=True, help='Database engine (postgres/mysql)')
        parser.add_argument('--target-version', help='Target version for run/rollback')
        parser.add_argument('--dry-run', action='store_true', help='Preview migrations without executing')
        parser.add_argument('--version', help='Version for generate command')
        parser.add_argument('--description', help='Description for generate command')
        
        args = parser.parse_args()
        
        # Database connection info
        db_connection_info = {
            'host': args.db_host,
            'port': args.db_port,
            'database': args.db_name,
            'username': args.db_user,
            'password': args.db_password,
            'engine': args.db_engine
        }
        
        migration_manager = MigrationManager()
        
        if args.command == 'run':
            results = migration_manager.run_migrations(
                args.migrations_path, 
                db_connection_info,
                args.target_version,
                args.dry_run
            )
            for result in results:
                status = "✅" if result.success else "❌"
                print(f"{status} {result.migration.filename}: {result.execution_time_ms}ms")
                
        elif args.command == 'rollback':
            if not args.target_version:
                print("❌ Target version required for rollback")
                sys.exit(1)
                
            results = migration_manager.rollback_migration(db_connection_info, args.target_version)
            for result in results:
                status = "✅" if result.success else "❌"
                print(f"{status} Rollback {result.migration.filename}: {result.execution_time_ms}ms")
                
        elif args.command == 'status':
            status = migration_manager.get_migration_status(db_connection_info)
            print(f"📊 Migration Status:")
            print(f"   Total: {status['total_migrations']}")
            print(f"   Completed: {status['completed_migrations']}")
            print(f"   Failed: {status['failed_migrations']}")
            print(f"   Last Version: {status['last_migration_version']}")
            
        elif args.command == 'generate':
            if not args.version or not args.description:
                print("❌ Version and description required for generate")
                sys.exit(1)
                
            filepath = migration_manager.generate_migration_template(
                args.version, 
                args.description, 
                args.migrations_path
            )
            print(f"✅ Migration template created: {filepath}")
    
    main()
