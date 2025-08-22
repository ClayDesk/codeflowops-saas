"""
Audit logging module for credential access tracking.
Provides comprehensive logging of all credential-related operations.
"""

import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from .storage import CredentialAccessLog

logger = logging.getLogger(__name__)

class AuditLogger:
    """Handles audit logging for credential operations."""
    
    def __init__(self):
        """Initialize audit logger."""
        self.logger = logging.getLogger('audit')
        
        # Configure audit logger with specific formatting
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_access(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log credential access event.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            action: Action performed (CREATE, READ, UPDATE, DELETE, etc.)
            resource_type: Type of resource accessed
            resource_id: Resource identifier
            success: Whether the operation succeeded
            error_message: Error message if failed
            error_code: Error code if failed
            ip_address: Client IP address
            user_agent: Client user agent
            session_id: Session identifier
            metadata: Additional metadata
            
        Returns:
            Log entry ID
        """
        try:
            # Create log entry
            log_entry = {
                'id': str(uuid.uuid4()),
                'tenant_id': tenant_id,
                'user_id': user_id,
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'success': success,
                'error_message': error_message,
                'error_code': error_code,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'session_id': session_id,
                'metadata': metadata,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Log to file/console
            log_message = self._format_log_message(log_entry)
            
            if success:
                self.logger.info(log_message)
            else:
                self.logger.error(log_message)
            
            # TODO: Store in database when session is available
            # self._store_log_entry(log_entry)
            
            return log_entry['id']
            
        except Exception as e:
            # Fallback logging - never fail the main operation due to audit logging
            self.logger.error(f"Failed to log audit event: {e}")
            return str(uuid.uuid4())
    
    def _format_log_message(self, log_entry: Dict[str, Any]) -> str:
        """Format log entry for human readability."""
        message_parts = [
            f"TENANT={log_entry['tenant_id']}",
            f"USER={log_entry['user_id']}",
            f"ACTION={log_entry['action']}",
            f"RESOURCE={log_entry['resource_type']}"
        ]
        
        if log_entry.get('resource_id'):
            message_parts.append(f"RESOURCE_ID={log_entry['resource_id']}")
        
        message_parts.append(f"SUCCESS={log_entry['success']}")
        
        if log_entry.get('ip_address'):
            message_parts.append(f"IP={log_entry['ip_address']}")
        
        if not log_entry['success'] and log_entry.get('error_message'):
            message_parts.append(f"ERROR={log_entry['error_message']}")
        
        if log_entry.get('metadata'):
            metadata_str = json.dumps(log_entry['metadata'], separators=(',', ':'))
            message_parts.append(f"METADATA={metadata_str}")
        
        return " | ".join(message_parts)
    
    def _store_log_entry(self, log_entry: Dict[str, Any], db_session: Session):
        """Store log entry in database."""
        try:
            audit_log = CredentialAccessLog(
                id=uuid.UUID(log_entry['id']),
                tenant_id=uuid.UUID(log_entry['tenant_id']),
                user_id=uuid.UUID(log_entry['user_id']),
                credential_id=uuid.UUID(log_entry['resource_id']) if log_entry.get('resource_id') else None,
                action=log_entry['action'],
                resource_type=log_entry['resource_type'],
                ip_address=log_entry.get('ip_address'),
                user_agent=log_entry.get('user_agent'),
                session_id=log_entry.get('session_id'),
                success=log_entry['success'],
                error_message=log_entry.get('error_message'),
                error_code=log_entry.get('error_code'),
                metadata=log_entry.get('metadata'),
                timestamp=datetime.fromisoformat(log_entry['timestamp'])
            )
            
            db_session.add(audit_log)
            db_session.commit()
            
        except Exception as e:
            logger.error(f"Failed to store audit log in database: {e}")
            db_session.rollback()
    
    def get_audit_logs(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs with filtering.
        
        Args:
            tenant_id: Tenant identifier
            user_id: Filter by user (optional)
            action: Filter by action (optional)
            resource_type: Filter by resource type (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            List of audit log entries
        """
        # TODO: Implement database query
        # For now, return empty list
        return []
    
    def get_security_summary(
        self,
        tenant_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get security summary for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            days: Number of days to analyze
            
        Returns:
            Security summary statistics
        """
        # TODO: Implement security analysis
        return {
            'total_accesses': 0,
            'failed_attempts': 0,
            'unique_users': 0,
            'unique_ips': 0,
            'most_common_actions': [],
            'suspicious_activities': []
        }
    
    def detect_anomalies(
        self,
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalous access patterns.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User to analyze (optional)
            
        Returns:
            List of detected anomalies
        """
        # TODO: Implement anomaly detection
        # - Unusual access times
        # - Geographic anomalies
        # - Access pattern changes
        # - Bulk operations
        # - Failed authentication spikes
        
        return []
