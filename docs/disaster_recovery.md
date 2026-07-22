# Disaster Recovery Plan

## 1. Disaster Scenarios & Response Playbooks

### Scenario A: Full Cluster Loss

**Definition**: All Kubernetes nodes are unreachable or destroyed.

**Impact**: Prediction API, Dashboard, Airflow all offline. Model serving halted.

**Response**:
1. Provision new Kubernetes cluster from IaC (Terraform/Pulumi).
2. Apply namespace and RBAC manifests: `kubectl apply -f deploy/kubernetes/namespace.yaml`
3. Create PVCs: `kubectl apply -f deploy/kubernetes/persistent-volumes.yaml`
4. Restore model artifacts: `bash scripts/restore/restore_mlflow.sh <backup_file>`
5. Deploy API and Dashboard via Helm: `helm upgrade --install traffic-prediction deploy/helm/`
6. Restore Airflow: `bash scripts/restore/restore_airflow.sh <backup_file>`
7. Verify smoke test: `bash scripts/smoke_test.sh <api_url>`
8. Re-enable Kafka producers and streaming consumers.

**RTO Target**: 4 hours | **RPO**: 24 hours (last daily backup).

---

### Scenario B: HDFS Disk Loss / NameNode Corruption

**Definition**: HDFS NameNode data directory is corrupt or DataNode disk fails.

**Impact**: Historical Parquet data unavailable. ETL and training pipelines blocked.

**Response**:
1. Stop HDFS: `$HADOOP_HOME/sbin/stop-dfs.sh`
2. Restore NameNode metadata: `bash scripts/restore/restore_hdfs.sh <backup_file>`
3. Start HDFS: `$HADOOP_HOME/sbin/start-dfs.sh`
4. Wait for DataNodes to reconnect and re-replicate blocks.
5. Verify: `hdfs dfsadmin -report`

**Note**: If replicationFactor=3 and only 1 DataNode disk fails, no action is needed — Hadoop auto-replicates from surviving DataNodes.

**RTO Target**: 2 hours (HDFS HA automatic failover: ~60s; manual restore: 2h).

---

### Scenario C: Bad Model Deployment

**Definition**: A new model version causes prediction errors or quality degradation.

**Response** (fast path — <5 minutes):
1. Execute MLOps rollback: `PYTHONPATH=. python3 -c "from src.mlops.rollback import RollbackEngine; RollbackEngine().rollback()"`
2. Restart API pods to reload previous model: `kubectl rollout restart deployment/traffic-prediction-api -n production`
3. Verify readiness: `kubectl rollout status deployment/traffic-prediction-api -n production`

**Response** (slow path — restore from backup):
1. `bash scripts/restore/restore_mlflow.sh <backup_file_from_before_bad_deploy>`
2. Restart API.

---

## 2. Emergency Contacts

| Role | Responsibility |
|---|---|
| Platform On-Call | Kubernetes, HDFS, backup systems |
| ML Engineer On-Call | Model rollback, MLflow, retraining |
| Data Engineer On-Call | Airflow DAGs, Kafka, ETL pipelines |

## 3. Recovery Verification Checklist

After any restore procedure, verify:
- [ ] `GET /health/live` returns HTTP 200
- [ ] `GET /health/ready` returns `model_loaded: true`
- [ ] `POST /v1/predictions` returns valid speed prediction
- [ ] Airflow DAGs resume scheduling on schedule
- [ ] HDFS `df -h` shows expected data volume
- [ ] Prometheus metrics are being scraped
