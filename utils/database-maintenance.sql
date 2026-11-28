\set ON_ERROR_STOP on
\timing on

-- Run with psql against the Buildbot database, outside a transaction block.
-- Run during a period of low database activity.

-- Previous values on buildbot.nyc1.psf.io, 2026-11-20:
-- These three tables had no per-table overrides and inherited:
-- autovacuum_vacuum_scale_factor = 0.2
-- autovacuum_analyze_scale_factor = 0.1
-- autovacuum_vacuum_insert_scale_factor = 0.2
-- Restore inheritance with the RESET commands below.

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

-- To restore the previous settings:
-- ALTER TABLE builds RESET (
--     autovacuum_vacuum_scale_factor,
--     autovacuum_analyze_scale_factor,
--     autovacuum_vacuum_insert_scale_factor
-- );
-- ALTER TABLE steps RESET (
--     autovacuum_vacuum_scale_factor, autovacuum_analyze_scale_factor
-- );
-- ALTER TABLE buildrequests RESET (
--     autovacuum_vacuum_scale_factor, autovacuum_analyze_scale_factor
-- );

-- Refresh statistics and the visibility maps without an exclusive table lock.
VACUUM (ANALYZE) builds;
VACUUM (ANALYZE) steps;
VACUUM (ANALYZE) buildrequests;
