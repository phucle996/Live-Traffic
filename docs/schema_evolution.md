# Data Contract & Schema Evolution Policy — Production Governance

This document describes versioning rules and backward-compatibility guidelines for schema updates.

---

## 1. Schema Versioning Rules

- **Major Version (`v1.0` -> `v2.0`)**: Triggered when breaking column removals, type modifications, or major restructuring occurs. Requires updating all Spark ETL jobs.
- **Minor Version (`v1.0` -> `v1.1`)**: Triggered when new optional columns are added. Backward compatibility MUST be preserved.

---

## 2. Backward Compatibility Enforcement

All schema updates are registered in `src/data_quality/schema_registry.py`. New optional fields MUST allow `null` values to maintain compatibility with historical CSV data.
