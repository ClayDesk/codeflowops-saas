"""
Project State Manager Service
Manages project deployment states across environments with persistence.
"""

import json
import sqlite3
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import threading

# Simple Environment enum (was in deployment_orchestrator, now removed)
class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class DeploymentStatus(Enum):
    NOT_DEPLOYED = "not_deployed"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"
    ROLLING_BACK = "rolling_back"

@dataclass
class EnvironmentDeployment:
    environment: Environment
    status: DeploymentStatus
    deployment_id: Optional[str] = None
    deployment_url: Optional[str] = None
    last_deployed: Optional[str] = None
    error_message: Optional[str] = None
    cost_estimate: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "environment": self.environment.value,
            "status": self.status.value,
            "deployment_id": self.deployment_id,
            "deployment_url": self.deployment_url,
            "last_deployed": self.last_deployed,
            "error_message": self.error_message,
            "cost_estimate": self.cost_estimate
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnvironmentDeployment":
        return cls(
            environment=Environment(data["environment"]),
            status=DeploymentStatus(data["status"]),
            deployment_id=data.get("deployment_id"),
            deployment_url=data.get("deployment_url"),
            last_deployed=data.get("last_deployed"),
            error_message=data.get("error_message"),
            cost_estimate=data.get("cost_estimate")
        )

@dataclass
class ProjectState:
    project_id: str
    project_name: str
    project_type: str
    repository_url: Optional[str]
    created_at: str
    updated_at: str
    environments: Dict[Environment, EnvironmentDeployment]
    total_deployments: int = 0
    last_activity: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "project_type": self.project_type,
            "repository_url": self.repository_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "environments": {env.value: deployment.to_dict() for env, deployment in self.environments.items()},
            "total_deployments": self.total_deployments,
            "last_activity": self.last_activity
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectState":
        environments = {}
        for env_name, env_data in data.get("environments", {}).items():
            env = Environment(env_name)
            environments[env] = EnvironmentDeployment.from_dict(env_data)
        
        return cls(
            project_id=data["project_id"],
            project_name=data["project_name"],
            project_type=data["project_type"],
            repository_url=data.get("repository_url"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            environments=environments,
            total_deployments=data.get("total_deployments", 0),
            last_activity=data.get("last_activity")
        )

class ProjectStateManager:
    """Manages project states with SQLite persistence"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path.cwd() / "project_states.db"
        
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    project_type TEXT NOT NULL,
                    repository_url TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    total_deployments INTEGER DEFAULT 0,
                    last_activity TEXT,
                    state_json TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS environment_deployments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    environment TEXT NOT NULL,
                    status TEXT NOT NULL,
                    deployment_id TEXT,
                    deployment_url TEXT,
                    deployed_at TEXT,
                    error_message TEXT,
                    cost_estimate REAL,
                    FOREIGN KEY (project_id) REFERENCES projects (project_id),
                    UNIQUE(project_id, environment)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS deployment_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    environment TEXT NOT NULL,
                    deployment_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    error_message TEXT,
                    deployment_url TEXT,
                    cost_estimate REAL,
                    FOREIGN KEY (project_id) REFERENCES projects (project_id)
                )
            ''')
            
            conn.commit()
    
    async def create_project(self,
                           project_id: str,
                           project_name: str,
                           project_type: str,
                           repository_url: str = None) -> ProjectState:
        """Create a new project state"""
        
        now = datetime.utcnow().isoformat()
        
        project_state = ProjectState(
            project_id=project_id,
            project_name=project_name,
            project_type=project_type,
            repository_url=repository_url,
            created_at=now,
            updated_at=now,
            environments={}
        )
        
        # Initialize all environments as not deployed
        for env in Environment:
            project_state.environments[env] = EnvironmentDeployment(
                environment=env,
                status=DeploymentStatus.NOT_DEPLOYED
            )
        
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO projects 
                    (project_id, project_name, project_type, repository_url, created_at, updated_at, state_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    project_id,
                    project_name,
                    project_type,
                    repository_url,
                    now,
                    now,
                    json.dumps(project_state.to_dict())
                ))
                
                # Initialize environment deployments
                for env in Environment:
                    conn.execute('''
                        INSERT OR REPLACE INTO environment_deployments
                        (project_id, environment, status)
                        VALUES (?, ?, ?)
                    ''', (project_id, env.value, DeploymentStatus.NOT_DEPLOYED.value))
                
                conn.commit()
        
        return project_state
    
    async def get_project_state(self, project_id: str) -> Optional[ProjectState]:
        """Get project state by ID"""
        
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT state_json FROM projects WHERE project_id = ?
                ''', (project_id,))
                
                row = cursor.fetchone()
                if row:
                    state_data = json.loads(row[0])
                    return ProjectState.from_dict(state_data)
        
        return None
    
    async def list_projects(self, user_id: str = None) -> List[ProjectState]:
        """List all projects or projects for a specific user"""
        
        projects = []
        
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT state_json FROM projects ORDER BY updated_at DESC
                ''')
                
                for row in cursor.fetchall():
                    state_data = json.loads(row[0])
                    projects.append(ProjectState.from_dict(state_data))
        
        return projects
    
    async def update_deployment_status(self,
                                     project_id: str,
                                     environment: Environment,
                                     status: DeploymentStatus,
                                     deployment_id: str = None,
                                     deployment_url: str = None,
                                     error_message: str = None,
                                     cost_estimate: float = None):
        """Update deployment status for an environment"""
        
        now = datetime.utcnow().isoformat()
        
        # Get current project state
        project_state = await self.get_project_state(project_id)
        if not project_state:
            raise ValueError(f"Project {project_id} not found")
        
        # Update environment deployment
        env_deployment = project_state.environments.get(environment)
        if not env_deployment:
            env_deployment = EnvironmentDeployment(
                environment=environment,
                status=status
            )
            project_state.environments[environment] = env_deployment
        
        env_deployment.status = status
        if deployment_id:
            env_deployment.deployment_id = deployment_id
        if deployment_url:
            env_deployment.deployment_url = deployment_url
        if error_message:
            env_deployment.error_message = error_message
        if cost_estimate:
            env_deployment.cost_estimate = cost_estimate
        
        if status == DeploymentStatus.DEPLOYED:
            env_deployment.last_deployed = now
            project_state.total_deployments += 1
        
        project_state.updated_at = now
        project_state.last_activity = now
        
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                # Update project state
                conn.execute('''
                    UPDATE projects 
                    SET updated_at = ?, total_deployments = ?, last_activity = ?, state_json = ?
                    WHERE project_id = ?
                ''', (
                    now,
                    project_state.total_deployments,
                    now,
                    json.dumps(project_state.to_dict()),
                    project_id
                ))
                
                # Update environment deployment
                conn.execute('''
                    UPDATE environment_deployments
                    SET status = ?, deployment_id = ?, deployment_url = ?, 
                        deployed_at = ?, error_message = ?, cost_estimate = ?
                    WHERE project_id = ? AND environment = ?
                ''', (
                    status.value,
                    deployment_id,
                    deployment_url,
                    now if status == DeploymentStatus.DEPLOYED else None,
                    error_message,
                    cost_estimate,
                    project_id,
                    environment.value
                ))
                
                # Add to deployment history
                conn.execute('''
                    INSERT INTO deployment_history
                    (project_id, environment, deployment_id, status, started_at, 
                     completed_at, error_message, deployment_url, cost_estimate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    project_id,
                    environment.value,
                    deployment_id or '',
                    status.value,
                    now,
                    now if status in [DeploymentStatus.DEPLOYED, DeploymentStatus.FAILED] else None,
                    error_message,
                    deployment_url,
                    cost_estimate
                ))
                
                conn.commit()
    
    async def get_deployment_history(self,
                                   project_id: str,
                                   environment: Environment = None,
                                   limit: int = 50) -> List[Dict[str, Any]]:
        """Get deployment history for a project"""
        
        history = []
        
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                if environment:
                    cursor = conn.execute('''
                        SELECT * FROM deployment_history 
                        WHERE project_id = ? AND environment = ?
                        ORDER BY started_at DESC
                        LIMIT ?
                    ''', (project_id, environment.value, limit))
                else:
                    cursor = conn.execute('''
                        SELECT * FROM deployment_history 
                        WHERE project_id = ?
                        ORDER BY started_at DESC
                        LIMIT ?
                    ''', (project_id, limit))
                
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    history.append(dict(zip(columns, row)))
        
        return history
    
    async def get_environment_stats(self, project_id: str = None) -> Dict[str, Any]:
        """Get environment deployment statistics"""
        
        stats = {
            "total_projects": 0,
            "environments": {env.value: {"deployed": 0, "failed": 0, "deploying": 0} for env in Environment},
            "recent_deployments": 0,
            "cost_total": 0.0
        }
        
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                # Total projects
                if project_id:
                    cursor = conn.execute('SELECT COUNT(*) FROM projects WHERE project_id = ?', (project_id,))
                else:
                    cursor = conn.execute('SELECT COUNT(*) FROM projects')
                stats["total_projects"] = cursor.fetchone()[0]
                
                # Environment stats
                for env in Environment:
                    for status in [DeploymentStatus.DEPLOYED, DeploymentStatus.FAILED, DeploymentStatus.DEPLOYING]:
                        if project_id:
                            cursor = conn.execute('''
                                SELECT COUNT(*) FROM environment_deployments 
                                WHERE environment = ? AND status = ? AND project_id = ?
                            ''', (env.value, status.value, project_id))
                        else:
                            cursor = conn.execute('''
                                SELECT COUNT(*) FROM environment_deployments 
                                WHERE environment = ? AND status = ?
                            ''', (env.value, status.value))
                        
                        count = cursor.fetchone()[0]
                        stats["environments"][env.value][status.value] = count
                
                # Recent deployments (last 7 days)
                week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
                if project_id:
                    cursor = conn.execute('''
                        SELECT COUNT(*) FROM deployment_history 
                        WHERE started_at > ? AND project_id = ?
                    ''', (week_ago, project_id))
                else:
                    cursor = conn.execute('''
                        SELECT COUNT(*) FROM deployment_history 
                        WHERE started_at > ?
                    ''', (week_ago,))
                stats["recent_deployments"] = cursor.fetchone()[0]
                
                # Total cost estimate
                if project_id:
                    cursor = conn.execute('''
                        SELECT SUM(cost_estimate) FROM environment_deployments 
                        WHERE cost_estimate IS NOT NULL AND project_id = ?
                    ''', (project_id,))
                else:
                    cursor = conn.execute('''
                        SELECT SUM(cost_estimate) FROM environment_deployments 
                        WHERE cost_estimate IS NOT NULL
                    ''')
                
                result = cursor.fetchone()[0]
                stats["cost_total"] = float(result) if result else 0.0
        
        return stats
    
    async def cleanup_old_deployments(self, days_to_keep: int = 30):
        """Clean up old deployment history records"""
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()
        
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    DELETE FROM deployment_history 
                    WHERE started_at < ? AND status IN (?, ?)
                ''', (cutoff_date, DeploymentStatus.DEPLOYED.value, DeploymentStatus.FAILED.value))
                
                deleted_count = cursor.rowcount
                conn.commit()
        
        return deleted_count
    
    async def delete_project(self, project_id: str):
        """Delete a project and all its deployment data"""
        
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM deployment_history WHERE project_id = ?', (project_id,))
                conn.execute('DELETE FROM environment_deployments WHERE project_id = ?', (project_id,))
                conn.execute('DELETE FROM projects WHERE project_id = ?', (project_id,))
                conn.commit()
