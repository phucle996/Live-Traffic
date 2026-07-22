# Zero-Downtime Secret Rotation Procedure — Lab 5 Traffic System

This runbook describes the zero-downtime secret rotation procedure for TomTom API keys and service credentials.

---

## 1. Zero-Downtime TomTom API Key Rotation

Because `SecretProvider` dynamically checks Docker Secrets `/run/secrets/tomtom_api_key` and environment variables, credentials can be rotated without rebuilding Docker container images.

### Step 1: Provision New Secret
In Docker Swarm / Kubernetes:
```bash
echo "new_tomtom_api_key_v2" | docker secret create tomtom_api_key_v2 -
```

### Step 2: Update Service Definition to Mount New Secret
```yaml
services:
  ingestion:
    secrets:
      - source: tomtom_api_key_v2
        target: tomtom_api_key
```

### Step 3: Trigger Rolling Service Update
```bash
docker service update --secret-rm tomtom_api_key --secret-add tomtom_api_key_v2 traffic_ingestion
```

### Step 4: Verify Health & Deprecate Old Key
Check `artifacts/reports/source_resolution.json` and logs to verify `ApiHealthCheck` passes with the new key before revoking the old key in TomTom Developer Portal.
