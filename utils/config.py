import json
import os

def load_config() -> dict:
    env = os.getenv("ENV", "prod")
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", f"{env}.json")
    with open(config_path) as f:
        return json.load(f)

config = load_config()
