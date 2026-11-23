# Sprint 6 Audit & Gate Check: Privacy and Healthcare Data Protection

**Sprint:** Sprint 6 (Track 3)  
**Target:** Data Inventory, GDPR Right to Erasure, Cascade Deletion RPC, Mobile Cache Purging, and Third-Party Compliance  
**Status:** **STAGE B — PLAN & GATE CHECK APPROVED**  
**Date:** 2026-11-22  

---

## 1. Confirmed Audit Scope & Baseline Defects

1. **PRIV-03: Simulated Account Deletion in `mobile/app/(tabs)/profile.tsx` & Missing Cascade RPC**
   - *Confirmed Root Cause:* Profile screen "Delete Account" button triggers a client-side alert without executing actual backend or database deletion. Database lacks an atomic `delete_user_account()` RPC that cascades across `scans`, `clinician_access_grants`, `follow_up_reminders`, and `profiles`, while preserving historical foreign key integrity on `clinician_reviews`.
   - *Proposed Remediation:* Author PostgreSQL migration `005_privacy_and_account_deletion.sql` defining `SECURITY DEFINER` function `delete_user_account()`. Wire `profile.tsx` to invoke this RPC upon user confirmation.
2. **PRIV-04: Residual Unencrypted PHI in Mobile Device Cache**
   - *Confirmed Root Cause:* Downloaded fundus images and exported PDF reports persist indefinitely in `FileSystem.cacheDirectory`.
   - *Proposed Remediation:* Add automated cache clearing hook in `mobile/context/AuthContext.tsx` on logout and after PDF sharing in `mobile/app/(tabs)/history.tsx`.
3. **PRIV-01 / PRIV-05: Third-Party AI Data Transmission & Compliance Governance**
   - *Confirmed Root Cause:* Retinal images transmitted to consumer Gemini API without BAA or patient informed consent.
   - *Proposed Remediation:* Document comprehensive data inventory, data-flow diagram, and legal/regulatory compliance roadmap in `docs/privacy_and_data_protection.md`. Gating third-party enterprise BAA execution under human approval.

---

## 2. Governance Gate Check

| Action | Nature | Gate Status |
| :--- | :--- | :--- |
| Deleting live real patient records in production | Production data | **BLOCKED — HUMAN APPROVAL REQUIRED** |
| Signing enterprise BAA with Google Cloud Vertex AI | Legal / Financial | **BLOCKED — HUMAN APPROVAL REQUIRED** |
| Forward migration `005_privacy_and_account_deletion.sql` | Local reversible migration | **Auto-proceed** |
| Wire `profile.tsx` to invoke deletion RPC for current session user | Local code & tests | **Auto-proceed** |
| Mobile cache purging on logout | Local code & tests | **Auto-proceed** |
| Privacy and data protection documentation | Documentation | **Auto-proceed** |

---

## 3. Implementation Plan & File Locks

- **Exclusive File Owner:** `Privacy & Database Engineer` (`teamwork_worker`)
- **Locked Files:**
  - `supabase/migrations/005_privacy_and_account_deletion.sql`
  - `mobile/app/(tabs)/profile.tsx`
  - `mobile/context/AuthContext.tsx`
  - `docs/privacy_and_data_protection.md`
  - `s:\unimate\diabetic\sprint_6_implementation.md`
- **Rollback Path:**
  - `git checkout -- mobile/app/(tabs)/profile.tsx mobile/context/AuthContext.tsx`
  - Delete `supabase/migrations/005_privacy_and_account_deletion.sql`, `docs/privacy_and_data_protection.md`, and `sprint_6_implementation.md`
