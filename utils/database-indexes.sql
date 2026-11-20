\set ON_ERROR_STOP on
\timing on

-- Run with psql against the Buildbot database, outside a transaction block.
-- These indexes support active builds, builder history, and worker history.
CREATE INDEX CONCURRENTLY IF NOT EXISTS builds_incomplete_id
    ON builds (id) WHERE complete_at IS NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS builds_builderid_complete_at
    ON builds (builderid, complete_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS builds_workerid_started_at
    ON builds (workerid, started_at DESC);
