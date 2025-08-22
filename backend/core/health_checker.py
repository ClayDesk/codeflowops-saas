# Phase 1: Health Checker and Monitoring
# backend/core/health_checker.py

"""
Comprehensive health checking and monitoring system
This is a NEW component that adds monitoring without affecting existing deployments
"""

import asyncio
import aiohttp
import boto3
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """Health check result"""
    service_name: str
    status: HealthStatus
    response_time_ms: float
    timestamp: datetime
    details: Dict[str, Any]
    error_message: Optional[str] = None

@dataclass
class ServiceEndpoint:
    """Service endpoint configuration"""
    name: str
    url: str
    method: str = "GET"
    expected_status: int = 200
    timeout_seconds: int = 10
    headers: Dict[str, str] = None
    body: Optional[str] = None

class HealthChecker:
    """
    Comprehensive health monitoring for deployed applications
    ✅ Monitors React, Next.js, APIs, and databases
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.cloudwatch = boto3.client('cloudwatch')
        self.rds = boto3.client('rds')
        self.elbv2 = boto3.client('elbv2')
        
        # ✅ Standard health check endpoints
        self.standard_endpoints = [
            '/',
            '/health',
            '/api/health',
            '/healthcheck',
            '/_next/static/health'  # Next.js specific
        ]
    
    async def check_application_health(self, base_url: str, app_type: str = "react") -> List[HealthCheckResult]:
        """
        Check health of deployed application
        ✅ Supports React, Next.js, static sites, and APIs
        """
        
        results = []
        endpoints = self._get_endpoints_for_app_type(app_type, base_url)
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for endpoint in endpoints:
                task = self._check_single_endpoint(session, endpoint)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and convert to HealthCheckResult
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                valid_results.append(HealthCheckResult(
                    service_name=endpoints[i].name,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0.0,
                    timestamp=datetime.now(),
                    details={},
                    error_message=str(result)
                ))
            else:
                valid_results.append(result)
        
        logger.info(f"✅ Completed health check for {base_url} - {len(valid_results)} endpoints checked")
        return valid_results
    
    def _get_endpoints_for_app_type(self, app_type: str, base_url: str) -> List[ServiceEndpoint]:
        """Get appropriate endpoints based on application type"""
        
        endpoints = []
        
        if app_type in ["react", "static"]:
            endpoints = [
                ServiceEndpoint(f"{app_type}_main", f"{base_url}/"),
                ServiceEndpoint(f"{app_type}_assets", f"{base_url}/static/js/", expected_status=404),  # Check assets load
            ]
            
        elif app_type == "nextjs":
            endpoints = [
                ServiceEndpoint("nextjs_main", f"{base_url}/"),
                ServiceEndpoint("nextjs_health", f"{base_url}/_next/static/health", expected_status=404),
                ServiceEndpoint("nextjs_api", f"{base_url}/api/health", expected_status=404),  # May not exist
            ]
            
        elif app_type.startswith("api"):
            endpoints = [
                ServiceEndpoint("api_health", f"{base_url}/health"),
                ServiceEndpoint("api_status", f"{base_url}/status"),
                ServiceEndpoint("api_info", f"{base_url}/info", expected_status=404),  # Optional
            ]
        
        return endpoints
    
    async def _check_single_endpoint(self, session: aiohttp.ClientSession, endpoint: ServiceEndpoint) -> HealthCheckResult:
        """Check a single endpoint"""
        
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=endpoint.timeout_seconds)
            
            async with session.request(
                endpoint.method,
                endpoint.url,
                headers=endpoint.headers or {},
                data=endpoint.body,
                timeout=timeout
            ) as response:
                
                response_time_ms = (time.time() - start_time) * 1000
                response_text = await response.text()
                
                # Determine health status
                if response.status == endpoint.expected_status:
                    status = HealthStatus.HEALTHY
                elif response.status in [200, 201, 202, 204]:
                    status = HealthStatus.HEALTHY  # Generally healthy statuses
                elif response.status in [404, 405]:
                    status = HealthStatus.DEGRADED  # Endpoint may not exist but app is running
                else:
                    status = HealthStatus.UNHEALTHY
                
                return HealthCheckResult(
                    service_name=endpoint.name,
                    status=status,
                    response_time_ms=response_time_ms,
                    timestamp=datetime.now(),
                    details={
                        'status_code': response.status,
                        'content_length': len(response_text),
                        'headers': dict(response.headers)
                    }
                )
                
        except asyncio.TimeoutError:
            response_time_ms = endpoint.timeout_seconds * 1000
            return HealthCheckResult(
                service_name=endpoint.name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                timestamp=datetime.now(),
                details={},
                error_message=f"Request timed out after {endpoint.timeout_seconds}s"
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name=endpoint.name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                timestamp=datetime.now(),
                details={},
                error_message=str(e)
            )
    
    def check_rds_health(self, db_instance_identifier: str) -> HealthCheckResult:
        """
        Check RDS database health
        ✅ Monitors database availability and performance
        """
        
        start_time = time.time()
        
        try:
            response = self.rds.describe_db_instances(
                DBInstanceIdentifier=db_instance_identifier
            )
            
            db_instance = response['DBInstances'][0]
            db_status = db_instance['DBInstanceStatus']
            
            # Determine health based on RDS status
            if db_status == 'available':
                status = HealthStatus.HEALTHY
            elif db_status in ['creating', 'modifying', 'backing-up']:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            response_time_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service_name=f"rds_{db_instance_identifier}",
                status=status,
                response_time_ms=response_time_ms,
                timestamp=datetime.now(),
                details={
                    'db_status': db_status,
                    'engine': db_instance['Engine'],
                    'engine_version': db_instance['EngineVersion'],
                    'allocated_storage': db_instance['AllocatedStorage'],
                    'multi_az': db_instance['MultiAZ']
                }
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name=f"rds_{db_instance_identifier}",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                timestamp=datetime.now(),
                details={},
                error_message=str(e)
            )
    
    def check_load_balancer_health(self, load_balancer_arn: str) -> HealthCheckResult:
        """
        Check Application Load Balancer health
        ✅ Monitors ALB and target health for API deployments
        """
        
        start_time = time.time()
        
        try:
            # Get load balancer details
            lb_response = self.elbv2.describe_load_balancers(
                LoadBalancerArns=[load_balancer_arn]
            )
            
            lb = lb_response['LoadBalancers'][0]
            lb_state = lb['State']['Code']
            
            # Get target groups
            tg_response = self.elbv2.describe_target_groups(
                LoadBalancerArn=load_balancer_arn
            )
            
            healthy_targets = 0
            total_targets = 0
            
            for target_group in tg_response['TargetGroups']:
                tg_arn = target_group['TargetGroupArn']
                health_response = self.elbv2.describe_target_health(
                    TargetGroupArn=tg_arn
                )
                
                for target_health in health_response['TargetHealthDescriptions']:
                    total_targets += 1
                    if target_health['TargetHealth']['State'] == 'healthy':
                        healthy_targets += 1
            
            # Determine overall health
            if lb_state == 'active' and healthy_targets == total_targets and total_targets > 0:
                status = HealthStatus.HEALTHY
            elif lb_state == 'active' and healthy_targets > 0:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            response_time_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service_name=f"alb_{lb['LoadBalancerName']}",
                status=status,
                response_time_ms=response_time_ms,
                timestamp=datetime.now(),
                details={
                    'lb_state': lb_state,
                    'healthy_targets': healthy_targets,
                    'total_targets': total_targets,
                    'dns_name': lb['DNSName'],
                    'target_groups': len(tg_response['TargetGroups'])
                }
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service_name="alb_unknown",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                timestamp=datetime.now(),
                details={},
                error_message=str(e)
            )
    
    def publish_metrics_to_cloudwatch(self, results: List[HealthCheckResult], namespace: str = "CodeFlowOps/Health"):
        """
        Publish health metrics to CloudWatch
        ✅ Custom metrics for monitoring and alerting
        """
        
        try:
            metrics = []
            
            for result in results:
                # Health status metric (1 = healthy, 0 = unhealthy)
                health_value = 1 if result.status == HealthStatus.HEALTHY else 0
                
                metrics.append({
                    'MetricName': 'ServiceHealth',
                    'Dimensions': [
                        {'Name': 'ServiceName', 'Value': result.service_name}
                    ],
                    'Value': health_value,
                    'Unit': 'None',
                    'Timestamp': result.timestamp
                })
                
                # Response time metric
                metrics.append({
                    'MetricName': 'ResponseTime',
                    'Dimensions': [
                        {'Name': 'ServiceName', 'Value': result.service_name}
                    ],
                    'Value': result.response_time_ms,
                    'Unit': 'Milliseconds',
                    'Timestamp': result.timestamp
                })
            
            # Publish in batches (CloudWatch limit is 20 metrics per request)
            for i in range(0, len(metrics), 20):
                batch = metrics[i:i+20]
                self.cloudwatch.put_metric_data(
                    Namespace=namespace,
                    MetricData=batch
                )
            
            logger.info(f"✅ Published {len(metrics)} metrics to CloudWatch")
            
        except Exception as e:
            logger.error(f"Failed to publish metrics to CloudWatch: {e}")
    
    def generate_health_report(self, results: List[HealthCheckResult]) -> Dict[str, Any]:
        """
        Generate comprehensive health report
        ✅ Summary report for dashboard display
        """
        
        total_services = len(results)
        healthy_services = sum(1 for r in results if r.status == HealthStatus.HEALTHY)
        degraded_services = sum(1 for r in results if r.status == HealthStatus.DEGRADED)
        unhealthy_services = sum(1 for r in results if r.status == HealthStatus.UNHEALTHY)
        
        avg_response_time = sum(r.response_time_ms for r in results) / total_services if total_services > 0 else 0
        
        # Overall system health
        if unhealthy_services == 0 and degraded_services == 0:
            overall_status = HealthStatus.HEALTHY
        elif unhealthy_services == 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNHEALTHY
        
        report = {
            'overall_status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_services': total_services,
                'healthy_services': healthy_services,
                'degraded_services': degraded_services,
                'unhealthy_services': unhealthy_services,
                'health_percentage': (healthy_services / total_services * 100) if total_services > 0 else 0,
                'avg_response_time_ms': round(avg_response_time, 2)
            },
            'service_details': [
                {
                    'service_name': r.service_name,
                    'status': r.status.value,
                    'response_time_ms': round(r.response_time_ms, 2),
                    'error_message': r.error_message,
                    'details': r.details
                }
                for r in results
            ]
        }
        
        logger.info(f"✅ Generated health report: {healthy_services}/{total_services} services healthy")
        return report
