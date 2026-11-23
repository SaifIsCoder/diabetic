# Healthcare Data Privacy & Protection Policy

**System:** Diabetic Retinopathy Autonomous Diagnostic System  
**Document Track:** Track 3 — Privacy & Healthcare Data Protection (Sprint 6)  
**Governing Regulations:** GDPR (Regulation (EU) 2016/679), Pakistan PECA 2016, National Health Data Protection Framework, PMDC Code of Ethics  
**Document Status:** Production Audited & Policy Enforced  
**Date:** 2026-11-22  

---

## 1. Executive Summary & Legal Framework

The Diabetic Retinopathy Diagnostic System processes sensitive patient ophthalmic biometrics, fundus imaging photographs, diagnostic predictions, and clinical second opinions. In healthcare applications, data protection is both a legal mandate and a clinical safety requirement.

This document establishes the system's end-to-end data inventory, technical and organizational security measures, data-flow boundaries, right-to-erasure workflows, and compliance alignment across international and regional Pakistani jurisdictions (specifically addressing primary eye care and clinical screening deployments in Sargodha, Punjab, Pakistan).

### 1.1 Governance Gate Status

| Compliance Dimension | Operational Status | Governance Gate |
| :--- | :--- | :--- |
| **PostgreSQL Atomic Erasure RPC** (`delete_user_account`) | Fully Implemented & Verified | **Auto-proceed** |
| **Mobile Zero-Cache Hook on Logout** (`AuthContext.tsx`) | Fully Implemented & Verified | **Auto-proceed** |
| **Mobile Account Deletion UI Binding** (`profile.tsx`) | Fully Implemented & Verified | **Auto-proceed** |
| **GDPR Art. 17 / PECA Data Mapping & Inventory** | Fully Documented | **Auto-proceed** |
| **Production Real-Patient Data Deletion** | Prohibited in Development | **BLOCKED — HUMAN APPROVAL REQUIRED** |
| **Google Cloud Vertex AI Enterprise BAA Execution** | Pending Corporate Signoff | **BLOCKED — HUMAN APPROVAL REQUIRED** |

---

## 2. Personal & Medical Healthcare Data Inventory

Every piece of data captured, stored, or processed by the system is cataloged into the inventory below with its classification, sensitivity level, retention rules, and erasure behaviors.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            HEALTH DATA INVENTORY                            │
├──────────────────────┬──────────────────────┬─────────────┬─────────────────┤
│ Data Category        │ Entity / Field       │ Sensitivity │ Erasure Rule    │
├──────────────────────┼──────────────────────┼─────────────┼─────────────────┤
│ Identity / Account   │ profiles.full_name   │ PII         │ Cascade Delete  │
│                      │ profiles.phone_number│ PII         │ Cascade Delete  │
│                      │ profiles.avatar_url  │ PII         │ Cascade Delete  │
│                      │ auth.users.email     │ PII         │ Hard Delete     │
├──────────────────────┼──────────────────────┼─────────────┼─────────────────┤
│ Clinician Credentials│ profiles.med_license │ Professional│ Cascade Delete  │
│                      │ profiles.institution │ Professional│ Cascade Delete  │
│                      │ profiles.specialty   │ Professional│ Cascade Delete  │
├──────────────────────┼──────────────────────┼─────────────┼─────────────────┤
│ Retinal Biometrics   │ scans.eye (OD/OS)    │ PHI         │ Cascade Delete  │
│ & AI Diagnosis       │ scans.grade (0..4)   │ PHI         │ Cascade Delete  │
│                      │ scans.probabilities  │ PHI         │ Cascade Delete  │
│                      │ scans.confidence     │ PHI         │ Cascade Delete  │
│                      │ scans.image_url      │ PHI         │ Cascade Delete  │
│                      │ storage.objects/scans│ Special PHI │ Physical Purge  │
├──────────────────────┼──────────────────────┼─────────────┼─────────────────┤
│ Clinical Overrides   │ clinician_reviews.*  │ Clinical PHI│ Anonymize       │
│ & Second Opinions    │ scans.clinician_notes│ Clinical PHI│ Anonymize/Purge │
├──────────────────────┼──────────────────────┼─────────────┼─────────────────┤
│ Care Continuity      │ follow_up_reminders  │ PHI         │ Cascade Delete  │
│ Access Delegation    │ clinician_access_gr. │ Token / PHI │ Revoke / Delete │
├──────────────────────┼──────────────────────┼─────────────┼─────────────────┤
│ Device Local State   │ FileSystem.cacheDir  │ PHI / Temp  │ Logout Purge    │
│                      │ SecureStore PHI keys │ PHI / Temp  │ Logout Purge    │
└──────────────────────┴──────────────────────┴─────────────┴─────────────────┘
```

### 2.1 Detailed Inventory Breakdown

1. **Patient Demographic & Account Identifiers (`public.profiles`, `auth.users`)**
   - *Fields:* `id` (UUID), `full_name`, `phone_number`, `avatar_url`, `created_at`, `updated_at`, `email` (in `auth.users`).
   - *Legal Basis:* Article 6(1)(b) GDPR (Contractual necessity) & Article 9(2)(h) (Healthcare management).
   - *Retention:* Maintained for active account lifecycle. Permanently erased upon account deletion invocation.
   - *Privacy Control:* Phone numbers masked from public clinician views (`verified_clinicians_directory`).

2. **Clinician Professional Verification Data (`public.profiles`)**
   - *Fields:* `medical_degree`, `medical_license_no`, `jurisdiction`, `institution_name`, `clinic_address_city`, `years_of_experience`, `is_verified`, `verification_status`, `verified_at`.
   - *Legal Basis:* Statutory clinical licensing requirements and patient safety auditing.
   - *Privacy Control:* Client-side role elevation prevented by BEFORE INSERT/UPDATE trigger `protect_profile_security()`.

3. **Diagnostic Retinal Scans & Machine Learning Phenotypes (`public.scans`)**
   - *Fields:* `id`, `patient_id`, `eye` (`OD` - Right, `OS` - Left, `OU` - Both), `grade` (0: None, 1: Mild, 2: Moderate, 3: Severe, 4: Proliferative), `label`, `probabilities` (JSONB array), `confidence` (numeric), `model_version`, `storage_path`, `image_url`, `patient_notes`, `is_favorite`, `created_at`, `updated_at`.
   - *Immutability Safeguard (SEC-06):* The database enforces diagnostic integrity via `trg_protect_scan_immutability`. Patients and clinicians cannot alter AI grades, model confidence, or timestamps. Only verified clinicians with an active delegation grant can append `clinician_notes`.
   - *Retention:* Erased immediately when the owning patient invokes `delete_user_account()`.

4. **Clinical Reviews & Human Second Opinions (`public.clinician_reviews`)**
   - *Fields:* `id`, `scan_id`, `clinician_id`, `confirmed_grade`, `review_notes`, `clinical_recommendation`, `created_at`.
   - *Asymmetric Retention Logic:* When a patient deletes their account, their scans are deleted, which cascades to delete all reviews. However, when a *clinician* deletes their account, the review records are **anonymized** (`clinician_id = NULL`) rather than deleted. This preserves the patient's longitudinal diagnostic history and care continuity without violating physician erasure rights.

5. **Patient-Authorized Access Grants (`public.clinician_access_grants`)**
   - *Fields:* `id`, `patient_id`, `clinician_id`, `grant_code` (ephemeral 6-character CSPRNG token), `status` (`active`, `revoked`, `expired`), `expires_at`, `created_at`.
   - *Privacy Control:* Grants expire automatically after a configurable TTL (1 to 168 hours, default 24h). Claiming codes is atomic (`claim_clinician_access`) and single-use.

6. **Longitudinal Care Reminders (`public.follow_up_reminders`)**
   - *Fields:* `id`, `patient_id`, `scan_id`, `reminder_date`, `note`, `is_completed`, `created_at`.
   - *Purpose:* Ensures patients with moderate to severe diabetic retinopathy return for surveillance or tertiary intervention.

7. **Raw Ophthalmic Fundus Photography (`storage.objects` in bucket `retinal-scans`)**
   - *Artifacts:* JPEG/PNG high-resolution fundus images stored under private path `<patient_id>/<scan_id>.<ext>`.
   - *Privacy Control:* Private bucket with strict RLS policies. Direct unauthenticated access is forbidden. Download URLs are time-limited signed URLs. Physically deleted from object storage upon account erasure.

8. **Device Local Cache & Unencrypted Ephemeral Artifacts (Client Storage)**
   - *Artifacts:* Exported PDF clinical screening summaries, camera preview frames, temporary image buffers in `FileSystem.cacheDirectory`, and session tokens in `SecureStore`.
   - *Privacy Control:* Completely purged on logout (PRIV-04).

---

## 3. End-to-End Data Flow Mapping

The diagram below illustrates the end-to-end data lifecycle across all system components, delineating trusted network boundaries, encryption standards, and external interfaces.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       END-TO-END DATA FLOW TOPOLOGY                         │
└─────────────────────────────────────────────────────────────────────────────┘

 [ Patient / Clinician Mobile Device ]
      │
      │ 1. Local Image Capture (Camera / Gallery)
      ▼
 [ Local Device Storage / Memory ]
   • Ephemeral buffer: FileSystem.cacheDirectory (Unencrypted until purged)
   • Local settings: SecureStore (Hardware-backed AES-256)
      │
      │ 2. HTTPS / TLS 1.3 (Multipart / Base64 Payload + JWT Bearer Token)
      ▼
 ┌──────────────────────────────────────────────────────────────┐
 │                      FLASK API GATEWAY                       │
 │  • Token Signature Verification (verify_auth_token)          │
 │  • Ephemeral RAM-Only Image Processing (io.BytesIO)          │
 │  • Zero Disk Caching (No file writes on backend server)       │
 └──────────────┬───────────────────────────────┬───────────────┘
                │                               │
   3. Pre-Screening Request (RAM)                │ 5. Deep Learning Inference (RAM)
      │                                         │    • DenseNet-121 Ordinal Head
      ▼                                         │    • Model: retfound_model.keras
 ┌─────────────────────────────────────────┐    │
 │       EXTERNAL AI PRE-SCREENING         │    ▼
 │       (Google Cloud Gemini API)         │ [ Local Inference Output ]
 │  • Validates Retinal Entropy/Variance   │   • Grade (0..4)
 │  • Validates Anatomical Quality         │   • Probabilities [5]
 │  • Status: CONSUMER API (NON-BAA)       │   • Confidence score
 │  • GOVERNANCE: BLOCKED — APPROVAL REQ.  │
 └─────────────────────────────────────────┘    │
                                                │ 6. JSON Response (Inference Results)
                                                ▼
 [ Patient / Clinician Mobile Device ]
      │
      │ 7. Authenticated PostgREST / Supabase Client (TLS 1.3)
      ├─────────────────────────────────────────┐
      ▼                                         ▼
 ┌───────────────────────────────────┐    ┌───────────────────────────────────┐
 │       SUPABASE POSTGRESQL 16      │    │     SUPABASE OBJECT STORAGE       │
 │  • public.profiles                │    │  • Bucket: retinal-scans (Private)│
 │  • public.scans                   │    │  • Path: <patient_id>/<file>.jpg  │
 │  • public.clinician_reviews       │    │  • Encryption: AES-256 at rest    │
 │  • public.clinician_access_grants │    │  • RLS: Patient upload & delete;  │
 │  • public.follow_up_reminders     │    │         Verified Doctor read-only │
 │  • Function: delete_user_account()│    └───────────────────────────────────┘
 └───────────────────────────────────┘
```

### 3.1 Step-by-Step Data Journey

1. **Image Ingestion:** Retinal photography is captured via a handheld fundus camera or uploaded from local media. The mobile app writes temporary buffers to `FileSystem.cacheDirectory`.
2. **Secure Transmission:** The image is transmitted over TLS 1.3 to the backend `/api/predict` endpoint accompanied by the patient's Supabase JWT Bearer token in the `Authorization` header.
3. **Authentication & Rate Limiting:** Flask verifies the HMAC-SHA256 signature against `SUPABASE_JWT_SECRET` and enforces a strict sliding rate limit (10 req/min).
4. **Pre-Screening Gate:** The image buffer is evaluated by `gemini_validator.py`. In local mode, variance and Shannon entropy are calculated. When cloud validation is active, image bytes are streamed to Gemini over HTTPS.
5. **Inference Execution:** The image is converted to RGB, resampled via LANCZOS to 224x224, normalized to `float32`, and passed to `densenet121_ordinal_v1`. Raw sigmoid outputs are thresholded at 0.5 to produce an ICDRS grade (0–4).
6. **Ephemeral Cleanup:** The Flask backend immediately discards the in-memory image buffer. No image files or logs containing patient data are written to disk.
7. **Client Persistence:** The mobile app stores the image in Supabase Storage (`retinal-scans/<patient_id>/`) and writes the diagnostic record to `public.scans`.

---

## 4. GDPR Article 17 Right to Erasure Implementation

The system implements strict compliance with GDPR Article 17 ("Right to be Forgotten") through PostgreSQL migration `005_privacy_and_account_deletion.sql`.

### 4.1 Technical Realization: `delete_user_account()` RPC

The account deletion workflow is encapsulated in an atomic PostgreSQL stored procedure:

```sql
CREATE OR REPLACE FUNCTION public.delete_user_account()
RETURNS jsonb AS $$
...
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

#### Key Architecture & Security Principles:
1. **Strict Identity Binding:** The procedure takes **zero parameters**. The target account is resolved strictly from `auth.uid()`. It is impossible for a user or malicious actor to supply an arbitrary UUID to delete another user's account (anti-BOLA protection).
2. **Privilege Elevation (`SECURITY DEFINER`):** Operates with elevated database permissions to permit cleaning up auth records and cascade tables while enforcing internal authorization checks.
3. **Asymmetric Role Handling:**
   - **For Patients:**
     - Deletes all records from `public.follow_up_reminders`.
     - Deletes all records from `public.clinician_access_grants`.
     - Deletes all records from `public.scans` (which cascades to delete any reviews on those scans).
     - Purges all files from `storage.objects` where `bucket_id = 'retinal-scans'` and folder matches `<auth.uid()>`.
     - Deletes the profile record from `public.profiles`.
     - Deletes the identity record from `auth.users`.
   - **For Clinicians:**
     - Updates `public.clinician_reviews` setting `clinician_id = NULL`. This anonymizes historical second opinions while preserving the clinical audit trail for patient safety.
     - Unassigns and revokes active grants in `public.clinician_access_grants` (`clinician_id = NULL, status = 'revoked'`).
     - Purges clinician storage objects if any exist.
     - Deletes the profile from `public.profiles`.
     - Deletes the identity record from `auth.users`.

### 4.2 Mobile UI Integration (`profile.tsx`)

In `mobile/app/(tabs)/profile.tsx`, the "Permanently Delete Account & Images" button triggers a two-tier confirmation dialog detailing the irreversible nature of medical data deletion. Upon confirmation:
1. Calls `supabase.rpc('delete_user_account')`.
2. On successful response, invokes `signOut()`.
3. Displays confirmation and routes the user to `/(auth)/login`.

---

## 5. Mobile Device Cache Purging (PRIV-04 Remediation)

### 5.1 Threat Model: Shared Community Devices
In primary healthcare screening environments in developing regions (such as mobile screening camps in Sargodha district, Punjab), clinical tablets and smartphones are frequently shared across multiple healthcare workers or used in public settings. If retinal photographs or exported PDF reports linger in local device caches, subsequent users of the device could access unencrypted Protected Health Information (PHI).

### 5.2 Remediation in `mobile/context/AuthContext.tsx`

The `clearResidualPhiCache()` function executes automatically during:
- User logout (`signOut()`).
- Supabase session invalidation (`onAuthStateChange` returning `!currentSession`).
- Successful account deletion.

#### Actions Performed:
1. **Native FileSystem:** Iterates through `FileSystem.cacheDirectory` and recursively deletes all generated files (including `clinical_retinal_summary_*.pdf`, camera temporary captures, and image pick caches).
2. **Web Browser Environment:** Purges `sessionStorage` and scrubs any PHI-related keys from `localStorage` (`scan_*`, `phi_*`, `offline_scans_*`, `report*`).
3. **SecureStore:** Deletes cached scan buffers and sensitive patient identifiers.

---

## 6. Regional Legal & Healthcare Regulatory Alignment

### 6.1 Pakistan Prevention of Electronic Crimes Act (PECA) 2016
- **Section 3 & 4 (Unauthorized Access to Information System & Data):** The system enforces strict authentication and authorization via RLS policies and cryptographic JWT verification, preventing unauthorized access to ophthalmic data.
- **Section 13 & 14 (Electronic Forgery & Fraud):** Addressed by database-enforced scan immutability (`trg_protect_scan_immutability`). Clinicians and patients cannot forge diagnostic scores or fabricate retroactive reviews.
- **Section 19 (Unauthorized Access to Sensitive Healthcare Data):** BOLA vulnerabilities eliminated via atomic RPCs (`claim_clinician_access`, `delete_user_account`).

### 6.2 Personal Data Protection Bill (PDPB) & Health Data Framework
- **Express Informed Consent:** Required before capturing retinal photography and transmitting data.
- **Purpose Limitation:** Ophthalmic scans are processed strictly for diabetic retinopathy evaluation and clinical referral.
- **Cross-Border Data Transfer:** Retinal images must not be transferred to jurisdictions lacking adequate data protection standards without explicit legal safeguards.

### 6.3 Punjab Healthcare Commission (PHC) & PMDC Code of Ethics
- **Preservation of Second Opinions:** Medical ethics require that once an ophthalmologist renders a clinical second opinion, the patient's medical chart must retain that opinion. The system reconciles this with privacy law by **anonymizing** clinician reviews upon doctor account deletion (`clinician_id = NULL`), ensuring the diagnosis remains intact while clinician PII is removed.
- **Doctor Verification Standards:** Unverified clinician accounts cannot submit clinical notes or second opinions until administrative review is approved (`is_verified = TRUE`).

---

## 7. Third-Party AI Services & Enterprise Compliance Roadmap

### 7.1 Current Pre-Screening Architecture
The system integrates an optional pre-screening stage via `gemini_validator.py` to filter non-fundus or degraded images before running deep learning inference:

```
[Input Image] ──► [Entropy / Variance Filter] ──► [Gemini Cloud API] ──► [DenseNet-121]
```

### 7.2 Privacy Risk: Consumer vs. Enterprise API (PRIV-01 / PRIV-05)
- **Current State:** The development prototype utilizes Google Gemini developer API keys (`GEMINI_API_KEY`). Under Google's consumer API terms, data transmitted could potentially be logged or evaluated unless covered by enterprise agreements.
- **Regulatory Requirement:** In a clinical healthcare environment, transmitting biometric retinal images to third-party cloud infrastructure requires a legally binding **Business Associate Agreement (BAA)** under HIPAA and equivalent data processing addenda under GDPR.

### 7.3 Governance Gate: BLOCKED — HUMAN APPROVAL REQUIRED

```
================================================================================
                    GOVERNANCE GATE: THIRD-PARTY AI BAA
================================================================================
  Action:        Execution of Enterprise Business Associate Agreement (BAA)
                 with Google Cloud Vertex AI and migration of inference endpoints.
  Status:        BLOCKED — HUMAN APPROVAL REQUIRED
  Rationale:     Requires commercial licensing, legal signatory authorization,
                 and paid cloud tier provisioning.
  Current State: Retinal pre-screening uses local heuristic variance/entropy
                 checks as the primary gate; external cloud validation is
                 disabled by default in test/staging without approved BAA.
================================================================================
```

### 7.4 On-Premise / Edge Alternative Roadmap
To achieve 100% data sovereignty and eliminate external cloud dependencies for rural Pakistani clinics:
1. Replace cloud pre-screening with a lightweight, containerized edge classifier (e.g. MobileNetV3 trained to distinguish retinal fundus vs non-fundus).
2. Host the entire inference pipeline on local hospital server hardware or offline edge devices.

---

## 8. Verification & Auditing Procedures

### 8.1 Database Erasure Verification
To independently verify that account deletion functions correctly without residual records:
1. Create a synthetic patient account and submit 2 test scans with 1 follow-up reminder.
2. Authenticate as the patient and call `SELECT public.delete_user_account();`.
3. Verify that `public.profiles`, `public.scans`, `public.follow_up_reminders`, and `public.clinician_access_grants` return 0 rows for that `user_id`.
4. Verify that `storage.objects` contains 0 objects for that user folder.

### 8.2 Clinician Anonymization Verification
1. Create a synthetic clinician account and submit a clinical review on a test scan.
2. Authenticate as the clinician and call `SELECT public.delete_user_account();`.
3. Verify that the scan's review in `public.clinician_reviews` remains intact with `clinician_id IS NULL`.
4. Verify that the clinician's profile row in `public.profiles` is deleted.

### 8.3 Mobile Cache Purging Verification
1. Generate a PDF report in the mobile app.
2. Verify file creation in `FileSystem.cacheDirectory`.
3. Call `signOut()`.
4. Inspect `FileSystem.cacheDirectory` to verify zero PDF or image files remain.

---

*This document is maintained under autonomous swarm governance for Track 3 (Sprint 6). Any modification to data retention periods, cloud API providers, or deletion cascades requires explicit architectural and compliance approval.*
