import os
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from massive import RESTClient
from massive.rest.models.snapshot import TickerSnapshot
from massive.rest.models.aggs import Agg, DailyOpenCloseAgg
from massive.rest.models.trades import Trade
from urllib3 import HTTPResponse
from config import Config


class MassiveClient:
    def __init__(self, config: Config):
        load_dotenv()
        self.config = config
        self.api_key = config.api_key or os.getenv('MASSIVE_API_KEY')
        if not self.api_key:
            raise ValueError("MASSIVE_API_KEY not found in environment variables or config")
        self.client = RESTClient(self.api_key)
        
        # Rate limiting tracking
        self.call_count = 0
        self.last_sleep = time.time()
    
    def _handle_rate_limiting(self):
        """Handle rate limiting with configurable sleep patterns"""
        self.call_count += 1
        if self.call_count >= self.config.calls_before_sleep:
            time.sleep(self.config.sleep_duration)
            self.call_count = 0
            self.last_sleep = time.time()
    
    def get_market_snapshot(self, tickers: List[str]) -> Optional[List[TickerSnapshot]]:
        """Get full market snapshot for multiple tickers"""
        try:
            self._handle_rate_limiting()
            tickers_param = ','.join(tickers)
            response = self.client.get_snapshot_all(market_type="stocks", tickers=tickers_param)
            
            if isinstance(response, HTTPResponse):
                print(f"API error getting market snapshot for {tickers}: HTTP {response.status}")
                return None
                
            return response
        except Exception as e:
            print(f"Error getting market snapshot for {tickers}: {e}")
            return None
    
    def get_single_ticker_snapshot(self, ticker: str) -> Optional[TickerSnapshot]:
        """Get snapshot for a single ticker"""
        try:
            self._handle_rate_limiting()
            response = self.client.get_snapshot_ticker(market_type="stocks", ticker=ticker)
            
            if isinstance(response, HTTPResponse):
                print(f"API error getting snapshot for {ticker}: HTTP {response.status}")
                return None
                
            return response
        except Exception as e:
            print(f"Error getting snapshot for {ticker}: {e}")
            return None
    
    def get_aggregates(self, ticker: str, multiplier: int, timespan: str, 
                      from_date: str, to_date: str, adjusted: bool = True) -> Optional[List[Agg]]:
        """Get aggregates/bars for a ticker over a date range"""
        try:
            self._handle_rate_limiting()
            response = self.client.list_aggs(
                ticker,
                multiplier,
                timespan,
                from_date,
                to_date,
                adjusted=adjusted
            )
            
            if isinstance(response, HTTPResponse):
                print(f"API error getting aggregates for {ticker}: HTTP {response.status}")
                return None
            
            # Convert iterator to list
            return list(response)
        except Exception as e:
            print(f"Error getting aggregates for {ticker}: {e}")
            return None
    
    def get_previous_day_data(self, ticker: str, date: str) -> Optional[DailyOpenCloseAgg]:
        """Get previous day OHLCV data for a ticker"""
        try:
            self._handle_rate_limiting()
            response = self.client.get_daily_open_close_agg(ticker=ticker, date=date)
            
            if isinstance(response, HTTPResponse):
                print(f"API error getting previous day data for {ticker} on {date}: HTTP {response.status}")
                return None
                
            return response
        except Exception as e:
            print(f"Error getting previous day data for {ticker} on {date}: {e}")
            return None
    
    def get_premarket_aggregates(self, ticker: str, date: str) -> Optional[List[Agg]]:
        """Get premarket aggregates using minute bars for premarket window"""
        # Extract timespan number from config (e.g., "5minute" -> 5)
        timespan_parts = self.config.premarket_timespan.split('minute')
        multiplier = int(timespan_parts[0]) if timespan_parts[0] else 1
        
        return self.get_aggregates(
            ticker=ticker,
            multiplier=multiplier,
            timespan="minute",
            from_date=date,
            to_date=date,
            adjusted=True
        )
    
    def get_recent_trades(self, ticker: str, timestamp_gte: Optional[str] = None, limit: int = 1000) -> List[Trade] | HTTPResponse | None:
        """Get recent trades for a ticker with optional timestamp filter"""
        try:
            self._handle_rate_limiting()
            response = self.client.list_trades(
                ticker=ticker,
                timestamp_gte=timestamp_gte,
                limit=limit
            )
            # Check if it's an HTTPResponse (error case)
            if isinstance(response, HTTPResponse):
                return response
            
            # If it's an iterator, convert to list
            return list(response)
            
        except Exception as e:
            print(f"Error getting trades for {ticker}: {e}")
            return None
    