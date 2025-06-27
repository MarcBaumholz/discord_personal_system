"""Unit tests for health analyzer."""
import pytest
from unittest.mock import patch

from health_analyzer import HealthAnalyzer, HealthStatus
from oura_client import HealthData


class TestHealthAnalyzer:
    """Test cases for HealthAnalyzer."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = HealthAnalyzer()
    
    def test_analyze_excellent_performance(self):
        """Test analysis with excellent health data."""
        # Create health data with excellent metrics
        health_data = HealthData(
            date="2024-01-15",
            total_calories=2500,  # Above target (2200)
            active_calories=600,  # Above target (450)
            inactive_calories=1900,
            steps=12000,  # Above target (8000)
            activity_score=95
        )
        
        insight = self.analyzer.analyze(health_data)
        
        assert insight.status == HealthStatus.EXCELLENT
        assert insight.score >= 90
        assert "Outstanding day" in insight.message
        assert len(insight.tips) >= 1
    
    def test_analyze_poor_performance(self):
        """Test analysis with poor health data."""
        # Create health data with poor metrics
        health_data = HealthData(
            date="2024-01-15",
            total_calories=1000,  # Well below target
            active_calories=150,  # Below target
            inactive_calories=850,
            steps=3000,  # Below target
            activity_score=20
        )
        
        insight = self.analyzer.analyze(health_data)
        
        assert insight.status == HealthStatus.NEEDS_IMPROVEMENT
        assert insight.score < 50
        assert "lighter day" in insight.message
        assert len(insight.tips) >= 2  # Should have multiple improvement tips
    
    def test_analyze_average_performance(self):
        """Test analysis with average health data."""
        # Create health data with average metrics
        health_data = HealthData(
            date="2024-01-15",
            total_calories=1400,  # Below target 
            active_calories=300,  # Below target
            inactive_calories=1100,
            steps=5500,  # Below target
            activity_score=55
        )
        
        insight = self.analyzer.analyze(health_data)
        
        assert insight.status == HealthStatus.AVERAGE
        assert 50 <= insight.score < 70
        assert "decent" in insight.message
        assert len(insight.tips) >= 1
    
    def test_score_calories_calculation(self):
        """Test calorie scoring calculation."""
        # Test exact target
        score = self.analyzer._score_calories(2200)
        assert score == 100
        
        # Test below target
        score = self.analyzer._score_calories(1100)  # 50% of target
        assert score == 50
        
        # Test above target (should cap at 100)
        score = self.analyzer._score_calories(3000)
        assert score == 100
        
        # Test zero calories
        score = self.analyzer._score_calories(0)
        assert score == 0
    
    def test_score_steps_calculation(self):
        """Test steps scoring calculation."""
        # Test exact target
        score = self.analyzer._score_steps(8000)
        assert score == 100
        
        # Test half target
        score = self.analyzer._score_steps(4000)
        assert score == 50
        
        # Test above target
        score = self.analyzer._score_steps(12000)
        assert score == 100
    
    def test_generate_tips_low_activity(self):
        """Test tip generation for low activity."""
        health_data = HealthData(
            date="2024-01-15",
            total_calories=1500,  # Low
            active_calories=200,  # Low
            inactive_calories=1300,
            steps=4000,  # Low
            activity_score=40
        )
        
        insight = self.analyzer.analyze(health_data)
        
        # Should have tips for all low metrics
        tips_text = " ".join(insight.tips)
        assert any("activity" in tip.lower() for tip in insight.tips)
        assert len(insight.tips) <= 3  # Should be limited to 3 tips
    
    def test_generate_tips_good_performance(self):
        """Test tip generation for good performance."""
        health_data = HealthData(
            date="2024-01-15",
            total_calories=2400,  # Good
            active_calories=500,  # Good
            inactive_calories=1900,
            steps=10000,  # Good
            activity_score=85
        )
        
        insight = self.analyzer.analyze(health_data)
        
        # Should have encouraging tips
        tips_text = " ".join(insight.tips)
        assert any("great" in tip.lower() or "variety" in tip.lower() for tip in insight.tips)
    
    def test_always_has_at_least_one_tip(self):
        """Test that analysis always provides at least one tip."""
        # Test with various data scenarios
        test_scenarios = [
            HealthData(date="2024-01-15", total_calories=2200, active_calories=450, 
                      inactive_calories=1750, steps=8000, activity_score=80),
            HealthData(date="2024-01-15", total_calories=1000, active_calories=100,
                      inactive_calories=900, steps=2000, activity_score=20),
            HealthData(date="2024-01-15", total_calories=3000, active_calories=800,
                      inactive_calories=2200, steps=15000, activity_score=100)
        ]
        
        for health_data in test_scenarios:
            insight = self.analyzer.analyze(health_data)
            assert len(insight.tips) >= 1, f"No tips generated for data: {health_data}" 