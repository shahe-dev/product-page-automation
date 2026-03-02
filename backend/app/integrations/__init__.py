"""
Integration layer for external services.

Provides centralized clients for:
- Anthropic API (Claude)
- Google Drive
"""

from app.integrations.anthropic_client import anthropic_service
from app.integrations.drive_client import DriveClient, drive_client

__all__ = ["anthropic_service", "DriveClient", "drive_client"]
