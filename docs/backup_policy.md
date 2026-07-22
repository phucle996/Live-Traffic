# Backup Policy Document

## 1. Backup Matrix

| Component | Method | Frequency | Retention | Off-Cluster | Encrypted |
|---|---|---|---|---|---|
| HDFS NameNode Metadata | `saveNamespace` + FsImage | Daily 02:00 UTC | 30 days | ✅ NFS/S3 | ✅ AES-256 |
| Raw Parquet traffic data | HDFS snapshot | Weekly Sunday | 90 days | ✅ NFS/S3 | ✅ AES-256 |
| Processed features | HDFS snapshot | Weekly Sunday | 60 days | ✅ NFS/S3 | ✅ AES-256 |
| Model artifacts | tar.gz after promotion | On every model promotion | 10 versions | ✅ NFS/S3 | ✅ AES-256 |
| MLflow metadata DB | `sqlite3 .dump` / `pg_dump` | Daily 03:00 UTC | 30 days | ✅ NFS/S3 | ✅ AES-256 |
| Airflow metadata DB | `pg_dump` / `sqlite3 .dump` | Daily 03:30 UTC | 30 days | ✅ NFS/S3 | ✅ AES-256 |
| App configuration | tar.gz of `config/` | On every deploy | 60 days | ✅ NFS/S3 | ✅ AES-256 |
| Grafana dashboards | JSON export via API | Daily 04:00 UTC | 30 days | ✅ NFS/S3 | ✅ AES-256 |

## 2. RPO / RTO Targets

| Metric | Target |
|---|---|
| **RPO** | **24 hours** — daily backup cadence; traffic data re-crawlable from TomTom API |
| **RTO** | **4 hours** — K8s pod restart + model artifacts + config restore |

## 3. Encryption Policy

- Algorithm: **AES-256-CBC with PBKDF2** key derivation.
- Key source: `$BACKUP_ENCRYPTION_KEY` environment secret injected by Kubernetes Secret or CI encrypted secret.
- **NEVER** store encryption key in code, config files, or unencrypted backup archives.
- Decryption: `openssl enc -d -aes-256-cbc -pbkdf2 -pass env:BACKUP_ENCRYPTION_KEY -in <file> -out <out>`

## 4. Off-Cluster Storage Requirements

- Backups must reside on storage **physically separate from the primary cluster**.
- Acceptable destinations: NFS mount on separate NAS, object storage (S3/GCS/MinIO), tape.
- Minimum: 2 physical locations for critical backups (HDFS metadata, model artifacts).

## 5. Retention Enforcement

- Retention is enforced automatically by `find ... -mtime +N -delete` within each backup script.
- Model artifacts retention uses version count (10 versions) rather than time-based.
- Retention audit must be verified during monthly restore tests.

## 6. Restore Test Schedule

| Test Type | Frequency | Owner |
|---|---|---|
| Backup file decrypt + integrity check | After every backup run (automated via `verify_backup.sh`) | Platform team |
| Full restore drill to staging environment | Monthly | Platform team |
| Disaster recovery full simulation | Quarterly | Platform + Engineering leads |
