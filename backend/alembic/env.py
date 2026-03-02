"""Alembic environment configuration for sync SQLAlchemy migrations."""

from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import pool, create_engine

from alembic import context

# Add the backend directory to the path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file manually to avoid importing app.config which creates async engines
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models Base for metadata (models don't import database config)
from app.models.database import Base

# Import all models to ensure they are registered with Base.metadata
from app.models.database import (
    User, Project, ProjectImage, ProjectFloorPlan, ProjectApproval,
    ProjectRevision, Job, JobStep, Prompt, PromptVersion, Template,
    QAComparison, Notification, WorkflowItem, PublicationChecklist,
    ExecutionHistory, QACheckpoint, QAIssue, QAOverride, ExtractedData,
    GeneratedContent, ContentQAResult
)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Get database URL from environment
# Convert asyncpg URL to psycopg2 URL for migrations
database_url = os.getenv("DATABASE_URL", "")
sync_database_url = database_url.replace("+asyncpg", "")
config.set_main_option('sqlalchemy.url', sync_database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(
        sync_database_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
