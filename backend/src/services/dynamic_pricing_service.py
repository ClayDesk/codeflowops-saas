"""
Dynamic Pricing Service
Provides personalized pricing based on user context, location, and behavior
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from ..models.billing_models import PlanTier, PLAN_CONFIGS
from ..models.enhanced_models import User

logger = logging.getLogger(__name__)


class DynamicPricingService:
    """Manages dynamic pricing based on user context and business rules"""
    
    def __init__(self):
        self.base_pricing = PLAN_CONFIGS
        
    def get_personalized_pricing(
        self, 
        db: Session,
        user: Optional[User] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get personalized pricing for a user based on context
        
        Args:
            user: User object if authenticated
            context: Additional context (country, referral source, etc.)
        """
        try:
            context = context or {}
            
            # Start with base pricing
            pricing = self._get_base_pricing()
            
            # Apply geographic pricing
            pricing = self._apply_geographic_pricing(pricing, context.get('country'))
            
            # Apply user-specific discounts
            if user:
                pricing = self._apply_user_discounts(pricing, user, db)
            
            # Apply promotional pricing
            pricing = self._apply_promotional_pricing(pricing, context)
            
            # Apply A/B testing variations
            pricing = self._apply_ab_testing(pricing, context)
            
            # Add trial information
            pricing = self._add_trial_information(pricing, context)
            
            return {
                "plans": pricing,
                "currency": context.get('currency', 'USD'),
                "personalization": self._get_personalization_info(user, context),
                "recommendations": self._get_plan_recommendations(user, context)
            }
            
        except Exception as e:
            logger.error(f"Error getting personalized pricing: {e}")
            return self._get_fallback_pricing()
    
    def _get_base_pricing(self) -> List[Dict[str, Any]]:
        """Get base pricing structure"""
        plans = []
        
        for tier, config in self.base_pricing.items():
            plan = {
                "id": config["id"],
                "name": config["name"],
                "tier": tier.value,
                "price_monthly": config["price_monthly"],
                "price_yearly": config["price_yearly"],
                "max_projects": config["max_projects"],
                "max_team_members": config["max_team_members"],
                "features": config.get("features_json", "[]"),
                "description": config["description"],
                "popular": tier == PlanTier.STARTER,  # Starter is our hero plan
                "trial_days": 14 if tier in [PlanTier.STARTER, PlanTier.PRO] else 0
            }
            plans.append(plan)
            
        return plans
    
    def _apply_geographic_pricing(self, plans: List[Dict], country: Optional[str]) -> List[Dict]:
        """Apply geographic pricing adjustments"""
        if not country:
            return plans
            
        # Define pricing multipliers by country/region
        pricing_adjustments = {
            # Developing markets - reduced pricing
            'IN': 0.3,  # India
            'BR': 0.4,  # Brazil
            'MX': 0.5,  # Mexico
            'ID': 0.3,  # Indonesia
            'VN': 0.3,  # Vietnam
            'PH': 0.4,  # Philippines
            
            # European markets - standard pricing
            'DE': 1.0,  # Germany
            'FR': 1.0,  # France
            'GB': 1.0,  # UK
            'NL': 1.0,  # Netherlands
            
            # Premium markets - potential premium pricing
            'CH': 1.2,  # Switzerland
            'NO': 1.1,  # Norway
            'DK': 1.1,  # Denmark
            
            # Default for US and others
            'default': 1.0
        }
        
        multiplier = pricing_adjustments.get(country, pricing_adjustments['default'])
        
        for plan in plans:
            if plan['price_monthly'] > 0:  # Don't adjust free plans
                plan['price_monthly'] = int(plan['price_monthly'] * multiplier)
                plan['price_yearly'] = int(plan['price_yearly'] * multiplier)
                plan['geographic_discount'] = multiplier < 1.0
                
        return plans
    
    def _apply_user_discounts(self, plans: List[Dict], user: User, db: Session) -> List[Dict]:
        """Apply user-specific discounts"""
        try:
            # First-time user discount (if registered < 7 days ago)
            if user.created_at and (datetime.utcnow() - user.created_at).days < 7:
                for plan in plans:
                    if plan['tier'] == 'starter':
                        plan['first_time_discount'] = 0.5  # 50% off first month
                        plan['promotional_price'] = int(plan['price_monthly'] * 0.5)
            
            # Student discount (if email contains .edu)
            if user.email and '.edu' in user.email:
                for plan in plans:
                    if plan['price_monthly'] > 0:
                        plan['student_discount'] = 0.7  # 30% off
                        plan['promotional_price'] = int(plan['price_monthly'] * 0.7)
            
            return plans
            
        except Exception as e:
            logger.error(f"Error applying user discounts: {e}")
            return plans
    
    def _apply_promotional_pricing(self, plans: List[Dict], context: Dict) -> List[Dict]:
        """Apply current promotional campaigns"""
        current_date = datetime.utcnow()
        
        # Black Friday / Holiday promotions
        if self._is_holiday_season(current_date):
            for plan in plans:
                if plan['tier'] in ['starter', 'pro']:
                    plan['holiday_discount'] = 0.6  # 40% off
                    plan['promotional_price'] = int(plan['price_monthly'] * 0.6)
                    plan['promotion_name'] = "Holiday Special"
                    plan['promotion_expires'] = "December 31st"
        
        # Referral discounts
        if context.get('referral_code'):
            for plan in plans:
                if plan['price_monthly'] > 0:
                    plan['referral_discount'] = 0.8  # 20% off
                    plan['promotional_price'] = int(plan['price_monthly'] * 0.8)
        
        return plans
    
    def _apply_ab_testing(self, plans: List[Dict], context: Dict) -> List[Dict]:
        """Apply A/B testing variations"""
        ab_variant = context.get('ab_variant', 'control')
        
        if ab_variant == 'aggressive_starter':
            # Test: Make starter plan more attractive
            for plan in plans:
                if plan['tier'] == 'starter':
                    plan['max_projects'] = 15  # Increase from 10 to 15
                    plan['ab_test'] = 'aggressive_starter'
        
        elif ab_variant == 'pro_emphasis':
            # Test: Make pro plan the popular choice
            for plan in plans:
                plan['popular'] = plan['tier'] == 'pro'
                if plan['tier'] == 'pro':
                    plan['ab_test'] = 'pro_emphasis'
        
        return plans
    
    def _add_trial_information(self, plans: List[Dict], context: Dict) -> List[Dict]:
        """Add trial period information"""
        for plan in plans:
            if plan['tier'] == 'starter':
                plan['trial_days'] = 14
                plan['trial_description'] = "14-day free trial, no credit card required"
            elif plan['tier'] == 'pro':
                plan['trial_days'] = 7
                plan['trial_description'] = "7-day free trial"
            else:
                plan['trial_days'] = 0
                
        return plans
    
    def _get_plan_recommendations(self, user: Optional[User], context: Dict) -> Dict[str, Any]:
        """Get personalized plan recommendations"""
        recommendations = {
            "recommended_plan": "starter",
            "reason": "Most popular choice for developers",
            "savings_opportunity": None
        }
        
        # Analyze user context for better recommendations
        if context.get('company_size'):
            size = context['company_size']
            if size == 'solo':
                recommendations['recommended_plan'] = 'starter'
                recommendations['reason'] = 'Perfect for individual developers'
            elif size in ['small_team', '2-10']:
                recommendations['recommended_plan'] = 'pro'
                recommendations['reason'] = 'Great for small teams with collaboration needs'
            elif size in ['large_team', '10+']:
                recommendations['recommended_plan'] = 'enterprise'
                recommendations['reason'] = 'Enterprise features for large teams'
        
        # Add savings opportunity
        if context.get('annual_billing_interest'):
            recommendations['savings_opportunity'] = {
                'type': 'annual_billing',
                'description': 'Save 20% with annual billing',
                'savings_amount': 'Up to $120/year'
            }
        
        return recommendations
    
    def _get_personalization_info(self, user: Optional[User], context: Dict) -> Dict[str, Any]:
        """Get information about applied personalizations"""
        personalizations = []
        
        if context.get('country') and context['country'] != 'US':
            personalizations.append({
                'type': 'geographic',
                'description': f'Pricing adjusted for {context["country"]}'
            })
        
        if user and user.email and '.edu' in user.email:
            personalizations.append({
                'type': 'student',
                'description': 'Student discount applied'
            })
        
        if context.get('referral_code'):
            personalizations.append({
                'type': 'referral',
                'description': 'Referral discount applied'
            })
        
        return {
            'applied': personalizations,
            'user_segment': self._get_user_segment(user, context)
        }
    
    def _get_user_segment(self, user: Optional[User], context: Dict) -> str:
        """Determine user segment for analytics"""
        if not user:
            return 'anonymous'
        
        if user.email and '.edu' in user.email:
            return 'student'
        
        if context.get('company_size') == 'solo':
            return 'individual_developer'
        elif context.get('company_size') in ['small_team', '2-10']:
            return 'small_team'
        elif context.get('company_size') in ['large_team', '10+']:
            return 'enterprise'
        
        return 'general'
    
    def _is_holiday_season(self, date: datetime) -> bool:
        """Check if current date is in holiday promotion period"""
        # Black Friday to New Year
        current_year = date.year
        holiday_start = datetime(current_year, 11, 25)  # Black Friday approx
        holiday_end = datetime(current_year + 1, 1, 3)   # End of New Year
        
        return holiday_start <= date <= holiday_end
    
    def _get_fallback_pricing(self) -> Dict[str, Any]:
        """Fallback pricing if personalization fails"""
        return {
            "plans": self._get_base_pricing(),
            "currency": "USD",
            "personalization": {"applied": [], "user_segment": "general"},
            "recommendations": {
                "recommended_plan": "starter",
                "reason": "Most popular choice"
            }
        }


# Global instance
dynamic_pricing_service = DynamicPricingService()
