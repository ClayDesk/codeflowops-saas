"""
Formatters utility for CodeFlowOps
Provides formatting functions for API responses and data presentation
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


def format_session_list(sessions: List[Dict[str, Any]], include_details: bool = False) -> List[Dict[str, Any]]:
    """
    Format session list for API response
    
    Args:
        sessions: List of session dictionaries
        include_details: Whether to include detailed information
        
    Returns:
        Formatted session list
    """
    try:
        formatted_sessions = []
        
        for session in sessions:
            formatted_session = {
                "session_id": session.get("session_id"),
                "status": session.get("status", "unknown"),
                "created_at": format_timestamp(session.get("created_at")),
                "updated_at": format_timestamp(session.get("updated_at")),
                "progress_percentage": session.get("progress_percentage", 0),
                "current_step": session.get("current_step"),
                "github_url": session.get("github_url"),
                "project_name": session.get("project_name")
            }
            
            # Add deployment URL if completed
            if session.get("deployment_url"):
                formatted_session["deployment_url"] = session.get("deployment_url")
            
            # Add error details if failed
            if session.get("status") == "failed" and session.get("error_details"):
                formatted_session["error"] = session.get("error_details")
            
            # Include detailed information if requested
            if include_details:
                formatted_session.update({
                    "analysis_result": format_analysis_result(session.get("analysis_result")),
                    "deployment_config": session.get("deployment_config"),
                    "logs": format_logs(session.get("logs", [])),
                    "metrics": format_metrics(session.get("metrics"))
                })
            
            formatted_sessions.append(formatted_session)
        
        return formatted_sessions
        
    except Exception as e:
        logger.error(f"Session list formatting failed: {str(e)}")
        return []


def format_analysis_result(analysis_result: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Format analysis result for API response
    
    Args:
        analysis_result: Analysis result dictionary
        
    Returns:
        Formatted analysis result
    """
    try:
        if not analysis_result:
            return None
        
        formatted_result = {
            "project_type": analysis_result.get("project_type"),
            "framework": analysis_result.get("framework"),
            "confidence": round(analysis_result.get("confidence", 0), 2),
            "primary_language": analysis_result.get("primary_language"),
            "languages": analysis_result.get("languages", {}),
            "build_config": {
                "build_commands": analysis_result.get("build_config", {}).get("build_commands", []),
                "build_output_directory": analysis_result.get("build_config", {}).get("build_output_directory"),
                "estimated_build_time": analysis_result.get("dependencies", {}).get("estimated_build_time")
            },
            "deployment_config": {
                "type": analysis_result.get("deployment_config", {}).get("type"),
                "estimated_resources": format_resource_estimation(
                    analysis_result.get("deployment_config", {}).get("estimated_resources")
                )
            },
            "repository_info": {
                "owner": analysis_result.get("repository_info", {}).get("owner"),
                "repo": analysis_result.get("repository_info", {}).get("repo"),
                "size": format_file_size(analysis_result.get("repository_info", {}).get("size", 0)),
                "is_private": analysis_result.get("repository_info", {}).get("is_private"),
                "default_branch": analysis_result.get("repository_info", {}).get("default_branch")
            }
        }
        
        return formatted_result
        
    except Exception as e:
        logger.error(f"Analysis result formatting failed: {str(e)}")
        return None


def format_resource_estimation(resource_estimation: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Format AWS resource estimation for display
    
    Args:
        resource_estimation: Resource estimation dictionary
        
    Returns:
        Formatted resource estimation
    """
    try:
        if not resource_estimation:
            return None
        
        formatted_estimation = {
            "services": {
                "s3_bucket": resource_estimation.get("s3_bucket", False),
                "cloudfront_distribution": resource_estimation.get("cloudfront_distribution", False),
                "lambda_functions": resource_estimation.get("lambda_functions", False),
                "api_gateway": resource_estimation.get("api_gateway", False)
            },
            "cost": {
                "estimated_monthly": resource_estimation.get("estimated_monthly_cost", "Unknown"),
                "performance_tier": resource_estimation.get("performance_tier", "standard")
            },
            "deployment": {
                "cdn_regions": resource_estimation.get("cdn_regions", []),
                "type": "serverless" if resource_estimation.get("lambda_functions") else "static"
            }
        }
        
        return formatted_estimation
        
    except Exception as e:
        logger.error(f"Resource estimation formatting failed: {str(e)}")
        return None


def format_logs(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format logs for API response
    
    Args:
        logs: List of log entries
        
    Returns:
        Formatted logs
    """
    try:
        formatted_logs = []
        
        for log in logs:
            formatted_log = {
                "timestamp": format_timestamp(log.get("timestamp")),
                "level": log.get("level", "info"),
                "message": log.get("message"),
                "step": log.get("step"),
                "progress": log.get("progress")
            }
            
            if log.get("error"):
                formatted_log["error"] = log.get("error")
            
            formatted_logs.append(formatted_log)
        
        # Sort logs by timestamp (newest first)
        formatted_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return formatted_logs
        
    except Exception as e:
        logger.error(f"Logs formatting failed: {str(e)}")
        return []


def format_metrics(metrics: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Format session metrics for API response
    
    Args:
        metrics: Metrics dictionary
        
    Returns:
        Formatted metrics
    """
    try:
        if not metrics:
            return None
        
        formatted_metrics = {
            "timing": {
                "analysis_duration": format_duration(metrics.get("analysis_duration")),
                "build_duration": format_duration(metrics.get("build_duration")),
                "deployment_duration": format_duration(metrics.get("deployment_duration")),
                "total_duration": format_duration(metrics.get("total_duration"))
            },
            "resource_usage": {
                "files_processed": metrics.get("files_processed", 0),
                "build_size": format_file_size(metrics.get("build_size", 0)),
                "deployment_files": metrics.get("deployment_files", 0)
            },
            "performance": {
                "build_speed": metrics.get("build_speed"),
                "deployment_speed": metrics.get("deployment_speed")
            }
        }
        
        return formatted_metrics
        
    except Exception as e:
        logger.error(f"Metrics formatting failed: {str(e)}")
        return None


def format_timestamp(timestamp: Optional[Union[str, datetime, float]]) -> Optional[str]:
    """
    Format timestamp for consistent API response
    
    Args:
        timestamp: Timestamp to format
        
    Returns:
        Formatted timestamp string
    """
    try:
        if not timestamp:
            return None
        
        if isinstance(timestamp, str):
            # If already a string, return as-is
            return timestamp
        elif isinstance(timestamp, datetime):
            # Format datetime object
            return timestamp.isoformat()
        elif isinstance(timestamp, (int, float)):
            # Convert Unix timestamp to ISO format
            dt = datetime.fromtimestamp(timestamp)
            return dt.isoformat()
        else:
            return str(timestamp)
            
    except Exception as e:
        logger.error(f"Timestamp formatting failed: {str(e)}")
        return None


def format_duration(duration: Optional[Union[int, float]]) -> Optional[str]:
    """
    Format duration in seconds to human-readable string
    
    Args:
        duration: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    try:
        if duration is None:
            return None
        
        if duration < 60:
            return f"{duration:.1f}s"
        elif duration < 3600:
            minutes = duration / 60
            return f"{minutes:.1f}m"
        else:
            hours = duration / 3600
            return f"{hours:.1f}h"
            
    except Exception as e:
        logger.error(f"Duration formatting failed: {str(e)}")
        return None


def format_file_size(size_bytes: Optional[Union[int, float]]) -> Optional[str]:
    """
    Format file size in bytes to human-readable string
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted file size string
    """
    try:
        if size_bytes is None:
            return None
        
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        
        return f"{s} {size_names[i]}"
        
    except Exception as e:
        logger.error(f"File size formatting failed: {str(e)}")
        return None


def format_deployment_summary(deployment_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format deployment summary for API response
    
    Args:
        deployment_info: Deployment information
        
    Returns:
        Formatted deployment summary
    """
    try:
        formatted_summary = {
            "deployment_id": deployment_info.get("session_id"),
            "status": deployment_info.get("status"),
            "site_url": deployment_info.get("deployment_url"),
            "deployment_time": format_timestamp(deployment_info.get("completed_at")),
            "project_info": {
                "name": deployment_info.get("project_name"),
                "type": deployment_info.get("project_type"),
                "framework": deployment_info.get("framework"),
                "repository": deployment_info.get("github_url")
            },
            "infrastructure": {
                "hosting": "AWS S3 + CloudFront",
                "region": deployment_info.get("aws_region"),
                "cdn_enabled": True,
                "https_enabled": True
            },
            "performance": format_metrics(deployment_info.get("metrics"))
        }
        
        if deployment_info.get("error_details"):
            formatted_summary["error"] = deployment_info.get("error_details")
        
        return formatted_summary
        
    except Exception as e:
        logger.error(f"Deployment summary formatting failed: {str(e)}")
        return {}


def format_bulk_operation_results(
    operation_type: str,
    results: List[Dict[str, Any]],
    summary: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Format bulk operation results for API response
    
    Args:
        operation_type: Type of bulk operation
        results: List of individual operation results
        summary: Summary statistics
        
    Returns:
        Formatted bulk operation results
    """
    try:
        formatted_results = []
        
        for result in results:
            formatted_result = {
                "session_id": result.get("session_id"),
                "success": result.get("success", False),
                "status": result.get("status"),
                "message": result.get("message")
            }
            
            if result.get("error"):
                formatted_result["error"] = result.get("error")
            
            formatted_results.append(formatted_result)
        
        formatted_response = {
            "operation_type": operation_type,
            "timestamp": format_timestamp(datetime.now()),
            "summary": {
                "total_operations": summary.get("total", len(results)),
                "successful": summary.get("successful", 0),
                "failed": summary.get("failed", 0),
                "success_rate": f"{(summary.get('successful', 0) / max(summary.get('total', 1), 1) * 100):.1f}%"
            },
            "results": formatted_results
        }
        
        return formatted_response
        
    except Exception as e:
        logger.error(f"Bulk operation results formatting failed: {str(e)}")
        return {
            "operation_type": operation_type,
            "error": str(e),
            "results": []
        }


def format_health_check_response(health_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format health check data for API response
    
    Args:
        health_data: Health check data
        
    Returns:
        Formatted health check response
    """
    try:
        formatted_response = {
            "status": health_data.get("status", "unknown"),
            "timestamp": format_timestamp(health_data.get("timestamp")),
            "check_duration": format_duration(health_data.get("check_duration_ms", 0) / 1000),
            "components": {}
        }
        
        # Format component statuses
        components = health_data.get("components", {})
        for component_name, component_data in components.items():
            formatted_response["components"][component_name] = {
                "status": component_data.get("status", "unknown"),
                "response_time": format_duration(component_data.get("response_time_ms", 0) / 1000)
            }
            
            if component_data.get("error"):
                formatted_response["components"][component_name]["error"] = component_data.get("error")
        
        # Add system metrics if available
        if health_data.get("system_metrics"):
            system_metrics = health_data["system_metrics"]
            formatted_response["system"] = {
                "cpu_usage": f"{system_metrics.get('cpu', {}).get('usage_percent', 0):.1f}%",
                "memory_usage": f"{system_metrics.get('memory', {}).get('percent', 0):.1f}%",
                "disk_usage": f"{system_metrics.get('disk', {}).get('percent', 0):.1f}%"
            }
        
        # Add summary if available
        if health_data.get("summary"):
            formatted_response["summary"] = health_data["summary"]
        
        return formatted_response
        
    except Exception as e:
        logger.error(f"Health check response formatting failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": format_timestamp(datetime.now())
        }


def format_api_error(error_message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Format API error response
    
    Args:
        error_message: Error message
        error_code: Optional error code
        details: Optional error details
        
    Returns:
        Formatted error response
    """
    try:
        error_response = {
            "error": True,
            "message": error_message,
            "timestamp": format_timestamp(datetime.now())
        }
        
        if error_code:
            error_response["code"] = error_code
        
        if details:
            error_response["details"] = details
        
        return error_response
        
    except Exception as e:
        logger.error(f"API error formatting failed: {str(e)}")
        return {
            "error": True,
            "message": "An unexpected error occurred",
            "timestamp": format_timestamp(datetime.now())
        }
