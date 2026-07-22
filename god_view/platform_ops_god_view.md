# God View — Platform & Operations
# Luồng: CI/CD → HA Deployment → Security → Orchestration → Backup & DR

---

## 1. CI/CD Pipeline (GitHub Actions)

```text
Pull Request / Push to main
         │
         ▼
[ci.yml] ─────────────────────────────── GATE: ALL MUST PASS
  ├── flake8 lint + black --check
  ├── pytest tests/unit/
  ├── pytest tests/mlops/
  ├── bandit SAST (HIGH severity)
  └── trivy container scan (HIGH/CRITICAL CVE)
         │ ALL PASS
         ▼
[build-images.yml]
  ├── docker build
  ├── docker push → ghcr.io/owner/traffic-prediction-api:{GIT_SHA}
  │     ⚠ ALWAYS immutable Git SHA tag — NEVER :latest
  └── scripts/generate_sbom.sh → sbom.json (artifact)
         │
         ▼
[deploy-staging.yml]
  ├── helm upgrade --install (namespace: staging)
  │     --set image.tag={GIT_SHA}
  └── scripts/smoke_test.sh → exits 1 if ANY endpoint fails
         │ PASS
         ▼
[deploy-production.yml]
  ├── GitHub Environment "production" → MANUAL APPROVAL required
  ├── helm upgrade --install --atomic (namespace: production)
  └── on failure → scripts/rollback_deployment.sh
        helm rollback → previous revision + Slack notification
```

**SBOM**: `scripts/generate_sbom.sh` — syft → pip-audit → pip-freeze fallback chain.
**Smoke Test**: 6 endpoints checked. `exit 1` blocks production deploy on any failure.

---

## 2. Kubernetes HA Deployment Architecture

```text
  ┌──────────────────────────────────────────────────────────────────────┐
  │  Kubernetes Production Cluster (≥3 Nodes, multi-AZ)                  │
  │                                                                       │
  │  [Nginx Ingress / LB]  ─── TLS termination, rate limit 100 rps       │
  │         ↓                                                             │
  │  [ClusterIP api-service]  ← no hardcoded IP, K8s DNS only            │
  │         ↓                                                             │
  │  api-deployment  3 replicas                                           │
  │    Pod-1@Node-A   Pod-2@Node-B   Pod-3@Node-C                        │
  │    topologySpreadConstraints: 1 pod per node                         │
  │    PodDisruptionBudget: minAvailable=2                                │
  │    HPA: min=3 / max=12 — CPU 60%, Memory 75%                         │
  │         ↑ scale-up 2 pods/30s  ↓ scale-down 1 pod/60s               │
  │                                                                       │
  │  NetworkPolicy:                                                       │
  │    Default DENY ALL → whitelist: ingress-controller, Prometheus,      │
  │                        dashboard pods only                            │
  │                                                                       │
  │  ServiceAccount: traffic-prediction-sa (RBAC: get/list ConfigMap     │
  │    only — no cluster-admin)                                           │
  │                                                                       │
  │  PersistentVolumeClaims:                                              │
  │    model-artifacts-pvc  (10Gi, ReadWriteMany)                         │
  │    hdfs-datanode-[1-3]-pvc (200Gi each, ReadWriteOnce)               │
  │    airflow-db-pvc  (20Gi)                                             │
  └──────────────────────────────────────────────────────────────────────┘
```

**No IP hardcoding**: all service addresses use Kubernetes DNS names (e.g. `traffic-prediction-api.production.svc.cluster.local`) defined in `deploy/kubernetes/configmap.yaml`.

---

## 3. HDFS High Availability (NameNode)

```text
  Active NameNode ──────────┐
  Standby NameNode ─────────┼── JournalNode × 3 (quorum: 2/3 agree)
                            └── ZooKeeper × 3 (ZKFC automatic failover)

  DataNode × 3+ (replicationFactor=3, cross-rack aware)

  Failover sequence:
    1. Active NameNode crash → ZKFC detects (ZK session expiry)
    2. ZKFC on Standby acquires ZK lock → fences old Active
    3. Standby replays JournalNode edit logs
    4. Standby becomes Active → ~30–60 seconds total
```

Config reference: `docs/hdfs_ha_config.md` — full `core-site.xml` and `hdfs-site.xml` spec.

---

## 4. Security Architecture

```text
Secrets:
  SecretProvider hierarchy:
    /run/secrets/<name>  →  env var  →  default
  API keys, DB passwords NEVER in code or config files.
  Secrets masked in logs: ***MASKED***

Nginx SSL Termination:
  TLS cert → Kubernetes Secret "traffic-prediction-tls"
  HTTPS forced (nginx.ingress.kubernetes.io/force-ssl-redirect: "true")

Authentication: Bearer token per API endpoint
Rate Limiting: 100 req/s per client IP (sliding window)
RBAC roles: viewer / analyst / admin

Network isolation:
  NetworkPolicy default DENY ALL ingress to API pods.
  Whitelisted:
    - ingress-nginx namespace (external traffic)
    - monitoring namespace (Prometheus scrape)
    - traffic-dashboard pods (internal API calls)
```

---

## 5. Workflow Orchestration (Airflow)

```text
Airflow Scheduler (airflow/dags/)
  │
  ├── traffic_ingestion_dag     — every 30 min
  │     SourceRouter → HDFS raw Parquet
  │     JobLock("ingestion_dag") prevents concurrent runs
  │
  ├── traffic_etl_dag           — hourly
  │     Spark ETL → HDFS processed Parquet
  │     JobLock("etl_dag")
  │
  ├── model_training_dag        — weekly / on-demand
  │     Train → Validate → Register → Promote
  │     JobLock("model_promoter")
  │
  └── model_monitoring_dag      — daily
        DriftDetector → RetrainingPolicy → trigger training if needed

Failure handling:
  notify_job_failure() → Slack/Email alert
  PipelineStateTracker.record_failure(dag_id, reason)

Config: config/airflow/airflow.cfg, pipeline_schedule.yaml
```

---

## 6. Backup & Disaster Recovery

### Backup Matrix

| Component | Frequency | Retention | Encrypted |
|---|---|---|---|
| HDFS NameNode metadata | Daily 02:00 UTC | 30 days | ✅ AES-256 |
| Model artifacts + MLflow DB | After every promotion | 10 versions | ✅ AES-256 |
| Airflow DB + App config + Grafana | Daily 03:00 UTC | 30 days | ✅ AES-256 |

All backups stored **off-cluster** (NFS/S3).
Encryption: `openssl enc -aes-256-cbc -pbkdf2 -pass env:BACKUP_ENCRYPTION_KEY`

### RPO / RTO

| Metric | Target |
|---|---|
| RPO (max data loss) | 24 hours |
| RTO (max downtime) | 4 hours |

### Restore Flow

```text
Disaster event
     │
     ▼
1. Run: bash scripts/backup/verify_backup.sh <file>
   → Actually decrypts + extracts + counts content (not just ls -la)
     │
     ▼
2. Component-specific restore:
   HDFS:    bash scripts/restore/restore_hdfs.sh <backup_file>
   MLflow:  bash scripts/restore/restore_mlflow.sh <backup_file>
   Airflow: bash scripts/restore/restore_airflow.sh <backup_file>
     │
     ▼
3. Verify recovery:
   curl GET /health/live → 200 OK
   curl GET /health/ready → model_loaded: true
   POST /v1/predictions → valid speed value
```

**DR Scenarios**:
- **Cluster loss** (Scenario A): Provision new K8s → apply manifests → restore artifacts → Helm deploy → smoke test → ~4h.
- **HDFS disk/NN corruption** (Scenario B): Stop HDFS → restore FsImage → restart → DataNodes reconnect → ~2h.
- **Bad model deploy** (Scenario C): `RollbackEngine.rollback()` → pod restart → ~5 minutes.

Reference: `docs/disaster_recovery.md`, `docs/restore_runbook.md`, `docs/backup_policy.md`
