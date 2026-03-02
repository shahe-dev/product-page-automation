"""
Authentication middleware for PDP Automation v.3

Handles:
- JWT validation
- Current user extraction
- Token refresh handling
"""

from typing import Optional
from uuid import UUID
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session as get_db
from app.services.auth_service import auth_service, AuthenticationError
from app.services.user_service import user_service
from app.models.database import User

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP authorization credentials
        db: Database session

    Returns:
        User model instance

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    try:
        # Verify token
        payload = auth_service.verify_token(token)

        # Extract user ID
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="INVALID_TOKEN: Missing user ID"
            )

        # Parse UUID
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="INVALID_TOKEN: Invalid user ID format"
            )

        # Get user from database
        user = await user_service.get_user_by_id(db, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="USER_NOT_FOUND"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ACCOUNT_INACTIVE"
            )

        return user

    except AuthenticationError as e:
        error_code = str(e)
        if error_code == "TOKEN_EXPIRED":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="TOKEN_EXPIRED",
                headers={"WWW-Authenticate": "Bearer"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="INVALID_TOKEN",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current authenticated user if token is provided, otherwise None.

    Useful for endpoints that have optional authentication.

    Args:
        credentials: HTTP authorization credentials (optional)
        db: Database session

    Returns:
        User model instance or None
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (verified active status).

    Args:
        current_user: Current user from get_current_user

    Returns:
        User model instance

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ACCOUNT_INACTIVE"
        )
    return current_user
