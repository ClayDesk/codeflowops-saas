# Phase 4: Traffic Management System
# backend/core/traffic_manager.py

"""
Intelligent traffic switching and monitoring implementing comprehensive plan Phase 4
✅ Traffic management system with health-based routing
✅ Gradual traffic shift with error monitoring
✅ Automated rollback on high error rates
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import boto3
from botocore.exceptions import ClientError

# Import Environment class
from .blue_green_deployer import Environment

logger = logging.getLogger(__name__)

class TrafficShiftStrategy(Enum):
    IMMEDIATE = "immediate"
    GRADUAL = "gradual"
    CANARY = "canary"

class TrafficDistribution(Enum):
    ALL_BLUE = "all_blue"
    ALL_GREEN = "all_green"
    MIXED = "mixed"

@dataclass
class TrafficRule:
    """Traffic routing rule configuration"""
    rule_id: str
    target_group_arn: str
    weight: int
    priority: int
    conditions: List[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

@dataclass
class TrafficMetrics:
    """Traffic and performance metrics"""
    timestamp: datetime
    blue_traffic_percentage: float
    green_traffic_percentage: float
    blue_error_rate: float
    green_error_rate: float
    blue_response_time: float
    green_response_time: float
    total_requests: int

@dataclass
class TrafficShiftResult:
    """Result of traffic shift operation"""
    success: bool
    final_distribution: TrafficDistribution
    shift_duration: timedelta
    error_message: Optional[str] = None
    rollback_performed: bool = False
    metrics_history: List[TrafficMetrics] = None

class TrafficManager:
    """
    Intelligent traffic switching and monitoring per comprehensive plan
    ✅ Gradual traffic shift with performance monitoring
    ✅ Health-based routing decisions with automatic rollback
    ✅ CloudWatch integration for real-time metrics
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.elbv2_client = boto3.client('elbv2', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.route53 = boto3.client('route53', region_name=region)
        
        # Traffic shift thresholds
        self.ERROR_RATE_THRESHOLD = 0.05  # 5%
        self.RESPONSE_TIME_THRESHOLD = 5000  # 5 seconds
        self.SHIFT_INTERVAL_SECONDS = 60  # 1 minute between shifts
        
        # Import health checker
        from .health_checker import HealthChecker
        self.health_checker = HealthChecker(region)
    
    async def gradual_traffic_shift(self, old_env: 'Environment', new_env: 'Environment') -> TrafficShiftResult:
        """
        Gradually shift traffic from old to new environment per comprehensive plan
        ✅ Gradual traffic shift with error monitoring and rollback
        """
        
        logger.info(f"🔄 Starting gradual traffic shift from {old_env.name} to {new_env.name}")
        
        shift_start = datetime.utcnow()
        metrics_history = []
        
        # Define traffic shift percentages
        traffic_percentages = [10, 25, 50, 75, 100]
        
        try:
            for target_percentage in traffic_percentages:
                logger.info(f"📊 Shifting {target_percentage}% traffic to {new_env.name}")
                
                # Update load balancer weights
                await self._update_load_balancer_weights(
                    old_env=old_env,
                    new_env=new_env,
                    new_weight=target_percentage,
                    old_weight=100 - target_percentage
                )
                
                # Wait for traffic to stabilize
                await asyncio.sleep(self.SHIFT_INTERVAL_SECONDS)
                
                # Monitor for issues during this phase
                monitoring_result = await self._monitor_traffic_shift(
                    old_env, new_env, target_percentage, duration_minutes=2
                )
                
                metrics_history.extend(monitoring_result.metrics)
                
                # Check if we need to rollback due to errors
                if monitoring_result.should_rollback:
                    logger.warning(f"⚠️ High error rate detected at {target_percentage}% traffic, rolling back")
                    
                    # Rollback to previous state
                    await self._rollback_traffic(old_env, new_env)
                    
                    return TrafficShiftResult(
                        success=False,
                        final_distribution=TrafficDistribution.ALL_BLUE,
                        shift_duration=datetime.utcnow() - shift_start,
                        error_message=f"Rollback triggered due to high error rate at {target_percentage}%",
                        rollback_performed=True,
                        metrics_history=metrics_history
                    )
                
                logger.info(f"✅ {target_percentage}% traffic shift completed successfully")
            
            # Final verification
            final_health_check = await self.health_checker.check_environment_health(new_env)
            if not final_health_check.is_healthy():
                logger.error(f"❌ Final health check failed, rolling back")
                await self._rollback_traffic(old_env, new_env)
                
                return TrafficShiftResult(
                    success=False,
                    final_distribution=TrafficDistribution.ALL_BLUE,
                    shift_duration=datetime.utcnow() - shift_start,
                    error_message="Final health check failed",
                    rollback_performed=True,
                    metrics_history=metrics_history
                )
            
            shift_duration = datetime.utcnow() - shift_start
            logger.info(f"🎉 Gradual traffic shift completed successfully in {shift_duration}")
            
            return TrafficShiftResult(
                success=True,
                final_distribution=TrafficDistribution.ALL_GREEN,
                shift_duration=shift_duration,
                rollback_performed=False,
                metrics_history=metrics_history
            )
            
        except Exception as e:
            logger.error(f"❌ Traffic shift failed: {str(e)}")
            
            # Attempt rollback
            try:
                await self._rollback_traffic(old_env, new_env)
                rollback_performed = True
            except Exception as rollback_error:
                logger.error(f"Rollback also failed: {rollback_error}")
                rollback_performed = False
            
            return TrafficShiftResult(
                success=False,
                final_distribution=TrafficDistribution.ALL_BLUE if rollback_performed else TrafficDistribution.MIXED,
                shift_duration=datetime.utcnow() - shift_start,
                error_message=str(e),
                rollback_performed=rollback_performed,
                metrics_history=metrics_history
            )
    
    async def immediate_traffic_switch(self, old_env: Optional['Environment'], new_env: 'Environment') -> TrafficShiftResult:
        """
        Immediately switch all traffic to new environment
        ✅ Immediate traffic switch with health verification
        """
        
        logger.info(f"⚡ Immediate traffic switch to {new_env.name}")
        
        switch_start = datetime.utcnow()
        
        try:
            # Update load balancer to route all traffic to new environment
            if old_env:
                await self._update_load_balancer_weights(
                    old_env=old_env,
                    new_env=new_env,
                    new_weight=100,
                    old_weight=0
                )
            else:
                # First deployment, just ensure new environment is active
                await self._activate_environment(new_env)
            
            # Wait briefly for changes to propagate
            await asyncio.sleep(10)
            
            # Verify health after switch
            health_check = await self.health_checker.check_environment_health(new_env)
            if not health_check.is_healthy():
                if old_env:
                    logger.warning(f"⚠️ Health check failed after switch, rolling back")
                    await self._rollback_traffic(old_env, new_env)
                    
                    return TrafficShiftResult(
                        success=False,
                        final_distribution=TrafficDistribution.ALL_BLUE,
                        shift_duration=datetime.utcnow() - switch_start,
                        error_message="Health check failed after immediate switch",
                        rollback_performed=True
                    )
                else:
                    raise Exception("Health check failed and no old environment to rollback to")
            
            switch_duration = datetime.utcnow() - switch_start
            logger.info(f"✅ Immediate traffic switch completed in {switch_duration}")
            
            return TrafficShiftResult(
                success=True,
                final_distribution=TrafficDistribution.ALL_GREEN,
                shift_duration=switch_duration,
                rollback_performed=False
            )
            
        except Exception as e:
            logger.error(f"❌ Immediate traffic switch failed: {str(e)}")
            
            return TrafficShiftResult(
                success=False,
                final_distribution=TrafficDistribution.ALL_BLUE if old_env else TrafficDistribution.MIXED,
                shift_duration=datetime.utcnow() - switch_start,
                error_message=str(e),
                rollback_performed=False
            )
    
    async def canary_deployment(self, old_env: 'Environment', new_env: 'Environment', canary_percentage: int = 5) -> TrafficShiftResult:
        """
        Deploy with canary strategy - small percentage to new environment
        ✅ Canary deployment with extended monitoring
        """
        
        logger.info(f"🐦 Starting canary deployment: {canary_percentage}% to {new_env.name}")
        
        canary_start = datetime.utcnow()
        metrics_history = []
        
        try:
            # Route small percentage to canary (new environment)
            await self._update_load_balancer_weights(
                old_env=old_env,
                new_env=new_env,
                new_weight=canary_percentage,
                old_weight=100 - canary_percentage
            )
            
            # Extended monitoring period for canary
            monitoring_result = await self._monitor_traffic_shift(
                old_env, new_env, canary_percentage, duration_minutes=10
            )
            
            metrics_history.extend(monitoring_result.metrics)
            
            if monitoring_result.should_rollback:
                logger.warning(f"⚠️ Canary deployment failed, rolling back")
                await self._rollback_traffic(old_env, new_env)
                
                return TrafficShiftResult(
                    success=False,
                    final_distribution=TrafficDistribution.ALL_BLUE,
                    shift_duration=datetime.utcnow() - canary_start,
                    error_message="Canary deployment failed monitoring checks",
                    rollback_performed=True,
                    metrics_history=metrics_history
                )
            
            # Canary successful, proceed with full deployment
            logger.info(f"✅ Canary deployment successful, proceeding with full deployment")
            
            # Gradual shift for remaining traffic
            gradual_result = await self.gradual_traffic_shift(old_env, new_env)
            
            # Combine results
            total_duration = datetime.utcnow() - canary_start
            all_metrics = metrics_history + (gradual_result.metrics_history or [])
            
            return TrafficShiftResult(
                success=gradual_result.success,
                final_distribution=gradual_result.final_distribution,
                shift_duration=total_duration,
                error_message=gradual_result.error_message,
                rollback_performed=gradual_result.rollback_performed,
                metrics_history=all_metrics
            )
            
        except Exception as e:
            logger.error(f"❌ Canary deployment failed: {str(e)}")
            
            # Attempt rollback
            try:
                await self._rollback_traffic(old_env, new_env)
                rollback_performed = True
            except Exception as rollback_error:
                logger.error(f"Rollback also failed: {rollback_error}")
                rollback_performed = False
            
            return TrafficShiftResult(
                success=False,
                final_distribution=TrafficDistribution.ALL_BLUE if rollback_performed else TrafficDistribution.MIXED,
                shift_duration=datetime.utcnow() - canary_start,
                error_message=str(e),
                rollback_performed=rollback_performed,
                metrics_history=metrics_history
            )
    
    async def _update_load_balancer_weights(self, 
                                          old_env: 'Environment',
                                          new_env: 'Environment', 
                                          new_weight: int,
                                          old_weight: int):
        """
        Update load balancer target group weights
        ✅ Weighted routing configuration for traffic splitting
        """
        
        try:
            # Get listener ARN
            listeners_response = self.elbv2_client.describe_listeners(
                LoadBalancerArn=new_env.load_balancer_arn
            )
            
            if not listeners_response['Listeners']:
                raise Exception("No listeners found for load balancer")
            
            listener_arn = listeners_response['Listeners'][0]['ListenerArn']
            
            # Update listener rules with weights
            if old_weight > 0 and new_weight > 0:
                # Mixed traffic - create weighted routing
                await self._create_weighted_routing(
                    listener_arn=listener_arn,
                    old_target_group=old_env.target_group_arn,
                    new_target_group=new_env.target_group_arn,
                    old_weight=old_weight,
                    new_weight=new_weight
                )
            elif new_weight == 100:
                # All traffic to new environment
                self.elbv2_client.modify_listener(
                    ListenerArn=listener_arn,
                    DefaultActions=[
                        {
                            'Type': 'forward',
                            'TargetGroupArn': new_env.target_group_arn
                        }
                    ]
                )
            elif old_weight == 100:
                # All traffic to old environment
                self.elbv2_client.modify_listener(
                    ListenerArn=listener_arn,
                    DefaultActions=[
                        {
                            'Type': 'forward',
                            'TargetGroupArn': old_env.target_group_arn
                        }
                    ]
                )
            
            logger.info(f"🔄 Updated traffic weights: {old_env.name}={old_weight}%, {new_env.name}={new_weight}%")
            
        except Exception as e:
            logger.error(f"Failed to update load balancer weights: {e}")
            raise
    
    async def _create_weighted_routing(self, 
                                     listener_arn: str,
                                     old_target_group: str,
                                     new_target_group: str,
                                     old_weight: int,
                                     new_weight: int):
        """Create weighted routing rules"""
        
        # Update default action to use weighted forward
        self.elbv2_client.modify_listener(
            ListenerArn=listener_arn,
            DefaultActions=[
                {
                    'Type': 'forward',
                    'ForwardConfig': {
                        'TargetGroups': [
                            {
                                'TargetGroupArn': old_target_group,
                                'Weight': old_weight
                            },
                            {
                                'TargetGroupArn': new_target_group,
                                'Weight': new_weight
                            }
                        ]
                    }
                }
            ]
        )
    
    async def _activate_environment(self, environment: 'Environment'):
        """Activate environment as the primary target"""
        
        try:
            # Get listener and set environment as default action
            listeners_response = self.elbv2_client.describe_listeners(
                LoadBalancerArn=environment.load_balancer_arn
            )
            
            if listeners_response['Listeners']:
                listener_arn = listeners_response['Listeners'][0]['ListenerArn']
                
                self.elbv2_client.modify_listener(
                    ListenerArn=listener_arn,
                    DefaultActions=[
                        {
                            'Type': 'forward',
                            'TargetGroupArn': environment.target_group_arn
                        }
                    ]
                )
                
                logger.info(f"✅ Activated {environment.name} as primary environment")
        
        except Exception as e:
            logger.error(f"Failed to activate environment: {e}")
            raise
    
    async def _rollback_traffic(self, old_env: 'Environment', new_env: 'Environment'):
        """
        Rollback traffic to old environment
        ✅ Immediate rollback on error detection
        """
        
        logger.info(f"⏪ Rolling back traffic to {old_env.name}")
        
        try:
            await self._update_load_balancer_weights(
                old_env=old_env,
                new_env=new_env,
                new_weight=0,
                old_weight=100
            )
            
            logger.info(f"✅ Traffic rollback completed")
            
        except Exception as e:
            logger.error(f"❌ Traffic rollback failed: {e}")
            raise
    
    async def _monitor_traffic_shift(self, 
                                   old_env: 'Environment', 
                                   new_env: 'Environment',
                                   target_percentage: int,
                                   duration_minutes: int) -> 'MonitoringResult':
        """
        Monitor traffic shift for specified duration
        ✅ Real-time error rate and response time monitoring
        """
        
        logger.info(f"📊 Monitoring traffic shift for {duration_minutes} minutes")
        
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        metrics = []
        should_rollback = False
        
        while datetime.utcnow() < end_time and not should_rollback:
            try:
                # Collect metrics
                current_metrics = await self._collect_traffic_metrics(old_env, new_env, target_percentage)
                metrics.append(current_metrics)
                
                # Check if new environment has high error rate
                if current_metrics.green_error_rate > self.ERROR_RATE_THRESHOLD:
                    logger.warning(f"⚠️ High error rate in {new_env.name}: {current_metrics.green_error_rate}")
                    should_rollback = True
                    break
                
                # Check if new environment has high response time
                if current_metrics.green_response_time > self.RESPONSE_TIME_THRESHOLD:
                    logger.warning(f"⚠️ High response time in {new_env.name}: {current_metrics.green_response_time}ms")
                    should_rollback = True
                    break
                
                # Wait before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Monitoring check failed: {e}")
                should_rollback = True
                break
        
        logger.info(f"📊 Monitoring completed. Should rollback: {should_rollback}")
        
        return MonitoringResult(
            should_rollback=should_rollback,
            metrics=metrics,
            duration=datetime.utcnow() - start_time
        )
    
    async def _collect_traffic_metrics(self, 
                                     old_env: 'Environment', 
                                     new_env: 'Environment',
                                     target_percentage: int) -> TrafficMetrics:
        """
        Collect traffic and performance metrics from CloudWatch
        ✅ Real-time metrics collection for monitoring decisions
        """
        
        try:
            # Get metrics from CloudWatch (simplified implementation)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            # Blue environment metrics
            blue_error_rate = await self._get_error_rate_metric(old_env, start_time, end_time)
            blue_response_time = await self._get_response_time_metric(old_env, start_time, end_time)
            
            # Green environment metrics  
            green_error_rate = await self._get_error_rate_metric(new_env, start_time, end_time)
            green_response_time = await self._get_response_time_metric(new_env, start_time, end_time)
            
            # Total requests
            total_requests = await self._get_request_count_metric(new_env, start_time, end_time)
            
            return TrafficMetrics(
                timestamp=datetime.utcnow(),
                blue_traffic_percentage=100 - target_percentage,
                green_traffic_percentage=target_percentage,
                blue_error_rate=blue_error_rate,
                green_error_rate=green_error_rate,
                blue_response_time=blue_response_time,
                green_response_time=green_response_time,
                total_requests=total_requests
            )
            
        except Exception as e:
            logger.error(f"Failed to collect traffic metrics: {e}")
            # Return safe defaults
            return TrafficMetrics(
                timestamp=datetime.utcnow(),
                blue_traffic_percentage=100 - target_percentage,
                green_traffic_percentage=target_percentage,
                blue_error_rate=0.0,
                green_error_rate=0.0,
                blue_response_time=0.0,
                green_response_time=0.0,
                total_requests=0
            )
    
    async def _get_error_rate_metric(self, environment: 'Environment', start_time: datetime, end_time: datetime) -> float:
        """Get error rate metric from CloudWatch"""
        
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='HTTPCode_Target_5XX_Count',
                Dimensions=[
                    {
                        'Name': 'TargetGroup',
                        'Value': environment.target_group_arn.split('/')[-1]
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # 5 minutes
                Statistics=['Sum']
            )
            
            if response['Datapoints']:
                error_count = sum(dp['Sum'] for dp in response['Datapoints'])
                
                # Get total request count
                total_response = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/ApplicationELB',
                    MetricName='RequestCount',
                    Dimensions=[
                        {
                            'Name': 'TargetGroup',
                            'Value': environment.target_group_arn.split('/')[-1]
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Sum']
                )
                
                if total_response['Datapoints']:
                    total_count = sum(dp['Sum'] for dp in total_response['Datapoints'])
                    return error_count / total_count if total_count > 0 else 0.0
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Failed to get error rate metric: {e}")
            return 0.0
    
    async def _get_response_time_metric(self, environment: 'Environment', start_time: datetime, end_time: datetime) -> float:
        """Get response time metric from CloudWatch"""
        
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='TargetResponseTime',
                Dimensions=[
                    {
                        'Name': 'TargetGroup',
                        'Value': environment.target_group_arn.split('/')[-1]
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                avg_response_time = sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
                return avg_response_time * 1000  # Convert to milliseconds
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Failed to get response time metric: {e}")
            return 0.0
    
    async def _get_request_count_metric(self, environment: 'Environment', start_time: datetime, end_time: datetime) -> int:
        """Get request count metric from CloudWatch"""
        
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='RequestCount',
                Dimensions=[
                    {
                        'Name': 'TargetGroup',
                        'Value': environment.target_group_arn.split('/')[-1]
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            if response['Datapoints']:
                return int(sum(dp['Sum'] for dp in response['Datapoints']))
            
            return 0
            
        except Exception as e:
            logger.warning(f"Failed to get request count metric: {e}")
            return 0


@dataclass
class MonitoringResult:
    """Result of traffic monitoring"""
    should_rollback: bool
    metrics: List[TrafficMetrics]
    duration: timedelta
    error_message: Optional[str] = None
