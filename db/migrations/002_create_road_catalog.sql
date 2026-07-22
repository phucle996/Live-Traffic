-- ==============================================================================
-- Database Migration 002 (db/migrations/002_create_road_catalog.sql)
-- Phase ROAD-1 — Bảng road_segment lưu trữ danh mục đoạn đường TP.HCM
-- ==============================================================================

CREATE TABLE IF NOT EXISTS road_segment (
    segment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    catalog_version TEXT NOT NULL,
    osm_way_id BIGINT,
    road_name TEXT,
    road_class TEXT NOT NULL,
    direction TEXT NOT NULL,
    length_m DOUBLE PRECISION NOT NULL,
    bearing DOUBLE PRECISION,
    lanes INTEGER DEFAULT 2,
    speed_limit_kph DOUBLE PRECISION DEFAULT 50.0,
    district TEXT,
    geometry geometry(LineString, 4326) NOT NULL,
    centroid geometry(Point, 4326) NOT NULL,
    geometry_hash TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tạo Spatial Index GIST cho geometry để tối ưu hóa truy vấn viewport BBOX và KNN search
CREATE INDEX IF NOT EXISTS idx_road_segment_geometry ON road_segment USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_road_segment_centroid ON road_segment USING GIST (centroid);
CREATE INDEX IF NOT EXISTS idx_road_segment_class ON road_segment(road_class);
CREATE INDEX IF NOT EXISTS idx_road_segment_district ON road_segment(district);
