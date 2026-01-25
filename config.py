

from datetime import datetime, timedelta
from typing import Optional


class Config:
    # Rate limiting settings
    calls_before_sleep: int = 5
    sleep_duration: float = 1.0
    
    # API Configuration
    api_key: Optional[str] = None
    
    # Backtesting parameters
    simulation_date: str = "2026-01-20"  # YYYY-MM-DD format
    simulation_time: str = "08:00"  # HH:MM format (24-hour)
    lookback_days: int = 5
    
    # Data collection settings
    premarket_timespan: str = "5minute"  # 5minute, 1minute, etc.
    premarket_start: str = "04:00"  # 4:00 AM EST
    market_open: str = "09:30"  # 9:30 AM EST
    
    # Data completeness thresholds
    require_last_trade: bool = True
    require_last_quote: bool = True
    require_prev_day: bool = True
    
    def __init__(self, **kwargs):
        """Initialize config with optional overrides"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown config parameter: {key}")
    
    def get_simulation_datetime(self) -> datetime:
        """Convert simulation_date and simulation_time to datetime"""
        return datetime.strptime(f"{self.simulation_date} {self.simulation_time}", "%Y-%m-%d %H:%M")
    
    def get_lookback_date(self) -> str:
        """Get the start date for historical data collection"""
        sim_date = datetime.strptime(self.simulation_date, "%Y-%m-%d")
        lookback_date = sim_date - timedelta(days=self.lookback_days)
        return lookback_date.strftime("%Y-%m-%d")
    
    def get_previous_day(self) -> str:
        """Get the previous trading day"""
        sim_date = datetime.strptime(self.simulation_date, "%Y-%m-%d")
        prev_day = sim_date - timedelta(days=1)
        return prev_day.strftime("%Y-%m-%d")