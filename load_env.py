"""
Simple .env file loader for agent configuration
Reads agent.env if it exists, otherwise uses system environment variables
"""

import os
from pathlib import Path


def load_env():
    """Load configuration from agent.env file if it exists"""
    env_file = Path(__file__).parent / "agent.env"
    
    if env_file.exists():
        print(f"[config] Loading configuration from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value
                        print(f"[config] Set {key}={value}")
    else:
        print(f"[config] No agent.env found, using system environment variables")


# Load on import
load_env()
