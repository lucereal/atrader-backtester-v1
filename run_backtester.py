from massive_client import MassiveClient
import json

class TestRunner:
    def __init__(self):
        self.massive_client = MassiveClient()
    
    def run_options_test(self):
        #def list_options_contracts_by_ticker(self, ticker, expiration_date, as_of=None, 
        # strike_price=None, order="asc", limit=10):
        contracts = self.massive_client.list_options_contracts_by_ticker("SPY", expiration_date="2024-12-02", 
                                                                         as_of="2024-12-02", limit=100)
        
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


# Example usage
if __name__ == "__main__":
    test_runner = TestRunner()
    result = test_runner.run_options_test()
    print(f"Retrieved {len(result)} contracts:")
    for contract in result:
        print(contract)
