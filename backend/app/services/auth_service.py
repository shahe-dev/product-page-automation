"""
Authentication service for PDP Automation v.3

Handles:
- Google OAuth token exchange with CSRF protection
- JWT generation and validation
- Refresh token management with database storage
- User session handling
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from urllib.parse import urlencode
from uuid import UUID
import logging

import httpx
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.config.settings import get_settings
from app.models.database import User, RefreshToken, OAuthState
from app.models.enums import UserRole

settings = get_settings()
logger = logging.getLogger(__name__)


def _mask_email(email: str) -> str:
    """Mask email address for logging (GDPR compliance)."""
    parts = email.split("@")
    if len(parts) == 2:
        local = parts[0]
        masked_local = local[:2] + "***" if len(local) > 2 else "***"
        return f"{masked_local}@{parts[1]}"
    return "***"


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthorizationError(Exception):
    """Raised when authorization fails."""
    pass


class AuthService:
    """Service for handling authentication and token management."""

    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.token_uri = settings.GOOGLE_TOKEN_URI
        self.auth_uri = settings.GOOGLE_AUTH_URI
        self.allowed_domain = settings.ALLOWED_EMAIL_DOMAIN
        self.jwt_secret = settings.JWT_SECRET
        self.jwt_algorithm = settings.JWT_ALGORITHM
        self.jwt_expiry_hours = settings.JWT_EXPIRY_HOURS
        self.refresh_expiry_days = settings.REFRESH_TOKEN_EXPIRY_DAYS

    # =========================================================================
    # OAuth State Management (CSRF Protection)
    # =========================================================================

    async def create_oauth_state(
        self,
        db: AsyncSession,
        redirect_uri: Optional[str] = None
    ) -> str:
        """
        Create OAuth state parameter for CSRF protection.

        Args:
            db: Database session
            redirect_uri: Optional redirect URI to store

        Returns:
            State parameter string
        """
        state = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        oauth_state = OAuthState(
            state=state,
            redirect_uri=redirect_uri,
            expires_at=expires_at
        )
        db.add(oauth_state)
        await db.commit()

        logger.debug(f"Created OAuth state, expires at {expires_at}")
        return state

    async def validate_oauth_state(
        self,
        db: AsyncSession,
        state: str
    ) -> Optional[str]:
        """
        Validate OAuth state parameter.

        Args:
            db: Database session
            state: State parameter to validate

        Returns:
            Redirect URI if state is valid, None otherwise

        Raises:
            AuthenticationError: If state is invalid or expired
        """
        result = await db.execute(
            select(OAuthState).where(
                OAuthState.state == state,
                OAuthState.used == False,
                OAuthState.expires_at > datetime.now(timezone.utc)
            )
        )
        oauth_state = result.scalar_one_or_none()

        if not oauth_state:
            logger.warning(f"Invalid or expired OAuth state: {state[:8]}...")
            raise AuthenticationError("Invalid or expired OAuth state")

        # Mark as used
        oauth_state.used = True
        await db.commit()

        return oauth_state.redirect_uri

    async def cleanup_expired_states(self, db: AsyncSession) -> int:
        """Clean up expired OAuth states."""
        result = await db.execute(
            delete(OAuthState).where(
                OAuthState.expires_at < datetime.now(timezone.utc)
            )
        )
        await db.commit()
        return result.rowcount

    def get_oauth_url(self, state: str, redirect_uri: str) -> str:
        """
        Build Google OAuth authorization URL.

        Args:
            state: OAuth state parameter
            redirect_uri: Redirect URI after auth

        Returns:
            Full OAuth URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{self.auth_uri}?{urlencode(params)}"

    # =========================================================================
    # Google OAuth Token Exchange
    # =========================================================================

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange OAuth authorization code for Google access token.

        Args:
            code: Authorization code from Google OAuth
            redirect_uri: Redirect URI used in OAuth flow

        Returns:
            Token response from Google

        Raises:
            AuthenticationError: If token exchange fails
        """
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.token_uri, data=data, timeout=30.0)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to exchange code for token: {e}")
            raise AuthenticationError("Failed to exchange authorization code for token")

    async def verify_google_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Google OAuth token and extract user info.

        Args:
            token: Google OAuth access token

        Returns:
            User info dictionary with email, name, picture, google_id

        Raises:
            AuthenticationError: If token is invalid or domain not allowed
        """
        try:
            async with httpx.AsyncClient() as client:
                # Get user info from Google
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )
                response.raise_for_status()
                user_info = response.json()

            email = user_info.get("email")
            email_verified = user_info.get("verified_email", False)

            if not email_verified:
                raise AuthenticationError("Email not verified")

            # Check domain restriction
            if not self._is_allowed_domain(email):
                logger.warning(f"Login attempt from unauthorized domain: {_mask_email(email)}")
                raise AuthenticationError(
                    f"Email domain not allowed. Must be @{self.allowed_domain}"
                )

            # Log successful verification (email masked for GDPR)
            logger.info(f"Successfully verified token for user: {_mask_email(email)}")

            return {
                "email": email,
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
                "google_id": user_info.get("id"),
            }

        except httpx.HTTPError as e:
            logger.error(f"Token verification failed: {e}")
            raise AuthenticationError("Invalid Google token")

    def _is_allowed_domain(self, email: str) -> bool:
        """Check if email domain is allowed."""
        return email.endswith(f"@{self.allowed_domain}")

    # =========================================================================
    # JWT Access Token Management
    # =========================================================================

    def create_access_token(self, user: User) -> str:
        """
        Create JWT access token.

        Args:
            user: User model instance

        Returns:
            JWT token string
        """
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "exp": now + timedelta(hours=self.jwt_expiry_hours),
            "iat": now,
            "jti": secrets.token_hex(16),
        }

        token = jwt.encode(
            payload,
            self.jwt_secret,
            algorithm=self.jwt_algorithm
        )

        logger.debug(f"Created access token for user {_mask_email(user.email)}, expires in {self.jwt_expiry_hours}h")
        return token

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token.

        Args:
            token: JWT token string

        Returns:
            Token payload

        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            return payload

        except ExpiredSignatureError:
            raise AuthenticationError("TOKEN_EXPIRED")
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise AuthenticationError("INVALID_TOKEN")

    # =========================================================================
    # Refresh Token Management (Database-backed)
    # =========================================================================

    async def create_refresh_token(
        self,
        db: AsyncSession,
        user: User,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """
        Create and store refresh token in database.

        Args:
            db: Database session
            user: User model instance
            user_agent: Client user agent for audit
            ip_address: Client IP for audit

        Returns:
            Refresh token string (unhashed)
        """
        # Generate token
        token = secrets.token_urlsafe(64)
        token_hash = self.hash_refresh_token(token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.refresh_expiry_days)

        # Store in database
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address
        )
        db.add(refresh_token)
        await db.commit()

        logger.debug(f"Created refresh token for user {_mask_email(user.email)}, expires at {expires_at}")
        return token

    async def validate_refresh_token(
        self,
        db: AsyncSession,
        token: str
    ) -> RefreshToken:
        """
        Validate refresh token against database.

        Args:
            db: Database session
            token: Refresh token string

        Returns:
            RefreshToken model instance

        Raises:
            AuthenticationError: If token is invalid, expired, or revoked
        """
        token_hash = self.hash_refresh_token(token)

        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc)
            )
        )
        refresh_token = result.scalar_one_or_none()

        if not refresh_token:
            logger.warning("Invalid, expired, or revoked refresh token")
            raise AuthenticationError("REFRESH_TOKEN_INVALID")

        return refresh_token

    async def rotate_refresh_token(
        self,
        db: AsyncSession,
        old_token: str,
        user: User,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """
        Rotate refresh token (revoke old, create new).

        Implements single-use refresh tokens for better security.

        Args:
            db: Database session
            old_token: Current refresh token to revoke
            user: User model instance
            user_agent: Client user agent
            ip_address: Client IP

        Returns:
            New refresh token string
        """
        # Revoke old token
        await self.revoke_refresh_token(db, old_token)

        # Create new token
        return await self.create_refresh_token(db, user, user_agent, ip_address)

    async def revoke_refresh_token(self, db: AsyncSession, token: str) -> bool:
        """
        Revoke a refresh token.

        Args:
            db: Database session
            token: Refresh token to revoke

        Returns:
            True if revoked, False if token not found
        """
        token_hash = self.hash_refresh_token(token)

        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        refresh_token = result.scalar_one_or_none()

        if refresh_token:
            refresh_token.is_revoked = True
            refresh_token.revoked_at = datetime.now(timezone.utc)
            await db.commit()
            logger.debug(f"Revoked refresh token for user {refresh_token.user_id}")
            return True

        return False

    async def revoke_all_user_tokens(self, db: AsyncSession, user_id: UUID) -> int:
        """
        Revoke all refresh tokens for a user (force logout everywhere).

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Number of tokens revoked
        """
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False
            )
        )
        tokens = result.scalars().all()

        now = datetime.now(timezone.utc)
        for token in tokens:
            token.is_revoked = True
            token.revoked_at = now

        await db.commit()
        logger.info(f"Revoked {len(tokens)} refresh tokens for user {user_id}")
        return len(tokens)

    async def cleanup_expired_tokens(self, db: AsyncSession) -> int:
        """
        Clean up expired refresh tokens.

        Args:
            db: Database session

        Returns:
            Number of tokens deleted
        """
        result = await db.execute(
            delete(RefreshToken).where(
                RefreshToken.expires_at < datetime.now(timezone.utc)
            )
        )
        await db.commit()
        return result.rowcount

    def hash_refresh_token(self, token: str) -> str:
        """
        Hash refresh token for storage.

        Uses SHA256 for one-way hashing to prevent token reuse if database is compromised.

        Args:
            token: Refresh token to hash

        Returns:
            Hashed token (64 char hex)
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def generate_token_jti(self) -> str:
        """
        Generate unique token identifier (JTI).

        Used for token tracking and revocation.

        Returns:
            Random hex string
        """
        return secrets.token_hex(16)


# Singleton instance
auth_service = AuthService()
