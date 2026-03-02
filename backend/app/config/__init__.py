"""
Configuration package for PDP Automation v.3

Exports settings, database, secrets, and logging utilities for easy import.
"""

from app.config.settings import Settings, get_settings
from app.config.database import (
    engine,
    async_session_factory,
    get_db_session,
    get_db_context,
    check_database_connection,
    initialize_database,
    close_database,
    get_connection_pool_status,
)
# Base is in app.models.database, not app.config.database
from app.models.database import Base
from app.config.secrets import (
    SecretManager,
    get_secret_manager,
    load_secrets_to_env,
)
from app.config.logging import (
    setup_logging,
    get_logger,
    JsonFormatter,
    ColoredFormatter,
)

__all__ = [
    # Settings
    "Settings",
    "get_settings",
    # Database
    "Base",
    "engine",
    "async_session_factory",
    "get_db_session",
    "get_db_context",
    "check_database_connection",
    "initialize_database",
    "close_database",
    "get_connection_pool_status",
    # Secrets
    "SecretManager",
    "get_secret_manager",
    "load_secrets_to_env",
    # Logging
    "setup_logging",
    "get_logger",
    "JsonFormatter",
    "ColoredFormatter",
]
