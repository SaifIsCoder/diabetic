# Sprint 8 Audit & Gate Check: Staging Infrastructure, Docker Containerization & CI/CD

**Sprint:** Sprint 8 (Track 6)  
**Target:** Dockerfile Hardening, Port & Healthcheck Alignment, Docker Compose Environment Forwarding, CI/CD Pytest Configuration, and Staging Architecture  
**Status:** **STAGE B — PLAN & GATE CHECK APPROVED**  
**Date:** 2026-11-23  

---

## 1. Confirmed Audit Findings & Target Defects

This audit evaluates the containerization, local orchestration, continuous integration test runner, and staging deployment posture of the Diabetic Retinopathy Diagnostic Application. Five confirmed infrastructure defects and security gaps are targeted for remediation in Sprint 8:

### 1.1 PR-01: Missing `gemini_validator.py` in Dockerfile (`ModuleNotFoundError` on Startup)
- **Severity:** Critical (Blocks Container Deployment)
- **Confirmed Root Cause:**  
  In `Dockerfile` (lines 24–28):
  ```dockerfile
  # Copy model and application source
  COPY retfound_model.keras .
  COPY app.py .
  COPY gunicorn.conf.py .
  ```
  `gemini_validator.py` was omitted from the `COPY` instructions. When the container executes `gunicorn --config gunicorn.conf.py "app:create_app()"`, Python attempts to import `app.py`. Line 40 of `app.py` directly executes:
  ```python
  from gemini_validator import (
      classify_fundus_image,
      validate_image_bytes,
      FundusValidationError,
      ...
  )
  ```
  Because `gemini_validator.py` is absent from `/app`, the import fails immediately with `ModuleNotFoundError: No module named 'gemini_validator'`. Gunicorn fails to bind workers, causing an immediate container crashloop (`exit code 1`).
- **Remediation Plan:**
  Update `Dockerfile` to explicitly copy `gemini_validator.py` alongside `app.py` and `gunicorn.conf.py`. Additionally, copy `retfound_model.tflite` to ensure full compatibility with the Sprint 7 TFLite dual-engine inference runtime.

---

### 1.2 PR-02: Port & Healthcheck Mismatch between Dockerfile (7860) and Docker Compose / Application (5000)
- **Severity:** High (False Unhealthy State & Container Restarts)
- **Confirmed Root Cause:**  
  `Dockerfile` hardcodes Hugging Face Spaces default port `7860`:
  ```dockerfile
  ENV PORT=7860
  EXPOSE 7860
  HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
      CMD curl -f http://localhost:7860/api/health || exit 1
  ```
  However, `docker-compose.yml` specifies:
  ```yaml
  ports:
    - "5000:5000"
  environment:
    - PORT=5000
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
  ```
  Furthermore, `.env.example`, `.env`, and `mobile/lib/supabase.ts` (`http://127.0.0.1:5000`) standardize on port `5000`.
  When a container is started using Docker Compose, the Gunicorn process binds to `PORT=5000`. If an orchestrator relies on the built-in image `HEALTHCHECK` instruction defined in the `Dockerfile`, `curl -f http://localhost:7860/api/health` queries port 7860, which returns `Connection refused`. The container is flagged as `unhealthy`, triggering automatic restart cycles.
- **Remediation Plan:**
  1. Standardize default port to `5000` in `Dockerfile`: `ENV PORT=5000`, `EXPOSE 5000`.
  2. Implement dynamic port resolution in the `HEALTHCHECK` directive using shell environment expansion:
     `CMD curl -f http://localhost:${PORT:-5000}/api/health || exit 1`.
  3. Ensure complete synchronization across `Dockerfile`, `docker-compose.yml`, `.env`, and documentation.

---

### 1.3 PR-04: Incomplete Environment Forwarding in `docker-compose.yml`
- **Severity:** High (Runtime AI & Concurrency Failures in Container)
- **Confirmed Root Cause:**  
  The existing `docker-compose.yml` environment block only passes:
  ```yaml
  environment:
    - PORT=5000
    - RETINA_MODEL_PATH=/app/retfound_model.keras
    - SUPABASE_JWT_SECRET=${SUPABASE_JWT_SECRET:-}
    - GUNICORN_WORKERS=2
    - GUNICORN_THREADS=2
    - LOG_LEVEL=info
  ```
  Crucial environment variables are omitted:
  - `GEMINI_API_KEY`: Without this variable, Gemini fundus image pre-screening fails with configuration errors or unhandled HTTP 500 responses when `ENABLE_GEMINI_VALIDATION=true`.
  - `ENABLE_GEMINI_VALIDATION`, `GEMINI_MODEL`, `GEMINI_TIMEOUT_SECONDS`: Cannot be tuned per container deployment.
  - `USE_TFLITE` and `RETINA_TFLITE_PATH`: Omitted, preventing the container from utilizing the Sprint 7 TFLite high-throughput runtime (11.85x latency speedup and 67% memory reduction).
  - `GUNICORN_THREADS`: Hardcoded to `2`, overriding the Sprint 7 PR-07 optimization in `gunicorn.conf.py` (which default-sizes workers=2, threads=4, total 8 slots minimum), re-introducing thread starvation risks.
  - `ALLOWED_ORIGINS` and `SCAN_HMAC_SECRET`: Missing, risking CORS rejections or scan receipt signature verification inconsistencies.
- **Remediation Plan:**
  Update `docker-compose.yml` to forward all essential variables with safe defaults:
  `GEMINI_API_KEY=${GEMINI_API_KEY:-}`, `ENABLE_GEMINI_VALIDATION=${ENABLE_GEMINI_VALIDATION:-true}`, `GEMINI_MODEL=${GEMINI_MODEL:-gemini-3.1-flash-lite}`, `GEMINI_TIMEOUT_SECONDS=${GEMINI_TIMEOUT_SECONDS:-15}`, `USE_TFLITE=${USE_TFLITE:-0}`, `RETINA_TFLITE_PATH=/app/retfound_model.tflite`, `GUNICORN_WORKERS=${GUNICORN_WORKERS:-2}`, `GUNICORN_THREADS=${GUNICORN_THREADS:-4}`, `ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-*}`, `SCAN_HMAC_SECRET=${SCAN_HMAC_SECRET:-}`. Update `.env.example` and `.env` accordingly.

---

### 1.4 CP-04: Root `test_supabase.py` Network Calls at Import & `exit(1)` Crashing Bare `pytest`
- **Severity:** Medium (Blocks CI/CD Automation & Local Test Discovery)
- **Confirmed Root Cause:**  
  The root file `test_supabase.py` is a manual connectivity diagnostic script, not a unit test module. However, because its name matches the default pytest pattern `test_*.py`, bare `pytest` discovers and attempts to import it during test collection.
  At module root level (lines 20–61), `test_supabase.py` executes imperative network requests to Supabase (`requests.get(f"{url}/auth/v1/health")`). If network connectivity is unavailable, DNS fails, or credentials are unconfigured, line 61 directly executes:
  ```python
  exit(1)
  ```
  Calling `exit(1)` abruptly terminates the pytest process during collection with `INTERNALERROR: SystemExit: 1`, executing 0 tests across the entire test suite.
  Furthermore, the repository lacks a `pytest.ini` configuration file, leaving test discovery unconstrained.
- **Remediation Plan:**
  1. Author `pytest.ini` in the repository root to explicitly constrain test discovery:
     `testpaths = tests`, `python_files = test_*.py`, `norecursedirs = mobile .venv node_modules supabase audit docs`.
  2. Refactor `test_supabase.py` into a modular diagnostic script where network requests and exit calls are encapsulated within a `run_diagnostics()` function guarded by `if __name__ == "__main__":`.
  3. Ensure that bare `pytest` runs cleanly, collecting 151+ tests with 0 collection errors and 0 internal errors.

---

### 1.5 SEC-05: Insecure Public `loca.lt` Reverse Tunnel without TLS Pinning
- **Severity:** High (HIPAA/GDPR Data Insecurity in Dev/Staging)
- **Confirmed Root Cause:**  
  In `mobile/.env`, the inference API endpoint is configured as `https://diabetic-retina-test.loca.lt`. Localtunnel is an unauthenticated public tunneling proxy with no mutual TLS, no Certificate Transparency enforcement, no enterprise SLA, and no signed Business Associate Agreement (BAA). Routing protected health information (PHI) and retinal fundus photographs over public reverse proxy tunnels exposes sensitive patient scans to eavesdropping and data interception.
- **Remediation Plan:**
  1. Local Configuration: Configure local development and container testing to use secure local loopback (`http://127.0.0.1:5000` or private LAN IP) rather than public tunnels.
  2. Staging Infrastructure Blueprint: Author `docs/deployment.md` defining the staging and production deployment topology:
     - Hardened Docker container configuration with non-root security context.
     - Production TLS reverse proxy (Nginx / Caddy / Traefik) terminating TLS 1.3 with Let's Encrypt / Cloudflare certificates, HSTS headers, and strict cipher suites.
     - Architecture migration blueprint for HIPAA-eligible cloud staging environments (e.g. AWS ECS / Fargate with ALB, GCP Cloud Run with Cloud Armor, or Azure Container Apps).

---

## 2. Governance Gate Check

In accordance with Section 1.3 of the Autonomous Swarm Governance Policy, all activities in Sprint 8 are evaluated against safety and financial gates:

| Activity / Action | Classification | Gate Status | Rationale |
| :--- | :--- | :--- | :--- |
| **Paid cloud infrastructure upgrades** (AWS / GCP / Azure provisioning, purchasing domains, configuring managed DNS) | Commercial & Financial Commitment | **BLOCKED — HUMAN APPROVAL REQUIRED** | Provisioning paid cloud infrastructure requires commercial account access, credit card billing, and organization owner approval. |
| **Live production staging deployment** (Pushing live containers to internet-facing public endpoints) | Production Deployment | **BLOCKED — HUMAN APPROVAL REQUIRED** | Deploying publicly accessible clinical endpoints handling health data requires formal organizational risk review and BAA validation. |
| **Fixing Dockerfile `COPY` instructions** (`gemini_validator.py`, `retfound_model.tflite`) | Reversible Local Container Config | **Auto-proceed** | Purely local configuration fix preventing `ModuleNotFoundError` during containerization. |
| **Aligning ports & healthcheck commands** (`PORT=5000` across Dockerfile & Compose) | Reversible Local Container Config | **Auto-proceed** | Resolves port mismatch and ensures container healthchecks report accurate status. |
| **Updating `docker-compose.yml` environment block** (`GEMINI_API_KEY`, `USE_TFLITE`, `GUNICORN_THREADS=4`) | Reversible Local Container Config | **Auto-proceed** | Enables full feature parity and concurrency tuning inside local Docker containers. |
| **Authoring root `pytest.ini`** (`testpaths = tests`) | Reversible CI Test Configuration | **Auto-proceed** | Constrains pytest discovery to `tests/` directory, restoring reliable CI automation. |
| **Refactoring root `test_supabase.py`** (Encapsulating top-level calls in `if __name__ == "__main__":`) | Reversible Local Script Refactoring | **Auto-proceed** | Eliminates import-time network requests and `exit(1)` crashes during test collection. |
| **Authoring regression test suite** (`tests/test_docker_ci_infrastructure.py`) | Automated Test Suite | **Auto-proceed** | Provides verifiable automated test assertions for all Docker, Compose, and CI fixes. |
| **Authoring Staging Architecture Guide** (`docs/deployment.md`) | Documentation & Architecture Blueprint | **Auto-proceed** | Provides detailed staging deployment and TLS pinning specifications without incurring cloud costs. |

---

## 3. Implementation Plan & File Locking

### 3.1 Exclusive File Ownership
- **Exclusive File Owner:** `DevOps & CI Engineer` (`teamwork_worker`)
- **Reviewer & Forensic Auditor:** `Independent QA Reviewer & Forensic Auditor`

### 3.2 Locked Files
The following files are strictly locked for exclusive modification by the `DevOps & CI Engineer`:
1. `Dockerfile`
2. `docker-compose.yml`
3. `pytest.ini` (New file)
4. `test_supabase.py`
5. `.env`
6. `.env.example`
7. `tests/test_docker_ci_infrastructure.py` (New regression test suite)
8. `docs/deployment.md` (New staging architecture documentation)
9. `sprint_8_implementation.md` (New sprint report)

### 3.3 Concrete Step-by-Step Implementation Sequence

1. **Step 1: Pytest Runner Configuration (`pytest.ini` & `test_supabase.py`)**
   - Author `pytest.ini` configuring `testpaths = tests`, `python_files = test_*.py`, `addopts = -ra -q --strict-markers`, and `norecursedirs = mobile .venv node_modules supabase audit docs`.
   - Refactor `test_supabase.py`: Wrap top-level diagnostic code in `def run_diagnostics():` and execute only under `if __name__ == "__main__":`.
   - Verify: Execute bare `python -m pytest` from project root and confirm that all 150+ tests collect and execute without collection crashes or `INTERNALERROR`.

2. **Step 2: Dockerfile Hardening & Defect Remediation (`PR-01`, `PR-02`)**
   - In `Dockerfile`:
     - Update `PORT=5000` and `EXPOSE 5000`.
     - Add `COPY gemini_validator.py .` to resolve `PR-01`.
     - Add `COPY retfound_model.tflite .` (if exists) for TFLite runtime support.
     - Update `HEALTHCHECK` command to dynamically use `${PORT:-5000}`.
   - Verify: Static Dockerfile inspection and syntax validation.

3. **Step 3: Docker Compose Environment & Concurrency Alignment (`PR-04`, `SEC-05`)**
   - In `docker-compose.yml`:
     - Synchronize port mappings `5000:5000`.
     - Forward `GEMINI_API_KEY=${GEMINI_API_KEY:-}`, `ENABLE_GEMINI_VALIDATION=${ENABLE_GEMINI_VALIDATION:-true}`, `GEMINI_MODEL=${GEMINI_MODEL:-gemini-3.1-flash-lite}`, `GEMINI_TIMEOUT_SECONDS=${GEMINI_TIMEOUT_SECONDS:-15}`.
     - Forward `USE_TFLITE=${USE_TFLITE:-0}` and `RETINA_TFLITE_PATH=${RETINA_TFLITE_PATH:-/app/retfound_model.tflite}`.
     - Set `GUNICORN_WORKERS=${GUNICORN_WORKERS:-2}` and `GUNICORN_THREADS=${GUNICORN_THREADS:-4}` (matching Sprint 7 concurrency tuning).
     - Forward `ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-*}` and `SCAN_HMAC_SECRET=${SCAN_HMAC_SECRET:-}`.
   - Update `.env.example` and `.env` with comprehensive documentation of all environment variables.

4. **Step 4: Comprehensive Staging & Deployment Architecture (`SEC-05`, `docs/deployment.md`)**
   - Author `docs/deployment.md` detailing:
     - Local containerized staging workflow using Docker & Docker Compose.
     - Secure TLS termination reverse proxy architecture (Nginx / Caddy / Traefik) eliminating insecure public tunnels (`loca.lt`).
     - Production deployment blueprint for HIPAA-eligible cloud platforms (AWS ECS / GCP Cloud Run / Azure Container Apps).
     - Health monitoring, container security hardening, non-root execution, and resource quotas.

5. **Step 5: Regression Test Suite Authoring (`tests/test_docker_ci_infrastructure.py`)**
   - Implement comprehensive automated tests verifying:
     - `Dockerfile` includes `gemini_validator.py`, exposes port 5000, has proper healthcheck.
     - `docker-compose.yml` forwards `GEMINI_API_KEY`, `USE_TFLITE`, `GUNICORN_THREADS=4`, and maps port 5000.
     - `test_supabase.py` can be safely imported without side effects, network requests, or `exit()`.
     - `pytest.ini` correctly sets `testpaths = tests` and bare pytest runs cleanly.
     - `.env.example` documents all required production variables.

6. **Step 6: Sprint Documentation & Tracker Updates**
   - Generate `sprint_8_implementation.md`.
   - Update `audit/master_bug_tracker.md` to reflect remediation of `PR-01`, `PR-02`, `PR-04`, `CP-04`, and `SEC-05`.

---

## 4. Rollback & Contingency Plan

If any regression is detected during implementation or verification:
1. **Dockerfile & Compose Rollback:**
   ```bash
   git checkout -- Dockerfile docker-compose.yml .env.example .env
   ```
2. **Pytest & Diagnostic Rollback:**
   ```bash
   git checkout -- test_supabase.py
   rm -f pytest.ini
   ```
3. **Artifact Removal:**
   ```bash
   rm -f tests/test_docker_ci_infrastructure.py docs/deployment.md sprint_8_implementation.md
   ```

---

## 5. Audit Conclusion & Gate Verdict

- **Governance Verdict:** **`STAGE B — PLAN & GATE CHECK APPROVED`**  
- **Scope Authorization:** The planned remediations for `PR-01`, `PR-02`, `PR-04`, `CP-04`, and `SEC-05` (local container configuration, CI test runner configuration, environment documentation, and automated tests) are strictly reversible and approved for autonomous implementation in Stage C.
- **Blocked Items:** Paid cloud hosting and live production deployment remain strictly **`BLOCKED — HUMAN APPROVAL REQUIRED`**.
