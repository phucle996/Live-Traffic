# Data Retention & Deletion Policy — Production Governance

This document defines retention windows and automated deletion/archival policies for raw ingestion files, processed Parquet partitions, and quarantined data.

---

## 1. Retention Matrix

| Dataset Category | HDFS Storage Path | Retention Window | Action After Expiry |
|---|---|---|---|
| Raw CSV/JSON Ingestion | `/traffic_project/raw/` | 30 Days | Archived to cold storage / compressed |
| Processed Parquet Data | `/traffic_project/processed/` | 365 Days | Retained for model re-training |
| Quarantined Error Data | `/traffic_project/quarantine/` | 90 Days | Permanently deleted after inspection |
| Data Lineage Reports | `artifacts/reports/data_lineage.json` | Permanent | Retained for auditability |
