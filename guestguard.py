import json
import os

# Load API keys from file
with open("config.json") as f:
    config = json.load(f)

SSC_API_KEY = config.get("security_scorecard_api_key")
GRAPH_API_TOKEN = config.get("graph_api_token")
