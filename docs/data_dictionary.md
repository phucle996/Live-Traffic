# Data Dictionary — Traffic Flow Dataset Specification

This document details the data contract schema, field definitions, data types, valid physical ranges, nullability rules, and business logic for the urban traffic prediction system.

---

## 1. Raw Traffic Ingestion Schema (`RAW_TRAFFIC_SCHEMA`)

| Field Name | Physical Type | Mandatory | Valid Bounds / Domain | Example Value | Description |
|---|---|---|---|---|---|
| `Timestamp` | String | Yes | `YYYY-MM-DD HH:MM:SS` | `"2026-07-21 17:30:00"` | Timestamp of traffic observation |
| `Location/Street` | String | Yes | Non-empty string | `"Nguyen Hue Street"` | Location or street segment name |
| `District` | String | Yes | Non-empty string | `"District 1"` | Administrative district |
| `Latitude` | Double | Yes | $[-90.0, 90.0]$ | `10.7769` | Geographical latitude coordinate |
| `Longitude` | Double | Yes | $[-180.0, 180.0]$ | `106.7009` | Geographical longitude coordinate |
| `CurrentSpeed` | Double | Yes | $\ge 0.0$ (km/h) | `25.5` | Observed traffic speed |
| `FreeFlowSpeed` | Double | Yes | $> 0.0$ (km/h) | `45.0` | Ideal free-flow traffic speed |
| `Confidence` | Double | Yes | $[0.0, 1.0]$ | `0.95` | API sensor quality/confidence score |

---

## 2. Processed Feature Engineering Schema (`PROCESSED_TRAFFIC_SCHEMA`)

| Field Name | Physical Type | Mandatory | Valid Range / Domain | Business Logic & Derivation |
|---|---|---|---|---|
| `Timestamp` | Timestamp | Yes | Timestamp object | Parsed from raw `Timestamp` string |
| `Location/Street` | String | Yes | Non-empty string | Cleaned street name |
| `District` | String | Yes | Non-empty string | Cleaned district name |
| `Latitude` | Double | Yes | $[-90.0, 90.0]$ | Validated geographical latitude |
| `Longitude` | Double | Yes | $[-180.0, 180.0]$ | Validated geographical longitude |
| `CurrentSpeed` | Double | Yes | $\ge 0.0$ (km/h) | Validated current traffic speed |
| `FreeFlowSpeed` | Double | Yes | $> 0.0$ (km/h) | Validated free-flow traffic speed |
| `Confidence` | Double | Yes | $[0.9, 1.0]$ | Filtered high-confidence score |
| `Hour` | Integer | Yes | $[0, 23]$ | Hour extracted from Timestamp |
| `Minute` | Integer | Yes | $[0, 59]$ | Minute extracted from Timestamp |
| `TimeInMinutes` | Integer | Yes | $[0, 1439]$ | `Hour * 60 + Minute` |
| `DayOfWeek` | Integer | Yes | $[0, 6]$ | Python standard: $0=\text{Monday}, \dots, 6=\text{Sunday}$ |
| `Weekend` | Integer | Yes | $\{0, 1\}$ | $1$ if `DayOfWeek` $\in \{5, 6\}$ else $0$ |
| `CongestionRatio` | Double | Yes | $\ge 0.0$ | `CurrentSpeed / FreeFlowSpeed` |

---

## 3. Data Quality & Quarantine Rules

1. **Latitude/Longitude Out-of-Bounds**: Records with coordinates outside valid geographic ranges are redirected to the Quarantine table.
2. **Negative Speeds**: Records with `CurrentSpeed < 0` or `FreeFlowSpeed <= 0` are quarantined.
3. **Low Confidence Filter**: Ingestion records with `Confidence < 0.9` are excluded during ETL feature processing.
4. **DayOfWeek Conversion**: PySpark `dayofweek()` ($1=\text{Sunday} \dots 7=\text{Saturday}$) is strictly converted via `(spark_dayofweek + 5) % 7` to align with Python standard conventions across ETL, training, and Streamlit inference engines.
