# used for myself and copilot to test code snippets from massive module
from massive_clients.massive_client import MassiveClient
from time_simulator import TimeSimulator
from config import Config
import json
from dotenv import load_dotenv
import os
load_dotenv()

config = Config()
mc = MassiveClient(config)
tsimi = TimeSimulator(config, is_live=False)

result = mc.get_single_ticker_snapshot("ONDS")
result2 = mc.get_market_snapshot(["ONDS", "AAPL", "MSFT"])

is_pm = tsimi.is_premarket_hours()
dc_window = tsimi.get_data_collection_window()

print(is_pm)
print(dc_window)