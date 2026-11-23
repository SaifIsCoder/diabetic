# Render Deployment Guide: Diabetic Retinopathy Diagnostic Service

**Service:** Diabetic Retinopathy Diagnostic API & Cloud Inference Engine  
**Deployment Platform:** [Render](https://render.com/)  
**Deployment Model:** Docker Web Service (Render Blueprint `render.yaml`)  
**Container Base:** `python:3.12-slim` (Hardened Non-Root `appuser` UID 1000)  
**Document Version:** `1.0.0` (Production Release)  
**Date:** November 2026  

---

## 1. Executive Summary & Architecture

The Diabetic Retinopathy backend is a containerized microservice built on Flask and Gunicorn serving an ordinal classification neural network (DenseNet-121) alongside Google Gemini multimodal validation and Supabase integration.

```
                              [ Internet Ingress ]
                                       │
                                       │ HTTPS (TLS 1.3 / Render Cloud Ingress)
                                       ▼
                   +───────────────────────────────────────+
                   |       Render Docker Web Service       |
                   |  - Binds to 0.0.0.0:$PORT (10000)     |
                   |  - Health checks: /health             |
                   |                                       |
                   |   +────────────────────────────────+  |
                   |   | Gunicorn WSGI Master (gthread) |  |
                   |   | (2 workers x 4 threads = 8 con)|  |
                   |   +────────────────────────────────+  |
                   |                   │                   |
                   |                   ▼                   |
                   |   +────────────────────────────────+  |
                   |   | Flask Application Factory      |  |
                   |   | - Fail-Closed Supabase JWT     |  |
                   |   | - HMAC Tamper-Evident Receipts |  |
                   |   | - Pre-screening: Gemini Vision |  |
                   |   | - Dual Engine: Keras / TFLite  |  |
                   |   +────────────────────────────────+  |
                   +───────────────────────────────────────+
                          │                         │
      (Biometric Validation)│                         │ (PostgreSQL 16 & Storage)
                          ▼                         ▼
            [ Google Gemini Vision API ]    [ Supabase Managed Cloud ]
            - Pre-filters non-fundus images  - RLS Policies (scans, profiles)
            - Reject corrupt/blurred inputs  - Private Storage: `retinal-scans`
```

---

## 2. Resource Requirements & Instance Sizing

### 2.1 Model Artifact Characteristics

| Engine / Model | File Artifact | Disk Size | Runtime Memory / Worker | Latency (CPU) |
| :--- | :--- | :--- | :--- | :--- |
| **Keras DenseNet-121** (Default) | `retfound_model.keras` | 82.3 MB | ~300 MB - 400 MB | ~200 - 350 ms |
| **Quantized TFLite** (High-Throughput) | `retfound_model.tflite` | 28.9 MB | ~60 MB - 100 MB | ~35 - 50 ms |

### 2.2 Sizing Guidelines & OOM Prevention

> [!WARNING]
> **Do not use Render's Free Instance Tier (512 MB RAM) with Keras DenseNet-121.**  
> TensorFlow 2.16 + Keras DenseNet-121 loads into RAM per Gunicorn worker process (`preload_app = False` is required for TensorFlow thread/fork safety). With 2 workers, baseline memory is ~1.2 GB, peaking to ~1.8 GB under concurrent image processing. Running Keras on 512 MB will trigger immediate OS kernel **OOM Killer (SIGKILL / Exit Code 137)**.

| Render Plan | Specs | Supported Runtime | Recommended Use Case |
| :--- | :--- | :--- | :--- |
| **Standard (Recommended)** | 2 GB RAM, 1 CPU ($25/mo) | Keras (`USE_TFLITE=0`) or TFLite (`USE_TFLITE=1`) | **Production Clinical Workloads** (Full precision Keras with 2 workers x 4 threads) |
| **Starter (Budget Option)** | 512 MB - 1 GB RAM ($7/mo) | TFLite ONLY (`USE_TFLITE=1`, `GUNICORN_WORKERS=1`) | **Staging / Testing / Budget** (Reduced memory footprint ~350 MB) |
| **Free (Not Recommended)** | 512 MB RAM | *Incompatible with Keras* (Will crash with OOM 137) | Not suitable for clinical model inference |

---

## 3. Environment Variables Reference

Render injects configuration into the container environment. Secrets must be entered in the Render Dashboard, never committed to git.

### 3.1 Production Environment Variables

| Variable Name | Required | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `FLASK_ENV` | **Yes** | `production` | Enables production mode; enforces fail-closed JWT authentication. |
| `PORT` | Auto | `10000` | Injected by Render. Gunicorn binds to `0.0.0.0:$PORT`. |
| `SUPABASE_JWT_SECRET` | **Yes (Prod)** | *None* | Supabase JWT Secret (from Supabase Dashboard -> Settings -> API -> JWT Secret). Validates Bearer tokens on protected endpoints. |
| `GEMINI_API_KEY` | **Yes (AI)** | *None* | Google Gemini API Key from Google AI Studio. Powers pre-screening fundus validation. |
| `SCAN_HMAC_SECRET` | Optional | *Fallback to JWT Secret* | Cryptographic key used to sign tamper-evident diagnostic scan receipts (`ARCH-01`). |
| `USE_TFLITE` | Optional | `0` | Set `1` to enable quantized TFLite inference (recommended for memory-constrained instances). |
| `RETINA_MODEL_PATH` | Optional | `/app/retfound_model.keras` | Absolute path to the trained Keras model inside container. |
| `RETINA_TFLITE_PATH` | Optional | `/app/retfound_model.tflite` | Absolute path to the quantized TFLite model inside container. |
| `ENABLE_GEMINI_VALIDATION`| Optional | `true` | Toggles Gemini fundus pre-validation gate. |
| `GEMINI_MODEL` | Optional | `gemini-3.1-flash-lite` | Gemini model variant used for visual inspection. |
| `GEMINI_TIMEOUT_SECONDS` | Optional | `15` | Timeout in seconds for Gemini API pre-screening calls. |
| `GUNICORN_WORKERS` | Optional | `2` | Number of Gunicorn worker processes. |
| `GUNICORN_THREADS` | Optional | `4` | Number of threads per worker (Total capacity: 8 concurrent slots). |
| `GUNICORN_TIMEOUT` | Optional | `60` | Gunicorn worker timeout in seconds. Prevents request drops during AI inference. |
| `ALLOWED_ORIGINS` | Optional | `*` or comma-list | Whitelist of allowed CORS origins (e.g. `https://your-app.com,http://localhost:8081`). |
| `RATE_LIMIT_PREDICT` | Optional | `10 per minute` | Rate limit for `/api/predict` and `/predict`. |
| `RATE_LIMIT_HEALTH` | Optional | `60 per minute` | Rate limit for `/health` and `/api/health`. |
| `RATE_LIMIT_VERIFY` | Optional | `30 per minute` | Rate limit for `/api/scans/verify-receipt`. |
| `LOG_LEVEL` | Optional | `info` | Gunicorn and Flask log verbosity (`debug`, `info`, `warning`, `error`). |

---

## 4. Supabase Database & Storage Setup

Before deploying the backend, initialize the Supabase PostgreSQL database and private storage buckets.

### 4.1 Execute Schema Migrations

Navigate to your Supabase Project -> **SQL Editor** -> **New Query**, and execute the migration files in strict numerical order:

```text
supabase/migrations/
├── 001_initial_schema.sql                # Core tables, RLS policies, storage bucket
├── 002_rls_and_profile_fixes.sql         # Safe profile insert, grant code indexation
├── 003_doctor_registration_and_roles.sql # Clinician vetting fields, security triggers
├── 004_security_remediation_sprint1.sql  # Atomic grant claim RPC, scan immutability
└── 005_privacy_and_account_deletion.sql  # GDPR Art. 17 atomic account deletion RPC
```

#### Verification Steps:
1. Open **Table Editor** in Supabase and verify the following 5 tables exist with **RLS Enabled**:
   - `profiles`
   - `scans`
   - `clinician_access_grants`
   - `clinician_reviews`
   - `follow_up_reminders`
2. Open **Database -> Functions** and verify RPCs are registered:
   - `claim_clinician_access`
   - `generate_patient_grant`
   - `generate_patient_grant_code`
   - `redeem_clinician_grant`
   - `delete_user_account`

### 4.2 Storage Bucket Configuration (`retinal-scans`)

Migration `001_initial_schema.sql` automatically registers the storage bucket. Verify the settings in the **Storage** dashboard:

1. **Bucket Name:** `retinal-scans`
2. **Access Control:** **Private** (Public URLs disabled).
3. **Policies Active:**
   - `Patients upload own scans to storage`: Allows users to upload only to their own subfolder: `(storage.foldername(name))[1] = auth.uid()::text`.
   - `Patients read own scans from storage`: Patients can access only their own fundus images.
   - `Authorized clinicians read patient scans from storage`: Grants read access if an active, unexpired grant exists in `clinician_access_grants`.
   - `Patients delete own scan images from storage` (from 004/005): Enforces GDPR Right to Erasure.

---

## 5. Step-by-Step Render Deployment Checklist

### Step 1: Prepare Repository
Ensure `render.yaml`, `Dockerfile`, `gunicorn.conf.py`, `retfound_model.keras`, and `retfound_model.tflite` are committed to the repository main branch:
```bash
git status
# Confirm render.yaml and Dockerfile are staged and committed
```

### Step 2: Create Service on Render

#### Method A: Using Render Blueprints (Recommended / IaC)
1. Log in to [dashboard.render.com](https://dashboard.render.com/).
2. Click **New +** -> **Blueprint**.
3. Connect your GitHub repository (`diabetic` or your organization fork).
4. Render detects `render.yaml` automatically.
5. In the Blueprint initialization screen, fill in the prompted secret values:
   - `GEMINI_API_KEY`: Paste your key from Google AI Studio.
   - `SUPABASE_JWT_SECRET`: Paste your Supabase project JWT secret.
   - `SCAN_HMAC_SECRET`: (Optional) Paste any 256-bit secret string or leave blank to inherit JWT secret.
6. Click **Apply**.

#### Method B: Manual Web Service Creation
1. Click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Configure the service settings:
   - **Name:** `diabetic-retinopathy-api`
   - **Region:** `Oregon (US West)` (or closest to your Supabase region)
   - **Branch:** `main`
   - **Runtime:** `Docker`
   - **Dockerfile Path:** `./Dockerfile`
   - **Docker Context:** `.`
   - **Instance Type:** `Standard` (2 GB RAM, 1 CPU)
   - **Health Check Path:** `/health` (or `/api/health`)
4. Add Environment Variables (as listed in Section 3).
5. Click **Create Web Service**.

### Step 3: Monitor Build and Initial Startup

1. Open the **Logs** tab in Render Dashboard.
2. Verify Docker image build steps:
   - System packages installed (`curl`, `libglib2.0-0`, `libgomp1`).
   - Python packages installed from `requirements.txt`.
   - Application files copied.
   - Unprivileged `appuser` (UID 1000) configured.
3. Verify Gunicorn WSGI startup log:
   ```text
   [INFO] Gunicorn starting: workers=2, threads=4 (total capacity=8 concurrent threads), timeout=60s, keepalive=5s
   [INFO] Listening at: http://0.0.0.0:10000
   ```
4. Verify the initial health check passes:
   ```text
   Health check passed: GET /health -> HTTP 200 OK
   Service is live at https://diabetic-retinopathy-api.onrender.com
   ```

### Step 4: Verify Deployment Health via CLI

Once deployed, run health checks against the live public URL:

```bash
# Set your Render service domain
RENDER_URL="https://diabetic-retinopathy-api.onrender.com"

# 1. Test health check endpoint
curl -i -X GET "${RENDER_URL}/health"

# Expected HTTP 200 Response:
# {
#   "auth_enforced": true,
#   "gemini_configured": true,
#   "gemini_validation_enabled": true,
#   "inference_engine": "keras",
#   "model_loaded": true,
#   "model_version": "densenet121_ordinal_v1",
#   "rate_limiting_enabled": true,
#   "scan_integrity_verification": true,
#   "status": "healthy",
#   "tflite_enabled": false
# }

# 2. Test alias health check endpoint
curl -i -X GET "${RENDER_URL}/api/health"
```

### Step 5: Connect Mobile & Web Clients

Update your mobile application environment configuration:

1. In `mobile/.env`:
   ```bash
   # Point mobile app to live Render backend
   EXPO_PUBLIC_INFERENCE_API_URL=https://diabetic-retinopathy-api.onrender.com

   # Configure Supabase Cloud endpoint
   EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
   ```
2. Test end-to-end mobile inference from an iOS simulator, Android emulator, or Expo Go client.

---

## 6. Operational Runbook & Troubleshooting

### Problem 1: Container Exits Immediately with Code 137 (OOM Killer)
- **Cause:** Instance RAM exhausted during TensorFlow 2.16 initialization or Keras model loading (occurs on Free / 512MB instances).
- **Remediation:**
  1. Upgrade Render instance to **Standard (2 GB RAM)**.
  2. Or, if running on budget tier, enable TFLite runtime in Render Environment Variables:
     - `USE_TFLITE=1`
     - `GUNICORN_WORKERS=1`
     - `GUNICORN_THREADS=2`

### Problem 2: Gunicorn Worker Timeout (`[CRITICAL] WORKER TIMEOUT`)
- **Cause:** Request processing took longer than Gunicorn timeout (often due to high-resolution image upload + Gemini validation latency on slow networks).
- **Remediation:**
  1. Check `GUNICORN_TIMEOUT`: Ensure it is set to `60` seconds (default in `gunicorn.conf.py`).
  2. Check `GEMINI_TIMEOUT_SECONDS`: Set to `15` seconds so Gemini fails gracefully before Gunicorn aborts the worker.

### Problem 3: HTTP 401 Unauthorized (`Authentication configuration error`)
- **Cause:** `FLASK_ENV=production` is enabled, but `SUPABASE_JWT_SECRET` is missing, empty, or misspelled.
- **Remediation:**
  1. In Supabase Dashboard, go to **Project Settings -> API -> JWT Settings**.
  2. Copy the **JWT Secret** (not the Anon Key or Service Role Key).
  3. Paste it into the `SUPABASE_JWT_SECRET` environment variable in the Render Dashboard and trigger a redeploy.

### Problem 4: CORS Errors in Web Browser
- **Cause:** Origin not present in `ALLOWED_ORIGINS`.
- **Remediation:**
  1. Add your web client URL to `ALLOWED_ORIGINS` in Render:
     `ALLOWED_ORIGINS=https://app.yourdomain.com,https://your-app.onrender.com`
  2. Render will automatically restart the service with updated origins.

---

## 7. Security Hardening Summary

| Layer | Implementation | Verification |
| :--- | :--- | :--- |
| **Edge & Transport** | Render TLS 1.3 automated SSL termination | HTTPS enforced, HTTP auto-redirects |
| **Container Isolation** | Dedicated unprivileged user `appuser` (UID 1000) | Non-root execution, immutable filesystem |
| **Authentication** | Supabase HS256 JWT validation (`audience: authenticated`) | Fail-closed in production |
| **Model Security** | Read-only weights loaded in memory | No external model downloads at runtime |
| **Auditability** | Cryptographic HMAC-SHA256 scan receipts (`ARCH-01`) | Detects patient ID or grade tampering |
| **Denial of Service** | Flask-Limiter IP/JWT rate limits (`RATE_LIMIT_PREDICT`) | HTTP 429 upon quota exhaustion |
