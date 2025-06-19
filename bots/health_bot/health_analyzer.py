"""Health data analyzer for generating status and insights."""
from enum import Enum
from typing import List
from pydantic import BaseModel

from oura_client import HealthData
from config import Config


class HealthStatus(Enum):
    """Health status levels."""
    EXCELLENT = "🟢 Excellent"
    GOOD = "🟡 Good" 
    AVERAGE = "🟠 Average"
    NEEDS_IMPROVEMENT = "🔴 Needs Improvement"


class HealthInsight(BaseModel):
    """Health insight and analysis."""
    status: HealthStatus
    score: int  # 0-100
    message: str
    tips: List[str]
    detailed_metrics: dict


class HealthAnalyzer:
    """Analyzes comprehensive health data and generates insights."""
    
    def __init__(self):
        self.config = Config()
    
    def analyze(self, health_data: HealthData) -> HealthInsight:
        """
        Analyze comprehensive health data and generate insights.
        
        Args:
            health_data: Comprehensive daily health data from Oura
            
        Returns:
            HealthInsight with status and recommendations
        """
        # Calculate overall score using all available Oura scores
        scores = []
        weights = []
        
        # Primary scores (highest weight)
        if health_data.sleep_score:
            scores.append(health_data.sleep_score)
            weights.append(0.3)  # 30%
            
        if health_data.readiness_score:
            scores.append(health_data.readiness_score)
            weights.append(0.3)  # 30%
            
        if health_data.activity_score:
            scores.append(health_data.activity_score)
            weights.append(0.25)  # 25%
        
        # Secondary scores (lower weight)
        if health_data.spo2_average and health_data.spo2_average > 90:
            # Convert SpO2 to 0-100 scale (95-100% → 50-100 points)
            spo2_score = min(100, max(0, (health_data.spo2_average - 90) * 10))
            scores.append(spo2_score)
            weights.append(0.1)  # 10%
        
        # Cardiovascular age bonus (if younger than actual age)
        cardio_bonus = 0
        if health_data.cardiovascular_age and health_data.cardiovascular_age < 25:  # User is 25
            cardio_bonus = min(10, (25 - health_data.cardiovascular_age) * 2)  # Max 10 point bonus
        
        # Calculate weighted average
        if scores and weights:
            # Normalize weights to sum to 1
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]
            
            overall_score = sum(score * weight for score, weight in zip(scores, normalized_weights))
            overall_score += cardio_bonus  # Add cardiovascular bonus
            overall_score = min(100, max(0, int(overall_score)))
        else:
            # Fallback to activity calculations if no Oura scores
            calorie_score = self._score_calories(health_data.total_calories)
            active_score = self._score_active_calories(health_data.active_calories)
            steps_score = self._score_steps(health_data.steps)
            overall_score = int((calorie_score * 0.4) + (active_score * 0.4) + (steps_score * 0.2))
        
        # Determine status based on score
        status = self._determine_status(overall_score)
        
        # Generate personalized message
        message = self._generate_message(health_data, overall_score)
        
        # Generate tips
        tips = self._generate_tips(health_data)
        
        # Prepare detailed metrics
        detailed_metrics = self._prepare_detailed_metrics(health_data)
        
        return HealthInsight(
            status=status,
            score=overall_score,
            message=message,
            tips=tips,
            detailed_metrics=detailed_metrics
        )
    
    def _score_calories(self, total_calories: int) -> int:
        """Score total calories burned (0-100)."""
        target = self.config.TARGET_CALORIES
        if total_calories == 0:
            return 0
        percentage = (total_calories / target) * 100
        return min(100, max(0, int(percentage)))
    
    def _score_active_calories(self, active_calories: int) -> int:
        """Score active calories burned (0-100)."""
        target = self.config.TARGET_ACTIVE_CALORIES
        if active_calories == 0:
            return 0
        percentage = (active_calories / target) * 100
        return min(100, max(0, int(percentage)))
    
    def _score_steps(self, steps: int) -> int:
        """Score daily steps (0-100)."""
        target = self.config.TARGET_STEPS
        if steps == 0:
            return 0
        percentage = (steps / target) * 100
        return min(100, max(0, int(percentage)))
    
    def _determine_status(self, score: int) -> HealthStatus:
        """Determine health status based on overall score."""
        if score >= 85:
            return HealthStatus.EXCELLENT
        elif score >= 70:
            return HealthStatus.GOOD
        elif score >= 50:
            return HealthStatus.AVERAGE
        else:
            return HealthStatus.NEEDS_IMPROVEMENT
    
    def _generate_message(self, data: HealthData, score: int) -> str:
        """Generate personalized health message based on comprehensive data."""
        
        # Create data summary with all available metrics
        data_parts = []
        
        # Core scores
        if data.sleep_score:
            data_parts.append(f"Sleep: {data.sleep_score}/100")
        
        if data.readiness_score:
            data_parts.append(f"Readiness: {data.readiness_score}/100")
        
        if data.activity_score:
            data_parts.append(f"Activity: {data.activity_score}/100")
        
        # Activity metrics
        if data.total_calories > 0:
            data_parts.append(f"{data.total_calories} calories ({data.active_calories} active)")
        
        if data.steps > 0:
            data_parts.append(f"{data.steps:,} steps")
        
        # Health indicators
        if data.spo2_average:
            data_parts.append(f"SpO2: {data.spo2_average:.1f}%")
        
        if data.cardiovascular_age:
            age_status = "💪 young" if data.cardiovascular_age < 25 else "👍 good" if data.cardiovascular_age <= 25 else "⚠️ elevated"
            data_parts.append(f"Cardio Age: {data.cardiovascular_age} ({age_status})")
        
        if data.resilience_level:
            resilience_emoji = {"strong": "💪", "good": "👍", "fair": "⚠️", "poor": "🔴"}.get(data.resilience_level, "📊")
            data_parts.append(f"Resilience: {resilience_emoji} {data.resilience_level}")
        
        data_summary = " | ".join(data_parts) if data_parts else "Limited data available"
        
        # Generate status-based messages
        status = self._determine_status(score)
        
        if status == HealthStatus.EXCELLENT:
            return f"🌟 Outstanding health performance! Your metrics are excellent: {data_summary}. You're in peak condition! 💪"
        elif status == HealthStatus.GOOD:
            return f"👍 Great health metrics! You're performing well: {data_summary}. Keep up the excellent work!"
        elif status == HealthStatus.AVERAGE:
            return f"📈 Solid health foundation with room for improvement: {data_summary}. Small changes can make a big difference!"
        else:
            return f"🎯 Your health metrics show potential for growth: {data_summary}. Let's focus on building better habits!"
    
    def _generate_tips(self, data: HealthData) -> List[str]:
        """Generate personalized tips based on comprehensive health data."""
        tips = []
        
        # Sleep-based tips
        if data.sleep_score is not None:
            if data.sleep_score < 70:
                tips.append("😴 Improve sleep quality: aim for 7-9 hours, consistent bedtime, and optimize sleep environment")
            elif data.sleep_score >= 85:
                tips.append("🌙 Excellent sleep! Your recovery is on point - this supports all other health metrics")
        
        # Readiness-based tips
        if data.readiness_score is not None:
            if data.readiness_score < 70:
                tips.append("🔋 Low readiness suggests prioritizing recovery: light activity, stress management, and rest")
            elif data.readiness_score >= 85:
                tips.append("💪 High readiness! Perfect time for challenging workouts or new fitness goals")
        
        # Activity-based tips
        if data.activity_score is not None:
            if data.activity_score < 70:
                tips.append("🏃 Boost activity: aim for more movement throughout the day, even short walks help")
            elif data.activity_score >= 85:
                tips.append("🔥 Great activity level! Consider varying your routine with new activities or sports")
        
        # Specific activity metrics
        if data.active_calories and data.active_calories > 1000:
            tips.append("🚀 Impressive active calorie burn! Make sure to fuel properly and stay hydrated")
        elif data.total_calories and data.total_calories < 2000:
            tips.append("⚡ Consider increasing daily movement to boost metabolism and energy levels")
        
        # SpO2-based tips
        if data.spo2_average is not None:
            if data.spo2_average < 95:
                tips.append("💨 SpO2 below optimal - consider breathing exercises and ensure good air quality")
            elif data.spo2_average >= 98:
                tips.append("🫁 Excellent oxygen saturation! Your respiratory health is outstanding")
        
        # Cardiovascular age tips
        if data.cardiovascular_age is not None:
            if data.cardiovascular_age < 25:  # User is 25
                tips.append(f"❤️ Amazing! Your cardiovascular age of {data.cardiovascular_age} is younger than your actual age")
            elif data.cardiovascular_age > 25:
                tips.append("💓 Focus on cardio health: regular aerobic exercise and heart-healthy nutrition")
        
        # Resilience tips
        if data.resilience_level:
            if data.resilience_level in ["poor", "fair"]:
                tips.append("🛡️ Build resilience: balance training with recovery, manage stress, and prioritize sleep")
            elif data.resilience_level == "strong":
                tips.append("🛡️ Strong resilience! You're well-equipped to handle training and life stresses")
        
        # Stress/Recovery balance
        if data.stress_summary:
            if data.stress_summary == "normal":
                tips.append("⚖️ Good stress-recovery balance maintained")
            else:
                tips.append("🧘 Focus on stress management: meditation, deep breathing, or relaxing activities")
        
        # General tips if limited data
        if not tips:
            tips.append("🎯 Stay consistent with healthy habits: regular movement, quality sleep, and mindful living")
            tips.append("📊 Keep wearing your Oura Ring for comprehensive health insights")
        
        # Encouraging tip based on overall data richness
        data_sources = sum([1 for x in [data.sleep_score, data.readiness_score, data.activity_score, 
                           data.spo2_average, data.cardiovascular_age] if x is not None])
        if data_sources >= 4:
            tips.append("🏆 Comprehensive health tracking! You have excellent data coverage for optimal insights")
        
        return tips[:3]  # Limit to 3 tips maximum
    
    def _prepare_detailed_metrics(self, data: HealthData) -> dict:
        """Prepare detailed metrics for display."""
        metrics = {}
        
        # Core scores
        if data.sleep_score:
            metrics["sleep"] = {"score": data.sleep_score, "contributors": data.sleep_contributors}
        if data.readiness_score:
            metrics["readiness"] = {"score": data.readiness_score, "contributors": data.readiness_contributors}
        if data.activity_score:
            metrics["activity"] = {"score": data.activity_score}
        
        # Activity details
        if data.total_calories or data.steps:
            metrics["movement"] = {
                "total_calories": data.total_calories,
                "active_calories": data.active_calories,
                "steps": data.steps
            }
        
        # Health indicators
        if data.spo2_average:
            metrics["respiratory"] = {
                "spo2_average": data.spo2_average,
                "breathing_disturbance_index": data.breathing_disturbance_index
            }
        
        if data.cardiovascular_age:
            metrics["cardiovascular"] = {"age": data.cardiovascular_age}
        
        if data.resilience_level:
            metrics["resilience"] = {
                "level": data.resilience_level,
                "contributors": data.resilience_contributors
            }
        
        if data.stress_summary:
            metrics["stress"] = {
                "summary": data.stress_summary,
                "stress_high": data.stress_high,
                "recovery_high": data.recovery_high
            }
        
        return metrics 