"""
Secret management for production environments.

Loads secrets from GCP Secret Manager when ENVIRONMENT=production,
falls back to environment variables for development.
"""

import logging
import os
from typing import Any, Dict
from functools import lru_cache

logger = logging.getLogger(__name__)


class SecretManager:
    """
    Secret manager that loads from GCP Secret Manager or environment variables.
    """

    def __init__(self, project_id: str, environment: str):
        self.project_id = project_id
        self.environment = environment
        self._client = None

    @property
    def client(self):
        """Lazy-load GCP Secret Manager client."""
        if self._client is None and self.environment == "production":
            try:
                from google.cloud import secretmanager
                self._client = secretmanager.SecretManagerServiceClient()
                logger.info("GCP Secret Manager client initialized")
            except ImportError:
                logger.error(
                    "google-cloud-secret-manager not installed. "
                    "Install with: pip install google-cloud-secret-manager"
                )
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Secret Manager client: {e}")
                raise

        return self._client

    def get_secret(self, secret_name: str, version: str = "latest") -> str | None:
        """
        Get secret value from GCP Secret Manager or environment variables.

        Args:
            secret_name: Name of the secret
            version: Version of the secret (default: "latest")

        Returns:
            Secret value or None if not found
        """
        # Always check environment variables first
        env_value = os.getenv(secret_name)
        if env_value:
            logger.debug(f"Secret '{secret_name}' loaded from environment variable")
            return env_value

        # In production, try to load from Secret Manager
        if self.environment == "production":
            try:
                secret_path = (
                    f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"
                )
                response = self.client.access_secret_version(name=secret_path)
                secret_value = response.payload.data.decode("UTF-8")
                logger.info(f"Secret '{secret_name}' loaded from GCP Secret Manager")
                return secret_value
            except Exception as e:
                logger.warning(
                    f"Failed to load secret '{secret_name}' from Secret Manager: {e}"
                )
                return None

        # Not in production and not in environment variables
        logger.warning(f"Secret '{secret_name}' not found")
        return None

    def get_secret_required(self, secret_name: str, version: str = "latest") -> str:
        """
        Get required secret value, raise error if not found.

        Args:
            secret_name: Name of the secret
            version: Version of the secret (default: "latest")

        Returns:
            Secret value

        Raises:
            ValueError: If secret is not found
        """
        value = self.get_secret(secret_name, version)
        if value is None:
            raise ValueError(
                f"Required secret '{secret_name}' not found in environment "
                f"variables or Secret Manager"
            )
        return value

    def list_secrets(self) -> list[str]:
        """
        List all secrets in GCP Secret Manager.

        Returns:
            List of secret names

        Raises:
            RuntimeError: If not in production environment
        """
        if self.environment != "production":
            raise RuntimeError("list_secrets only available in production environment")

        try:
            parent = f"projects/{self.project_id}"
            secrets = self.client.list_secrets(request={"parent": parent})
            secret_names = [secret.name.split("/")[-1] for secret in secrets]
            logger.info(f"Found {len(secret_names)} secrets in Secret Manager")
            return secret_names
        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
            raise

    def create_secret(self, secret_name: str, secret_value: str) -> None:
        """
        Create a new secret in GCP Secret Manager.

        Args:
            secret_name: Name of the secret
            secret_value: Secret value

        Raises:
            RuntimeError: If not in production environment
        """
        if self.environment != "production":
            raise RuntimeError("create_secret only available in production environment")

        try:
            parent = f"projects/{self.project_id}"

            # Create secret
            secret = self.client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_name,
                    "secret": {"replication": {"automatic": {}}},
                }
            )

            # Add secret version
            self.client.add_secret_version(
                request={
                    "parent": secret.name,
                    "payload": {"data": secret_value.encode("UTF-8")},
                }
            )

            logger.info(f"Secret '{secret_name}' created in Secret Manager")
        except Exception as e:
            logger.error(f"Failed to create secret '{secret_name}': {e}")
            raise

    def update_secret(self, secret_name: str, secret_value: str) -> None:
        """
        Update existing secret in GCP Secret Manager by adding new version.

        Args:
            secret_name: Name of the secret
            secret_value: New secret value

        Raises:
            RuntimeError: If not in production environment
        """
        if self.environment != "production":
            raise RuntimeError("update_secret only available in production environment")

        try:
            parent = f"projects/{self.project_id}/secrets/{secret_name}"

            # Add new secret version
            self.client.add_secret_version(
                request={
                    "parent": parent,
                    "payload": {"data": secret_value.encode("UTF-8")},
                }
            )

            logger.info(f"Secret '{secret_name}' updated in Secret Manager")
        except Exception as e:
            logger.error(f"Failed to update secret '{secret_name}': {e}")
            raise


@lru_cache
def get_secret_manager(
    project_id: str | None = None,
    environment: str | None = None
) -> SecretManager:
    """
    Get cached SecretManager instance.

    Args:
        project_id: GCP project ID (defaults to env var GCP_PROJECT_ID)
        environment: Environment name (defaults to env var ENVIRONMENT)

    Returns:
        SecretManager instance
    """
    project_id = project_id or os.getenv("GCP_PROJECT_ID")
    if not project_id:
        raise ValueError("GCP_PROJECT_ID environment variable must be set")
    environment = environment or os.getenv("ENVIRONMENT", "development")

    return SecretManager(project_id=project_id, environment=environment)


def load_secrets_to_env(secret_names: list[str]) -> None:
    """
    Load secrets from Secret Manager and set as environment variables.

    Useful for loading secrets at application startup before settings are loaded.

    Args:
        secret_names: List of secret names to load
    """
    secret_manager = get_secret_manager()

    for secret_name in secret_names:
        try:
            value = secret_manager.get_secret(secret_name)
            if value:
                os.environ[secret_name] = value
                logger.info(f"Loaded secret '{secret_name}' to environment")
        except Exception as e:
            logger.error(f"Failed to load secret '{secret_name}': {e}")
