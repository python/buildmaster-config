\set ON_ERROR_STOP on
\timing on

-- Run with psql against the Buildbot database, outside a transaction block.
-- Run during a period of low database activity.

-- The default scale factors delay maintenance on these large tables.
ALTER TABLE builds SET (
    autovacuum_vacuum_scale_factor = 0.01,
    autovacuum_analyze_scale_factor = 0.01,
    autovacuum_vacuum_insert_scale_factor = 0.01
);
ALTER TABLE steps SET (
    autovacuum_vacuum_scale_factor = 0.01,
    autovacuum_analyze_scale_factor = 0.01
);
ALTER TABLE buildrequests SET (
    autovacuum_vacuum_scale_factor = 0.01,
    autovacuum_analyze_scale_factor = 0.01
);

-- Refresh statistics and the visibility maps without an exclusive table lock.
VACUUM (ANALYZE) builds;
VACUUM (ANALYZE) steps;
VACUUM (ANALYZE) buildrequests;
