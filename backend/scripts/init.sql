-- PDP Automation v.3 - Database Initialization Script
-- This script runs automatically when the PostgreSQL container starts for the first time.
-- It sets up extensions and initial configuration to match Neon PostgreSQL.

-- ===========================================
-- Required Extensions
-- ===========================================
-- These extensions are available in both local PostgreSQL and Neon

-- UUID generation (for primary keys)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Trigram support (for fuzzy text search on project names, developers)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ===========================================
-- Configuration Notes
-- ===========================================
-- The following settings are handled by Neon automatically in production:
-- - Connection pooling (PgBouncer) - use -pooler endpoint
-- - SSL/TLS encryption - sslmode=require in connection string
-- - Password encryption - scram-sha-256 (default in PostgreSQL 16)
--
-- Local development does not require these configurations.

-- ===========================================
-- Development Seed Data (Optional)
-- ===========================================
-- Uncomment to create a test admin user after running Alembic migrations
-- This requires the users table to exist first (run: alembic upgrade head)
--
-- INSERT INTO users (id, email, name, role, is_active, created_at, updated_at)
-- VALUES (
--     gen_random_uuid(),
--     'admin@your-domain.com',
--     'Dev Admin',
--     'admin',
--     true,
--     NOW(),
--     NOW()
-- ) ON CONFLICT (email) DO NOTHING;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'PDP Automation database initialized successfully';
    RAISE NOTICE 'PostgreSQL version: %', version();
END $$;
