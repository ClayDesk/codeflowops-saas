"""
Enhanced Production Monitoring Service
Comprehensive monitoring with CloudWatch integration, alerting, and performance tracking
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import boto3
import aiohttp
import time

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class MetricType(Enum):
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"

@dataclass
class PerformanceMetric:
    metric_type: MetricType
    value: float
    timestamp: datetime
    unit: str
    deployment_id: str
    tags: Optional[Dict[str, str]] = field(default=None)

@dataclass
class Alert:
    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    deployment_id: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None

class ProductionMonitoringService:
    """Enhanced monitoring service for production deployments"""
    
    def __init__(self, aws_region: str = "us-east-1"):
        self.aws_region = aws_region
        self.cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
        self.sns = boto3.client('sns', region_name=aws_region)
        
        # In-memory stores (in production, use Redis/DynamoDB)
        self.active_deployments: Dict[str, Dict] = {}
        self.performance_metrics: Dict[str, List[PerformanceMetric]] = {}
        self.active_alerts: Dict[str, Alert] = {}
        
        # Monitoring configuration
        self.monitoring_config = {
            "health_check_interval": 60,  # seconds
            "performance_check_interval": 300,  # seconds
            "alert_thresholds": {
                MetricType.RESPONSE_TIME: 3000,  # ms
                MetricType.ERROR_RATE: 5.0,  # percentage
                MetricType.CPU_USAGE: 80.0,  # percentage
                MetricType.MEMORY_USAGE: 85.0,  # percentage
            }
        }
    
    async def start_monitoring_deployment(
        self,
        deployment_id: str,
        deployment_url: str,
        monitoring_config: Optional[Dict] = None
    ) -> bool:
        """Start comprehensive monitoring for a deployment"""
        try:
            deployment_info = {
                "deployment_id": deployment_id,
                "deployment_url": deployment_url,
                "monitoring_started": datetime.utcnow(),
                "status": "monitoring",
                "health_status": "unknown",
                "last_health_check": None,
                "performance_summary": {},
                "alert_count": 0,
                "config": monitoring_config or self.monitoring_config
            }
            
            self.active_deployments[deployment_id] = deployment_info
            self.performance_metrics[deployment_id] = []
            
            # Start monitoring tasks
            asyncio.create_task(self._health_check_loop(deployment_id))
            asyncio.create_task(self._performance_monitoring_loop(deployment_id))
            asyncio.create_task(self._cost_monitoring_loop(deployment_id))
            
            logger.info(f"✅ Started comprehensive monitoring for deployment: {deployment_id}")
            
            # Send initial CloudWatch metric
            await self._send_cloudwatch_metric(
                "DeploymentMonitoring",
                "MonitoringStarted",
                1,
                deployment_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start monitoring for {deployment_id}: {e}")
            return False
    
    async def _health_check_loop(self, deployment_id: str):
        """Continuous health checking loop"""
        deployment = self.active_deployments.get(deployment_id)
        if not deployment:
            return
        
        interval = deployment["config"].get("health_check_interval", 60)
        
        while deployment_id in self.active_deployments:
            try:
                health_result = await self._perform_health_check(deployment_id)
                
                # Update deployment status
                deployment["health_status"] = health_result["status"]
                deployment["last_health_check"] = datetime.utcnow()
                
                # Send CloudWatch metrics
                await self._send_cloudwatch_metric(
                    "DeploymentHealth",
                    "HealthStatus",
                    1 if health_result["status"] == "healthy" else 0,
                    deployment_id
                )
                
                if health_result["response_time"]:
                    await self._send_cloudwatch_metric(
                        "DeploymentPerformance",
                        "ResponseTime",
                        health_result["response_time"],
                        deployment_id,
                        unit="Milliseconds"
                    )
                
                # Check for alerts
                await self._evaluate_health_alerts(deployment_id, health_result)
                
            except Exception as e:
                logger.error(f"Health check failed for {deployment_id}: {e}")
                await self._create_alert(
                    deployment_id,
                    AlertSeverity.WARNING,
                    "Health Check Failed",
                    f"Health check error: {str(e)}"
                )
            
            await asyncio.sleep(interval)
    
    async def _performance_monitoring_loop(self, deployment_id: str):
        """Continuous performance monitoring loop"""
        deployment = self.active_deployments.get(deployment_id)
        if not deployment:
            return
        
        interval = deployment["config"].get("performance_check_interval", 300)
        
        while deployment_id in self.active_deployments:
            try:
                performance_data = await self._collect_performance_metrics(deployment_id)
                
                # Store metrics
                for metric in performance_data:
                    self.performance_metrics[deployment_id].append(metric)
                    
                    # Send to CloudWatch
                    await self._send_cloudwatch_metric(
                        "DeploymentPerformance",
                        metric.metric_type.value,
                        metric.value,
                        deployment_id,
                        unit=metric.unit
                    )
                
                # Update performance summary
                await self._update_performance_summary(deployment_id)
                
                # Check for performance alerts
                await self._evaluate_performance_alerts(deployment_id, performance_data)
                
            except Exception as e:
                logger.error(f"Performance monitoring failed for {deployment_id}: {e}")
            
            await asyncio.sleep(interval)
    
    async def _cost_monitoring_loop(self, deployment_id: str):
        """Monitor deployment costs and usage"""
        while deployment_id in self.active_deployments:
            try:
                cost_data = await self._collect_cost_metrics(deployment_id)
                
                # Send cost metrics to CloudWatch
                if cost_data:
                    await self._send_cloudwatch_metric(
                        "DeploymentCost",
                        "HourlyCost",
                        cost_data.get("hourly_cost", 0),
                        deployment_id,
                        unit="Count"
                    )
                
            except Exception as e:
                logger.error(f"Cost monitoring failed for {deployment_id}: {e}")
            
            # Check costs every hour
            await asyncio.sleep(3600)
    
    async def _perform_health_check(self, deployment_id: str) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        deployment = self.active_deployments[deployment_id]
        url = deployment["deployment_url"]
        
        health_result = {
            "status": "unhealthy",
            "response_time": None,
            "status_code": None,
            "error": None
        }
        
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                # Test main URL
                async with session.get(url) as response:
                    response_time = (time.time() - start_time) * 1000
                    health_result["response_time"] = response_time
                    health_result["status_code"] = response.status
                    
                    if response.status < 400:
                        health_result["status"] = "healthy"
                    else:
                        health_result["status"] = "degraded"
                        health_result["error"] = f"HTTP {response.status}"
                
                # Test health endpoint if available
                try:
                    health_url = f"{url.rstrip('/')}/health"
                    async with session.get(health_url) as health_response:
                        if health_response.status == 200:
                            health_data = await health_response.json()
                            health_result["health_endpoint"] = health_data
                except:
                    pass  # Health endpoint is optional
        
        except Exception as e:
            health_result["error"] = str(e)
            health_result["status"] = "unhealthy"
        
        return health_result
    
    async def _collect_performance_metrics(self, deployment_id: str) -> List[PerformanceMetric]:
        """Collect comprehensive performance metrics"""
        metrics = []
        timestamp = datetime.utcnow()
        
        try:
            deployment = self.active_deployments[deployment_id]
            url = deployment["deployment_url"]
            
            # Response time metric
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        response_time = (time.time() - start_time) * 1000
                        metrics.append(PerformanceMetric(
                            MetricType.RESPONSE_TIME,
                            response_time,
                            timestamp,
                            "Milliseconds",
                            deployment_id
                        ))
                        
                        # Error rate metric (simplified)
                        error_rate = 100.0 if response.status >= 400 else 0.0
                        metrics.append(PerformanceMetric(
                            MetricType.ERROR_RATE,
                            error_rate,
                            timestamp,
                            "Percent",
                            deployment_id
                        ))
                        
                except Exception as e:
                    # High error rate if request fails
                    metrics.append(PerformanceMetric(
                        MetricType.ERROR_RATE,
                        100.0,
                        timestamp,
                        "Percent",
                        deployment_id
                    ))
            
            # Mock infrastructure metrics (in production, get from CloudWatch/ECS)
            metrics.extend([
                PerformanceMetric(MetricType.CPU_USAGE, 45.2, timestamp, "Percent", deployment_id),
                PerformanceMetric(MetricType.MEMORY_USAGE, 62.8, timestamp, "Percent", deployment_id),
                PerformanceMetric(MetricType.THROUGHPUT, 150.0, timestamp, "Count/Second", deployment_id)
            ])
            
        except Exception as e:
            logger.error(f"Failed to collect performance metrics for {deployment_id}: {e}")
        
        return metrics
    
    async def _collect_cost_metrics(self, deployment_id: str) -> Dict[str, Any]:
        """Collect cost and usage metrics"""
        try:
            # In production, integrate with AWS Cost Explorer API
            # For now, return mock data
            return {
                "hourly_cost": 0.15,
                "daily_cost": 3.60,
                "monthly_estimate": 108.00,
                "resource_breakdown": {
                    "compute": 0.08,
                    "storage": 0.02,
                    "network": 0.05
                }
            }
        except Exception as e:
            logger.error(f"Failed to collect cost metrics for {deployment_id}: {e}")
            return {}
    
    async def _evaluate_health_alerts(self, deployment_id: str, health_result: Dict[str, Any]):
        """Evaluate health check results and create alerts if needed"""
        if health_result["status"] == "unhealthy":
            await self._create_alert(
                deployment_id,
                AlertSeverity.CRITICAL,
                "Deployment Unhealthy",
                f"Health check failed: {health_result.get('error', 'Unknown error')}"
            )
        elif health_result["status"] == "degraded":
            await self._create_alert(
                deployment_id,
                AlertSeverity.WARNING,
                "Deployment Degraded",
                f"HTTP {health_result.get('status_code')} response from deployment"
            )
    
    async def _evaluate_performance_alerts(self, deployment_id: str, metrics: List[PerformanceMetric]):
        """Evaluate performance metrics and create alerts if thresholds are exceeded"""
        thresholds = self.monitoring_config["alert_thresholds"]
        
        for metric in metrics:
            threshold = thresholds.get(metric.metric_type)
            if threshold and metric.value > threshold:
                await self._create_alert(
                    deployment_id,
                    AlertSeverity.WARNING,
                    f"High {metric.metric_type.value.replace('_', ' ').title()}",
                    f"{metric.metric_type.value} is {metric.value}{metric.unit}, exceeding threshold of {threshold}"
                )
    
    async def _create_alert(
        self,
        deployment_id: str,
        severity: AlertSeverity,
        title: str,
        description: str
    ):
        """Create and process an alert"""
        alert_id = f"{deployment_id}-{int(time.time())}"
        
        alert = Alert(
            alert_id=alert_id,
            severity=severity,
            title=title,
            description=description,
            deployment_id=deployment_id,
            timestamp=datetime.utcnow()
        )
        
        self.active_alerts[alert_id] = alert
        
        # Update deployment alert count
        if deployment_id in self.active_deployments:
            self.active_deployments[deployment_id]["alert_count"] += 1
        
        # Send CloudWatch metric
        await self._send_cloudwatch_metric(
            "DeploymentAlerts",
            "AlertCreated",
            1,
            deployment_id,
            dimensions={"Severity": severity.value}
        )
        
        # Log alert
        logger.warning(f"🚨 ALERT [{severity.value.upper()}] {title}: {description}")
        
        # In production, send to SNS for notifications
        # await self._send_sns_notification(alert)
    
    async def _send_cloudwatch_metric(
        self,
        namespace: str,
        metric_name: str,
        value: float,
        deployment_id: str,
        unit: str = "Count",
        dimensions: Optional[Dict[str, str]] = None
    ):
        """Send metric to CloudWatch"""
        try:
            metric_dimensions = [
                {"Name": "DeploymentId", "Value": deployment_id}
            ]
            
            if dimensions:
                for key, val in dimensions.items():
                    metric_dimensions.append({"Name": key, "Value": val})
            
            self.cloudwatch.put_metric_data(
                Namespace=f"CodeFlowOps/{namespace}",
                MetricData=[
                    {
                        "MetricName": metric_name,
                        "Value": value,
                        "Unit": unit,
                        "Dimensions": metric_dimensions,
                        "Timestamp": datetime.utcnow()
                    }
                ]
            )
            
        except Exception as e:
            logger.error(f"Failed to send CloudWatch metric: {e}")
    
    async def _update_performance_summary(self, deployment_id: str):
        """Update performance summary for deployment"""
        try:
            metrics = self.performance_metrics.get(deployment_id, [])
            if not metrics:
                return
            
            # Get recent metrics (last hour)
            recent_time = datetime.utcnow() - timedelta(hours=1)
            recent_metrics = [m for m in metrics if m.timestamp > recent_time]
            
            # Calculate summaries
            summary = {}
            for metric_type in MetricType:
                type_metrics = [m for m in recent_metrics if m.metric_type == metric_type]
                if type_metrics:
                    values = [m.value for m in type_metrics]
                    summary[metric_type.value] = {
                        "current": values[-1] if values else 0,
                        "average": sum(values) / len(values),
                        "max": max(values),
                        "min": min(values),
                        "count": len(values)
                    }
            
            # Update deployment performance summary
            if deployment_id in self.active_deployments:
                self.active_deployments[deployment_id]["performance_summary"] = summary
                
        except Exception as e:
            logger.error(f"Failed to update performance summary for {deployment_id}: {e}")
    
    def get_monitoring_dashboard(self, deployment_id: str) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        deployment = self.active_deployments.get(deployment_id)
        if not deployment:
            return {"error": "Deployment not found"}
        
        # Get recent alerts
        recent_alerts = [
            alert for alert in self.active_alerts.values()
            if alert.deployment_id == deployment_id and not alert.resolved
        ]
        
        return {
            "deployment_info": deployment,
            "performance_summary": deployment.get("performance_summary", {}),
            "active_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "description": alert.description,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in recent_alerts
            ],
            "monitoring_status": "active" if deployment_id in self.active_deployments else "inactive",
            "uptime_percentage": self._calculate_uptime(deployment_id),
            "cost_summary": {
                "current_hourly": 0.15,
                "daily_estimate": 3.60,
                "monthly_estimate": 108.00
            }
        }
    
    def _calculate_uptime(self, deployment_id: str) -> float:
        """Calculate deployment uptime percentage"""
        # Simplified calculation - in production, use actual health check history
        deployment = self.active_deployments.get(deployment_id)
        if not deployment:
            return 0.0
        
        if deployment["health_status"] == "healthy":
            return 99.9
        elif deployment["health_status"] == "degraded":
            return 95.0
        else:
            return 0.0
    
    async def stop_monitoring_deployment(self, deployment_id: str) -> bool:
        """Stop monitoring a deployment"""
        try:
            if deployment_id in self.active_deployments:
                del self.active_deployments[deployment_id]
                
                # Send final CloudWatch metric
                await self._send_cloudwatch_metric(
                    "DeploymentMonitoring",
                    "MonitoringStopped",
                    1,
                    deployment_id
                )
                
                logger.info(f"✅ Stopped monitoring for deployment: {deployment_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to stop monitoring for {deployment_id}: {e}")
            return False

# Singleton instance
production_monitoring_service = ProductionMonitoringService()
