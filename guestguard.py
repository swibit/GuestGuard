import json
import os

# Function to load required config via 'config.json' file
def load_config(config_path='config.json'):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    with open(config_path, 'r') as file:
        try:
            config = json.load(file)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in config.json")

    # Optional: set defaults
    return {
        "ssc_api_key": config.get("security_scorecard_api_key", ""),
        "graph_token": config.get("graph_api_token", "")
    }

