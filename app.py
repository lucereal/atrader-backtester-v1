# used for myself and copilot to test code snippets from massive module
from massive_clients.massive_client import MassiveClient
from time_simulator import TimeSimulator
from premarket_data_service import PremarketDataService
from config import Config
import json
from dotenv import load_dotenv
import os
load_dotenv()

config = Config()
mc = MassiveClient(config)
tsimi = TimeSimulator(config, is_live=False)
pmds = PremarketDataService(mc, tsimi, config)

sd_result = pmds.collect_session_data(["ONDS"])

print(sd_result.session_time)