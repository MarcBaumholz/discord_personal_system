"""
Deutsche Bahn API client for train schedule and delay information.
"""
import httpx
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from config import config
import asyncio
import json

logger = structlog.get_logger()

@dataclass
class TrainDeparture:
    """Represents a train departure with delay information."""
    train_number: str
    destination: str
    scheduled_time: datetime
    actual_time: Optional[datetime] = None
    delay_minutes: int = 0
    platform: Optional[str] = None
    is_cancelled: bool = False
    messages: List[str] = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []

@dataclass
class StationInfo:
    """Information about a train station."""
    name: str
    eva_number: str
    location: Optional[Dict[str, float]] = None

class DBApiClient:
    """Client for Deutsche Bahn Timetables API."""
    
    def __init__(self):
        self.base_url = config.DB_API_BASE_URL
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = timedelta(minutes=config.CACHE_TTL_MINUTES)
        
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make an authenticated request to the DB API."""
        if not config.DB_API_KEY:
            logger.warning("DB API key not configured - using mock data")
            return await self._get_mock_data(endpoint, params)
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = config.get_db_headers()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error("DB API request failed", 
                        status_code=e.response.status_code,
                        endpoint=endpoint,
                        error=str(e))
            return None
        except Exception as e:
            logger.error("DB API request error", endpoint=endpoint, error=str(e))
            return None
    
    async def _get_mock_data(self, endpoint: str, params: Dict = None) -> Dict:
        """Generate mock data for testing when API is not available."""
        logger.info("Using mock data for DB API", endpoint=endpoint)
        
        if "stations" in endpoint:
            return {
                "result": [
                    {
                        "name": "Berlin Hauptbahnhof",
                        "evaNumbers": [{"number": "8011160"}],
                        "location": {"latitude": 52.525589, "longitude": 13.369548}
                    },
                    {
                        "name": "Hamburg Hauptbahnhof", 
                        "evaNumbers": [{"number": "8002549"}],
                        "location": {"latitude": 53.552736, "longitude": 10.006909}
                    }
                ]
            }
        
        elif "departures" in endpoint:
            base_time = datetime.now()
            return {
                "departures": [
                    {
                        "name": "ICE 123",
                        "type": "ICE",
                        "stopId": "8011160-1",
                        "stop": "Berlin Hauptbahnhof",
                        "when": (base_time + timedelta(minutes=15)).isoformat(),
                        "plannedWhen": (base_time + timedelta(minutes=10)).isoformat(),
                        "delay": 300,  # 5 minutes delay in seconds
                        "platform": "7",
                        "cancelled": False,
                        "direction": "Hamburg Hbf",
                        "remarks": [{"text": "Verzögerung durch vorangegangenen Zug"}]
                    },
                    {
                        "name": "RE 456",
                        "type": "RE", 
                        "stopId": "8011160-2",
                        "stop": "Berlin Hauptbahnhof",
                        "when": (base_time + timedelta(minutes=25)).isoformat(),
                        "plannedWhen": (base_time + timedelta(minutes=25)).isoformat(),
                        "delay": 0,
                        "platform": "12",
                        "cancelled": False,
                        "direction": "Rostock Hbf",
                        "remarks": []
                    }
                ]
            }
        
        return {"result": []}
    
    def _get_cache_key(self, endpoint: str, params: Dict = None) -> str:
        """Generate a cache key for the request."""
        if params:
            param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            return f"{endpoint}?{param_str}"
        return endpoint
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if a cache entry is still valid."""
        return datetime.now() - cache_entry["timestamp"] < self.cache_ttl
    
    async def search_stations(self, query: str) -> List[StationInfo]:
        """Search for train stations by name."""
        cache_key = self._get_cache_key("stations/search", {"query": query})
        
        # Check cache first
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            data = self.cache[cache_key]["data"]
        else:
            data = await self._make_request("stations", {"query": query})
            if data:
                self.cache[cache_key] = {
                    "data": data,
                    "timestamp": datetime.now()
                }
        
        if not data or "result" not in data:
            return []
        
        stations = []
        for station_data in data["result"][:5]:  # Limit to top 5 results
            eva_number = ""
            if "evaNumbers" in station_data and station_data["evaNumbers"]:
                eva_number = station_data["evaNumbers"][0].get("number", "")
            
            location = None
            if "location" in station_data:
                location = {
                    "lat": station_data["location"].get("latitude"),
                    "lon": station_data["location"].get("longitude")
                }
            
            stations.append(StationInfo(
                name=station_data.get("name", ""),
                eva_number=eva_number,
                location=location
            ))
        
        return stations
    
    async def get_departures(self, station_name: str, limit: int = 10) -> List[TrainDeparture]:
        """Get departures from a station with delay information."""
        # First, get the station ID
        stations = await self.search_stations(station_name)
        if not stations:
            logger.warning("Station not found", station=station_name)
            return []
        
        station = stations[0]  # Use the best match
        cache_key = self._get_cache_key(f"departures/{station.eva_number}", {"limit": limit})
        
        # Check cache first
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            data = self.cache[cache_key]["data"]
        else:
            data = await self._make_request(f"departures/{station.eva_number}", {"limit": limit})
            if data:
                self.cache[cache_key] = {
                    "data": data,
                    "timestamp": datetime.now()
                }
        
        if not data or "departures" not in data:
            return []
        
        departures = []
        for dep in data["departures"]:
            try:
                scheduled_time = datetime.fromisoformat(dep["plannedWhen"].replace('Z', '+00:00'))
                actual_time = None
                delay_minutes = 0
                
                if "when" in dep and dep["when"]:
                    actual_time = datetime.fromisoformat(dep["when"].replace('Z', '+00:00'))
                
                if "delay" in dep and dep["delay"]:
                    delay_minutes = dep["delay"] // 60  # Convert seconds to minutes
                
                messages = []
                if "remarks" in dep:
                    messages = [remark.get("text", "") for remark in dep["remarks"] if remark.get("text")]
                
                departures.append(TrainDeparture(
                    train_number=dep.get("name", ""),
                    destination=dep.get("direction", ""),
                    scheduled_time=scheduled_time,
                    actual_time=actual_time,
                    delay_minutes=delay_minutes,
                    platform=dep.get("platform"),
                    is_cancelled=dep.get("cancelled", False),
                    messages=messages
                ))
                
            except Exception as e:
                logger.warning("Failed to parse departure", departure=dep, error=str(e))
                continue
        
        return departures
    
    async def get_connection_status(self, from_station: str, to_station: str) -> Dict[str, Any]:
        """Get the current status for a specific train connection."""
        departures = await self.get_departures(from_station, limit=20)
        
        # Filter departures that go to the destination
        relevant_trains = []
        for dep in departures:
            # This is simplified - in reality we'd need to check the full route
            if to_station.lower() in dep.destination.lower():
                relevant_trains.append(dep)
        
        if not relevant_trains:
            # If no direct trains found, get general departure info
            relevant_trains = departures[:3]
        
        # Calculate summary statistics
        total_delay = sum(train.delay_minutes for train in relevant_trains)
        avg_delay = total_delay / len(relevant_trains) if relevant_trains else 0
        max_delay = max(train.delay_minutes for train in relevant_trains) if relevant_trains else 0
        cancelled_count = sum(1 for train in relevant_trains if train.is_cancelled)
        
        return {
            "from_station": from_station,
            "to_station": to_station,
            "trains": relevant_trains,
            "summary": {
                "total_trains": len(relevant_trains),
                "average_delay": avg_delay,
                "max_delay": max_delay,
                "cancelled_trains": cancelled_count,
                "on_time_ratio": len([t for t in relevant_trains if t.delay_minutes <= 2]) / len(relevant_trains) if relevant_trains else 0
            },
            "timestamp": datetime.now()
        }
    
    def clear_cache(self) -> None:
        """Clear the API cache."""
        self.cache.clear()
        logger.info("API cache cleared")

# Create a global DB API client instance
db_api = DBApiClient()