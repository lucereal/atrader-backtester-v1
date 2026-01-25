from typing import List
import time
from config import Config
from massive_clients.massive_client import MassiveClient
from time_simulator import TimeSimulator
from premarket_data_service import PremarketDataService, PremarketSession


class TickerProcessor:
    """Orchestrates the complete premarket research pipeline"""
    
    def __init__(self, config: Config, is_live: bool = False):
        self.config = config
        self.is_live = is_live
        
        # Initialize components
        self.time_simulator = TimeSimulator(config, is_live)
        self.client = MassiveClient(config)
        self.data_service = PremarketDataService(self.client, self.time_simulator, config)
        
        # State tracking
        self.incomplete_tickers = []
        self.retry_count = 0
        self.max_retries = 3
    
    def run_premarket_research(self, tickers: List[str]) -> PremarketSession:
        """Run complete premarket research pipeline for a list of tickers"""
        
        print(f"Starting premarket research at {self.time_simulator.get_current_time()}")
        print(f"Mode: {'LIVE' if self.is_live else 'SIMULATION'}")
        print(f"Processing tickers: {tickers}")
        print("-" * 50)
        
        # Initial data collection
        session = self.data_service.collect_session_data(tickers)
        
        self._print_session_summary(session)
        
        # Handle incomplete tickers
        if session.incomplete_tickers:
            print(f"\nFound {len(session.incomplete_tickers)} incomplete tickers")
            self._handle_incomplete_tickers(session)
        
        return session
    
    def _handle_incomplete_tickers(self, session: PremarketSession):
        """Handle tickers with incomplete data"""
        self.incomplete_tickers = session.incomplete_tickers.copy()
        
        if self.is_live:
            print("Live mode: Will retry incomplete tickers in next update cycle")
        else:
            print("Simulation mode: Marking incomplete tickers for reference")
            for ticker in session.incomplete_tickers:
                ticker_data = session.tickers_data[ticker]
                print(f"  {ticker}: Missing {ticker_data.missing_data}")
    
    def retry_incomplete_tickers(self) -> PremarketSession | None:
        """Retry data collection for previously incomplete tickers"""
        if not self.incomplete_tickers:
            print("No incomplete tickers to retry")
            return None
        
        if self.retry_count >= self.max_retries:
            print(f"Max retries ({self.max_retries}) reached. Skipping retry.")
            return None
        
        self.retry_count += 1
        print(f"\nRetry attempt {self.retry_count}/{self.max_retries} for incomplete tickers...")
        
        session = self.data_service.collect_session_data(self.incomplete_tickers)
        
        # Update incomplete ticker list
        self.incomplete_tickers = [t for t in self.incomplete_tickers 
                                 if t in session.incomplete_tickers]
        
        self._print_session_summary(session)
        
        return session
    
    def run_continuous_updates(self, tickers: List[str], update_interval_minutes: int = 5):
        """Run continuous updates for live trading (not for backtesting)"""
        if not self.is_live:
            print("Continuous updates only available in live mode")
            return
        
        print(f"Starting continuous updates every {update_interval_minutes} minutes...")
        
        while True:
            try:
                # Run data collection
                session = self.run_premarket_research(tickers)
                
                # Check if we're still in premarket hours
                if not self.time_simulator.is_premarket_hours():
                    print("Market has opened. Stopping continuous updates.")
                    break
                
                # Wait for next update
                print(f"\nWaiting {update_interval_minutes} minutes for next update...")
                time.sleep(update_interval_minutes * 60)
                
                # Retry incomplete tickers
                if self.incomplete_tickers:
                    self.retry_incomplete_tickers()
                
            except KeyboardInterrupt:
                print("\nStopping continuous updates...")
                break
            except Exception as e:
                print(f"Error in continuous updates: {e}")
                time.sleep(30)  # Wait 30 seconds before retrying
    
    def _print_session_summary(self, session: PremarketSession):
        """Print a summary of the premarket session data"""
        print(f"\nSession Summary ({session.session_time})")
        print("-" * 30)
        print(f"Total tickers: {len(session.tickers_data)}")
        print(f"Complete tickers: {len(session.complete_tickers)}")
        print(f"Incomplete tickers: {len(session.incomplete_tickers)}")
        
        if session.complete_tickers:
            print("\nComplete Tickers Data:")
            for ticker in session.complete_tickers:
                data = session.tickers_data[ticker]
                self._print_ticker_summary(data)
        
        if session.incomplete_tickers:
            print("\nIncomplete Tickers:")
            for ticker in session.incomplete_tickers:
                data = session.tickers_data[ticker]
                print(f"  {ticker}: Missing {', '.join(data.missing_data)}")
    
    def _print_ticker_summary(self, data):
        """Print a summary for a single ticker's data"""
        print(f"\n  {data.ticker}:")
        
        if data.gap_percent is not None:
            print(f"    Gap: {data.gap_percent:.2f}%")
        
        if data.last_trade_price and data.prev_close:
            print(f"    Price: ${data.last_trade_price:.2f} (Prev: ${data.prev_close:.2f})")
        
        if data.bid_price and data.ask_price:
            print(f"    Quote: ${data.bid_price:.2f} x ${data.ask_price:.2f}")
        
        if data.spread_percent is not None:
            print(f"    Spread: {data.spread_percent:.2f}%")
        
        if data.premarket_volume:
            print(f"    Volume: {data.premarket_volume:,}")
        
        if data.time_since_last_trade is not None:
            print(f"    Last Trade: {data.time_since_last_trade:.1f} min ago")
    
    def get_simulation_report(self, session: PremarketSession) -> dict:
        """Generate a structured report for simulation results"""
        report = {
            'session_time': session.session_time,
            'mode': 'SIMULATION',
            'config': {
                'simulation_date': self.config.simulation_date,
                'simulation_time': self.config.simulation_time,
                'lookback_days': self.config.lookback_days
            },
            'summary': {
                'total_tickers': len(session.tickers_data),
                'complete_tickers': len(session.complete_tickers),
                'incomplete_tickers': len(session.incomplete_tickers)
            },
            'tickers': {}
        }
        
        for ticker, data in session.tickers_data.items():
            report['tickers'][ticker] = {
                'is_complete': data.is_complete,
                'missing_data': data.missing_data,
                'gap_percent': data.gap_percent,
                'last_trade_price': data.last_trade_price,
                'prev_close': data.prev_close,
                'spread_percent': data.spread_percent,
                'premarket_volume': data.premarket_volume,
                'time_since_last_trade': data.time_since_last_trade
            }
        
        return report