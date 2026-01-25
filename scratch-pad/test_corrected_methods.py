#!/usr/bin/env python3
"""Test script to explore actual method signatures and return types."""

import os
from dotenv import load_dotenv
from massive import RESTClient

# Load environment variables
load_dotenv()

def test_corrected_methods():
    api_key = os.getenv('MASSIVE_API_KEY')
    if not api_key:
        print("MASSIVE_API_KEY not found in environment variables")
        return

    client = RESTClient(api_key)
    
    print("Testing corrected method signatures and return types...")
    print("=" * 60)
    
    # Test 1: Single ticker snapshot with market_type
    print("1. Testing get_snapshot_ticker with market_type:")
    try:
        response = client.get_snapshot_ticker(market_type="stocks", ticker="AAPL")
        print(f"   Response type: {type(response)}")
        if hasattr(response, '__dict__'):
            print(f"   Response attrs: {list(vars(response).keys())}")
        print(f"   Response: {response}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test 2: Multiple ticker snapshots with market_type
    print("2. Testing get_snapshot_all with market_type:")
    try:
        response = client.get_snapshot_all(market_type="stocks", tickers="AAPL,MSFT")
        print(f"   Response type: {type(response)}")
        if hasattr(response, '__dict__'):
            print(f"   Response attrs: {list(vars(response).keys())}")
        print(f"   Response: {response}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test 3: List aggregates - iterate the generator to get actual data
    print("3. Testing list_aggs (iterate generator):")
    try:
        response = client.list_aggs(
            ticker="AAPL",
            multiplier=1,
            timespan="day",
            from_="2026-01-20",
            to="2026-01-21"
        )
        print(f"   Generator type: {type(response)}")
        
        # Convert generator to list to see actual data
        results = list(response)
        if results:
            first_result = results[0]
            print(f"   First result type: {type(first_result)}")
            print(f"   First result: {first_result}")
        else:
            print("   No results found")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test 4: Daily open close with a real date
    print("4. Testing get_daily_open_close_agg with real date:")
    try:
        response = client.get_daily_open_close_agg(ticker="AAPL", date="2026-01-23")
        print(f"   Response type: {type(response)}")
        print(f"   Response: {response}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_corrected_methods()