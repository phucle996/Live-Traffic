-- ==============================================================================
-- Database Migration 001 (db/migrations/001_enable_postgis.sql)
-- Phase ROAD-1 — Bật tiện ích mở rộng PostGIS cho PostgreSQL
-- ==============================================================================

-- Bật PostGIS extension để hỗ trợ lưu trữ geometry và truy vấn không gian (Spatial Queries)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
