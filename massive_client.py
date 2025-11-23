import os
from dotenv import load_dotenv
from massive import RESTClient


class MassiveClient:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('MASSIVE_API_KEY')
        if not self.api_key:
            raise ValueError("MASSIVE_API_KEY not found in environment variables")
        self.client = RESTClient(self.api_key)
    
    def get_options_contracts(self, order="asc", limit=10, sort="ticker"):
        contracts = []
        for contract in self.client.list_options_contracts(
            order=order,
            limit=limit,
            sort=sort,
        ):
            contracts.append(contract)
        return contracts
    
    def get_options_trades(self, contract_id):
        return self.client.get_options_trades(contract_id)
    
    #as_of pecify a point in time for contracts as of this date with format YYYY-MM-DD. Defaults to today's date.
    def list_options_contracts_by_ticker(self, ticker, contract_type=None, expiration_date=None, as_of=None, strike_price=None, order="asc", limit=10):
        contracts = []
        for c in self.client.list_options_contracts(
            underlying_ticker=ticker,
            contract_type=contract_type,
            expiration_date=expiration_date,
            as_of=as_of,
            strike_price=strike_price,
            order=order,
            limit=limit
        ): contracts.append(c)
        return contracts

    def list_trades_for_contract(self, contract_ticker, timestamp, order="asc", limit=10, sort="timestamp"):
        trades = []
        for t in self.client.list_trades(
            ticker=contract_ticker,
            timestamp=timestamp,
            order=order,
            limit=limit,
            sort=sort
        ):  trades.append(t)
        return trades

    def list_aggs(self, ticker, multiplier, timespan, from_date, to_date, adjusted="true", sort="asc", limit=5000):
        aggs = []
        for a in self.client.list_aggs(
            ticker,
            multiplier,
            timespan,
            from_date,
            to_date,
            adjusted=adjusted,
            sort=sort,
            limit=limit,
        ):
            aggs.append(a)
        return aggs

    def get_snapshot_option(self, underlying_ticker, option_contract):
        snapshot = self.client.get_snapshot_option(
            underlying_ticker,
            option_contract 
        )
        return snapshot

# Example usage
if __name__ == "__main__":
    client = MassiveClient()
    contracts = client.get_options_contracts()
    print(contracts)
