"""
Unit tests for authentication service

Run with: pytest tests/test_auth_service.py -v
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.auth_service import auth_service, AuthenticationError
from app.models.database import User
from app.models.enums import UserRole


class TestAuthService:
    """Test suite for AuthService."""

    def test_is_allowed_domain_valid(self):
        """Test domain validation with valid domain."""
        assert auth_service._is_allowed_domain("user@your-domain.com") is True

    def test_is_allowed_domain_invalid(self):
        """Test domain validation with invalid domain."""
        assert auth_service._is_allowed_domain("user@gmail.com") is False
        assert auth_service._is_allowed_domain("user@example.com") is False

    def test_create_access_token(self):
        """Test JWT access token creation."""
        user = User(
            id=uuid4(),
            email="test@your-domain.com",
            name="Test User",
            google_id="12345",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        token = auth_service.create_access_token(user)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are long

    def test_create_refresh_token(self):
        """Test JWT refresh token creation."""
        user = User(
            id=uuid4(),
            email="test@your-domain.com",
            name="Test User",
            google_id="12345",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        token = auth_service.create_refresh_token(user)
        assert token is not None
        assert isinstance(token, str)

    def test_verify_valid_token(self):
        """Test JWT token verification with valid token."""
        user = User(
            id=uuid4(),
            email="test@your-domain.com",
            name="Test User",
            google_id="12345",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        token = auth_service.create_access_token(user)
        payload = auth_service.verify_token(token)

        assert payload["sub"] == str(user.id)
        assert payload["email"] == user.email
        assert payload["role"] == user.role.value

    def test_verify_invalid_token(self):
        """Test JWT token verification with invalid token."""
        with pytest.raises(AuthenticationError) as exc_info:
            auth_service.verify_token("invalid.token.here")

        assert "INVALID_TOKEN" in str(exc_info.value)

    def test_hash_refresh_token(self):
        """Test refresh token hashing."""
        token = "sample_refresh_token_12345"
        hashed = auth_service.hash_refresh_token(token)

        assert hashed is not None
        assert hashed != token
        assert len(hashed) == 64  # SHA256 hex = 64 chars

        # Same token should produce same hash
        hashed2 = auth_service.hash_refresh_token(token)
        assert hashed == hashed2

    def test_generate_token_jti(self):
        """Test JTI generation."""
        jti1 = auth_service.generate_token_jti()
        jti2 = auth_service.generate_token_jti()

        assert jti1 != jti2
        assert len(jti1) == 32  # 16 bytes hex = 32 chars
        assert len(jti2) == 32


class TestTokenExpiry:
    """Test suite for token expiry handling."""

    def test_access_token_has_expiry(self):
        """Test that access token has expiry claim."""
        user = User(
            id=uuid4(),
            email="test@your-domain.com",
            name="Test User",
            google_id="12345",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        token = auth_service.create_access_token(user)
        payload = auth_service.verify_token(token)

        assert "exp" in payload
        assert "iat" in payload

        # Check expiry is in the future
        exp = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()
        assert exp > now

    def test_refresh_token_has_type(self):
        """Test that refresh token has type claim."""
        user = User(
            id=uuid4(),
            email="test@your-domain.com",
            name="Test User",
            google_id="12345",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        token = auth_service.create_refresh_token(user)
        payload = auth_service.verify_token(token)

        assert payload.get("type") == "refresh"
