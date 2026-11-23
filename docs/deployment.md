# Staging Infrastructure, Docker Containerization & Deployment Architecture

**Service:** Diabetic Retinopathy Diagnostic Inference Engine  
**Track:** Track 6 (DevOps, Containerization & CI/CD)  
**Status:** Staging & Architecture Blueprint (Stage B / Sprint 8)  
**Date:** 2026-11-23  

---

## 1. Overview & Architecture

This document specifies the deployment architecture, container configuration, local staging workflows, and production staging blueprints for the Diabetic Retinopathy Diagnostic Application backend inference service.

The inference service provides automated diabetic retinopathy grading from retinal fundus photographs utilizing a dual-engine architecture:
- **TFLite High-Throughput Engine:** Int8/Float32 quantized model (`retfound_model.tflite`) for sub-50ms low-latency inference with 67% memory reduction.
- **Keras Deep Learning Engine:** Full-precision checkpoint (`retfound_model.keras`) serving as the standard fallback runtime.
- **Gemini Pre-screening Gate:** Google Gemini multimodal vision validation (`gemini_validator.py`) pre-filtering non-fundus or corrupt images before neural inference.

### Service Topology

```
                  +----------------------------------------------+
                  |         Client Layer (Mobile / Web)          |
                  | Expo React Native / Clinician Web Portal     |
                  +----------------------------------------------+
                                         |
                                         | HTTPS (TLS 1.3 Only)
                                         v
                  +----------------------------------------------+
                  |      Secure Reverse Proxy (TLS Termination)  |
                  |          Nginx / Caddy / Cloud ALB           |
                  |  - Let's Encrypt / Managed TLS 1.3           |
                  |  - HSTS, CSP, Frame Options, Sniff Guard     |
                  |  - Rate Limiting & Cloud Armor / WAF         |
                  +----------------------------------------------+
                                         |
                                         | HTTP / Keepalive (Internal LAN/VPC)
                                         v
                  +----------------------------------------------+
                  |    Hardened Docker Container (Port 5000)     |
                  |                                              |
                  |  +----------------------------------------+  |
                  |  | Gunicorn WSGI Master (2 workers x 4 th) |  |
                  |  +----------------------------------------+  |
                  |                     |                        |
                  |  +----------------------------------------+  |
                  |  | Flask Application Factory              |  |
                  |  | - Auth / JWT Validation (SEC-02)       |  |
                  |  | - HMAC Tamper Receipts (ARCH-01)       |  |
                  |  | - Gemini Validator (PR-01)             |  |
                  |  | - Dual-Engine TFLite/Keras (PERF-01)   |  |
                  |  +----------------------------------------+  |
                  |                                              |
                  |  Non-root user execution (`appuser`: 1000)   |
                  |  Resource Limits: 2.0 CPUs, 2500MB RAM       |
                  +----------------------------------------------+
```

---

## 2. Sprint 8 Defect Remediations

Sprint 8 addresses five critical containerization, orchestration, security, and continuous integration defects:

| Defect ID | Component | Severity | Description & Resolution |
| :--- | :--- | :--- | :--- |
| **PR-01** | `Dockerfile` | **Critical** | Missing `gemini_validator.py` caused immediate `ModuleNotFoundError` on container startup. Resolved by explicitly bundling `gemini_validator.py` and `retfound_model.tflite` into `/app`. |
| **PR-02** | `Dockerfile` & `docker-compose.yml` | **High** | Port mismatch: Dockerfile defaulted to Hugging Face Spaces port 7860 while Compose and client expected port 5000. Resolved by standardizing default port to `5000` and implementing dynamic healthcheck `http://localhost:${PORT:-5000}/api/health`. |
| **PR-04** | `docker-compose.yml` | **High** | Missing environment variable forwarding (`GEMINI_API_KEY`, `USE_TFLITE`, `GUNICORN_THREADS=4`, etc.) crippled AI pre-screening and concurrency. Resolved by forwarding all required runtime variables with safe fallbacks. |
| **SEC-05** | Infrastructure / Mobile | **High** | Development relied on unauthenticated public reverse proxy tunnel (`loca.lt`) without TLS cert pinning. Resolved by enforcing local loopback/VPC staging and detailing TLS 1.3 reverse proxy configurations. |
| **CP-04** | Root `test_supabase.py` & CI | **Medium** | Bare `pytest` crashed during test discovery due to unconstrained collection and `exit(1)` in `test_supabase.py`. Resolved by adding root `pytest.ini` (`testpaths = tests`) and wrapping diagnostic execution in `if __name__ == "__main__":`. |

---

## 3. Container Deployment & Local Staging

### 3.1 Dockerfile Hardening & Structure

The container image is built from `python:3.12-slim` with minimal build dependencies, security isolation, and healthchecks:

- **Minimal Base Image:** `python:3.12-slim` minimizes attack surface and container size.
- **Standardized Port:** `ENV PORT=5000` and `EXPOSE 5000`.
- **Complete Application Bundle:**
  ```dockerfile
  COPY retfound_model.keras .
  COPY retfound_model.tflite .
  COPY gemini_validator.py .
  COPY app.py .
  COPY gunicorn.conf.py .
  ```
- **Non-Root Execution:** A dedicated unprivileged system user (`appuser`, UID 1000) owns `/app` and executes the WSGI daemon, preventing container escape privileges.
- **Dynamic Healthcheck:**
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
      CMD curl -f http://localhost:${PORT:-5000}/api/health || exit 1
  ```

### 3.2 Docker Compose Local Staging

`docker-compose.yml` orchestrates the local staging container:

```yaml
services:
  retina-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: diabetic-retinopathy-api
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - PORT=5000
      - RETINA_MODEL_PATH=/app/retfound_model.keras
      - RETINA_TFLITE_PATH=${RETINA_TFLITE_PATH:-/app/retfound_model.tflite}
      - USE_TFLITE=${USE_TFLITE:-0}
      - GEMINI_API_KEY=${GEMINI_API_KEY:-}
      - ENABLE_GEMINI_VALIDATION=${ENABLE_GEMINI_VALIDATION:-true}
      - GEMINI_MODEL=${GEMINI_MODEL:-gemini-3.1-flash-lite}
      - GEMINI_TIMEOUT_SECONDS=${GEMINI_TIMEOUT_SECONDS:-15}
      - SUPABASE_JWT_SECRET=${SUPABASE_JWT_SECRET:-}
      - SCAN_HMAC_SECRET=${SCAN_HMAC_SECRET:-}
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-*}
      - GUNICORN_WORKERS=${GUNICORN_WORKERS:-2}
      - GUNICORN_THREADS=${GUNICORN_THREADS:-4}
      - LOG_LEVEL=${LOG_LEVEL:-info}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 2500M
        reservations:
          cpus: "1.0"
          memory: 1024M
```

### 3.3 Quickstart: Local Staging Commands

1. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your GEMINI_API_KEY and SUPABASE_JWT_SECRET
   ```

2. **Build and Run Container:**
   ```bash
   docker compose up --build -d
   ```

3. **Verify Container Status & Health:**
   ```bash
   docker compose ps
   docker inspect --format='{{json .State.Health.Status}}' diabetic-retinopathy-api
   ```

4. **Verify Health Endpoint via Local Loopback:**
   ```bash
   curl -i http://localhost:5000/api/health
   ```

5. **Stop Container:**
   ```bash
   docker compose down
   ```

---

## 4. Remediation of Insecure Public Tunnels (SEC-05)

### 4.1 The Security Vulnerability of `loca.lt`

In initial development configurations, mobile clients were configured to communicate with endpoints like `https://diabetic-retina-test.loca.lt`. This presents severe HIPAA and GDPR compliance violations:

1. **Unauthenticated Public Proxy:** Anyone with knowledge of the subdomain can inspect or replay requests.
2. **Absence of Business Associate Agreement (BAA):** Third-party tunnel operators do not sign HIPAA BAAs. Processing Protected Health Information (PHI) through them is a direct HIPAA violation.
3. **No TLS Certificate Pinning:** Tunnels terminate TLS at their edge, creating an unmonitored plaintext transit point.
4. **Reliability & Availability Failures:** Public tunnels suffer from intermittent connection drops, throttling, and anti-phishing interstitial pages that disrupt API JSON payloads.

### 4.2 Approved Local Development Workflows

For development and physical mobile device testing:
1. **Localhost Loopback:** Simulator/emulator targets `http://10.0.2.2:5000` (Android emulator) or `http://127.0.0.1:5000` (iOS simulator / Web).
2. **Private LAN Development:** Physical mobile devices on the same secure Wi-Fi network target the host machine's private IP (e.g., `http://192.168.1.150:5000`).
3. **Encrypted Point-to-Point VPN:** For remote developers, use an encrypted WireGuard or Tailscale mesh network with mutual key exchange, eliminating public internet exposure.

---

## 5. Production Reverse Proxy & TLS 1.3 Termination

In staging and production, the Docker container MUST NEVER be directly exposed to the public internet without an authenticating, rate-limiting reverse proxy terminating TLS 1.3.

### 5.1 Nginx Reverse Proxy Configuration

Below is the hardened Nginx virtual host configuration (`/etc/nginx/conf.d/retina_api.conf`):

```nginx
# Upstream Gunicorn WSGI Cluster
upstream retina_backend {
    server 127.0.0.1:5000 fail_timeout=0;
    keepalive 32;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name api.retina-staging.example.com;
    return 301 https://$host$request_uri;
}

# HTTPS Server - TLS 1.3 Hardened
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.retina-staging.example.com;

    # SSL Certificates (Let's Encrypt / Automated ACME)
    ssl_certificate /etc/letsencrypt/live/api.retina-staging.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.retina-staging.example.com/privkey.pem;

    # TLS Protocols & Cipher Suites (Mozilla Modern Configuration)
    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    # SSL Session Optimization
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    # Security Headers (HSTS, Anti-Clickjacking, Sniff Guard)
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'none'; frame-ancestors 'none';" always;

    # Request Body Size (Permit high-resolution fundus images up to 16MB)
    client_max_body_size 16M;

    # Timeouts
    client_body_timeout 15s;
    client_header_timeout 15s;
    keepalive_timeout 65s;
    send_timeout 15s;

    location / {
        proxy_pass http://retina_backend;
        proxy_http_version 1.1;

        # Forwarded Headers
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # Proxy Buffering & Timeouts
        proxy_buffering on;
        proxy_buffer_size 16k;
        proxy_buffers 8 32k;
        proxy_read_timeout 30s;
        proxy_connect_timeout 5s;
    }

    # Lightweight Healthcheck Location
    location /api/health {
        proxy_pass http://retina_backend/api/health;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        access_log off;
    }
}
```

### 5.2 Caddy Alternative Configuration

For teams preferring zero-maintenance automated TLS management, Caddy provides built-in TLS 1.3 and automatic certificate renewal:

```caddy
api.retina-staging.example.com {
    tls {
        protocols tls1.3
    }

    # Security Headers
    header {
        Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
    }

    # Request Size Limit
    request_body {
        max_size 16MB
    }

    reverse_proxy 127.0.0.1:5000 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-Proto {scheme}
        health_uri /api/health
        health_interval 30s
        health_timeout 5s
    }
}
```

---

## 6. HIPAA-Eligible Cloud Staging Blueprint

*Note: In accordance with Swarm Governance Policy Section 1.3, paid cloud infrastructure provisioning and live public endpoint deployment remain `BLOCKED — HUMAN APPROVAL REQUIRED`. The following blueprints define the architectural plan for authorized implementation.*

### 6.1 AWS Fargate Architecture Blueprint

- **Compute:** AWS ECS running Fargate tasks (Serverless container runtime).
  - CPU: 2 vCPU, RAM: 4 GB.
  - Non-root container execution in read-only root filesystem with ephemeral `/tmp` storage.
- **Networking & Ingress:**
  - Application Load Balancer (ALB) terminating TLS 1.3 using ACM certificate.
  - AWS WAF attached to ALB with rate-limiting rules and OWASP Top 10 rule sets.
  - Tasks located in private subnets with no public IPv4 addresses; outbound access via NAT Gateway.
- **Secrets Management:**
  - `GEMINI_API_KEY`, `SUPABASE_JWT_SECRET`, and `SCAN_HMAC_SECRET` injected directly into ECS task definitions from AWS Secrets Manager.
- **Compliance & Encryption:**
  - EBS ephemeral volume encryption with AWS KMS customer-managed key.
  - AWS CloudTrail logging all API calls.
  - Executed AWS Business Associate Addendum (BAA).

### 6.2 Google Cloud Run Blueprint

- **Compute:** Google Cloud Run (Fully Managed Container Service).
  - Minimum instances: 1 (to eliminate cold start latency for clinical triage).
  - Maximum instances: 10 with autoscaling based on concurrent request count.
  - Memory: 2 GiB, CPU: 2 vCPU.
- **Ingress & Security:**
  - HTTPS-only ingress with Google-managed TLS certificates.
  - Cloud Armor security policies enforcing IP whitelisting or geo-fencing for staging.
- **Secrets:**
  - Environment variables bound to Google Secret Manager secrets at deploy time.
- **Compliance:**
  - Google Cloud BAA covering Cloud Run, Secret Manager, and Cloud KMS.

---

## 7. CI/CD Integration & Pytest Runner Standardization (CP-04)

### 7.1 Pytest Configuration (`pytest.ini`)

To prevent diagnostic scripts and third-party files from interfering with automated CI test runs, `pytest.ini` standardizes discovery:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
norecursedirs = mobile .venv node_modules supabase audit docs
addopts = -ra -q --strict-markers
```

### 7.2 Safe Diagnostic Script Execution (`test_supabase.py`)

The root `test_supabase.py` script is encapsulated so it only executes when invoked as the main module:

```bash
# Manual Supabase connectivity diagnostic check
.venv\Scripts\python test_supabase.py
```

Importing `test_supabase` during automated test runs produces zero side effects, makes no network requests, and never calls `exit()`.

### 7.3 Continuous Integration Pipeline Verification

Every CI workflow execution verifies the repository with:

```bash
# 1. Run full automated test suite cleanly
python -m pytest

# 2. Run Docker and CI regression suite
python -m pytest tests/test_docker_ci_infrastructure.py -v
```
