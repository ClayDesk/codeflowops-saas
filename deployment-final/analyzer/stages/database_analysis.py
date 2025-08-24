"""
Stage 4: Database Analysis
================================================================================
Comprehensive database detection and analysis - finds ALL database-related files,
configurations, migrations, schemas, and determines database requirements.

Mission: Analyze EVERY database-related file to provide complete database intelligence.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
import logging

from ..contracts import AnalysisContext

logger = logging.getLogger(__name__)

class DatabaseAnalysisStage:
    """
    Comprehensive database analysis stage
    
    Responsibilities:
    - Detect ALL database files (models, migrations, schemas, seeds)
    - Analyze database configurations 
    - Identify database type and requirements
    - Extract schema information
    - Detect ORM usage patterns
    - Find database connection strings
    """
    
    # Database configuration files
    DATABASE_CONFIG_FILES = {
        # Django
        'settings.py', 'settings_local.py', 'local_settings.py',
        # Laravel
        'database.php', '.env', '.env.example',
        # Node.js
        'knexfile.js', 'database.js', 'config.js', 'db.js',
        # Rails
        'database.yml', 'database.yaml',
        # General
        'config.json', 'config.yaml', 'config.yml', 
        'docker-compose.yml', 'docker-compose.yaml'
    }
    
    # Migration directories and patterns
    MIGRATION_PATTERNS = {
        'migrations/', 'migrate/', 'db/migrate/', 'database/migrations/',
        'db/migrations/', 'src/migrations/', 'app/migrations/',
        'prisma/migrations/', 'sequelize/migrations/'
    }
    
    # Model file patterns (only actual database model directories)
    MODEL_PATTERNS = {
        'models/', 'app/models/', 'src/models/', 'database/models/', 'db/models/', 'entities/'
    }
    
    # Skip frontend model directories that aren't database related
    FRONTEND_MODEL_PATTERNS = {
        'src/app/model/', 'src/app/models/', 'app/model/', 'app/models/', 'models/ui/', 'models/view/'
    }
    
    # Schema and seed patterns
    SCHEMA_PATTERNS = {
        'schema/', 'schemas/', 'db/schema/', 'database/schema/',
        'seeds/', 'seeders/', 'db/seeds/', 'database/seeds/'
    }
    
    # SQL file extensions
    SQL_EXTENSIONS = {'.sql', '.mysql', '.pgsql', '.sqlite', '.psql'}
    
    # Database type indicators in file content
    DATABASE_INDICATORS = {
        'postgresql': ['postgresql://', 'postgres://', 'psycopg2', 'pg_', 'POSTGRES', 'PostgreSQL'],
        'mysql': ['mysql://', 'mysqli', 'MySQL', 'MYSQL', 'mysql2', 'MariaDB'],
        'sqlite': ['sqlite://', 'sqlite3', 'SQLite', 'SQLITE', '.sqlite', '.db'],
        'mongodb': ['mongodb://', 'mongoose', 'MongoDB', 'MONGODB', 'mongo'],
        'redis': ['redis://', 'Redis', 'REDIS', 'redisdb'],
        'oracle': ['oracle://', 'Oracle', 'ORACLE', 'cx_Oracle'],
        'mssql': ['mssql://', 'SQL Server', 'MSSQL', 'pyodbc']
    }
    
    # Asset directories and extensions to skip
    SKIP_DIRS = {"assets","plugins","vendor","node_modules","dist","build","public","public/assets"}
    SKIP_EXTS = {".css",".map",".scss",".less"}
    CODE_EXTS = {".php",".py",".js",".ts",".tsx",".java",".rb",".go",".cs"}
    
    async def analyze(self, context: AnalysisContext):
        """Run comprehensive database analysis"""
        logger.info(f"💾 Analyzing database configuration and files: {context.repo_path}")
        
        database_analysis = {
            "database_files_found": [],
            "configuration_files": [],
            "migration_files": [],
            "model_files": [],
            "schema_files": [],
            "seed_files": [],
            "sql_files": [],
            "database_types_detected": set(),
            "orm_detected": set(),
            "database_required": False,
            "database_confidence": 0.0,
            "evidence": [],
            "connection_strings_found": [],
            "database_technologies": {}
        }
        
        # Analyze all files for database indicators
        await self._scan_all_files(context, database_analysis)
        
        # Analyze directory structure
        await self._analyze_directory_structure(context, database_analysis)
        
        # Determine final database requirements
        database_result = self._determine_database_requirements(database_analysis)
        
        # Store results in context
        context.intelligence_profile["database"] = database_result
        
        logger.info(f"✅ Database analysis complete: {len(database_analysis['database_files_found'])} database files, "
                   f"{len(database_analysis['database_types_detected'])} database types detected")
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped for database analysis"""
        # Skip asset directories
        if any(part.lower() in self.SKIP_DIRS for part in file_path.parts):
            return True
        
        # Skip asset extensions
        if file_path.suffix.lower() in self.SKIP_EXTS:
            return True
            
        # Only analyze code files for database indicators
        return file_path.suffix.lower() not in self.CODE_EXTS and not self._is_database_file(str(file_path))
    
    async def _scan_all_files(self, context: AnalysisContext, analysis: Dict[str, Any]):
        """Scan every file for database indicators"""
        
        for file_metadata in context.files:
            file_path = Path(context.repo_path) / file_metadata["path"]
            
            # Skip asset files and non-code files for database detection
            if self._should_skip_file(file_path):
                continue
            
            # Check if it's a database-related file by name
            if self._is_database_file(file_metadata["path"]):
                analysis["database_files_found"].append(file_metadata["path"])
                
                # Categorize the file
                self._categorize_database_file(file_metadata["path"], analysis)
            
            # For text files, scan content for database indicators
            if not file_metadata["is_binary"] and file_metadata["size"] < 1024 * 1024:  # Skip large files
                try:
                    await self._analyze_file_content(file_path, file_metadata["path"], analysis)
                except Exception as e:
                    logger.debug(f"Could not analyze content of {file_metadata['path']}: {e}")
    
    async def _analyze_file_content(self, file_path: Path, rel_path: str, analysis: Dict[str, Any]):
        """Analyze file content for database indicators"""
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            content_lower = content.lower()
            file_ext = file_path.suffix.lower()
            
            # Language-aware database detection to prevent false positives
            detected_dbs = set()
            
            if file_ext == ".php":
                # PHP-specific database patterns
                if any(pattern in content for pattern in ['Predis\\Client', 'new Redis(', 'use Redis']):
                    detected_dbs.add('redis')
                if any(pattern in content for pattern in ['mysqli_connect', 'PDO:', 'mysql:']):
                    detected_dbs.add('mysql')
                if any(pattern in content for pattern in ['pg_connect', 'pgsql:', 'postgres:']):
                    detected_dbs.add('postgresql')
                    
            elif file_ext in ['.js', '.ts', '.tsx']:
                # JavaScript/TypeScript-specific patterns
                if any(pattern in content for pattern in ['redis.createClient(', 'from \'redis\'', 'ioredis']):
                    detected_dbs.add('redis')
                if any(pattern in content for pattern in ['mysql.createConnection', 'mysql2']):
                    detected_dbs.add('mysql')
                if any(pattern in content for pattern in ['new Client(', 'pg.Pool']):
                    detected_dbs.add('postgresql')
                if any(pattern in content for pattern in ['MongoClient', 'mongoose.connect']):
                    detected_dbs.add('mongodb')
                    
            elif file_ext == ".py":
                # Python-specific patterns
                if any(pattern in content for pattern in ['import redis', 'Redis()']):
                    detected_dbs.add('redis')
                if any(pattern in content for pattern in ['import mysql', 'MySQLdb']):
                    detected_dbs.add('mysql')
                if any(pattern in content for pattern in ['import psycopg2', 'postgresql://']):
                    detected_dbs.add('postgresql')
                if any(pattern in content for pattern in ['import sqlite3', '.db']):
                    detected_dbs.add('sqlite')
                    
            # Add detected databases with evidence
            for db_type in detected_dbs:
                analysis["database_types_detected"].add(db_type)
                analysis["evidence"].append(f"{db_type} code patterns found in {rel_path}")
            
            # Check for ORM patterns (only in non-commented code)
            orm_patterns = {
                'django-orm': ['models.Model', 'django.db', 'ForeignKey', 'CharField'],
                'laravel-eloquent': ['Eloquent', 'Model extends', 'Schema::', 'Migration'],
                'sequelize': ['sequelize', 'DataTypes', 'belongsTo', 'hasMany'],
                'typeorm': ['TypeORM', '@Entity', '@Column', 'Repository'],
                'prisma': ['@prisma/client', 'PrismaClient', '@@map', 'model '],
                'sqlalchemy': ['SQLAlchemy', 'from sqlalchemy', 'import sqlalchemy', 'Column(Integer', 'Column(String', 'relationship(']
            }
            
            for orm_name, patterns in orm_patterns.items():
                for pattern in patterns:
                    # Skip commented lines to avoid false positives
                    lines = content.split('\n')
                    for line_num, line in enumerate(lines, 1):
                        line_stripped = line.strip()
                        # Skip commented lines
                        if line_stripped.startswith('//') or line_stripped.startswith('#') or line_stripped.startswith('*'):
                            continue
                        if pattern.lower() in line.lower():
                            analysis["orm_detected"].add(orm_name)
                            analysis["evidence"].append(f"{orm_name} pattern ({pattern}) in {rel_path}:{line_num}")
                            break  # Only count once per file
            
            # Look for connection strings
            connection_patterns = [
                r'postgresql://[^\s\'"]+',
                r'mysql://[^\s\'"]+', 
                r'mongodb://[^\s\'"]+',
                r'sqlite:///[^\s\'"]+',
                r'redis://[^\s\'"]+',
                r'DATABASE_URL\s*=\s*[\'"][^\'"]+[\'"]'
            ]
            
            for pattern in connection_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    analysis["connection_strings_found"].append({
                        "file": rel_path,
                        "connection": match[:50] + "..." if len(match) > 50 else match
                    })
                    
        except Exception as e:
            logger.debug(f"Failed to read content from {rel_path}: {e}")
    
    async def _analyze_directory_structure(self, context: AnalysisContext, analysis: Dict[str, Any]):
        """Analyze directory structure for database patterns"""
        
        for root, dirs, files in os.walk(context.repo_path):
            rel_root = os.path.relpath(root, context.repo_path)
            
            # Check for migration directories
            for migration_pattern in self.MIGRATION_PATTERNS:
                if migration_pattern.rstrip('/') in rel_root or migration_pattern.rstrip('/') in dirs:
                    analysis["evidence"].append(f"Migration directory found: {rel_root}")
                    analysis["database_required"] = True
            
            # Check for model directories (skip frontend model patterns)
            is_frontend_model = any(pattern.rstrip('/') in rel_root for pattern in self.FRONTEND_MODEL_PATTERNS)
            if not is_frontend_model:
                for model_pattern in self.MODEL_PATTERNS:
                    if model_pattern.rstrip('/') in rel_root or model_pattern.rstrip('/') in dirs:
                        analysis["evidence"].append(f"Database model directory found: {rel_root}")
                        analysis["database_required"] = True
    
    def _is_database_file(self, file_path: str) -> bool:
        """Check if file is database-related"""
        
        file_path_lower = file_path.lower()
        filename = Path(file_path).name.lower()
        
        # HARD FILTERS: Exclude asset files that cause false positives
        excluded_extensions = {'.css', '.map', '.min.js', '.min.css'}
        excluded_patterns = [
            'assets/', 'plugins/', 'vendor/', 'node_modules/', 
            'dist/', 'build/', 'public/', 'static/'
        ]
        
        # Skip files that commonly contain false positive database strings
        if Path(file_path).suffix.lower() in excluded_extensions:
            return False
            
        for pattern in excluded_patterns:
            if pattern in file_path_lower:
                return False
        
        # Check configuration files
        if filename in [f.lower() for f in self.DATABASE_CONFIG_FILES]:
            return True
            
        # Check extensions
        if Path(file_path).suffix.lower() in self.SQL_EXTENSIONS:
            return True
            
        # Check path patterns
        database_path_patterns = [
            'migration', 'migrate', 'model', 'schema', 'seed', 'database', 'db/'
        ]
        
        for pattern in database_path_patterns:
            if pattern in file_path_lower:
                return True
                
        return False
    
    def _categorize_database_file(self, file_path: str, analysis: Dict[str, Any]):
        """Categorize database file type"""
        
        file_path_lower = file_path.lower()
        filename = Path(file_path).name.lower()
        
        if filename in [f.lower() for f in self.DATABASE_CONFIG_FILES]:
            analysis["configuration_files"].append(file_path)
        elif 'migration' in file_path_lower or 'migrate' in file_path_lower:
            analysis["migration_files"].append(file_path)
        elif 'model' in file_path_lower:
            analysis["model_files"].append(file_path)
        elif 'schema' in file_path_lower:
            analysis["schema_files"].append(file_path)
        elif 'seed' in file_path_lower:
            analysis["seed_files"].append(file_path)
        elif Path(file_path).suffix.lower() in self.SQL_EXTENSIONS:
            analysis["sql_files"].append(file_path)
    
    def _determine_database_requirements(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Determine final database requirements and recommendations"""
        
        evidence = analysis["evidence"]
        database_types = list(analysis["database_types_detected"])
        orm_detected = list(analysis["orm_detected"])
        
        # Calculate confidence based on evidence
        confidence = 0.0
        
        if analysis["migration_files"]:
            confidence += 0.3
            evidence.append(f"{len(analysis['migration_files'])} migration files found")
            
        if analysis["model_files"]:
            confidence += 0.3
            evidence.append(f"{len(analysis['model_files'])} model files found")
            
        if analysis["configuration_files"]:
            confidence += 0.2
            evidence.append(f"{len(analysis['configuration_files'])} config files found")
            
        if database_types:
            confidence += 0.2
            evidence.append(f"Database types detected: {', '.join(database_types)}")
            
        if orm_detected:
            confidence += 0.1
            evidence.append(f"ORM detected: {', '.join(orm_detected)}")
        
        # Determine primary database type
        primary_db_type = None
        if database_types:
            # Priority order for common databases
            priority = ['postgresql', 'mysql', 'sqlite', 'mongodb', 'redis']
            for db_type in priority:
                if db_type in database_types:
                    primary_db_type = db_type
                    break
            if not primary_db_type:
                primary_db_type = database_types[0]
        
        # Database is required if we have high confidence or explicit indicators
        required = (confidence >= 0.4 or 
                   analysis["migration_files"] or 
                   analysis["model_files"] or
                   analysis["connection_strings_found"])
        
        # If no database indicators found, return None
        if confidence == 0.0 and not database_types and not evidence:
            return {
                "kind": None,
                "required": False,
                "confidence": 0.0,
                "evidence": [],
                "database_types_detected": [],
                "orm_technologies": [],
                "files_analyzed": {
                    "total_database_files": len(analysis["database_files_found"]),
                    "configuration_files": len(analysis["configuration_files"]),
                    "migration_files": len(analysis["migration_files"]),
                    "model_files": len(analysis["model_files"]),
                    "schema_files": len(analysis["schema_files"]),
                    "sql_files": len(analysis["sql_files"])
                },
                "connection_strings": analysis["connection_strings_found"]
            }
        
        return {
            "kind": primary_db_type,  # No default fallback
            "required": required,
            "confidence": min(confidence, 0.99),
            "evidence": evidence[:5],  # Top 5 pieces of evidence
            "database_types_detected": database_types,
            "orm_technologies": orm_detected,
            "files_analyzed": {
                "total_database_files": len(analysis["database_files_found"]),
                "configuration_files": len(analysis["configuration_files"]),
                "migration_files": len(analysis["migration_files"]),
                "model_files": len(analysis["model_files"]),
                "schema_files": len(analysis["schema_files"]),
                "sql_files": len(analysis["sql_files"])
            },
            "connection_strings": analysis["connection_strings_found"]
        }
