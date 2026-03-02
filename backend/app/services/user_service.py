"""
User management service for PDP Automation v.3

Handles:
- User creation and retrieval
- Profile management
- Role management (admin only)
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import EmailAllowlist, User
from app.models.enums import UserRole

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    """Raised when user is not found."""
    pass


class UserService:
    """Service for user management operations."""

    async def get_or_create_user(
        self,
        db: AsyncSession,
        user_info: Dict[str, Any]
    ) -> User:
        """
        Get existing user or create new one from OAuth data.

        Args:
            db: Database session
            user_info: User information from Google OAuth

        Returns:
            User model instance
        """
        email = user_info["email"]
        google_id = user_info["google_id"]

        # --- Allowlist check ---
        allowlist_count = (await db.execute(
            select(func.count()).select_from(EmailAllowlist).where(
                EmailAllowlist.is_active == True
            )
        )).scalar() or 0

        allowlist_entry = None
        if allowlist_count > 0:
            result = await db.execute(
                select(EmailAllowlist).where(
                    EmailAllowlist.email == email,
                    EmailAllowlist.is_active == True,
                )
            )
            allowlist_entry = result.scalar_one_or_none()
            if not allowlist_entry:
                raise PermissionError(
                    f"Email {email} is not authorized -- contact admin"
                )

        # Try to find user by email
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            # Update user info
            user.name = user_info.get("name", user.name)
            user.picture_url = user_info.get("picture", user.picture_url)
            user.last_login_at = datetime.now(timezone.utc)

            # Update google_id if it changed (rare but possible)
            if user.google_id != google_id:
                user.google_id = google_id

            # Sync role from allowlist if entry exists
            if allowlist_entry and user.role != allowlist_entry.role:
                user.role = allowlist_entry.role

            logger.info(f"User logged in: {user.email}")
        else:
            # Determine role: from allowlist if available, else default USER
            role = allowlist_entry.role if allowlist_entry else UserRole.USER
            now = datetime.now(timezone.utc)
            user = User(
                email=email,
                name=user_info.get("name", email.split("@")[0]),
                picture_url=user_info.get("picture"),
                google_id=google_id,
                role=role,
                is_active=True,
                last_login_at=now,
                created_at=now,
                updated_at=now,
            )
            db.add(user)
            logger.info(f"New user created: {user.email} with role {role.value}")

        await db.commit()
        await db.refresh(user)

        return user

    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> Optional[User]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            User model instance or None
        """
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(
        self,
        db: AsyncSession,
        email: str
    ) -> Optional[User]:
        """
        Get user by email.

        Args:
            db: Database session
            email: User email

        Returns:
            User model instance or None
        """
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user_role(
        self,
        db: AsyncSession,
        user_id: UUID,
        new_role: UserRole,
        admin_user: User
    ) -> User:
        """
        Update user role (admin only).

        Args:
            db: Database session
            user_id: User UUID to update
            new_role: New role to assign
            admin_user: Admin user performing the action

        Returns:
            Updated user

        Raises:
            UserNotFoundError: If user not found
            PermissionError: If admin_user is not admin
        """
        if admin_user.role != UserRole.ADMIN:
            raise PermissionError("Only admins can change user roles")

        user = await self.get_user_by_id(db, user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")

        old_role = user.role
        user.role = new_role

        await db.commit()
        await db.refresh(user)

        logger.info(
            f"User role changed: {user.email} from {old_role} to {new_role} by {admin_user.email}"
        )

        return user

    async def deactivate_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        admin_user: User
    ) -> User:
        """
        Deactivate user account (admin only).

        Args:
            db: Database session
            user_id: User UUID to deactivate
            admin_user: Admin user performing the action

        Returns:
            Deactivated user

        Raises:
            UserNotFoundError: If user not found
            PermissionError: If admin_user is not admin
        """
        if admin_user.role != UserRole.ADMIN:
            raise PermissionError("Only admins can deactivate users")

        user = await self.get_user_by_id(db, user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")

        user.is_active = False

        await db.commit()
        await db.refresh(user)

        logger.warning(f"User deactivated: {user.email} by {admin_user.email}")

        return user

    async def reactivate_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        admin_user: User
    ) -> User:
        """
        Reactivate user account (admin only).

        Args:
            db: Database session
            user_id: User UUID to reactivate
            admin_user: Admin user performing the action

        Returns:
            Reactivated user

        Raises:
            UserNotFoundError: If user not found
            PermissionError: If admin_user is not admin
        """
        if admin_user.role != UserRole.ADMIN:
            raise PermissionError("Only admins can reactivate users")

        user = await self.get_user_by_id(db, user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")

        user.is_active = True

        await db.commit()
        await db.refresh(user)

        logger.info(f"User reactivated: {user.email} by {admin_user.email}")

        return user


# Singleton instance
user_service = UserService()
