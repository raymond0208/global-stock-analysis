import os
from pathlib import Path
import yaml
import json
from typing import Optional

class ConfigManager:
    def __init__(self):
        self.config_dir = Path("config")
        self.yaml_path = self.config_dir / "config.yaml"
        self.json_path = self.config_dir / "config.json"
        self.load_config()

    def load_config(self):
        # Try loading from YAML first, then JSON as fallback
        if self.yaml_path.exists():
            with open(self.yaml_path, 'r') as f:
                self.config = yaml.safe_load(f)
        elif self.json_path.exists():
            with open(self.json_path, 'r') as f:
                self.config = json.load(f)
        else:
            # Create default config
            self.config = {
                'api_keys': {
                    'fred_api_key': '',
                    'alpha_vantage_key': ''
                },
                'features': {
                    'enable_macro_analysis': True,
                    'enable_technical_analysis': False
                }
            }
            self.save_config()

    def save_config(self):
        os.makedirs(self.config_dir, exist_ok=True)
        # Save in both formats for compatibility
        with open(self.yaml_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        with open(self.json_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get_api_key(self, api_name: str) -> str:
        # Try environment variables first
        env_var = f"STOCK_ANALYZER_{api_name.upper()}"
        if env_key := os.getenv(env_var):
            return env_key
        # Fall back to config file
        return self.config['api_keys'].get(api_name, '')

    def update_api_key(self, api_name, key):
        self.config['api_keys'][api_name] = key
        self.save_config()

    def get_feature_flag(self, feature_name):
        return self.config['features'].get(feature_name, False)

    def update_feature_flag(self, feature_name, enabled):
        self.config['features'][feature_name] = enabled
        self.save_config() 