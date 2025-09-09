"""Health data analyzer for generating status and insights."""
from enum import Enum
from typing import List, Optional, Tuple
from pydantic import BaseModel

from oura_client import HealthData
from config import Config
from notion_calories_client import NotionCaloriesClient


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
    individual_insights: List[str]
    calories_analysis: Optional[dict] = None  # Added calories analysis


class HealthAnalyzer:
    """Analyzes comprehensive health data and generates insights."""
    
    def __init__(self):
        self.config = Config()
        # Initialize Notion calories client
        try:
            self.calories_client = NotionCaloriesClient(
                notion_token=self.config.NOTION_TOKEN,
                database_id=self.config.FOODIATE_DB_ID
            )
        except Exception as e:
            print(f"Warning: Could not initialize Notion calories client: {e}")
            self.calories_client = None
    
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
        
        # Generate 2 specific individual insights based on detailed data analysis
        individual_insights = self._generate_individual_insights(health_data)
        
        # Prepare detailed metrics
        detailed_metrics = self._prepare_detailed_metrics(health_data)
        
        # Analyze calories (consumed vs burned)
        calories_analysis = self._analyze_calories_balance(health_data)
        
        return HealthInsight(
            status=status,
            score=overall_score,
            message=message,
            tips=tips,
            detailed_metrics=detailed_metrics,
            individual_insights=individual_insights,
            calories_analysis=calories_analysis
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
    
    def _generate_individual_insights(self, data: HealthData) -> List[str]:
        """
        Generate 2 specific individualized insights based on detailed data analysis.
        
        Args:
            data: Comprehensive health data from Oura
            
        Returns:
            List of exactly 2 specific, actionable insights
        """
        insights = []
        
        # INSIGHT 1: Sleep Quality Analysis (REM, Deep Sleep, etc.)
        sleep_insight = self._analyze_sleep_details(data)
        if sleep_insight:
            insights.append(sleep_insight)
        
        # INSIGHT 2: Activity Balance & Recovery Analysis
        activity_insight = self._analyze_activity_balance(data)
        if activity_insight:
            insights.append(activity_insight)
        
        # INSIGHT 3: Stress & Recovery Balance (if first two aren't available)
        if len(insights) < 2:
            stress_insight = self._analyze_stress_recovery(data)
            if stress_insight:
                insights.append(stress_insight)
        
        # INSIGHT 4: Cardiovascular & Respiratory Health (fallback)
        if len(insights) < 2:
            cardio_insight = self._analyze_cardio_respiratory(data)
            if cardio_insight:
                insights.append(cardio_insight)
        
        # Ensure we always return exactly 2 insights
        if len(insights) < 2:
            insights.append("📊 Keep wearing your Oura Ring consistently for more detailed insights tomorrow")
        
        return insights[:2]  # Return exactly 2 insights
    
    def _analyze_sleep_details(self, data: HealthData) -> str:
        """Analyze detailed sleep contributors for specific improvements."""
        if not data.sleep_contributors or not data.sleep_score:
            return None
        
        contributors = data.sleep_contributors
        sleep_score = data.sleep_score
        
        # Analyze specific sleep contributors
        rem_sleep = contributors.get("rem_sleep")
        deep_sleep = contributors.get("deep_sleep")
        restfulness = contributors.get("restfulness")
        sleep_efficiency = contributors.get("sleep_efficiency")
        sleep_latency = contributors.get("sleep_latency")
        
        # Find the weakest sleep component for specific advice
        weak_areas = []
        
        if rem_sleep and rem_sleep < 70:
            weak_areas.append(("REM sleep", rem_sleep, "Go to bed 30 minutes earlier, keep room temperature 18-20°C, avoid alcohol 3+ hours before bed"))
        
        if deep_sleep and deep_sleep < 70:
            weak_areas.append(("Deep sleep", deep_sleep, "Create cooler sleeping environment (16-19°C), avoid late meals, consider magnesium supplement"))
        
        if restfulness and restfulness < 70:
            weak_areas.append(("Sleep restfulness", restfulness, "Reduce blue light 2 hours before bed, try blackout curtains, keep phone in airplane mode"))
        
        if sleep_efficiency and sleep_efficiency < 80:
            weak_areas.append(("Sleep efficiency", sleep_efficiency, "Establish consistent bedtime routine, avoid caffeine after 2 PM, try 4-7-8 breathing"))
        
        if sleep_latency and sleep_latency < 70:
            weak_areas.append(("Sleep onset", sleep_latency, "Practice progressive muscle relaxation, avoid screens 1 hour before bed, try chamomile tea"))
        
        if weak_areas:
            # Pick the weakest area for targeted advice
            weakest = min(weak_areas, key=lambda x: x[1])
            return f"🛌 **Sleep Optimization**: Your {weakest[0]} scored {weakest[1]}/100. Try this: {weakest[2]}"
        
        # If sleep is good, give maintenance advice
        if sleep_score >= 80:
            return f"😴 **Sleep Excellence**: Your sleep score of {sleep_score}/100 is excellent! Maintain your current routine and bedtime consistency for continued success"
        
        return None
    
    def _analyze_activity_balance(self, data: HealthData) -> str:
        """Analyze activity level and provide recovery/intensity guidance."""
        if not data.activity_score:
            return None
        
        activity_score = data.activity_score
        readiness_score = data.readiness_score or 75  # Default if not available
        
        # Analyze activity vs readiness for recovery guidance
        if activity_score < 50 and readiness_score > 80:
            return f"🚀 **Activity Boost**: Yesterday's activity was low ({activity_score}/100) but your readiness is high ({readiness_score}/100). Perfect day for a challenging workout or new activity!"
        
        elif activity_score < 50 and readiness_score < 70:
            return f"🚶 **Gentle Recovery**: Both activity ({activity_score}/100) and readiness ({readiness_score}/100) are low. Focus on 20-minute gentle walk + 10 minutes stretching instead of intense exercise"
        
        elif activity_score > 85 and readiness_score < 70:
            return f"🛌 **Recovery Priority**: High activity yesterday ({activity_score}/100) with low readiness ({readiness_score}/100). Take a recovery day with light yoga or meditation"
        
        elif activity_score > 85 and readiness_score > 80:
            return f"💪 **Peak Performance**: Excellent activity ({activity_score}/100) and readiness ({readiness_score}/100)! You're in optimal condition - consider trying a new fitness challenge"
        
        # Moderate activity recommendations
        if 50 <= activity_score <= 85:
            if data.steps and data.steps < 8000:
                return f"👟 **Step Goal**: Activity score is moderate ({activity_score}/100) with {data.steps:,} steps. Aim for 10,000+ steps today with 3 short walking breaks"
            else:
                return f"⚡ **Activity Balance**: Good activity level ({activity_score}/100). Mix today with both cardio and strength training for optimal variety"
        
        return None
    
    def _analyze_stress_recovery(self, data: HealthData) -> str:
        """Analyze stress and recovery balance."""
        if not data.stress_high or not data.recovery_high:
            return None
        
        stress_time = data.stress_high / 3600  # Convert to hours
        recovery_time = data.recovery_high / 3600  # Convert to hours
        
        # Calculate stress-recovery ratio
        if recovery_time > 0:
            stress_ratio = stress_time / recovery_time
        else:
            stress_ratio = float('inf')
        
        if stress_ratio > 0.5:  # High stress relative to recovery
            return f"🧘 **Stress Management**: High stress time ({stress_time:.1f}h) vs recovery ({recovery_time:.1f}h). Try 10 minutes meditation or deep breathing exercises today"
        
        elif stress_ratio < 0.2:  # Great recovery
            return f"🌿 **Recovery Champion**: Excellent stress-recovery balance ({stress_time:.1f}h stress, {recovery_time:.1f}h recovery). Your body is well-adapted to current stress levels"
        
        else:  # Balanced
            return f"⚖️ **Balanced State**: Good stress-recovery ratio ({stress_time:.1f}h:{recovery_time:.1f}h). Maintain current stress management practices"
    
    def _analyze_cardio_respiratory(self, data: HealthData) -> str:
        """Analyze cardiovascular and respiratory health."""
        insights = []
        
        # Cardiovascular age analysis
        if data.cardiovascular_age:
            if data.cardiovascular_age < 20:  # Exceptional
                insights.append(f"❤️ **Cardio Superstar**: Cardiovascular age of {data.cardiovascular_age} is exceptional! Your heart health is in the top 5% for your age")
            elif data.cardiovascular_age > 30:  # Needs improvement
                insights.append(f"💓 **Cardio Focus**: Cardiovascular age of {data.cardiovascular_age} suggests focusing on aerobic exercise - aim for 150min moderate cardio weekly")
        
        # SpO2 analysis
        if data.spo2_average:
            if data.spo2_average >= 98:
                insights.append(f"🫁 **Oxygen Efficiency**: SpO2 of {data.spo2_average:.1f}% is outstanding! Your respiratory system is performing excellently")
            elif data.spo2_average < 95:
                insights.append(f"💨 **Breathing Focus**: SpO2 of {data.spo2_average:.1f}% is below optimal. Try 5 minutes of box breathing (4-4-4-4 count) twice daily")
        
        # Return the best insight available
        return insights[0] if insights else None
    
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
    
    def _analyze_calories_balance(self, health_data: HealthData) -> Optional[dict]:
        """
        Analyze calories consumed vs burned from Notion database.
        
        Args:
            health_data: Health data from Oura Ring
            
        Returns:
            Dictionary with calories analysis or None if not available
        """
        if not self.calories_client:
            return None
        
        try:
            # Get yesterday's calories consumed from Notion
            consumed_calories, food_entries = self.calories_client.get_yesterday_calories("Marc")
            
            if consumed_calories == 0:
                return {
                    "consumed_calories": 0,
                    "burned_calories": health_data.total_calories,
                    "net_calories": -health_data.total_calories,
                    "balance_status": "no_food_data",
                    "message": "No food data found for yesterday",
                    "food_entries": []
                }
            
            # Calculate net calories (consumed - burned)
            burned_calories = health_data.total_calories
            net_calories = consumed_calories - burned_calories
            
            # Determine balance status
            if net_calories > 500:
                balance_status = "calorie_surplus"
                message = f"Calorie surplus: +{net_calories} kcal (consumed {consumed_calories}, burned {burned_calories})"
            elif net_calories < -500:
                balance_status = "calorie_deficit"
                message = f"Calorie deficit: {net_calories} kcal (consumed {consumed_calories}, burned {burned_calories})"
            else:
                balance_status = "calorie_balanced"
                message = f"Calorie balanced: {net_calories:+d} kcal (consumed {consumed_calories}, burned {burned_calories})"
            
            return {
                "consumed_calories": consumed_calories,
                "burned_calories": burned_calories,
                "net_calories": net_calories,
                "balance_status": balance_status,
                "message": message,
                "food_entries": food_entries,
                "food_count": len(food_entries)
            }
            
        except Exception as e:
            print(f"Error analyzing calories balance: {e}")
            return None