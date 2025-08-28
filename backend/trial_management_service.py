"""
Comprehensive Trial Management Service
AI-Powered trial analytics with engagement scoring and conversion prediction
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class TrialMetrics:
    """Trial metrics with AI-driven insights"""
    trial_start: datetime
    trial_end: datetime
    total_deployments: int
    quota_used: int
    quota_limit: int
    days_remaining: int
    usage_percentage: float
    engagement_score: float
    conversion_likelihood: float
    last_activity: Optional[datetime]
    activity_frequency: float
    feature_usage: Dict[str, int]

class TrialAnalyticsEngine:
    """AI-powered trial analytics for engagement scoring"""
    
    def __init__(self):
        self.engagement_weights = {
            'deployment_frequency': 0.3,
            'feature_diversity': 0.25,
            'session_duration': 0.2,
            'quota_utilization': 0.15,
            'recent_activity': 0.1
        }
    
    def calculate_engagement_score(self, metrics: TrialMetrics, user_sessions: List[Dict]) -> float:
        """Calculate AI-driven engagement score (0-1)"""
        try:
            scores = {}
            
            # Deployment frequency score
            days_elapsed = max(1, (datetime.now() - metrics.trial_start).days)
            deployment_rate = metrics.total_deployments / days_elapsed
            scores['deployment_frequency'] = min(1.0, deployment_rate / 2.0)  # Normalize to 2 deployments/day max
            
            # Feature diversity score (how many different features used)
            feature_count = len(metrics.feature_usage)
            scores['feature_diversity'] = min(1.0, feature_count / 10.0)  # Max 10 features
            
            # Session duration score (average session time)
            if user_sessions:
                avg_session_duration = sum(s.get('duration', 0) for s in user_sessions) / len(user_sessions)
                scores['session_duration'] = min(1.0, avg_session_duration / 1800)  # 30 min max
            else:
                scores['session_duration'] = 0.0
            
            # Quota utilization score
            scores['quota_utilization'] = metrics.usage_percentage / 100.0
            
            # Recent activity score
            if metrics.last_activity:
                hours_since_activity = (datetime.now() - metrics.last_activity).total_seconds() / 3600
                scores['recent_activity'] = max(0.0, 1.0 - (hours_since_activity / 72))  # Decay over 3 days
            else:
                scores['recent_activity'] = 0.0
            
            # Weighted combination
            engagement_score = sum(
                scores[factor] * weight 
                for factor, weight in self.engagement_weights.items()
            )
            
            return round(engagement_score, 3)
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 0.5  # Default middle score
    
    def predict_conversion_likelihood(self, engagement_score: float, metrics: TrialMetrics) -> float:
        """AI-driven conversion prediction based on usage patterns"""
        try:
            # Base conversion likelihood from engagement
            base_likelihood = engagement_score * 0.7  # Strong correlation
            
            # Boost factors
            boosts = []
            
            # High quota usage indicates serious usage
            if metrics.usage_percentage > 80:
                boosts.append(0.15)
            elif metrics.usage_percentage > 50:
                boosts.append(0.08)
            
            # Multiple deployments indicate commitment
            if metrics.total_deployments >= 5:
                boosts.append(0.12)
            elif metrics.total_deployments >= 2:
                boosts.append(0.06)
            
            # Late-trial activity is strong signal
            days_remaining = metrics.days_remaining
            if days_remaining <= 3 and metrics.last_activity:
                hours_since = (datetime.now() - metrics.last_activity).total_seconds() / 3600
                if hours_since <= 24:
                    boosts.append(0.2)  # Very strong signal
            
            # Feature diversity indicates exploration
            feature_count = len(metrics.feature_usage)
            if feature_count >= 5:
                boosts.append(0.1)
            
            # Apply boosts
            final_likelihood = base_likelihood + sum(boosts)
            return min(1.0, round(final_likelihood, 3))
            
        except Exception as e:
            logger.error(f"Error predicting conversion: {e}")
            return engagement_score * 0.6  # Fallback

class TrialManagementService:
    """Complete trial management with AI analytics"""
    
    def __init__(self, db_path: str = "data/codeflowops.db"):
        self.db_path = db_path
        self.analytics_engine = TrialAnalyticsEngine()
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure trial-related tables exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Trial sessions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS trial_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        session_end TIMESTAMP,
                        duration INTEGER,
                        actions_taken TEXT,
                        features_used TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Trial analytics table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS trial_analytics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        engagement_score REAL,
                        conversion_likelihood REAL,
                        last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metrics_snapshot TEXT
                    )
                """)
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error creating trial tables: {e}")
    
    def get_trial_status(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive trial status with AI insights"""
        try:
            # Get base trial information
            base_metrics = self._get_base_trial_metrics(user_id)
            if not base_metrics:
                return {"error": "No trial found for user"}
            
            # Get user sessions for analytics
            user_sessions = self._get_user_sessions(user_id)
            
            # Calculate AI metrics
            engagement_score = self.analytics_engine.calculate_engagement_score(base_metrics, user_sessions)
            conversion_likelihood = self.analytics_engine.predict_conversion_likelihood(engagement_score, base_metrics)
            
            # Update analytics record
            self._update_analytics_record(user_id, engagement_score, conversion_likelihood, base_metrics)
            
            # Generate smart recommendations
            recommendations = self._generate_smart_recommendations(base_metrics, engagement_score, conversion_likelihood)
            
            # Check for warnings
            warnings = self._check_trial_warnings(base_metrics)
            
            return {
                "trial_active": True,
                "metrics": {
                    "trial_start": base_metrics.trial_start.isoformat(),
                    "trial_end": base_metrics.trial_end.isoformat(),
                    "days_remaining": base_metrics.days_remaining,
                    "total_deployments": base_metrics.total_deployments,
                    "quota_used": base_metrics.quota_used,
                    "quota_limit": base_metrics.quota_limit,
                    "usage_percentage": base_metrics.usage_percentage,
                    "engagement_score": engagement_score,
                    "conversion_likelihood": conversion_likelihood,
                    "activity_frequency": base_metrics.activity_frequency,
                    "feature_usage": base_metrics.feature_usage
                },
                "analytics": {
                    "engagement_level": self._categorize_engagement(engagement_score),
                    "conversion_category": self._categorize_conversion(conversion_likelihood),
                    "trial_health": self._assess_trial_health(base_metrics, engagement_score),
                    "usage_trend": self._analyze_usage_trend(user_sessions)
                },
                "recommendations": recommendations,
                "warnings": warnings,
                "next_actions": self._suggest_next_actions(base_metrics, engagement_score, conversion_likelihood)
            }
            
        except Exception as e:
            logger.error(f"Error getting trial status: {e}")
            return {"error": f"Failed to get trial status: {str(e)}"}
    
    def _get_base_trial_metrics(self, user_id: str) -> Optional[TrialMetrics]:
        """Get base trial metrics from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get user info
                user_result = conn.execute(
                    "SELECT created_at FROM users WHERE id = ?", (user_id,)
                ).fetchone()
                
                if not user_result:
                    return None
                
                trial_start = datetime.fromisoformat(user_result['created_at'].replace('Z', '+00:00')).replace(tzinfo=None)
                trial_end = trial_start + timedelta(days=14)
                days_remaining = max(0, (trial_end - datetime.now()).days)
                
                # Get deployment count
                deployment_count = conn.execute(
                    "SELECT COUNT(*) as count FROM deployments WHERE user_id = ?", (user_id,)
                ).fetchone()['count']
                
                # Get quota info (assume 5 for trial users)
                quota_limit = 5
                quota_used = deployment_count
                usage_percentage = (quota_used / quota_limit) * 100
                
                # Get feature usage
                feature_usage = {"deployments": deployment_count}
                
                # Calculate activity frequency
                activity_frequency = self._calculate_activity_frequency(user_id, trial_start)
                
                # Get last activity
                last_activity = self._get_last_activity(user_id)
                
                return TrialMetrics(
                    trial_start=trial_start,
                    trial_end=trial_end,
                    total_deployments=deployment_count,
                    quota_used=quota_used,
                    quota_limit=quota_limit,
                    days_remaining=days_remaining,
                    usage_percentage=usage_percentage,
                    engagement_score=0.0,  # Will be calculated
                    conversion_likelihood=0.0,  # Will be calculated
                    last_activity=last_activity,
                    activity_frequency=activity_frequency,
                    feature_usage=feature_usage
                )
                
        except Exception as e:
            logger.error(f"Error getting base trial metrics: {e}")
            return None
    
    def _get_user_sessions(self, user_id: str) -> List[Dict]:
        """Get user session data for analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                sessions = conn.execute(
                    """SELECT * FROM trial_sessions 
                       WHERE user_id = ? 
                       ORDER BY session_start DESC LIMIT 20""",
                    (user_id,)
                ).fetchall()
                
                return [dict(session) for session in sessions]
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    def _calculate_activity_frequency(self, user_id: str, trial_start: datetime) -> float:
        """Calculate user activity frequency"""
        try:
            days_elapsed = max(1, (datetime.now() - trial_start).days)
            
            with sqlite3.connect(self.db_path) as conn:
                # Count distinct days with activity
                activity_days = conn.execute(
                    """SELECT COUNT(DISTINCT DATE(created_at)) as days
                       FROM deployments 
                       WHERE user_id = ? AND created_at >= ?""",
                    (user_id, trial_start.isoformat())
                ).fetchone()[0]
            
            return round(activity_days / days_elapsed, 3)
        except Exception as e:
            logger.error(f"Error calculating activity frequency: {e}")
            return 0.0
    
    def _get_last_activity(self, user_id: str) -> Optional[datetime]:
        """Get last user activity timestamp"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = conn.execute(
                    """SELECT MAX(created_at) as last_activity
                       FROM deployments 
                       WHERE user_id = ?""",
                    (user_id,)
                ).fetchone()
                
                if result and result[0]:
                    return datetime.fromisoformat(result[0].replace('Z', '+00:00')).replace(tzinfo=None)
                return None
        except Exception as e:
            logger.error(f"Error getting last activity: {e}")
            return None
    
    def _update_analytics_record(self, user_id: str, engagement_score: float, 
                               conversion_likelihood: float, metrics: TrialMetrics):
        """Update analytics record in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO trial_analytics 
                       (user_id, engagement_score, conversion_likelihood, metrics_snapshot)
                       VALUES (?, ?, ?, ?)""",
                    (user_id, engagement_score, conversion_likelihood, json.dumps(asdict(metrics), default=str))
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating analytics record: {e}")
    
    def _generate_smart_recommendations(self, metrics: TrialMetrics, 
                                      engagement_score: float, conversion_likelihood: float) -> List[str]:
        """Generate AI-driven personalized recommendations"""
        recommendations = []
        
        # Low engagement recommendations
        if engagement_score < 0.3:
            recommendations.append("🚀 Try deploying a sample React app to see CodeFlowOps in action")
            recommendations.append("📚 Check out our quick-start tutorials for guided deployment")
        
        # Usage-based recommendations
        if metrics.usage_percentage < 20:
            recommendations.append("💡 You have plenty of deployments left - try different project types")
        elif metrics.usage_percentage > 80:
            recommendations.append("⚡ You're using your trial efficiently! Consider upgrading for unlimited deployments")
        
        # Time-based recommendations
        if metrics.days_remaining <= 3:
            recommendations.append("⏰ Trial ending soon - upgrade now to keep your deployments running")
            if conversion_likelihood > 0.7:
                recommendations.append("🎯 Based on your usage, our Pro plan would be perfect for your needs")
        
        # Feature recommendations
        if len(metrics.feature_usage) < 3:
            recommendations.append("🔧 Explore our advanced features like custom domains and SSL certificates")
        
        return recommendations
    
    def _check_trial_warnings(self, metrics: TrialMetrics) -> Dict[str, Any]:
        """Check for trial warnings"""
        warnings = {}
        
        if metrics.days_remaining <= 1:
            warnings = {
                "type": "urgent",
                "title": "Trial Expiring Tomorrow",
                "message": "Your trial expires in 1 day. Upgrade now to avoid service interruption."
            }
        elif metrics.days_remaining <= 3:
            warnings = {
                "type": "warning", 
                "title": "Trial Ending Soon",
                "message": f"Your trial expires in {metrics.days_remaining} days. Consider upgrading to continue using CodeFlowOps."
            }
        elif metrics.usage_percentage >= 100:
            warnings = {
                "type": "limit",
                "title": "Deployment Limit Reached", 
                "message": "You've used all your trial deployments. Upgrade for unlimited deployments."
            }
        
        return warnings
    
    def _categorize_engagement(self, score: float) -> str:
        """Categorize engagement level"""
        if score >= 0.8:
            return "highly_engaged"
        elif score >= 0.5:
            return "moderately_engaged"
        else:
            return "low_engagement"
    
    def _categorize_conversion(self, likelihood: float) -> str:
        """Categorize conversion likelihood"""
        if likelihood >= 0.8:
            return "very_likely"
        elif likelihood >= 0.6:
            return "likely"
        elif likelihood >= 0.4:
            return "possible"
        else:
            return "unlikely"
    
    def _assess_trial_health(self, metrics: TrialMetrics, engagement_score: float) -> str:
        """Assess overall trial health"""
        if engagement_score >= 0.7 and metrics.usage_percentage >= 50:
            return "excellent"
        elif engagement_score >= 0.5 and metrics.usage_percentage >= 20:
            return "good"
        elif engagement_score >= 0.3 or metrics.usage_percentage >= 10:
            return "fair"
        else:
            return "needs_attention"
    
    def _analyze_usage_trend(self, sessions: List[Dict]) -> str:
        """Analyze usage trend from recent sessions"""
        if len(sessions) < 2:
            return "insufficient_data"
        
        recent_sessions = sessions[:5]
        older_sessions = sessions[5:10] if len(sessions) > 5 else []
        
        if not older_sessions:
            return "new_user"
        
        recent_avg = sum(s.get('duration', 0) for s in recent_sessions) / len(recent_sessions)
        older_avg = sum(s.get('duration', 0) for s in older_sessions) / len(older_sessions)
        
        if recent_avg > older_avg * 1.2:
            return "increasing"
        elif recent_avg < older_avg * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def _suggest_next_actions(self, metrics: TrialMetrics, engagement_score: float, 
                            conversion_likelihood: float) -> List[str]:
        """Suggest personalized next actions"""
        actions = []
        
        if metrics.total_deployments == 0:
            actions.append("Create your first deployment")
        elif metrics.total_deployments < 3:
            actions.append("Try deploying different project types")
        
        if engagement_score < 0.5:
            actions.append("Explore our documentation and tutorials")
        
        if conversion_likelihood > 0.6:
            actions.append("Review our pricing plans")
            
        if metrics.days_remaining <= 3:
            actions.append("Consider upgrading to Pro plan")
        
        return actions

# Global instance
trial_service = TrialManagementService()
