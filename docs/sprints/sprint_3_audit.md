# Sprint 3 Audit & Gate Check: Patient and Clinician E2E Workflows

**Sprint:** Sprint 3 (Track 3)  
**Target:** Patient Screening & Receipt Verification, Clinician Fundus Image Preview & Review Workflow  
**Status:** **STAGE B — PLAN & GATE CHECK APPROVED**  
**Date:** 2026-11-22  

---

## 1. Confirmed Audit Scope & Baseline Defects

1. **QA-01: Blind Clinician Review Modal in `mobile/app/(tabs)/clinicians.tsx`**
   - *Confirmed Root Cause:* Clinician inspection modal displays AI grades and numerical probabilities but completely lacks a fundus image viewer or preview canvas. Clinicians are forced to review blind without visual confirmation of the retina.
   - *Proposed Remediation:* Render retinal fundus image inside the inspection modal using the scan's `storage_path` or `image_url` with zoom/pan support and graceful error/placeholder handling.
2. **ARCH-02: Screening Submission Auth & Receipt Plumbing in `mobile/app/(tabs)/index.tsx`**
   - *Confirmed Root Cause:* Mobile client screening submission does not attach JWT Authorization header from active Supabase session and does not verify server HMAC scan receipt.
   - *Proposed Remediation:* Plumb `session.access_token` into inference request Authorization header; call `/api/scans/verify-receipt` to validate server authenticity before local state persistence.
3. **E2E Workflow Test Fixture Adaptation in `tests/test_e2e_workflows.py`**
   - *Confirmed Root Cause:* Preprocessing test uses flat gray block (`color=128`), which correctly trips the newly implemented Sprint 2 OOD heuristic variance filter.
   - *Proposed Remediation:* Update test fixture with synthetic retinal gradient/contrast pattern that represents valid fundus variance.

---

## 2. Governance Gate Check

| Action | Nature | Gate Status |
| :--- | :--- | :--- |
| Real patient records or clinical diagnosis | Real clinical data | **BLOCKED — HUMAN APPROVAL REQUIRED** |
| Production database modifications | Production data | **BLOCKED — HUMAN APPROVAL REQUIRED** |
| Reversible mobile component updates (`clinicians.tsx`, `index.tsx`) | Local code | **Auto-proceed** |
| Test suite fixture adaptation & execution | Local tests | **Auto-proceed** |

---

## 3. Implementation Plan & File Locks

- **Exclusive File Owner:** `Mobile & Workflow Engineer` (`teamwork_worker`)
- **Locked Files:**
  - `mobile/app/(tabs)/clinicians.tsx`
  - `mobile/app/(tabs)/index.tsx`
  - `tests/test_e2e_workflows.py`
  - `s:\unimate\diabetic\sprint_3_implementation.md`
- **Rollback Path:**
  - `git checkout -- mobile/app/(tabs)/clinicians.tsx mobile/app/(tabs)/index.tsx tests/test_e2e_workflows.py`
  - Delete `sprint_3_implementation.md`
