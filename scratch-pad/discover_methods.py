#!/usr/bin/env python3
"""Test script to discover available methods on Massive RESTClient."""

import os
from dotenv import load_dotenv
from massive import RESTClient

# Load environment variables
load_dotenv()

def discover_client_methods():
    api_key = os.getenv('MASSIVE_API_KEY')
    if not api_key:
        print("MASSIVE_API_KEY not found in environment variables")
        return

    client = RESTClient(api_key)
    
    print("Available methods on RESTClient:")
    print("=" * 50)
    
    # Get all methods that don't start with underscore
    methods = [method for method in dir(client) if not method.startswith('_') and callable(getattr(client, method))]
    
    # Group by common patterns
    snapshot_methods = [m for m in methods if 'snapshot' in m.lower()]
    agg_methods = [m for m in methods if 'agg' in m.lower()]
    trade_methods = [m for m in methods if 'trade' in m.lower()]
    quote_methods = [m for m in methods if 'quote' in m.lower()]
    list_methods = [m for m in methods if m.startswith('list_')]
    get_methods = [m for m in methods if m.startswith('get_')]
    other_methods = [m for m in methods if m not in snapshot_methods + agg_methods + trade_methods + quote_methods + list_methods + get_methods]
    
    print("SNAPSHOT METHODS:")
    for method in sorted(snapshot_methods):
        print(f"  {method}")
    
    print("\nAGGREGATE METHODS:")
    for method in sorted(agg_methods):
        print(f"  {method}")
    
    print("\nTRADE METHODS:")
    for method in sorted(trade_methods):
        print(f"  {method}")
    
    print("\nQUOTE METHODS:")
    for method in sorted(quote_methods):
        print(f"  {method}")
    
    print("\nLIST METHODS:")
    for method in sorted(list_methods):
        print(f"  {method}")
    
    print("\nGET METHODS:")
    for method in sorted(get_methods):
        print(f"  {method}")
    
    print("\nOTHER METHODS:")
    for method in sorted(other_methods):
        print(f"  {method}")
    
    print(f"\nTotal methods: {len(methods)}")

if __name__ == "__main__":
    discover_client_methods()