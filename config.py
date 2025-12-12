"""
Configuration management for the self-healing browser automation system.
Handles environment variables, API settings, and path management.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Helper function to get config from various sources
# Circuit breaker to prevent repeated "No secrets found" warnings locally
_secrets_disabled = False

def get_config_value(key: str, default: str = "") -> str:
    global _secrets_disabled
    
    # 1. Try environment variable
    value = os.getenv(key)
    if value:
        return value.strip()
        
    # 2. Try Streamlit secrets (if not disabled)
    if not _secrets_disabled:
        try:
            import streamlit as st
            # Check root level secrets
            if key in st.secrets:
                return st.secrets[key]
                
            # Check "env" section (common pattern)
            if "env" in st.secrets and key in st.secrets.env:
                return st.secrets.env[key]
                
        except (FileNotFoundError, ImportError):
            # Secrets file missing or not in streamlit, disable for future calls
            _secrets_disabled = True
        except Exception:
            # Other errors, just ignore
            pass
        
    return default

def is_cloud_environment() -> bool:
    """Detect if running in a cloud/containerized environment without display"""
    # Check for common cloud environment indicators
    # Streamlit Cloud sets specific env vars
    if os.getenv("STREAMLIT_SHARING_MODE"):
        return True
    # Check if DISPLAY is not set (Linux without X server)
    if os.name != 'nt' and not os.getenv("DISPLAY"):
        return True
    # Check for common container indicators
    if os.path.exists("/.dockerenv"):
        return True
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        return True
    # Check for Streamlit Cloud's home directory pattern
    if os.getenv("HOME", "").startswith("/home/appuser"):
        return True
    return False

# Cache the cloud detection result
IS_CLOUD = is_cloud_environment()

class Config:
    """Central configuration for the automation system"""
    
    # Environment Detection
    IS_CLOUD_ENVIRONMENT = IS_CLOUD
    
    # OpenRouter API Configuration
    OPENROUTER_API_KEY = get_config_value("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = get_config_value("DEFAULT_MODEL", "anthropic/claude-3.5-haiku")
    FALLBACK_MODEL = get_config_value("FALLBACK_MODEL", "openai/gpt-4o-mini")
    
    # Cost Controls
    MAX_COST_PER_RUN = float(get_config_value("MAX_COST_PER_RUN", "0.50"))
    DAILY_BUDGET = float(get_config_value("DAILY_BUDGET", "5.00"))
    
    # Playwright Configuration
    # In cloud environments, ALWAYS force headless mode (no display available)
    # Locally, default to headless=false so users can see the browser
    _headless_setting = get_config_value("HEADLESS", "false").lower() == "true"
    HEADLESS = True if IS_CLOUD else _headless_setting
    BROWSER_TYPE = get_config_value("BROWSER_TYPE", "chromium")
    DEFAULT_TIMEOUT = int(get_config_value("DEFAULT_TIMEOUT", "30000"))
    VIEWPORT_WIDTH = 1920
    VIEWPORT_HEIGHT = 1080
    
    # Storage Paths
    BASE_DIR = Path(__file__).parent
    ARTIFACTS_DIR = BASE_DIR / "artifacts"
    SCREENSHOTS_DIR = ARTIFACTS_DIR / "screenshots"
    VIDEOS_DIR = ARTIFACTS_DIR / "videos"
    LOGS_DIR = ARTIFACTS_DIR / "logs"
    SCRIPTS_DIR = ARTIFACTS_DIR / "scripts"
    
    # Retry & Healing Settings
    MAX_REPAIR_ATTEMPTS = int(get_config_value("MAX_REPAIR_ATTEMPTS", "3"))
    AUTO_HEAL = get_config_value("AUTO_HEAL", "true").lower() == "true"
    
    # Model Pricing (per 1M tokens)
    MODEL_PRICING = {
        "anthropic/claude-3.5-haiku": {"input": 0.25, "output": 1.25},
        "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "anthropic/claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
        "openai/gpt-4": {"input": 30.00, "output": 60.00},
    }
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        for dir_path in [cls.ARTIFACTS_DIR, cls.SCREENSHOTS_DIR, 
                        cls.VIDEOS_DIR, cls.LOGS_DIR, cls.SCRIPTS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls):
        """Validate configuration and check for required settings"""
        if not cls.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY not found in environment. "
                "Please copy .env.example to .env and set your API key."
            )
        
        cls.ensure_directories()
        return True

# Validate configuration on import
try:
    Config.validate()
    print("✓ Configuration loaded successfully")
except ValueError as e:
    print(f"⚠ Configuration warning: {e}")
