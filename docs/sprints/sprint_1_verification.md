# Sprint 1 Verification & Reproduction Report

**Target Project:** Diabetic Retinopathy Diagnostic Application (`s:/unimate/diabetic`)  
**Phase:** Phase 2 — Controlled Remediation Sprint 1  
**Lead Verifiers:** Application Security Auditor (`@security`), Independent QA Agent (`@qa`), Privacy Auditor (`@privacy`)  
**Status:** **ALL 10 TARGET FINDINGS REPRODUCED & CONFIRMED IN BASELINE**

---

## 1. Executive Summary

In accordance with Step 1 of the Sprint 1 Protocol, before any source code or database migrations were applied, an independent verification team consisting of the Security Agent, Database Agent, Backend Agent, Privacy Agent, and Independent QA Agent re-examined the codebase at branch `sprint-1-security-remediation` (forked from `main`).

Every target finding was located in source code, experimentally reproduced, and assessed for architectural dependencies, safest remediation strategies, and potential regression vectors.

---

## 2. Detailed Reproduction of Audit Findings

### 2.1 SEC-01: BOLA in Clinician Grant Claim
- **Original Finding:** Row-Level Security policy on `clinician_access_grants` permits any authenticated clinician to claim any active patient grant without providing the authorization code.
- **Exact Implementation Location:** [003_doctor_registration_and_roles.sql:147-163](file:///s:/unimate/diabetic/supabase/migrations/003_doctor_registration_and_roles.sql#L147-L163)
- **Baseline Confirmation:** Confirmed. The policy `Clinicians claim active grant with code` evaluated `USING (status = 'active' AND expires_at > NOW() AND clinician_id IS NULL) WITH CHECK (clinician_id = auth.uid())`. Notice that `grant_code` was never evaluated in either `USING` or `WITH CHECK`. Any authenticated user with role `clinician` could execute `UPDATE clinician_access_grants SET clinician_id = auth.uid()` and take ownership of all unassigned grants across all patients.
- **Affected Dependencies:** `mobile/app/(tabs)/clinicians.tsx` (delegation flow), `supabase/migrations/001_initial_schema.sql`, `003_doctor_registration_and_roles.sql`.
- **Safest Remediation:** Drop the permissive table-level `UPDATE` policy entirely. Implement an atomic PostgreSQL `SECURITY DEFINER` function `claim_clinician_access(p_code TEXT)` with row-level locking (`SELECT ... FOR UPDATE`), matching code, single-use nullification, and non-expiration checks.
- **Potential Regressions:** Mobile client calling `.update()` directly on `clinician_access_grants` fails with RLS error if not updated to invoke `.rpc('claim_clinician_access')`.

---

### 2.2 SEC-02: Authentication Bypass / Fail-Open When `SUPABASE_JWT_SECRET` Is Unset
- **Original Finding:** Backend prediction endpoint allows unauthenticated inference if `SUPABASE_JWT_SECRET` is unset; mobile client never sends JWT Authorization headers.
- **Exact Implementation Location:** [app.py:178-183](file:///s:/unimate/diabetic/app.py#L178-L183)
- **Baseline Confirmation:** Confirmed. `verify_auth_token()` explicitly executed:
  ```python
  if not SUPABASE_JWT_SECRET:
      return True, None  # Dev bypass
  ```
  In local/staging environments or if the secret was omitted, all authentication was disabled, returning `(True, None)`.
- **Affected Dependencies:** `app.py:api_predict`, mobile client `mobile/constants/api.ts`, `mobile/app/(tabs)/index.tsx`.
- **Safest Remediation:** Enforce fail-closed behavior. If `is_production()` or `is_auth_enforced()` is active, missing JWT secret or missing/invalid/expired Bearer tokens return HTTP 401 Unauthorized.
- **Potential Regressions:** Automated tests without mock JWTs fail with HTTP 401; local dev environments require explicit setting of dev secret or mock token.

---

### 2.3 ARCH-01 / SEC-06: Client-Side Scan Record Persistence & Record Mutation
- **Original Finding:** Mobile client directly persists AI diagnosis grades to `scans` table from device without server integrity verification; existing RLS policy allows patients to update diagnostic grades.
- **Exact Implementation Location:** [mobile/app/(tabs)/index.tsx:212-224](file:///s:/unimate/diabetic/mobile/app/(tabs)/index.tsx#L212-L224) and [001_initial_schema.sql:124-127](file:///s:/unimate/diabetic/supabase/migrations/001_initial_schema.sql#L124-L127)
- **Baseline Confirmation:** Confirmed. After receiving inference response from `api.predictImage()`, mobile client constructed scan record and performed `supabase.from('scans').insert(...)`. A malicious client or network proxy could tamper with `grade`, `confidence`, and `probabilities`. Furthermore, the policy `Patients update own scans` permitted updating all columns on existing scans.
- **Affected Dependencies:** `mobile/app/(tabs)/index.tsx`, `mobile/app/(tabs)/history.tsx`, `supabase/migrations/001_initial_schema.sql`.
- **Safest Remediation:** 
  1. Backend generates an HMAC-SHA256 tamper-evident receipt binding `image_sha256`, `grade`, `probabilities`, and `patient_id`.
  2. Database trigger `protect_scan_immutability()` blocks updates to `grade`, `confidence`, `image_url`, `created_at`, and `patient_id`.
- **Potential Regressions:** Legitimate updates to patient notes could be blocked if trigger is overly broad. Remediation explicitly allows updating `clinician_notes` for verified doctors and `patient_notes` for patients.

---

### 2.4 SEC-03: CORS Origin Wildcard Reflection with Credentials Enabled
- **Original Finding:** Flask CORS configuration reflects incoming caller origin with `Access-Control-Allow-Credentials: true`.
- **Exact Implementation Location:** [app.py:206](file:///s:/unimate/diabetic/app.py#L206)
- **Baseline Confirmation:** Confirmed. `CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)` combined with dynamic origin reflection allowed arbitrary cross-origin sites (e.g. `evil.com`) to make authenticated requests and read responses.
- **Affected Dependencies:** `app.py`, all web/mobile API clients.
- **Safest Remediation:** Eliminate wildcard reflection with credentials. Maintain a strict whitelist of permitted origins (`ALLOWED_ORIGINS`) including local Expo bundlers (`http://localhost:8081`), web dev ports, and production mobile schemes. Reject unlisted origins without CORS headers.
- **Potential Regressions:** Local Expo development from non-standard ports (e.g. 19000, 8082) could receive CORS blocks if not added to `ALLOWED_ORIGINS`.

---

### 2.5 SEC-04: Unverified Clinicians Access Medical Records
- **Original Finding:** Clinicians with `is_verified = FALSE` can view delegated patient scans and download raw retinal imagery.
- **Exact Implementation Location:** [001_initial_schema.sql:132-142, 211-222](file:///s:/unimate/diabetic/supabase/migrations/001_initial_schema.sql#L132-L142)
- **Baseline Confirmation:** Confirmed. The SELECT policy `Authorized clinicians view patient scans` only checked `EXISTS (SELECT 1 FROM clinician_access_grants WHERE ... clinician_id = auth.uid())` without verifying `clinician_profiles.is_verified = TRUE`. Any self-registered doctor account could view and export retinal images prior to admin credential verification.
- **Affected Dependencies:** `supabase/migrations/001_initial_schema.sql`, `003_doctor_registration_and_roles.sql`, `mobile/app/(tabs)/clinicians.tsx`.
- **Safest Remediation:** Update `scans` SELECT and `storage.objects` SELECT policies to join `profiles` / `clinician_profiles` and strictly require `p.is_verified = TRUE`.
- **Potential Regressions:** Newly registered doctors cannot see test scans until an administrator or fixture marks their account `is_verified = TRUE`.

---

### 2.6 SEC-07: Complete Absence of API Rate Limiting
- **Original Finding:** Zero rate limiting on compute-intensive TensorFlow DenseNet inference and paid Google Gemini API triage gate.
- **Exact Implementation Location:** [app.py](file:///s:/unimate/diabetic/app.py)
- **Baseline Confirmation:** Confirmed. No rate-limiting middleware or decorators existed on `/api/predict`, `/predict`, or `/api/health`. An automated script could flood the endpoint, exhausting cloud billing quotas and triggering container CPU starvation.
- **Affected Dependencies:** `app.py`, `requirements.txt`.
- **Safest Remediation:** Integrate `Flask-Limiter` with in-memory or Redis storage, keying on authenticated user ID (`sub`) with fallback to client IP. Configure tiered limits: 10/min on `/api/predict`, 60/min on `/api/health`, 30/min on `/api/scans/verify`.
- **Potential Regressions:** Rapid manual testing or burst testing could trigger HTTP 429 Too Many Requests if limits are too restrictive. Tests must be aware of limits.

---

### 2.7 SEC-08: Weak Client-Side Pseudo-Random Grant Code Generation
- **Original Finding:** 6-character alphanumeric grant code generated client-side with `Math.random()`, vulnerable to brute force and collision.
- **Exact Implementation Location:** [mobile/app/(tabs)/clinicians.tsx:348](file:///s:/unimate/diabetic/mobile/app/(tabs)/clinicians.tsx#L348)
- **Baseline Confirmation:** Confirmed. Client executed `Math.random().toString(36).substring(2, 8).toUpperCase()`, yielding only ~810,000 combinations without cryptographic randomness, and stored directly into database.
- **Affected Dependencies:** `mobile/app/(tabs)/clinicians.tsx`, `supabase/migrations/001_initial_schema.sql`.
- **Safest Remediation:** Move grant code generation to a database `SECURITY DEFINER` RPC function `generate_patient_grant_code()` utilizing `extensions.gen_random_bytes(6)` across a 32-character keyspace with zero modulo bias.
- **Potential Regressions:** Mobile client must invoke `.rpc('generate_patient_grant_code')` instead of local string generation.

---

### 2.8 PRIV-01: Unprotected Biometric PHI Transmission to Consumer Gemini API
- **Original Finding:** Full raw retinal fundus image bytes transmitted to Google Gemini consumer API without HIPAA Business Associate Agreement (BAA).
- **Exact Implementation Location:** [app.py:361](file:///s:/unimate/diabetic/app.py#L361) and [gemini_validator.py:251-325](file:///s:/unimate/diabetic/gemini_validator.py#L251-L325)
- **Baseline Confirmation:** Confirmed. Full image buffer is encoded and sent to `gemini-3.1-flash-lite` via `google.genai` SDK using an API key from Google AI Studio. Google AI Studio terms permit logging and human evaluation.
- **Affected Dependencies:** `gemini_validator.py`, `app.py`.
- **Safest Remediation:** Document Vertex AI enterprise BAA migration requirement; add configurable fallback to local validation mode; implement storage DELETE policy for GDPR right-to-erasure.
- **Potential Regressions:** Disabling Gemini API in environments without Vertex AI configuration requires a validated local classifier fallback.

---

### 2.9 PR-08: Live Gemini API Key Committed in Repository Root `.env`
- **Original Finding:** Active plaintext Google Gemini API key committed in repository `.env` file.
- **Exact Implementation Location:** Root [.env:5](file:///s:/unimate/diabetic/.env#L5)
- **Baseline Confirmation:** Confirmed. Active credential `[REVOKED_KEY_REDACTED_P9rw]` was present in plaintext in root `.env`.
- **Affected Dependencies:** Root `.env`, `.env.example`, Git history.
- **Safest Remediation:** Purge key from `.env`, set `GEMINI_API_KEY=`, add rotation notice and Secret Manager guidance in `.env.example`, rotate key in Google Cloud Console.
- **Potential Regressions:** Local manual testing fails if developer does not supply a personal development key.

---

## 3. Verification Sign-Off

All 10 findings were unanimously verified by the independent verification panel. Implementation proceeded according to priority under the Change Control Plan.
