# config.py
import os
import yaml
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def load_yaml_config(yaml_path: str = "app_config.yaml") -> dict:
    """
    Load the unified YAML configuration from the specified path.
    """
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Config file not found at {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
    return config_data