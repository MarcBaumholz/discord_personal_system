"""
Data models for WHOOP API responses.
Uses Pydantic for validation and serialization.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class WhoopUser(BaseModel):
    """WHOOP user profile data."""
    user_id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class WhoopBodyMeasurement(BaseModel):
    """WHOOP body measurement data."""
    height_meter: Optional[float] = None
    weight_kilogram: Optional[float] = None
    max_heart_rate: Optional[int] = None


class WhoopCycleScore(BaseModel):
    """WHOOP cycle score data."""
    strain: Optional[float] = None
    kilojoules: Optional[float] = None
    average_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None


class WhoopCycle(BaseModel):
    """WHOOP cycle (physiological day) data."""
    id: Union[str, int]  # Can be string UUID or integer
    user_id: int
    start: datetime
    end: Optional[datetime] = None  # Can be null
    timezone_offset: str
    score: Optional[WhoopCycleScore] = None


class WhoopSleepStageSummary(BaseModel):
    """WHOOP sleep stage summary."""
    time_in_bed_seconds: Optional[int] = None
    awake_time_seconds: Optional[int] = None
    light_sleep_time_seconds: Optional[int] = None
    slow_wave_sleep_time_seconds: Optional[int] = None
    rem_sleep_time_seconds: Optional[int] = None
    number_of_disturbances: Optional[int] = None


class WhoopSleepNeeded(BaseModel):
    """WHOOP sleep needed breakdown."""
    baseline_seconds: Optional[int] = None
    need_from_sleep_debt_seconds: Optional[int] = None
    need_from_recent_strain_seconds: Optional[int] = None
    need_from_recent_recovery_seconds: Optional[int] = None


class WhoopSleep(BaseModel):
    """WHOOP sleep data."""
    id: Union[str, int]  # Can be string UUID or integer
    user_id: int
    start: datetime
    end: datetime
    timezone_offset: str
    nap: bool
    score: Optional[dict] = None  # Changed to dict as it's a complex object
    stage_summary: Optional[WhoopSleepStageSummary] = None
    sleep_needed: Optional[WhoopSleepNeeded] = None
    respiratory_rate: Optional[float] = None
    sleep_performance_percentage: Optional[float] = None
    sleep_consistency_percentage: Optional[float] = None
    sleep_efficiency_percentage: Optional[float] = None


class WhoopRecovery(BaseModel):
    """WHOOP recovery data."""
    id: Union[str, int]  # Can be string UUID or integer
    user_id: int
    cycle_id: Union[str, int]  # Can be string UUID or integer
    start: datetime
    end: datetime
    timezone_offset: str
    score: Optional[float] = None
    resting_heart_rate: Optional[int] = None
    hrv_rmssd_milli_seconds: Optional[float] = None
    spo2_percentage: Optional[float] = None
    skin_temp_celsius: Optional[float] = None


class WhoopWorkoutScore(BaseModel):
    """WHOOP workout score data."""
    strain: Optional[float] = None
    average_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    kilojoules: Optional[float] = None
    percent_recorded: Optional[float] = None


class WhoopWorkoutZoneDuration(BaseModel):
    """WHOOP workout zone duration."""
    zone_zero_duration_seconds: Optional[int] = None
    zone_one_duration_seconds: Optional[int] = None
    zone_two_duration_seconds: Optional[int] = None
    zone_three_duration_seconds: Optional[int] = None
    zone_four_duration_seconds: Optional[int] = None
    zone_five_duration_seconds: Optional[int] = None


class WhoopWorkout(BaseModel):
    """WHOOP workout data."""
    id: Union[str, int]  # Can be string UUID or integer
    user_id: int
    start: datetime
    end: datetime
    timezone_offset: str
    sport_id: Optional[int] = None  # Optional as it may not exist in v2
    sport_name: str
    score: Optional[WhoopWorkoutScore] = None
    distance_meter: Optional[float] = None
    altitude_gain_meter: Optional[float] = None
    altitude_change_meter: Optional[float] = None
    zone_durations: Optional[WhoopWorkoutZoneDuration] = None


class WhoopTokenResponse(BaseModel):
    """WHOOP OAuth token response."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


class WhoopError(BaseModel):
    """WHOOP API error response."""
    error: str
    error_description: Optional[str] = None
    error_uri: Optional[str] = None


class WhoopPaginatedResponse(BaseModel):
    """WHOOP paginated response wrapper."""
    records: List[Dict[str, Any]]
    next_token: Optional[str] = None


class WhoopWebhookEvent(BaseModel):
    """WHOOP webhook event."""
    event_type: str
    user_id: int
    resource_id: Optional[int] = None
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None
