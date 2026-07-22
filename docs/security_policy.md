# Production Security Policy — Lab 5 Urban Traffic Prediction System

This document outlines the security specifications, environment isolation, network shielding rules, and secret protection policies for production deployment.

---

## 1. Environment Isolation & Configuration

- **Development (`config/development.yaml`)**: Used for local coding, debugging, and offline unit testing.
- **Staging (`config/staging.yaml`)**: Used for integration testing with mock services and schema validation.
- **Production (`config/production.yaml`)**: Hardened environment where `debug: false`, secrets are read from `/run/secrets/`, HTTPS is mandatory, and rate limits are enforced.

---

## 2. Network Isolation & Service Shielding

1. **Nginx Reverse Proxy**: All public access passes through Nginx on port 443 with TLS 1.2/1.3.
2. **Internal Service Shielding**: Hadoop NameNode Web UI (`9870`), DataNode (`9864`), Spark Master UI (`8080`), and Spark Worker UI (`8081`) MUST NOT be published or exposed to the public Internet.
3. **HTTP to HTTPS Redirection**: Port 80 traffic automatically redirects to HTTPS port 443 with HSTS enabled (`max-age=31536000`).

---

## 3. Secret Protection & Secret Provider

- Secret values (e.g. `TOMTOM_API_KEY`, database passwords) MUST NEVER be committed to Git repositories or written in `.env` on production servers.
- Secrets are managed via `SecretProvider` (`src/security/secret_provider.py`), prioritizing Docker Secrets at `/run/secrets/`.
- All logging handlers automatically mask secret keys (`key=***MASKED***`).
