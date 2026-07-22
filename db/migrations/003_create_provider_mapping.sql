-- ==============================================================================
-- Database Migration 003 (db/migrations/003_create_provider_mapping.sql)
-- Phase ROAD-1 / HERE-4 — Bảng provider_segment_mapping cache kết quả spatial matching
-- ==============================================================================

CREATE TABLE IF NOT EXISTS provider_segment_mapping (
    mapping_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider TEXT NOT NULL,                         -- "here" | "tomtom"
    provider_segment_id TEXT NOT NULL,             -- ID đoạn đường từ provider
    catalog_version TEXT NOT NULL,
    segment_id UUID NOT NULL REFERENCES road_segment(segment_id),
    match_score DOUBLE PRECISION NOT NULL,          -- Đánh giá khớp từ 0.0 đến 1.0
    matching_algorithm_version TEXT NOT NULL,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_provider_mapping UNIQUE (provider, provider_segment_id, catalog_version)
);

CREATE INDEX IF NOT EXISTS idx_provider_mapping_lookup ON provider_segment_mapping(provider, provider_segment_id);
CREATE INDEX IF NOT EXISTS idx_provider_mapping_segment ON provider_segment_mapping(segment_id);
