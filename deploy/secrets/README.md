# Production Secrets Provisioning Guide

This directory documents the production secret management strategy for Docker Secrets and HashiCorp Vault integration.

---

## 1. Docker Secrets Provisioning

In production Docker Compose or Swarm environments, secrets are mounted into containers at `/run/secrets/`:

```bash
# Create Docker Secrets
echo "your_tomtom_api_key_here" | docker secret create tomtom_api_key -
echo "your_db_password_here" | docker secret create db_password -
```

In `docker-compose.prod.yml`:
```yaml
secrets:
  tomtom_api_key:
    external: true
  db_password:
    external: true
```

The application's `SecretProvider` (`src/security/secret_provider.py`) reads from `/run/secrets/tomtom_api_key` automatically.
