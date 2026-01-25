from datetime import datetime, timedelta
from typing import Optional
from config import Config


class TimeSimulator:
    """Handles time simulation for backtesting vs live trading"""
    
    def __init__(self, config: Config, is_live: bool = False):
        self.config = config
        self.is_live = is_live
        
        if not is_live:
            # Set simulation time from config
            self._simulation_time = config.get_simulation_datetime()
        else:
            self._simulation_time = None
    
    def get_current_time(self) -> datetime:
        """Get current time (simulation time for backtesting, real time for live)"""
        if self.is_live:
            return datetime.now()
        else:
            if self._simulation_time is None:
                raise ValueError("Simulation time not properly initialized")
            return self._simulation_time
    
    def get_premarket_start_time(self) -> datetime:
        """Get premarket start time for the current date"""
        current_date = self.get_current_time().date()
        premarket_time = datetime.strptime(self.config.premarket_start, "%H:%M").time()
        return datetime.combine(current_date, premarket_time)
    
    def get_market_open_time(self) -> datetime:
        """Get market open time for the current date"""
        current_date = self.get_current_time().date()
        market_open_time = datetime.strptime(self.config.market_open, "%H:%M").time()
        return datetime.combine(current_date, market_open_time)
    
    def get_data_collection_window(self) -> tuple[datetime, datetime]:
        """Get the time window for initial data collection (premarket start to simulation time)"""
        premarket_start = self.get_premarket_start_time()
        current = self.get_current_time()
        
        return premarket_start, current
    
    def is_premarket_hours(self) -> bool:
        """Check if current time is within premarket hours"""
        current = self.get_current_time()
        premarket_start = self.get_premarket_start_time()
        market_open = self.get_market_open_time()
        
        return premarket_start <= current < market_open
    
    def is_market_hours(self) -> bool:
        """Check if current time is within regular market hours"""
        current = self.get_current_time()
        market_open = self.get_market_open_time()
        
        # Assuming market closes at 4:00 PM
        market_close_time = datetime.strptime("16:00", "%H:%M").time()
        market_close = datetime.combine(current.date(), market_close_time)
        
        return market_open <= current < market_close
    
    def advance_simulation_time(self, minutes: int = 1):
        """Advance simulation time (only for backtesting)"""
        if not self.is_live and self._simulation_time:
            self._simulation_time += timedelta(minutes=minutes)
    
    def get_historical_cutoff(self) -> datetime:
        """Get the cutoff time for historical data (only data before this time should be used)"""
        return self.get_current_time()
    
    def format_time_for_api(self, dt: datetime) -> str:
        """Format datetime for API calls (ISO format)"""
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def get_date_string(self) -> str:
        """Get current date as string for API calls"""
        return self.get_current_time().strftime("%Y-%m-%d")