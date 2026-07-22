# Restore Runbook

> [!IMPORTANT]
> Always run `verify_backup.sh` on the target backup file BEFORE proceeding with any restore.
> Never restore without confirming the backup decrypts and contains valid content.

---

## Pre-Restore Checklist

- [ ] Identify the correct backup file (timestamp, component type).
- [ ] Confirm `BACKUP_ENCRYPTION_KEY` is available in environment.
- [ ] Run verify: `bash scripts/backup/verify_backup.sh <backup_file>`
- [ ] Notify team that restore is in progress (Slack #incidents).
- [ ] Document start time and restore reason.

---

## Component 1: HDFS Metadata Restore

**Script**: [restore_hdfs.sh](file:///home/phucle/Desktop/lab5/scripts/restore/restore_hdfs.sh)

```bash
export BACKUP_ENCRYPTION_KEY="$(cat /run/secrets/backup_key)"
bash scripts/restore/restore_hdfs.sh /mnt/backups/hdfs_metadata/hdfs_metadata_20240101_020000Z.tar.gz.enc
```

**Steps performed by script**:
1. Prompts operator for explicit `YES` confirmation.
2. Stops HDFS services.
3. Decrypts backup archive.
4. Saves pre-restore copy of current NameNode metadata.
5. Restores FsImage to NameNode data directory.
6. Restarts HDFS and runs `hdfs dfsadmin -report`.

**Post-restore verification**:
```bash
hdfs dfsadmin -report          # Check DataNode connections
hdfs dfs -ls /data/traffic/    # Verify data paths are accessible
```

---

## Component 2: MLflow & Model Artifacts Restore

**Script**: [restore_mlflow.sh](file:///home/phucle/Desktop/lab5/scripts/restore/restore_mlflow.sh)

```bash
export BACKUP_ENCRYPTION_KEY="$(cat /run/secrets/backup_key)"
bash scripts/restore/restore_mlflow.sh /mnt/backups/models/models_20240101_030000Z.tar.gz.enc
```

**Steps performed by script**:
1. Decrypts and extracts backup.
2. Dumps restored SQL into MLflow DB (saves pre-restore copy).
3. Copies model artifacts back to `artifacts/` directory.
4. Restores `registry.json` to `artifacts/mlops/`.

**Post-restore verification**:
```bash
PYTHONPATH=. python3 -c "
from src.mlops.model_registry import ModelRegistry
r = ModelRegistry()
prod = r.get_production_version()
print('Production model:', prod)
"
# Then restart API pods:
kubectl rollout restart deployment/traffic-prediction-api -n production
curl http://api.traffic-prediction.local/health/ready
```

---

## Component 3: Airflow Restore

**Script**: [restore_airflow.sh](file:///home/phucle/Desktop/lab5/scripts/restore/restore_airflow.sh)

```bash
export BACKUP_ENCRYPTION_KEY="$(cat /run/secrets/backup_key)"
bash scripts/restore/restore_airflow.sh /mnt/backups/databases/databases_20240101_033000Z.tar.gz.enc
```

**Post-restore verification**:
```bash
airflow dags list                        # DAGs must be visible
airflow dags trigger traffic_etl_dag     # Trigger a test run
airflow dags list-runs -d traffic_etl_dag --state running
```

---

## Backup Verification Command Reference

```bash
# Verify any encrypted backup file (ALWAYS run before restore):
export BACKUP_ENCRYPTION_KEY="$(cat /run/secrets/backup_key)"
bash scripts/backup/verify_backup.sh <backup_file>

# Run all backups manually:
bash scripts/backup/backup_hdfs_metadata.sh
bash scripts/backup/backup_models.sh
bash scripts/backup/backup_databases.sh
```
