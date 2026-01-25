# used for myself and copilot to test code snippets from massive module
from massive import RESTClient
import json
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv('MASSIVE_API_KEY')
if not api_key:
    print("MASSIVE_API_KEY not found in environment variables")
client = RESTClient(api_key)


