# API Ingestion Guide — TomTom Flow Segment API & Seed Mode

This document specifies the TomTom Traffic Flow Segment API integration, HTTP retry mechanics, rate limiting rules, secret key protection, and offline seed mode fallback.

---

## 1. TomTom Flow Segment API Specification

- **Endpoint URL**: `https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json`
- **HTTP Method**: `GET`
- **Query Parameters**:
  - `key` (string, mandatory): TomTom API Key.
  - `point` (string, mandatory): Latitude and Longitude (`"{lat},{lon}"`).
  - `unit` (string): `"KMPH"`

---

## 2. HTTP Resiliency & Fail-Fast Mechanics

1. **Timeout Enforcement**: Every request sets explicit timeout ($10$ seconds).
2. **Bounded Exponential Backoff**: Transient server errors (500, 502, 503, 504) trigger up to $5$ retries with exponential backoff delay ($2\text{s}, 4\text{s}, 8\text{s}\dots$).
3. **Fail-Fast Authentication**: HTTP 401 (Unauthorized) or 403 (Forbidden) abort immediately without retrying to prevent wasting API quotas.

---

## 3. Dual Ingestion Mode Operation

Set mode via `.env` or environment variable:

```bash
# Option A: Seed Mode (Offline - No API key or internet required)
export INGESTION_MODE=seed

# Option B: Live API Crawl Mode
export INGESTION_MODE=api
export TOMTOM_API_KEY="your_api_key_here"
```

To run ingestion pipeline:
```bash
bash scripts/run_ingestion.sh
```
