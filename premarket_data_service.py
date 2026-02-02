from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import sys
import os
# Add the massive-clients directory to the path
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'massive-clients'))
from massive_clients.massive_client import MassiveClient
from time_simulator import TimeSimulator
from config import Config


@dataclass
class TickerData:
    """Data structure for a single ticker's V1 premarket research data"""
    ticker: str
    
    # Ticker Identity/Reference
    company_name: Optional[str] = None
    exchange: Optional[str] = None
    
    # Previous Day Context
    prev_close: Optional[float] = None
    prev_high: Optional[float] = None
    prev_low: Optional[float] = None
    prev_volume: Optional[int] = None
    
    # Premarket Price State
    last_trade_price: Optional[float] = None
    premarket_high: Optional[float] = None
    premarket_low: Optional[float] = None
    premarket_volume: Optional[int] = None
    
    # Liquidity/Tradability
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    
    # Activity/Urgency Signals
    last_trade_time: Optional[datetime] = None
    trade_count: Optional[int] = None
    volume_per_minute: Optional[float] = None
    
    # Data Completeness Flags
    is_complete: bool = False
    missing_data: List[str] = field(default_factory=list)
    
    # Derived Metrics (computed)
    gap_percent: Optional[float] = None
    premarket_range_percent: Optional[float] = None
    spread_percent: Optional[float] = None
    time_since_last_trade: Optional[float] = None


@dataclass 
class PremarketSession:
    """Container for a complete premarket research session"""
    session_time: datetime
    tickers_data: Dict[str, TickerData]
    incomplete_tickers: List[str]
    complete_tickers: List[str]


class PremarketDataService:
    """Service layer for collecting and processing V1 premarket research data"""
    
    def __init__(self, client: MassiveClient, time_simulator: TimeSimulator, config: Config):
        self.client = client
        self.time_simulator = time_simulator
        self.config = config
    
    def collect_session_data(self, tickers: List[str]) -> PremarketSession:
        """Collect complete premarket session data for a list of tickers"""
        session_time = self.time_simulator.get_current_time()
        tickers_data = {}
        incomplete_tickers = []
        complete_tickers = []
        
        for ticker in tickers:
            print(f"Collecting data for {ticker}...")
            ticker_data = self._collect_ticker_data(ticker)
            
            if ticker_data.is_complete:
                complete_tickers.append(ticker)
            else:
                incomplete_tickers.append(ticker)
                print(f"  Warning: {ticker} missing data: {ticker_data.missing_data}")
            
            tickers_data[ticker] = ticker_data
        
        return PremarketSession(
            session_time=session_time,
            tickers_data=tickers_data,
            incomplete_tickers=incomplete_tickers,
            complete_tickers=complete_tickers
        )
    
    def _collect_ticker_data(self, ticker: str) -> TickerData:
        """Collect all V1 data for a single ticker"""
        ticker_data = TickerData(ticker=ticker)
        
        # Collect current snapshot data (handles live vs historical)
        self._collect_snapshot_data(ticker_data)
        
        # Collect previous day data (uses time simulator)
        self._collect_previous_day_data(ticker_data)
        
        # Collect detailed premarket aggregates (backtest mode only)
        self._collect_premarket_aggregates(ticker_data)
        
        # Calculate derived metrics
        self._calculate_derived_metrics(ticker_data)
        
        # Check data completeness
        self._check_data_completeness(ticker_data)
        
        return ticker_data
    
    def _collect_snapshot_data(self, ticker_data: TickerData):
        """Collect current snapshot data for a ticker - live or historical based on time simulator"""
        
        if self.time_simulator.is_live:
            # Live mode - use snapshot endpoint
            snapshot = self.client.get_single_ticker_snapshot(ticker_data.ticker)
            
            if not snapshot:
                ticker_data.missing_data.append("snapshot")
                return
            
            self._process_live_snapshot(snapshot, ticker_data)
        else:
            # Backtest mode - use historical aggregates to simulate snapshot
            self._collect_historical_snapshot_data(ticker_data)
    
    def _process_live_snapshot(self, snapshot, ticker_data: TickerData):
        """Process live snapshot data from the API"""
        # Extract last trade data
        if hasattr(snapshot, 'last_trade') and snapshot.last_trade:
            last_trade = snapshot.last_trade
            ticker_data.last_trade_price = getattr(last_trade, 'price', None)
            if hasattr(last_trade, 'participant_timestamp') and last_trade.participant_timestamp:
                # Convert nanosecond timestamp to datetime
                ticker_data.last_trade_time = datetime.fromtimestamp(last_trade.participant_timestamp / 1_000_000_000)
        
        # Extract quote data
        if hasattr(snapshot, 'last_quote') and snapshot.last_quote and self.config.enable_quotes_data:
            last_quote = snapshot.last_quote
            ticker_data.bid_price = getattr(last_quote, 'bid', None)
            ticker_data.ask_price = getattr(last_quote, 'ask', None)
            ticker_data.bid_size = getattr(last_quote, 'bid_size', None)
            ticker_data.ask_size = getattr(last_quote, 'ask_size', None)
        
        # Extract current day data (includes premarket activity)
        if hasattr(snapshot, 'day') and snapshot.day:
            day_data = snapshot.day
            ticker_data.premarket_high = getattr(day_data, 'high', None)
            ticker_data.premarket_low = getattr(day_data, 'low', None)
            ticker_data.premarket_volume = getattr(day_data, 'volume', None)
        
        # Extract previous day data if available
        if hasattr(snapshot, 'prev_day') and snapshot.prev_day:
            prev_day = snapshot.prev_day
            ticker_data.prev_close = getattr(prev_day, 'close', None)
            ticker_data.prev_high = getattr(prev_day, 'high', None)
            ticker_data.prev_low = getattr(prev_day, 'low', None)
            ticker_data.prev_volume = getattr(prev_day, 'volume', None)
    
    def _collect_historical_snapshot_data(self, ticker_data: TickerData):
        """Collect historical data to simulate snapshot for backtesting"""
        current_date = self.time_simulator.get_date_string()
        
        # Get 15-minute historical aggregates for the simulated date
        aggregates = self.client.get_historical_snapshot_equivalent(
            ticker=ticker_data.ticker,
            date=current_date,
            timespan="minute",
            multiplier=15
        )
        
        if not aggregates:
            ticker_data.missing_data.append("historical_snapshot")
            return
        
        # Normalize the historical aggregates to simulate live snapshot data
        self._normalize_historical_aggregates(aggregates, ticker_data)
    
    def _normalize_historical_aggregates(self, aggregates, ticker_data: TickerData):
        """Normalize historical aggregates to match live snapshot data structure"""
        if not aggregates:
            return
        
        # Get the most recent bar as "current" trade data
        latest_bar = aggregates[-1]
        
        # Simulate last trade data from latest bar
        ticker_data.last_trade_price = getattr(latest_bar, 'close', None)
        
        if hasattr(latest_bar, 'timestamp') and latest_bar.timestamp:
            ticker_data.last_trade_time = datetime.fromtimestamp(latest_bar.timestamp / 1_000_000_000)
        
        # Calculate day's high, low, volume from all bars
        ticker_data.premarket_high = max(getattr(bar, 'high', 0) for bar in aggregates)
        ticker_data.premarket_low = min(
            getattr(bar, 'low', float('inf')) for bar in aggregates 
            if getattr(bar, 'low', 0) > 0
        )
        ticker_data.premarket_volume = sum(getattr(bar, 'volume', 0) for bar in aggregates)
        
        # Fetch historical quotes for bid/ask data (only if enabled)
        if self.config.enable_quotes_data:
            self._collect_historical_quotes(ticker_data)
    
    def _collect_historical_quotes(self, ticker_data: TickerData):
        """Collect historical quotes to get bid/ask data for backtesting"""
        current_date = self.time_simulator.get_date_string()
        
        # Get historical quotes for the simulated date
        quotes = self.client.get_historical_quotes(
            ticker=ticker_data.ticker,
            date=current_date,
            limit=1000  # Get recent quotes
        )
        
        if not quotes:
            # Mark as missing if we can't get historical quotes
            ticker_data.missing_data.extend(["bid_price", "ask_price", "bid_size", "ask_size"])
            return
        
        # Get the most recent quote for current bid/ask
        latest_quote = quotes[-1] if quotes else None
        
        if latest_quote:
            ticker_data.bid_price = getattr(latest_quote, 'bid', None)
            ticker_data.ask_price = getattr(latest_quote, 'ask', None)
            ticker_data.bid_size = getattr(latest_quote, 'bid_size', None)
            ticker_data.ask_size = getattr(latest_quote, 'ask_size', None)
        else:
            # Mark as missing if quote data is incomplete
            ticker_data.missing_data.extend(["bid_price", "ask_price", "bid_size", "ask_size"])
    
    def _collect_previous_day_data(self, ticker_data: TickerData):
        """Collect previous day OHLCV data if not available from snapshot"""
        if ticker_data.prev_close is not None:
            return  # Already have previous day data from snapshot
        
        # Try to find the most recent day with actual trading data
        # Start from the day before simulation date and keep going back
        max_attempts = 10  # Don't go back more than 10 days
        current_date = self.time_simulator.get_current_time().date()
        
        for days_back in range(1, max_attempts + 1):
            # Calculate the date to try
            from datetime import timedelta
            try_date = current_date - timedelta(days=days_back)
            date_str = try_date.strftime("%Y-%m-%d")
            
            # Try to get data for this date
            prev_day_data = self.client.get_previous_day_data(ticker_data.ticker, date_str)
            
            if prev_day_data and hasattr(prev_day_data, 'close') and prev_day_data.close is not None:
                # Found valid trading data
                ticker_data.prev_close = getattr(prev_day_data, 'close', None)
                ticker_data.prev_high = getattr(prev_day_data, 'high', None)
                ticker_data.prev_low = getattr(prev_day_data, 'low', None)
                ticker_data.prev_volume = getattr(prev_day_data, 'volume', None)
                print(f"  Found previous day data from {date_str} (went back {days_back} days)")
                return
        
        # If we get here, we couldn't find any valid trading data
        ticker_data.missing_data.append("previous_day")
        print(f"  Warning: Could not find previous day trading data within {max_attempts} days")
    
    def _collect_premarket_aggregates(self, ticker_data: TickerData):
        """Collect premarket minute aggregates for detailed analysis"""
        # Only collect detailed premarket aggregates in backtest mode
        if self.time_simulator.is_live:
            return  # Live mode gets premarket data from snapshot
        
        current_date = self.time_simulator.get_date_string()
        aggregates = self.client.get_premarket_aggregates(ticker_data.ticker, current_date)
        
        if not aggregates:
            ticker_data.missing_data.append("premarket_aggregates")
            return
        
        # Filter to premarket hours only (4:00 AM - 9:30 AM)
        premarket_bars = self._filter_premarket_bars(aggregates)
        
        if premarket_bars:
            # Calculate premarket-specific metrics
            ticker_data.trade_count = len(premarket_bars)
            
            # Calculate volume per minute (approximate)
            total_minutes = len(premarket_bars) * 15  # 15-minute bars (from our historical snapshot)
            if total_minutes > 0 and ticker_data.premarket_volume:
                ticker_data.volume_per_minute = ticker_data.premarket_volume / total_minutes
    
    def _filter_premarket_bars(self, bars: List[Any]) -> List[Any]:
        """Filter bars to only include premarket hours"""
        premarket_bars = []
        
        for bar in bars:
            # Agg objects use 'timestamp' field, not participant_timestamp
            if not hasattr(bar, 'timestamp'):
                continue
            
            # Convert timestamp to datetime (nanoseconds to seconds)
            bar_time = datetime.fromtimestamp(bar.timestamp / 1_000_000_000)
            
            # Check if within premarket hours (4:00 - 9:30)
            if (bar_time.hour >= 4 and bar_time.hour < 9) or (bar_time.hour == 9 and bar_time.minute < 30):
                premarket_bars.append(bar)
        
        return premarket_bars
    
    def _calculate_derived_metrics(self, ticker_data: TickerData):
        """Calculate derived V1 metrics from raw data"""
        
        # Gap percentage
        if ticker_data.prev_close and ticker_data.last_trade_price:
            ticker_data.gap_percent = ((ticker_data.last_trade_price - ticker_data.prev_close) / 
                                     ticker_data.prev_close) * 100
        
        # Premarket range percentage
        if ticker_data.premarket_high and ticker_data.premarket_low and ticker_data.prev_close:
            range_value = ticker_data.premarket_high - ticker_data.premarket_low
            ticker_data.premarket_range_percent = (range_value / ticker_data.prev_close) * 100
        
        # Spread percentage
        if ticker_data.bid_price and ticker_data.ask_price and ticker_data.last_trade_price:
            spread = ticker_data.ask_price - ticker_data.bid_price
            ticker_data.spread_percent = (spread / ticker_data.last_trade_price) * 100
        
        # Time since last trade (in minutes)
        if ticker_data.last_trade_time:
            current_time = self.time_simulator.get_current_time()
            time_diff = current_time - ticker_data.last_trade_time
            ticker_data.time_since_last_trade = time_diff.total_seconds() / 60
    
    def _check_data_completeness(self, ticker_data: TickerData):
        """Check if ticker has all required data based on config"""
        required_fields = []
        
        if self.config.require_last_trade:
            if not ticker_data.last_trade_price:
                required_fields.append("last_trade_price")
            if not ticker_data.last_trade_time:
                required_fields.append("last_trade_time")
        
        if self.config.require_last_quote and self.config.enable_quotes_data:
            if not ticker_data.bid_price:
                required_fields.append("bid_price")
            if not ticker_data.ask_price:
                required_fields.append("ask_price")
        
        if self.config.require_prev_day:
            if not ticker_data.prev_close:
                required_fields.append("prev_close")
        
        if required_fields:
            ticker_data.missing_data.extend([field for field in required_fields if field not in ticker_data.missing_data])
            ticker_data.is_complete = False
        else:
            ticker_data.is_complete = True