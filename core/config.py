"""
Centralized configuration management for the Emotional Companion Bot.
Provides type-safe configuration with validation and environment variable support.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class BotConfig:
    """Main bot configuration."""
    telegram_token: str = ""
    groq_api_key: str = ""
    admin_ids: List[int] = field(default_factory=list)

    # Database
    db_path: str = "bot_data.sqlite"

    # Logging
    log_level: str = "INFO"
    log_file: str = "bot.log"
    max_log_size: int = 10 * 1024 * 1024  # 10MB
    log_backups: int = 5

    # Memory System
    memory_dir: str = "conversation_memory"
    max_conversations_per_user: int = 50
    memory_compression: bool = True

    # AI Parameters
    max_tokens: int = 450
    temperature: float = 0.8
    timeout: int = 15

    # Credits System
    image_credit_cost: int = 10
    error_refund_credits: bool = True

    # Limits
    max_message_length: int = 2000
    max_prompt_length: int = 1500
    rate_limit_per_minute: int = 30

    # External Services
    donation_url: str = ""
    support_email: str = ""

    # Advanced Features
    enable_memory_system: bool = True
    enable_self_awareness: bool = True
    enable_emotional_analysis: bool = True

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_required_fields()
        self._set_defaults_from_env()

    def _validate_required_fields(self):
        """Validate that required fields are present."""
        required = ['telegram_token', 'groq_api_key']
        missing = [field for field in required if not getattr(self, field)]

        if missing:
            raise ValueError(f"Missing required configuration fields: {', '.join(missing)}")

        if not self.admin_ids:
            logger.warning("No admin IDs configured. Some features may not work properly.")

    def _set_defaults_from_env(self):
        """Set default values from environment variables."""
        env_mappings = {
            'TELEGRAM_TOKEN': 'telegram_token',
            'GROQ_API_KEY': 'groq_api_key',
            'ADMIN_IDS': 'admin_ids',
            'DB_PATH': 'db_path',
            'LOG_LEVEL': 'log_level',
            'LOG_FILE': 'log_file',
            'MEMORY_DIR': 'memory_dir',
            'IMAGE_CREDIT_COST': 'image_credit_cost',
            'DONATION_URL': 'donation_url'
        }

        for env_var, config_attr in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                if config_attr == 'admin_ids':
                    # Parse comma-separated admin IDs
                    try:
                        self.admin_ids = [int(x.strip()) for x in env_value.split(',') if x.strip()]
                    except ValueError as e:
                        logger.error(f"Invalid admin IDs in environment: {e}")
                elif config_attr in ['image_credit_cost']:
                    try:
                        setattr(self, config_attr, int(env_value))
                    except ValueError:
                        logger.warning(f"Invalid {env_var} value, using default")
                else:
                    setattr(self, config_attr, env_value)

    @classmethod
    def from_env(cls) -> 'BotConfig':
        """Create configuration from environment variables."""
        return cls()

    def get_database_url(self) -> str:
        """Get database connection URL."""
        return f"sqlite:///{self.db_path}"

    def get_memory_path(self) -> Path:
        """Get memory directory path."""
        return Path(self.memory_dir)

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return user_id in self.admin_ids

    def should_enable_feature(self, feature: str) -> bool:
        """Check if a feature should be enabled."""
        return getattr(self, f"enable_{feature}", True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization."""
        return {
            'telegram_token': '***masked***',  # Don't expose sensitive data
            'groq_api_key': '***masked***',
            'admin_ids': self.admin_ids,
            'db_path': self.db_path,
            'log_level': self.log_level,
            'memory_dir': self.memory_dir,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'image_credit_cost': self.image_credit_cost,
            'enable_memory_system': self.enable_memory_system,
            'enable_self_awareness': self.enable_self_awareness
        }

# Global configuration instance
config = BotConfig.from_env()

# Export for easy importing
__all__ = ['BotConfig', 'config']
