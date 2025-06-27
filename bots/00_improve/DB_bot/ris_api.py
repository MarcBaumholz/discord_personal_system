"""
RIS API Client for S-Bahn Live Data (Schwaikheim ↔ Stuttgart Feuersee)
"""
import httpx
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from config import config
import asyncio

logger = structlog.get_logger()

@dataclass
class SBahnJourney:
    """Represents an S-Bahn journey with delay information."""
    line: str  # S-Bahn line (e.g., "S4")
    departure_planned: datetime
    departure_actual: Optional[datetime]
    arrival_planned: datetime
    arrival_actual: Optional[datetime]
    delay_minutes: int
    platform: Optional[str]
    is_cancelled: bool
    messages: List[str]
    route_name: str

@dataclass
class RouteStatus:
    """Status information for a complete route."""
    route_name: str
    next_journeys: List[SBahnJourney]
    average_delay: float
    max_delay: int
    disruptions: List[str]
    last_updated: datetime

class RISApiClient:
    """Client for Deutsche Bahn RIS API (S-Bahn specific)."""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = timedelta(minutes=2)  # Fresh data every 2 minutes
        
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to RIS API."""
        if not config.DB_API_KEY:
            logger.warning("DB API key not configured - using mock S-Bahn data")
            return await self._get_mock_sbahn_data(endpoint, params)
        
        headers = config.get_db_headers()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(endpoint, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error("RIS API request failed", 
                        status_code=e.response.status_code,
                        endpoint=endpoint,
                        error=str(e))
            return await self._get_mock_sbahn_data(endpoint, params)
        except Exception as e:
            logger.error("RIS API request error", endpoint=endpoint, error=str(e))
            return await self._get_mock_sbahn_data(endpoint, params)
    
    async def _get_mock_sbahn_data(self, endpoint: str, params: Dict = None) -> Dict:
        """Generate realistic mock S-Bahn data."""
        logger.info("Using mock S-Bahn data", endpoint=endpoint)
        
        now = datetime.now()
        
        # Determine route based on origin/destination
        origin = params.get("origin", "") if params else ""
        destination = params.get("destination", "") if params else ""
        
        if origin == config.SCHWAIKHEIM_ID:  # Route 1: Schwaikheim → Feuersee
            line = "S4"
            journey_time = 12  # minutes
        else:  # Route 2: Feuersee → Schwaikheim
            line = "S4"
            journey_time = 12  # minutes
        
        # Generate next 5 S-Bahn departures
        journeys = []
        for i in range(5):
            base_departure = now + timedelta(minutes=i*10 + 2)  # Every 10 minutes
            delay = [0, 1, 2, 3, 5, 8][i % 6]  # Realistic S-Bahn delays
            
            actual_departure = base_departure + timedelta(minutes=delay)
            actual_arrival = actual_departure + timedelta(minutes=journey_time)
            
            journey = {
                "legs": [{
                    "origin": {
                        "name": "Schwaikheim" if origin == config.SCHWAIKHEIM_ID else "Stuttgart Feuersee",
                        "plannedDepartureTime": base_departure.isoformat(),
                        "actualDepartureTime": actual_departure.isoformat() if delay > 0 else None,
                        "departureDelay": delay * 60,  # seconds
                        "platform": "1" if origin == config.SCHWAIKHEIM_ID else "2"
                    },
                    "destination": {
                        "name": "Stuttgart Feuersee" if origin == config.SCHWAIKHEIM_ID else "Schwaikheim",
                        "plannedArrivalTime": (base_departure + timedelta(minutes=journey_time)).isoformat(),
                        "actualArrivalTime": actual_arrival.isoformat() if delay > 0 else None,
                        "arrivalDelay": delay * 60  # seconds
                    },
                    "line": {
                        "name": line,
                        "product": "S"
                    },
                    "cancelled": False,
                    "remarks": [
                        {"text": f"Verzögerung durch erhöhtes Fahrgastaufkommen"} 
                        if delay > 3 else {}
                    ]
                }]
            }
            journeys.append(journey)
        
        return {"journeys": journeys}
    
    def _parse_journey(self, journey_data: Dict, route_name: str) -> SBahnJourney:
        """Parse journey data from RIS API response."""
        leg = journey_data["legs"][0]  # S-Bahn is direct connection
        
        origin = leg["origin"]
        destination = leg["destination"]
        line_info = leg.get("line", {})
        
        # Parse times
        dep_planned = datetime.fromisoformat(origin["plannedDepartureTime"].replace('Z', '+00:00'))
        arr_planned = datetime.fromisoformat(destination["plannedArrivalTime"].replace('Z', '+00:00'))
        
        dep_actual = None
        if origin.get("actualDepartureTime"):
            dep_actual = datetime.fromisoformat(origin["actualDepartureTime"].replace('Z', '+00:00'))
        
        arr_actual = None
        if destination.get("actualArrivalTime"):
            arr_actual = datetime.fromisoformat(destination["actualArrivalTime"].replace('Z', '+00:00'))
        
        # Calculate delay
        delay_seconds = origin.get("departureDelay", 0)
        delay_minutes = delay_seconds // 60
        
        # Extract messages
        messages = []
        for remark in leg.get("remarks", []):
            if remark.get("text"):
                messages.append(remark["text"])
        
        return SBahnJourney(
            line=line_info.get("name", "S4"),
            departure_planned=dep_planned,
            departure_actual=dep_actual,
            arrival_planned=arr_planned,
            arrival_actual=arr_actual,
            delay_minutes=delay_minutes,
            platform=origin.get("platform"),
            is_cancelled=leg.get("cancelled", False),
            messages=messages,
            route_name=route_name
        )
    
    async def get_route_status(self, route_number: int) -> RouteStatus:
        """Get live status for route 1 or 2."""
        route_config = config.get_route_config(route_number)
        
        # Check cache
        cache_key = f"route_{route_number}"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["data"]
        
        # Build RIS API URL
        journeys_url = f"{config.RIS_JOURNEYS_URL}/journeys"
        params = {
            "origin": route_config["origin"],
            "destination": route_config["destination"],
            "when": datetime.now().isoformat(),
            "limit": config.MAX_JOURNEY_RESULTS
        }
        
        # Fetch data
        data = await self._make_request(journeys_url, params)
        
        if not data or "journeys" not in data:
            logger.warning("No journey data available", route=route_number)
            return RouteStatus(
                route_name=route_config["name"],
                next_journeys=[],
                average_delay=0,
                max_delay=0,
                disruptions=["Keine aktuellen Daten verfügbar"],
                last_updated=datetime.now()
            )
        
        # Parse journeys
        journeys = []
        for journey_data in data["journeys"]:
            try:
                journey = self._parse_journey(journey_data, route_config["name"])
                journeys.append(journey)
            except Exception as e:
                logger.warning("Failed to parse journey", error=str(e))
                continue
        
        # Calculate statistics
        delays = [j.delay_minutes for j in journeys if not j.is_cancelled]
        avg_delay = sum(delays) / len(delays) if delays else 0
        max_delay = max(delays) if delays else 0
        
        # Collect disruptions
        disruptions = []
        for journey in journeys:
            disruptions.extend(journey.messages)
        disruptions = list(set(disruptions))  # Remove duplicates
        
        # Create status
        status = RouteStatus(
            route_name=route_config["name"],
            next_journeys=journeys,
            average_delay=avg_delay,
            max_delay=max_delay,
            disruptions=disruptions,
            last_updated=datetime.now()
        )
        
        # Cache result
        self.cache[cache_key] = {
            "data": status,
            "timestamp": datetime.now()
        }
        
        return status
    
    def clear_cache(self):
        """Clear the API cache."""
        self.cache.clear()
        logger.info("RIS API cache cleared")

# Global RIS API client
ris_api = RISApiClient()

if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("Testing Route 1 (Schwaikheim → Feuersee)...")
        status1 = await ris_api.get_route_status(1)
        print(f"Next S-Bahn: {status1.next_journeys[0].line} at {status1.next_journeys[0].departure_planned.strftime('%H:%M')}")
        print(f"Delay: {status1.next_journeys[0].delay_minutes} min")
        
        print("\nTesting Route 2 (Feuersee → Schwaikheim)...")
        status2 = await ris_api.get_route_status(2)
        print(f"Next S-Bahn: {status2.next_journeys[0].line} at {status2.next_journeys[0].departure_planned.strftime('%H:%M')}")
        print(f"Delay: {status2.next_journeys[0].delay_minutes} min")
    
    asyncio.run(test())