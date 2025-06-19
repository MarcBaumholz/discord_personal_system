"""Oura API client for fetching health data."""
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class HealthData(BaseModel):
    """Comprehensive health data model from Oura Ring."""
    date: str
    # Activity data (5-day delay)
    total_calories: int
    active_calories: int
    inactive_calories: int
    steps: int
    activity_score: Optional[int] = None
    # Sleep data (1-day delay)
    sleep_score: Optional[int] = None
    sleep_contributors: Optional[Dict] = None
    # Readiness data (1-day delay)
    readiness_score: Optional[int] = None
    readiness_contributors: Optional[Dict] = None
    temperature_deviation: Optional[float] = None
    # Additional health metrics
    spo2_average: Optional[float] = None
    breathing_disturbance_index: Optional[int] = None
    stress_high: Optional[int] = None
    recovery_high: Optional[int] = None
    stress_summary: Optional[str] = None
    cardiovascular_age: Optional[int] = None
    resilience_level: Optional[str] = None
    resilience_contributors: Optional[Dict] = None


class OuraClient:
    """Client for interacting with Oura API v2."""
    
    BASE_URL = "https://api.ouraring.com/v2/usercollection"
    
    def __init__(self, access_token: str):
        """Initialize Oura client with access token."""
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        })
    
    def get_daily_sleep(self, date: str) -> Optional[Dict]:
        """Fetch daily sleep data for a specific date."""
        try:
            url = f"{self.BASE_URL}/daily_sleep"
            params = {"start_date": date, "end_date": date}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("data"):
                return data["data"][0]
            return None
        except Exception as e:
            logger.error(f"Error fetching sleep data: {e}")
            return None
    
    def get_daily_readiness(self, date: str) -> Optional[Dict]:
        """Fetch daily readiness data for a specific date."""
        try:
            url = f"{self.BASE_URL}/daily_readiness"
            params = {"start_date": date, "end_date": date}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("data"):
                return data["data"][0]
            return None
        except Exception as e:
            logger.error(f"Error fetching readiness data: {e}")
            return None
    
    def get_daily_activity(self, date: str) -> Optional[Dict]:
        """Fetch daily activity data for a specific date."""
        try:
            url = f"{self.BASE_URL}/daily_activity"
            params = {"start_date": date, "end_date": date}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("data"):
                return data["data"][0]
            return None
        except Exception as e:
            logger.error(f"Error fetching activity data: {e}")
            return None
    
    def get_daily_spo2(self, date: str) -> Optional[Dict]:
        """Fetch daily SpO2 data for a specific date."""
        try:
            url = f"{self.BASE_URL}/daily_spo2"
            params = {"start_date": date, "end_date": date}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("data"):
                return data["data"][0]
            return None
        except Exception as e:
            logger.error(f"Error fetching SpO2 data: {e}")
            return None
    
    def get_daily_stress(self, date: str) -> Optional[Dict]:
        """Fetch daily stress data for a specific date."""
        try:
            url = f"{self.BASE_URL}/daily_stress"
            params = {"start_date": date, "end_date": date}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("data"):
                return data["data"][0]
            return None
        except Exception as e:
            logger.error(f"Error fetching stress data: {e}")
            return None
    
    def get_daily_cardiovascular_age(self, date: str) -> Optional[Dict]:
        """Fetch daily cardiovascular age data for a specific date."""
        try:
            url = f"{self.BASE_URL}/daily_cardiovascular_age"
            params = {"start_date": date, "end_date": date}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("data"):
                return data["data"][0]
            return None
        except Exception as e:
            logger.error(f"Error fetching cardiovascular age data: {e}")
            return None
    
    def get_daily_resilience(self, date: str) -> Optional[Dict]:
        """Fetch daily resilience data for a specific date."""
        try:
            url = f"{self.BASE_URL}/daily_resilience"
            params = {"start_date": date, "end_date": date}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("data"):
                return data["data"][0]
            return None
        except Exception as e:
            logger.error(f"Error fetching resilience data: {e}")
            return None
    
    def get_latest_activity_data(self) -> Optional[Dict]:
        """Get the most recent activity data (accounting for 5-day delay)."""
        # Activity data has a 5-day delay, so we need to check a wider range
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        try:
            url = f"{self.BASE_URL}/daily_activity"
            params = {"start_date": start_date, "end_date": end_date}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("data"):
                # Return the most recent activity data
                return data["data"][-1]
            return None
        except Exception as e:
            logger.error(f"Error fetching latest activity data: {e}")
            return None
    
    def get_comprehensive_health_data(self, date: str) -> Optional[HealthData]:
        """
        Fetch comprehensive health data combining all available endpoints.
        
        Args:
            date: Date in YYYY-MM-DD format (for recent data like sleep/readiness)
            
        Returns:
            HealthData object or None if no data available
        """
        logger.info(f"Fetching comprehensive health data for: {date}")
        
        # Get recent data (1-day delay)
        sleep_data = self.get_daily_sleep(date)
        readiness_data = self.get_daily_readiness(date)
        spo2_data = self.get_daily_spo2(date)
        stress_data = self.get_daily_stress(date)
        cardio_data = self.get_daily_cardiovascular_age(date)
        resilience_data = self.get_daily_resilience(date)
        
        # Get latest activity data (5-day delay)
        activity_data = self.get_latest_activity_data()
        
        # Determine the most appropriate date for the report
        report_date = date
        if activity_data and activity_data.get("day"):
            # If we have activity data, it might be from a different date
            activity_date = activity_data.get("day")
            if activity_date != date:
                logger.info(f"Using activity data from {activity_date} (most recent available)")
        
        # If we have at least one data source, create a report
        if any([sleep_data, readiness_data, activity_data, spo2_data, stress_data]):
            logger.info(f"Found data - Sleep: {'✅' if sleep_data else '❌'}, "
                       f"Readiness: {'✅' if readiness_data else '❌'}, "
                       f"Activity: {'✅' if activity_data else '❌'}, "
                       f"SpO2: {'✅' if spo2_data else '❌'}, "
                       f"Stress: {'✅' if stress_data else '❌'}")
            
            return HealthData(
                date=report_date,
                # Activity data (may be from different date due to delay)
                total_calories=activity_data.get("total_calories", 0) if activity_data else 0,
                active_calories=activity_data.get("active_calories", 0) if activity_data else 0,
                inactive_calories=activity_data.get("inactive_calories", 0) if activity_data else 0,
                steps=activity_data.get("steps", 0) if activity_data else 0,
                activity_score=activity_data.get("score") if activity_data else None,
                # Sleep data
                sleep_score=sleep_data.get("score") if sleep_data else None,
                sleep_contributors=sleep_data.get("contributors") if sleep_data else None,
                # Readiness data
                readiness_score=readiness_data.get("score") if readiness_data else None,
                readiness_contributors=readiness_data.get("contributors") if readiness_data else None,
                temperature_deviation=readiness_data.get("temperature_deviation") if readiness_data else None,
                # SpO2 data
                spo2_average=spo2_data.get("spo2_percentage", {}).get("average") if spo2_data else None,
                breathing_disturbance_index=spo2_data.get("breathing_disturbance_index") if spo2_data else None,
                # Stress data
                stress_high=stress_data.get("stress_high") if stress_data else None,
                recovery_high=stress_data.get("recovery_high") if stress_data else None,
                stress_summary=stress_data.get("day_summary") if stress_data else None,
                # Cardiovascular data
                cardiovascular_age=cardio_data.get("vascular_age") if cardio_data else None,
                # Resilience data
                resilience_level=resilience_data.get("level") if resilience_data else None,
                resilience_contributors=resilience_data.get("contributors") if resilience_data else None
            )
        
        logger.warning(f"No health data found for date: {date}")
        return None
    
    def get_yesterday_data(self) -> Optional[HealthData]:
        """Get yesterday's comprehensive health data."""
        # Try last 3 days to find recent data (for sleep/readiness)
        for days_back in range(1, 4):
            date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            logger.info(f"Trying to fetch data for date: {date}")
            
            data = self.get_comprehensive_health_data(date)
            if data:
                logger.info(f"Found health data for date: {date}")
                return data
        
        logger.warning("No health data found for the last 3 days")
        return None 