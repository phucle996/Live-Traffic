# Data Lineage Specification — End-to-End Data Origin Tracking

This document outlines the lineage graph tracing architecture mapping raw ingestion batches to training datasets and ML models.

---

## 1. Lineage Graph Model

```
 [Raw Batch ID: batch_<uuid>]
          │
          ▼ (Data Quality Gate: quality_runner.py)
 [HDFS Partition: /traffic_project/raw/source=.../event_date=.../]
          │
          ▼ (Spark Parquet ETL: process_spark.py)
 [Processed Feature Dataset: processed_data_spark.parquet]
          │
          ▼ (MLlib Training: train_gbt.py)
 [ML Model Artifact: models/gbt_traffic_model]
```

Lineage metadata is written to `artifacts/reports/data_lineage.json` after every batch execution by `LineageWriter` (`src/data_quality/lineage_writer.py`).
