"""
Configuration management for the self-healing browser automation system.
Handles environment variables, API settings, and path management.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Central configuration for the automation system"""
    
    # OpenRouter API Configuration
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "anthropic/claude-3.5-haiku")
    FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "openai/gpt-4o-mini")
    
    # Cost Controls
    MAX_COST_PER_RUN = float(os.getenv("MAX_COST_PER_RUN", "0.50"))
    DAILY_BUDGET = float(os.getenv("DAILY_BUDGET", "5.00"))
    
    # Playwright Configuration
    HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
    BROWSER_TYPE = os.getenv("BROWSER_TYPE", "chromium")
    DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "30000"))
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
    MAX_REPAIR_ATTEMPTS = int(os.getenv("MAX_REPAIR_ATTEMPTS", "3"))
    AUTO_HEAL = os.getenv("AUTO_HEAL", "true").lower() == "true"
    
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
