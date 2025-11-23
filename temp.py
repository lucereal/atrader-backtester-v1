from massive_client import MassiveClient
import json
from datetime import datetime, timedelta

class TestRunner:
    def __init__(self):
        self.massive_client = MassiveClient()
    
    def run_options_test(self):
        contracts = self.massive_client.list_options_contracts_by_ticker("SPY", contract_type="call", expiration_date="2024-12-02", 
                                                                         as_of="2024-12-02", strike_price=600, limit=10)
        
        print(f"Found {len(contracts)} contracts for ticker SPY")

        for contract in contracts:
            print(json.dumps(contract.__dict__, indent=2))
            aggs = self.massive_client.list_aggs(contract.ticker, multiplier=1, 
                                                   timespan="hour", from_date="2024-12-02", 
                                                   to_date="2024-12-02", limit=5000)
            print(f"Found {len(aggs)} aggs for contract {contract.ticker}")
            for agg in aggs:
                print(json.dumps(agg.__dict__, indent=2))

    def load_todays_trades(self, entry_date):
        """
        Build a function that returns "Today's trade" for a given entry date.
        
        Process:
        1. Find 20∆ put
        2. Find 20∆ call
        3. Build the 0DTE condor structure
        4. Record entry mid-price using early aggregates (first 30 min)
        
        Args:
            entry_date (str): Date in format "YYYY-MM-DD"
            
        Returns:
            dict: Contains condor structure and entry prices
        """
        
        # Step 1: Get all SPY options contracts expiring on the entry date (0DTE)
        contracts = self.massive_client.list_options_contracts_by_ticker(
            ticker="SPY", 
            expiration_date=entry_date, 
            as_of=entry_date, 
            limit=100  # Get more contracts to find the right deltas
        )
        
        print(f"Found {len(contracts)} contracts expiring on {entry_date}")
        
        # Separate calls and puts
        calls = [c for c in contracts if c.contract_type == "call"]
        puts = [c for c in contracts if c.contract_type == "put"]
        
        # Sort by strike price
        calls.sort(key=lambda x: x.strike_price)
        puts.sort(key=lambda x: x.strike_price)
        
        # Step 2: Find 20∆ contracts (approximation based on strike prices)
        # Note: This is a simplified approach. Real delta calculation would require 
        # underlying price, volatility, time to expiration, and risk-free rate
        
        # For now, we'll use strike price relative to underlying as a proxy for delta
        # Typically, 20∆ options are somewhat out-of-the-money
        
        # Get the middle strikes as approximation for 20∆
        if len(calls) > 4 and len(puts) > 4:
            # Take strikes that are likely around 20∆ (roughly 1/5 from ATM)
            call_20_delta_idx = len(calls) // 5 * 4  # Upper 20% of strikes
            put_20_delta_idx = len(puts) // 5  # Lower 20% of strikes
            
            call_20_delta = calls[call_20_delta_idx] if call_20_delta_idx < len(calls) else calls[-1]
            put_20_delta = puts[put_20_delta_idx] if put_20_delta_idx < len(puts) else puts[0]
        else:
            print("Not enough contracts found to build condor")
            return None
        
        print(f"Selected 20∆ Call: {call_20_delta.ticker} (Strike: {call_20_delta.strike_price})")
        print(f"Selected 20∆ Put: {put_20_delta.ticker} (Strike: {put_20_delta.strike_price})")
        
        # Step 3: Build 0DTE Iron Condor structure
        # Iron Condor = Short Call + Short Put + Long Call (higher strike) + Long Put (lower strike)
        
        # Find protection strikes (further OTM)
        call_protection = None
        put_protection = None
        
        # Find long call (higher strike than short call)
        for call in calls:
            if call.strike_price > call_20_delta.strike_price:
                call_protection = call
                break
        
        # Find long put (lower strike than short put)
        for put in reversed(puts):  # Start from lowest strikes
            if put.strike_price < put_20_delta.strike_price:
                put_protection = put
                break
        
        if not call_protection or not put_protection:
            print("Could not find protection strikes for condor")
            return None
        
        condor_structure = {
            "short_call": call_20_delta,
            "short_put": put_20_delta,
            "long_call": call_protection,
            "long_put": put_protection,
            "entry_date": entry_date,
            "structure_type": "iron_condor"
        }
        
        print(f"Iron Condor Structure:")
        print(f"  Short Call: {call_20_delta.ticker} (Strike: {call_20_delta.strike_price})")
        print(f"  Long Call:  {call_protection.ticker} (Strike: {call_protection.strike_price})")
        print(f"  Short Put:  {put_20_delta.ticker} (Strike: {put_20_delta.strike_price})")
        print(f"  Long Put:   {put_protection.ticker} (Strike: {put_protection.strike_price})")
        
        # Step 4: Get early aggregates (first 30 minutes) for entry pricing
        entry_prices = {}
        
        contracts_to_price = [call_20_delta, put_20_delta, call_protection, put_protection]
        
        for contract in contracts_to_price:
            try:
                # Get minute-level data for the first 30 minutes of trading
                aggs = self.massive_client.list_aggs(
                    ticker=contract.ticker,
                    multiplier=1,
                    timespan="minute",
                    from_date=entry_date,
                    to_date=entry_date,
                    limit=30  # First 30 minutes
                )
                
                if aggs:
                    # Calculate mid-price from first 30 minutes
                    total_mid = 0
                    count = 0
                    for agg in aggs[:30]:  # Ensure we only take first 30
                        mid_price = (agg.high + agg.low) / 2
                        total_mid += mid_price
                        count += 1
                    
                    avg_mid_price = total_mid / count if count > 0 else None
                    entry_prices[contract.ticker] = {
                        "avg_mid_price": avg_mid_price,
                        "first_30_min_data_points": count,
                        "contract_type": contract.contract_type,
                        "strike_price": contract.strike_price
                    }
                    
                    print(f"Entry price for {contract.ticker}: ${avg_mid_price:.2f} (from {count} data points)")
                else:
                    print(f"No pricing data found for {contract.ticker}")
                    entry_prices[contract.ticker] = None
                    
            except Exception as e:
                print(f"Error getting pricing for {contract.ticker}: {e}")
                entry_prices[contract.ticker] = None
        
        # Calculate net premium received (short positions - long positions)
        short_call_price = entry_prices.get(call_20_delta.ticker, {}).get("avg_mid_price", 0)
        short_put_price = entry_prices.get(put_20_delta.ticker, {}).get("avg_mid_price", 0)
        long_call_price = entry_prices.get(call_protection.ticker, {}).get("avg_mid_price", 0)
        long_put_price = entry_prices.get(put_protection.ticker, {}).get("avg_mid_price", 0)
        
        net_premium = (short_call_price + short_put_price) - (long_call_price + long_put_price)
        
        result = {
            "condor_structure": condor_structure,
            "entry_prices": entry_prices,
            "net_premium_received": net_premium,
            "entry_summary": {
                "date": entry_date,
                "net_premium": net_premium,
                "max_profit": net_premium,  # Max profit = premium received
                "structure": "iron_condor"
            }
        }
        
        print(f"\nTrade Summary for {entry_date}:")
        print(f"Net Premium Received: ${net_premium:.2f}")
        print(f"Max Profit: ${net_premium:.2f}")
        
        return result


# Example usage
if __name__ == "__main__":
    test_runner = TestRunner()
    
    # Test the new function
    trade_data = test_runner.load_todays_trades("2024-12-02")
    
    if trade_data:
        print("\n" + "="*50)
        print("TRADE DATA SUMMARY:")
        print(json.dumps(trade_data["entry_summary"], indent=2))