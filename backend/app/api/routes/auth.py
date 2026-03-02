"""
Authentication API routes for PDP Automation v.3

Endpoints:
- GET /auth/login - Get Google OAuth URL with state parameter
- POST /auth/google - Authenticate with Google OAuth (with state validation)
- POST /auth/refresh - Refresh access token (with token rotation)
- GET /auth/me - Get current user profile
- POST /auth/logout - Logout and invalidate session
- POST /auth/logout/all - Logout from all devices
"""

from datetime import datetime, timezone
from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Cookie
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session as get_db
from app.config.settings import get_settings
from app.services.auth_service import auth_service, AuthenticationError
from app.services.user_service import user_service
from app.middleware.auth import get_current_user
from app.models.database import User

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================================
# Request/Response Models
# ============================================================================


class OAuthLoginResponse(BaseModel):
    """Response with OAuth URL and state."""
    oauth_url: str
    state: str


class GoogleAuthRequest(BaseModel):
    """Request body for Google OAuth authentication."""
    code: str = Field(..., description="Google OAuth authorization code")
    state: str = Field(..., description="OAuth state parameter for CSRF protection (required)")


class RefreshTokenRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str = Field(..., description="Refresh token")


class UserResponse(BaseModel):
    """User profile response."""
    id: str
    email: str
    name: str
    picture_url: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Authentication response with tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshResponse(BaseModel):
    """Token refresh response."""
    access_token: str
    refresh_token: str  # New rotated token
    token_type: str = "bearer"
    expires_in: int


class LogoutResponse(BaseModel):
    """Logout response."""
    success: bool
    message: str
    tokens_revoked: Optional[int] = None


# ============================================================================
# Helper Functions
# ============================================================================


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP from request.

    Only trusts X-Forwarded-For when the direct client is a known proxy.
    """
    client_ip = request.client.host if request.client else None
    forwarded = request.headers.get("X-Forwarded-For")
    # TODO: Replace with centralized TRUSTED_PROXY_IPS from settings
    trusted_proxies = {"127.0.0.1", "::1"}
    if forwarded and client_ip in trusted_proxies:
        return forwarded.split(",")[0].strip()
    return client_ip


def get_user_agent(request: Request) -> Optional[str]:
    """Extract user agent from request."""
    return request.headers.get("User-Agent")


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/login", response_model=OAuthLoginResponse, status_code=status.HTTP_200_OK)
async def get_oauth_login_url(
    redirect_uri: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get Google OAuth login URL with CSRF state parameter.

    Args:
        redirect_uri: Optional custom redirect URI
        db: Database session

    Returns:
        OAuthLoginResponse with OAuth URL and state
    """
    # Validate redirect_uri against whitelist to prevent open redirect
    allowed_redirect_uris = {settings.GOOGLE_REDIRECT_URI}
    if redirect_uri and redirect_uri not in allowed_redirect_uris:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect URI"
        )
    final_redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI

    # Create state parameter (stored in database)
    state = await auth_service.create_oauth_state(db, final_redirect_uri)

    # Build OAuth URL
    oauth_url = auth_service.get_oauth_url(state, final_redirect_uri)

    return OAuthLoginResponse(
        oauth_url=oauth_url,
        state=state
    )


@router.post("/google", response_model=AuthResponse, status_code=status.HTTP_200_OK)
async def google_auth(
    request_body: GoogleAuthRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user with Google OAuth token.

    Verifies the Google OAuth token, validates state parameter (if provided),
    creates or retrieves user account, and returns JWT access and refresh tokens.

    Args:
        request_body: Google OAuth token and optional state
        request: FastAPI request for client info
        response: FastAPI response for setting cookies
        db: Database session

    Returns:
        AuthResponse with access token, refresh token, and user profile

    Raises:
        HTTPException: 401 if authentication fails, 403 if domain not allowed
    """
    try:
        # Validate state parameter (CSRF protection -- always required)
        await auth_service.validate_oauth_state(db, request_body.state)

        # Exchange authorization code for access token
        token_response = await auth_service.exchange_code_for_token(
            request_body.code,
            settings.GOOGLE_REDIRECT_URI
        )

        # Verify Google token and get user info
        user_info = await auth_service.verify_google_token(token_response["access_token"])

        # Get or create user
        user = await user_service.get_or_create_user(db, user_info)

        # Get client info for audit
        client_ip = get_client_ip(request)
        user_agent = get_user_agent(request)

        # Create tokens (refresh token stored in database)
        access_token = auth_service.create_access_token(user)
        refresh_token = await auth_service.create_refresh_token(
            db, user, user_agent, client_ip
        )

        # Set refresh token in HTTP-only cookie with path restriction
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            path="/api/v1/auth",
            max_age=settings.REFRESH_TOKEN_EXPIRY_DAYS * 24 * 60 * 60,
        )

        logger.info(f"User authenticated successfully: {user.email} from {client_ip}")

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_EXPIRY_HOURS * 3600,
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                name=user.name,
                picture_url=user.picture_url,
                role=user.role.value,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login_at=user.last_login_at
            )
        )

    except AuthenticationError as e:
        error_msg = str(e)
        if "domain not allowed" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="DOMAIN_NOT_ALLOWED"
            )
        elif "state" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="INVALID_OAUTH_STATE"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="INVALID_GOOGLE_TOKEN"
            )
    except Exception as e:
        logger.exception(f"Unexpected error during authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
async def refresh_access_token(
    request_body: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    refresh_token_cookie: Optional[str] = Cookie(None, alias="refresh_token")
):
    """
    Refresh access token using refresh token.

    Validates the refresh token against database, rotates it (single-use),
    and returns new access and refresh tokens.

    Args:
        request_body: Refresh token (can also use cookie)
        request: FastAPI request for client info
        db: Database session
        refresh_token_cookie: Refresh token from cookie

    Returns:
        RefreshResponse with new access and refresh tokens

    Raises:
        HTTPException: 401 if refresh token is invalid or expired
    """
    # Use token from body or cookie
    token = request_body.refresh_token or refresh_token_cookie

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="REFRESH_TOKEN_REQUIRED"
        )

    try:
        # Validate refresh token against database
        refresh_token_record = await auth_service.validate_refresh_token(db, token)

        # Get user
        user = await user_service.get_user_by_id(db, refresh_token_record.user_id)

        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        # Get client info
        client_ip = get_client_ip(request)
        user_agent = get_user_agent(request)

        # Rotate refresh token (revoke old, create new)
        new_refresh_token = await auth_service.rotate_refresh_token(
            db, token, user, user_agent, client_ip
        )

        # Create new access token
        access_token = auth_service.create_access_token(user)

        logger.debug(f"Tokens rotated for user: {user.email}")

        return RefreshResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.JWT_EXPIRY_HOURS * 3600
        )

    except AuthenticationError as e:
        logger.warning(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="REFRESH_TOKEN_INVALID"
        )
    except Exception as e:
        logger.exception(f"Unexpected error during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user profile.

    Args:
        current_user: Current user from JWT token

    Returns:
        UserResponse with user profile
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        picture_url=current_user.picture_url,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at
    )


@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    refresh_token_cookie: Optional[str] = Cookie(None, alias="refresh_token")
):
    """
    Logout user by revoking refresh token and clearing cookie.

    Args:
        response: FastAPI response for clearing cookies
        db: Database session
        current_user: Current user from JWT token
        refresh_token_cookie: Refresh token from cookie

    Returns:
        LogoutResponse with success message
    """
    tokens_revoked = 0

    # Revoke refresh token if present
    if refresh_token_cookie:
        revoked = await auth_service.revoke_refresh_token(db, refresh_token_cookie)
        if revoked:
            tokens_revoked = 1

    # Clear refresh token cookie
    response.delete_cookie(key="refresh_token", path="/api/v1/auth")

    logger.info(f"User logged out: {current_user.email}")

    return LogoutResponse(
        success=True,
        message="Logged out successfully",
        tokens_revoked=tokens_revoked
    )


@router.post("/logout/all", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
async def logout_all_devices(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Logout user from all devices by revoking all refresh tokens.

    Args:
        response: FastAPI response for clearing cookies
        db: Database session
        current_user: Current user from JWT token

    Returns:
        LogoutResponse with number of tokens revoked
    """
    # Revoke all refresh tokens for user
    tokens_revoked = await auth_service.revoke_all_user_tokens(db, current_user.id)

    # Clear refresh token cookie
    response.delete_cookie(key="refresh_token", path="/api/v1/auth")

    logger.info(f"User logged out from all devices: {current_user.email}, {tokens_revoked} tokens revoked")

    return LogoutResponse(
        success=True,
        message=f"Logged out from all devices",
        tokens_revoked=tokens_revoked
    )


# Auth health check removed (P3-8): redundant with global /health endpoint.
# If auth-specific checks are needed in the future, add them to the global
# health check or create a /health/detailed endpoint that verifies all subsystems.
