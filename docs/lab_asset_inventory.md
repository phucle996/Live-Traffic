# Lab Asset Inventory — Lab 5 Resource Index

This document summarizes the extracted Lab 5 historical raw datasets, reference processed files, and geographical coordinate files imported from `Data & process_data-20260709T105216Z-3-001.zip` and `Code & Model-20260709T105215Z-2-001.zip`.

---

## 1. Inventory Summary

- **Total Imported Files**: 76 files
- **Manifest Location**: `artifacts/manifests/lab_assets.json`

---

## 2. Directory Layout & Classification

### 2.1 Raw Historical Data (`data/lab_raw/*.csv`)
Contains raw historical traffic observations collected during Lab 5 setup. Used as the primary offline dataset when `DATA_SOURCE_MODE=offline`.

### 2.2 Target Coordinates List (`data/locations/data_converted.csv`)
Contains street names, district names, latitude, and longitude coordinates. Used for online TomTom API calls.

### 2.3 Reference Outputs (`data/lab_reference/process_data_spark.csv`)
Contains pre-processed reference Spark output provided in Lab 5. Used strictly for ETL result comparison and validation.
