# Sprint 4 Audit & Gate Check: Sargodha Provider Directory & Onboarding Protocol

**Sprint:** Sprint 4 (Track 2)  
**Target:** Healthcare Provider Directory & Clinical Pilot Onboarding for Sargodha, Punjab, Pakistan  
**Status:** **STAGE B — PLAN & GATE CHECK APPROVED**  
**Date:** 2026-11-22  

---

## 1. Confirmed Audit Scope & Requirements

1. **Context & Geography:**
   - Location: Sargodha, Punjab, Pakistan.
   - Clinical Need: Diabetic retinopathy screening referral pathway to verified eye care facilities and licensed ophthalmologists.
2. **Current Baseline Defect (PROV-01):**
   - The repository lacks verified provider data for Sargodha. Previous stubs contained mock names or placeholder records without PMDC verification, verifiable addresses, or official contact channels.
3. **Research Objectives:**
   - Identify publicly verifiable hospitals, specialized eye centers, and ophthalmologists in Sargodha.
   - Record PMDC registration status, clinical qualifications, hospital affiliations, verified phone numbers, and official source URLs.
   - Mark all unconfirmed information explicitly as `UNVERIFIED`.
   - Prepare a structured, database-ready provider directory.
   - Author a clinical onboarding and outreach protocol specifying ethical governance, informed consent, and pilot requirements.

---

## 2. Governance Gate Check

| Action | Nature | Gate Status |
| :--- | :--- | :--- |
| External emails, phone calls, or messages to doctors | External outreach | **BLOCKED — HUMAN APPROVAL REQUIRED** |
| Scheduling patient appointments or making clinical commitments | Clinical commitment | **BLOCKED — HUMAN APPROVAL REQUIRED** |
| Creating or activating real doctor accounts in production | Account provisioning | **BLOCKED — HUMAN APPROVAL REQUIRED** |
| Claiming formal partnership or pilot participation | Legal / Institutional | **BLOCKED — HUMAN APPROVAL REQUIRED** |
| Read-only research from public hospital/PMDC/academic sources | Research & documentation | **Auto-proceed** |
| Structured directory markdown artifact generation | Documentation | **Auto-proceed** |
| Drafting provider onboarding and ethics protocol | Documentation | **Auto-proceed** |

---

## 3. Implementation Plan & File Locks

- **Exclusive File Owner:** `Provider Researcher` (`teamwork_worker`)
- **Locked Files:**
  - `audit/sargodha_provider_directory.md`
  - `docs/provider_onboarding_protocol.md`
- **Rollback Path:**
  - Delete `audit/sargodha_provider_directory.md` and `docs/provider_onboarding_protocol.md`
