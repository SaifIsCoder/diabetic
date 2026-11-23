# Sprint 1 Changes & Implementation Manifest

**Target Project:** Diabetic Retinopathy Diagnostic System (`s:/unimate/diabetic`)  
**Sprint:** Sprint 1 — Security, Privacy & Integrity Remediation  
**Branch:** `sprint-1-security-remediation`  
**Status:** **IMPLEMENTATION COMPLETE & VERIFIED**

---

## 1. Summary of Changes

During Sprint 1, targeted remediations were implemented to resolve 10 critical and high-severity security vulnerabilities (`SEC-01`, `SEC-02`, `ARCH-01`, `SEC-03`, `SEC-04`, `SEC-06`, `SEC-07`, `SEC-08`, `PRIV-01`, and `PR-08`).

Modifications followed the Change Control Plan:
- Single implementation ownership per shared module.
- Server-side authorization as the primary security boundary.
- No editing of historical migrations; all database changes consolidated in a new forward migration: `004_security_remediation_sprint1.sql`.
- Zero hardcoded credentials or test data.

---

## 2. File-by-File Changes

### 2.1 Database Migration: `supabase/migrations/004_security_remediation_sprint1.sql` (NEW)
**Owner:** Database Agent (`@database`)
- **SEC-01 (BOLA Remediation):**
  - Executed `DROP POLICY IF EXISTS "Clinicians claim active grant with code" ON public.clinician_access_grants;`
  - Created `SECURITY DEFINER` function `claim_clinician_access(p_code TEXT)` (and alias `redeem_clinician_grant(p_code TEXT)`) that:
    - Enforces `auth.uid() IS NOT NULL` and verifies caller has `role = 'clinician'`.
    - Sanitizes and upper-cases input code.
    - Uses `SELECT ... FOR UPDATE` row-level lock.
    - Matches active, unexpired (`expires_at > NOW()`), unclaimed (`clinician_id IS NULL`) grants.
    - Atomically sets `clinician_id = auth.uid()` and sets `grant_code = NULL` (one-time use).
- **SEC-04 (Clinician Verification Enforcement):**
  - Updated `scans` table `SELECT` policy `Authorized clinicians view patient scans` to strictly require `clinician_profiles.is_verified = TRUE`.
  - Updated `storage.objects` `SELECT` policy for bucket `retinal-scans` to strictly require `clinician_profiles.is_verified = TRUE`.
- **SEC-06 & ARCH-01 (Scan Immutability & Diagnostic Protection):**
  - Added diagnostic columns to `scans`: `confidence NUMERIC`, `image_url TEXT`, `clinician_notes TEXT`, `updated_at TIMESTAMPTZ`.
  - Created database trigger `protect_scan_immutability()`:
    - Rejects client-side updates to `grade`, `confidence`, `image_url`, `created_at`, `patient_id`, `storage_path`, `label`, `probabilities`, `model_version`, or `eye`.
    - Restricts updates to `clinician_notes` strictly to verified clinicians with active grant access.
- **SEC-08 (Cryptographically Secure Grant Codes):**
  - Created `SECURITY DEFINER` function `generate_patient_grant_code(p_expires_in_hours INT DEFAULT 48)` utilizing PostgreSQL `extensions.gen_random_bytes(6)` over a 32-character keyspace (`23456789ABCDEFGHJKLMNPQRSTUVWXYZ`) with zero modulo bias.
- **GDPR Art. 17 / SEC-09 (Storage Right to Erasure):**
  - Created `storage.objects` `DELETE` policy `Patients delete own scans from storage` enabling patients to purge their own uploaded retinal scans.

---

### 2.2 Backend Application: `app.py`
**Owner:** Backend Agent (`@backend`)
- **PR-08 (Credential Sanitization):**
  - Removed plaintext API key fallback. Required key injection exclusively via environment variables.
- **SEC-02 (Fail-Closed JWT Authentication):**
  - Implemented `is_production()` and `is_auth_enforced()` helper functions.
  - Rewrote `verify_auth_token()`:
    - Rejects missing, non-Bearer, malformed, or expired JWT tokens with HTTP 401 Unauthorized.
    - Validates audience (`aud = 'authenticated'`), algorithm (`HS256`), and secret signature.
    - In production mode, missing `SUPABASE_JWT_SECRET` raises a fatal configuration error rather than falling back to unauthenticated bypass.
    - Extracts authenticated user ID (`sub`) and attaches it to request context (`g.user_id`).
- **SEC-03 (CORS Origin Whitelisting):**
  - Eliminated wildcard origin reflection with credentials.
  - Configured Flask-CORS with an explicit whitelist: `ALLOWED_ORIGINS` (supporting `http://localhost:8081`, `http://localhost:19006`, `http://localhost:3000`, `http://localhost:5000`, and `127.0.0.1` equivalents).
  - Unlisted origins receive no CORS allow headers.
- **SEC-07 (Rate Limiting with Flask-Limiter):**
  - Integrated `Flask-Limiter` with fallback keying on `g.user_id` (authenticated user) or client IP.
  - Decorated endpoints:
    - `/api/predict`: `@limiter.limit("10 per minute")`
    - `/predict`: `@limiter.limit("10 per minute")`
    - `/api/health`: `@limiter.limit("60 per minute")`
    - `/api/scans/verify-receipt`: `@limiter.limit("30 per minute")`
  - Created JSON 429 error handler returning standardized payload:
    `{"error": "Too many requests", "code": "RATE_LIMIT_EXCEEDED"}`.
- **ARCH-01 (Server-Side Scan Verification & HMAC Receipt):**
  - Added HMAC-SHA256 receipt generation inside `/api/predict` binding `image_sha256`, `grade`, `probabilities`, and `patient_id`.
  - Added `POST /api/scans/verify-receipt` endpoint to validate receipts before client persistence.
  - Added `POST /api/scans/create` endpoint for server-side persistence via Supabase service role.

---

### 2.3 Dependencies: `requirements.txt`
**Owner:** Backend Agent (`@backend`)
- Added `Flask-Limiter>=3.5.0` for rate limiting.

---

### 2.4 Environment Configurations: `.env` and `.env.example`
**Owner:** Backend Agent (`@backend`)
- **`.env`:** Cleared plaintext `GEMINI_API_KEY=` and populated with placeholder.
- **`.env.example`:** Added security warning regarding compromised key rotation and guidance for production secret injection via Google Cloud Secret Manager / Kubernetes Secrets.

---

### 2.5 Mobile Client: `mobile/app/(tabs)/clinicians.tsx`
**Owner:** Database Agent (`@database`)
- Updated delegation flow to generate grant codes via `supabase.rpc('generate_patient_grant_code')`.
- Updated clinician redemption flow to call `supabase.rpc('claim_clinician_access', { p_code: sanitizedCode })` instead of directly executing table-level `UPDATE`.
- Fallbacks gracefully to client crypto generation if RPC is temporarily unavailable.

---

### 2.6 Privacy Safeguards: `gemini_validator.py`
**Owner:** Privacy Agent (`@privacy`)
- Documented Google Cloud Vertex AI BAA compliance path.
- Enforced strict input byte sanitization and validation error classifications.
