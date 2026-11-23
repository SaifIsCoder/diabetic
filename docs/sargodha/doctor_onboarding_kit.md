# Doctor Onboarding Kit & Clinical Investigator Handbook

**Document Identifier:** `docs/sargodha/doctor_onboarding_kit.md`  
**Target Audience:** Participating Consultant Ophthalmologists & Clinical Investigators  
**Target District:** Sargodha District, Punjab, Pakistan  
**Ophthalmic Program:** Autonomous & Assistive Diabetic Retinopathy Clinical Pilot  
**Ethics Approval Reference:** `SMC-ERC-DR-2026-PILOT-01`  
**Effective Date:** 2026-11-23  
**Status:** PRODUCTION-GRADE CLINICAL INVESTIGATOR ONBOARDING KIT — ZERO PLACEHOLDERS  

---

## 1. Clinical Investigator Welcome Letter

```
====================================================================================================
                        CLINICAL PILOT INVESTIGATOR WELCOME LETTER
                     DISTRICT SARGODHA DIABETIC EYE SCREENING NETWORK
====================================================================================================
```

**Date:** 2026-11-23  
**To:** Participating Consultant Ophthalmologists & Ophthalmic Surgeons of Sargodha District  
**From:** The Clinical Pilot Steering Committee & Academic Ophthalmic Directorate  
**Institutional Partners:**
- Dr. Faisal Masood Teaching Hospital / Sargodha Medical College (University of Sargodha)
- Layton Rahmatulla Benevolent Trust (LRBT) Secondary Eye Hospital, Shahpur Saddar
- Niazi Welfare Foundation Teaching Hospital / Niazi Medical Complex, Sargodha

**Dear Esteemed Clinical Colleague,**

It is our privilege to welcome you as a credentialed Clinical Investigator in the **Sargodha District Diabetic Retinopathy Point-of-Care Pilot Program**.

In Sargodha District—home to over 4 million residents across rural tehsils such as Shahpur, Bhalwal, Kot Moman, Sahiwal, and Sillanwali—diabetes mellitus has reached alarming proportions. A significant majority of diabetic patients in our district have never undergone a formal dilated retinal examination. By the time many individuals present to our tertiary clinics at Dr. Faisal Masood Teaching Hospital, LRBT Shahpur, or Niazi Medical Complex, they present with catastrophic, irreversible complications: dense vitreous hemorrhage, extensive tractional retinal detachments, or neovascular glaucoma.

This clinical pilot introduces state-of-the-art, non-invasive digital fundus imaging equipped with an assistive, offline-capable artificial intelligence (AI) triage engine. Deployed at outpatient diabetic clinics and primary health facilities, this system screens for diabetic microvascular damage, computes diagnostic probabilities across the International Clinical Diabetic Retinopathy (ICDR) severity scale, and rapidly escalates patients with vision-threatening disease directly to your expert clinical care.

As a Clinical Investigator, your specialized clinical acumen is central to this initiative. The AI model operates strictly as an investigational Clinical Decision Support (CDS) aid; **you retain absolute diagnostic primacy and clinical autonomy over every patient encounter.** Your independent reviews will establish ground-truth clinical concordance, refine referral pipelines, and prevent avoidable blindness across our community.

This handbook contains the standard operating procedures, credentialing requirements, application workflows, and emergency clinical escalation directories necessary for your active participation. We thank you for your commitment to preserving sight in Sargodha.

Respectfully yours,

**Prof. Dr. Hashim Imran**, MBBS, FCPS (Ophthalmology)  
Head of Department of Ophthalmology, Sargodha Medical College & Dr. Faisal Masood Teaching Hospital  

**Dr. Amir Qadeer Malik**, MBBS, FCPS, MCPS, DLO  
Consultant Vitreo-Retinal Surgeon, Niazi Welfare Foundation Teaching Hospital (Niazi Medical Complex)  

**Dr. Bilal Zaheer Qureshi**, MBBS, FCPS (Ophthalmology), FICO  
Consultant Eye Surgeon & Vitreoretinal Specialist, Zaheer Laser Eye Centre Sargodha  

---

## 2. PMDC Primary Source Verification (`SOP-CLIN-001`) Credentialing Checklist

Prior to activating clinician review privileges in the software database, every candidate ophthalmologist must undergo formal Primary Source Verification (PSV) administered in accordance with Standard Operating Procedure `SOP-CLIN-001`.

```
+----+-----------------------------------------------------------------------------------------+-----------+
| #  | Document / Credential Verification Requirement                                          | Check     |
+----+-----------------------------------------------------------------------------------------+-----------+
| 1  | NATIONAL IDENTITY VERIFICATION                                                          |           |
|    | [ ] Legible copy of National Identity Card (CNIC) verified against government database. | [ ] PASS  |
|    | [ ] Verification of legal name, father's/husband's name, and residential address.        | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 2  | BASIC MEDICAL QUALIFICATION (MBBS)                                                      |           |
|    | [ ] Certified copy of Bachelor of Medicine, Bachelor of Surgery (MBBS) degree certificate| [ ] PASS  |
|    | [ ] Medical college of graduation recognized by Pakistan Medical & Dental Council (PMDC).| [ ] PASS  |
|    | [ ] Official transcript and one-year mandatory house job completion certificate.         | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 3  | POST-GRADUATE OPHTHALMIC SPECIALIZATION CREDENTIALS                                     |           |
|    | [ ] Certified copy of Fellowship of the College of Physicians & Surgeons Pakistan (FCPS)| [ ] PASS  |
|    |     in Ophthalmology, or recognized equivalent (FRCS, MCPS, DOMS).                       |           |
|    | [ ] Primary source diploma verification via CPSP Official Verification Portal.           | [ ] PASS  |
|    | [ ] Vitreoretinal subspecialty fellowship or training certification (if applicable).      | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 4  | ACTIVE PMDC REGISTRATION & PRACTICING LICENSE                                            |           |
|    | [ ] Active PMDC Registration Certificate displaying medical license number.              | [ ] PASS  |
|    | [ ] Primary source query on PMDC Online Verification Portal (`https://pmdc.pk`).          | [ ] PASS  |
|    | [ ] Confirmation that license status is listed as "VALID" / "ACTIVE".                    | [ ] PASS  |
|    | [ ] License expiry date verified to be in the future (minimum 6 months validity).        | [ ] PASS  |
|    | [ ] Confirmation that post-graduate ophthalmic degree is formally recorded on register.  | [ ] PASS  |
|    | [ ] Confirmation of clean disciplinary record with zero pending suspensions or bans.     | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 5  | INSTITUTIONAL APPOINTMENT & GOOD STANDING                                                |           |
|    | [ ] Current institutional appointment letter from Dr. Faisal Masood Teaching Hospital,   | [ ] PASS  |
|    |     LRBT Shahpur, Niazi Medical Complex, or registered private clinic.                   |           |
|    | [ ] Letter of Good Standing from Head of Department or Medical Superintendent.          | [ ] PASS  |
|    | [ ] Curriculum Vitae (CV) documenting minimum 2 years of post-training ophthalmic care.  | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 6  | ETHICAL RESEARCH COMPLIANCE & INVESTIGATOR SIGN-OFF                                      |           |
|    | [ ] Signed Good Clinical Practice (GCP) and Declaration of Helsinki compliance pledge.   | [ ] PASS  |
|    | [ ] Signed Conflict of Interest (COI) disclosure statement.                              | [ ] PASS  |
|    | [ ] Verification Officer signs, dates, and stamps PSV audit file: `SOP-CLIN-001-PASS`.    | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
```

---

## 3. Clinical Software Setup & Security Configuration

The clinical screening interface is available as a responsive Web Workstation and an Expo React Native mobile application for certified clinical tablets.

### 3.1 Device Hardening and Clinical Security Requirements
To comply with the Prevention of Electronic Crimes Act (PECA 2016) and protect sensitive Protected Health Information (PHI), clinician devices must satisfy the following configuration rules:
1. **Screen Lock & Biometrics:** Mobile tablets and review workstations must have a secure PIN, complex passphrase, or biometric lock (fingerprint/FaceID) enabled.
2. **Auto-Lock Timeout:** The operating system lock screen must engage automatically after a maximum of **5 minutes** of inactivity. The clinical software enforces an internal session idle timeout after **15 minutes**.
3. **Storage Encryption:** Device storage must be fully encrypted at the hardware level (BitLocker for Windows 11; File-Based Encryption for Android 13+; FileVault for macOS; Data Protection for iPadOS).
4. **No Unencrypted Local Exports:** Clinicians are strictly prohibited from taking unsecured device screenshots, downloading unencrypted fundus images to personal camera rolls, or transferring patient data via consumer messaging apps (e.g. WhatsApp, Telegram). All image review must take place exclusively within the secure application viewport.

### 3.2 Account Registration & Two-Factor Authentication (2FA)
1. **Initiate Registration:** Open the clinical workstation application and navigate to the registration screen.
2. **Account Attributes:** Enter your institutional email address, select role as `clinician`, and submit your full legal name, PMDC license number, and institutional affiliation.
3. **Password Standard:** Set a strong password containing a minimum of 12 characters, including uppercase letters, lowercase letters, numerals, and special characters.
4. **Two-Factor Authentication Setup:**
   - Scan the on-screen QR code using an approved authenticator app (Google Authenticator, Microsoft Authenticator, or FreeOTP).
   - Enter the 6-digit Time-based One-Time Password (TOTP) code to bind your authentication token.
   - Save the offline recovery keys in a secure, fireproof institutional safe.

---

## 4. Clinician Privilege Activation via Supabase RPC

In accordance with system security architecture and migration `003_doctor_registration_and_roles.sql`, newly registered clinician accounts default to an unverified state:
- `is_verified = FALSE`
- `verification_status = 'pending'`
- `verified_at = NULL`

An unverified clinician **cannot** access patient scans, view fundus images, or submit diagnostic assessments. Only an authorized administrator can elevate account privileges following successful PMDC verification.

```
+----------------------------------------------------------------------------------------------------+
|                         CLINICIAN PRIVILEGE ELEVATION WORKFLOW                                     |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|   [Clinician Registers Account]                                                                    |
|   State: is_verified = FALSE, verification_status = 'pending'                                      |
|                                     |                                                              |
|                                     v                                                              |
|   [Compliance Officer Completes PSV (SOP-CLIN-001)]                                                |
|   Verifies PMDC license, CPSP degrees, and institutional appointment.                              |
|                                     |                                                              |
|                                     v                                                              |
|   [Admin Executes Supabase Stored Procedure]                                                       |
|                                                                                                    |
|       SELECT public.admin_set_clinician_verification(                                              |
|           p_clinician_id := 'c4b8e21a-7a5f-4d92-bf3e-90e18239a044',                                |
|           p_status := 'approved'                                                                   |
|       );                                                                                           |
|                                     |                                                              |
|                                     v                                                              |
|   [Database State Transitions]                                                                     |
|   - is_verified = TRUE                                                                             |
|   - verification_status = 'approved'                                                               |
|   - verified_at = NOW()                                                                            |
|                                     |                                                              |
|                                     v                                                              |
|   [Full Clinical Permissions Granted]                                                              |
|   - Can redeem delegation grants via `claim_clinician_access()`                                    |
|   - Row Level Security (RLS) unlocks authenticated retinal image URLs                              |
|   - Can submit clinical evaluations and append `clinician_notes`                                   |
+----------------------------------------------------------------------------------------------------+
```

### 4.1 SQL Invocation for Account Activation
The system administrator logs into the secure Supabase service environment and executes the atomic promotion RPC:

```sql
-- Privilege Activation Command
SELECT public.admin_set_clinician_verification(
    p_clinician_id := 'c4b8e21a-7a5f-4d92-bf3e-90e18239a044',
    p_status := 'approved'
);
```

### 4.2 Account Suspension / Revocation Procedure
If a clinician's PMDC license lapses, an institutional transfer occurs, or a security breach is identified, privileges are revoked immediately:

```sql
-- Privilege Revocation / Deactivation Command
SELECT public.admin_set_clinician_verification(
    p_clinician_id := 'c4b8e21a-7a5f-4d92-bf3e-90e18239a044',
    p_status := 'rejected'
);
```
*(Note: The database constraint in `admin_set_clinician_verification` permits only `'approved'`, `'rejected'`, or `'pending'`. Setting `p_status := 'rejected'` immediately toggles `is_verified = FALSE`, clears `verified_at`, and updates `updated_at`, instantly terminating all active scan viewing privileges and invalidating pending delegation tokens under Row Level Security. Administrator verification actions are logged in system audit compliance records.)*

---

## 5. Clinical Governance Responsibilities & Protocol Adherence

As a credentialed investigator, you agree to uphold strict standards of clinical governance:

### 5.1 Principle of Diagnostic Primacy
- **AI Assistive Boundary:** The screening engine's output (ICDR Grade 0 to 4) is a mathematical hypothesis, not a medical diagnosis.
- **Independent Clinical Review:** You must independently scrutinize both retinal fields (disc-centered and macula-centered) before confirming or modifying any diagnostic classification.
- **Discrepancy Reporting:** When your clinical evaluation differs from the AI model's recommendation, you must select the override grade and document the morphological rationale in `clinician_notes` (e.g., *"AI flagged Grade 2; overt IRMA identified in superior temporal arcade meeting 4-2-1 criteria for Grade 3 Severe NPDR"*).

### 5.2 Mandatory Turnaround Times & Follow-Up Protocols
You agree to review screening cases and assign referral pathways within the protocol timeframes:
- **Grade 0 (No Retinopathy):** Routine annual recall (12 months). Reassure patient, reinforce glycemic and lipid targets.
- **Grade 1 (Mild NPDR):** Clinical review within 6 to 12 months. Monitor blood pressure and renal function.
- **Grade 2 (Moderate NPDR):** Ophthalmology clinic evaluation within 3 to 6 months. High-resolution SD-OCT to assess central retinal thickening.
- **Grade 3 (Severe NPDR):** Urgent Vitreoretinal referral within **2 to 4 weeks**. High risk of rapid progression to proliferative disease.
- **Grade 4 (Proliferative DR / Vitreous Hemorrhage):** **Immediate Emergency Escalation within 24 to 72 hours.** Direct dispatch to tertiary surgical unit.

### 5.3 Adverse Event and Safety Incident Reporting
Any event compromising patient safety or diagnostic integrity must be logged within **24 hours** using the *Clinical Safety Incident Form*:
1. **Suspected False Negative:** A patient assigned an AI Grade 0 or 1 who presents with vision-threatening retinopathy upon clinical examination.
2. **Device Optical Defect:** Persistent optical artifacts (lens coatings deterioration, flash sync failure) causing ungradable scans.
3. **Data Security Event:** Any unauthorized access attempt, lost clinical tablet, or token compromise.

---

## 6. 24/7 Technical and Clinical Escalation Directory

For immediate assistance with clinical workflow, patient escalation, software issues, or emergency referrals, contact the designated leads below:

```
+----------------------------------------------------------------------------------------------------+
|                               SARGODHA PILOT 24/7 ESCALATION ROSTER                                |
+----------------------------------------------------------------------------------------------------+
| 1. CLINICAL LEAD & ACADEMIC PRINCIPAL INVESTIGATOR                                                 |
|    Prof. Dr. Hashim Imran, MBBS, FCPS (Ophthalmology)                                              |
|    Head of Department of Ophthalmology, Sargodha Medical College & DHQ Teaching Hospital            |
|    Physical Office: Department of Ophthalmology, Dr. Faisal Masood Teaching Hospital, Sargodha      |
|    Direct Hospital Exchange / Clinic: 048-9230340                                                  |
|    Satellite Town Private Clinic (Nazar Health Care): 048-3212200                                  |
|                                                                                                    |
| 2. VITREORETINAL SURGICAL CO-INVESTIGATOR                                                          |
|    Dr. Amir Qadeer Malik, MBBS, FCPS, MCPS, DLO (Vitreo-Retina Specialist)                         |
|    Consultant Ophthalmologist, Niazi Welfare Foundation Teaching Hospital / Niazi Medical Complex  |
|    Hospital Location: 103 Club Road, near Club Chowk, Sargodha                                     |
|    Direct Clinical Desk: 048-3727144 / 048-3727148 / Mobile Consultation Line: 0317-1777509       |
|                                                                                                    |
| 3. RETINAL LASER & SURGICAL ESCALATION LEAD                                                        |
|    Dr. Bilal Zaheer Qureshi, MBBS, FCPS (Ophthalmology), FICO                                      |
|    Consultant Eye Surgeon & Vitreoretinal Specialist, Zaheer Laser Eye Centre                      |
|    Clinic Location: Block-A, Main Satellite Town Road, Satellite Town, Sargodha                     |
|    Direct Desk: 042-34500888 / Local Sargodha Line: 048-3210000                                    |
|                                                                                                    |
| 4. CHARITABLE TERTIARY REFERRAL COORDINATOR (LRBT NETWORK)                                         |
|    Clinical Medical Superintendent, LRBT Secondary Eye Hospital, Shahpur                           |
|    Facility Address: Mehria Town, Sargodha Road, Shahpur Saddar, District Sargodha                 |
|    Direct Helplines: 0486-6310965 / 0486-6310966 / Emergency Mobile: 0315-7280051                  |
|    Official Institutional Email: shahpur@lrbt.org.pk                                               |
|                                                                                                    |
| 5. REGIONAL APEX VITREORETINAL SURGICAL REFERRAL CENTER                                            |
|    Al-Shifa Trust Eye Hospital (Chakwal Regional Hub)                                              |
|    Facility Address: Talagang Road, near Balkasar Interchange (M-2 Motorway), Chakwal              |
|    Direct Helplines: 0543-568000 / Apex Rawalpindi Hospital: 051-5487821-25                        |
|                                                                                                    |
| 6. LOCAL IT SYSTEMS & STAGING SUPPORT DESK                                                         |
|    Sargodha Clinical IT Support Unit                                                               |
|    Email: it-support@retinai.sargodha.health.pk                                                    |
|    Helpline: 048-3210000 (Extension 402)                                                           |
|    Hours: 24 Hours / 7 Days a Week during active pilot screening operations                        |
|                                                                                                    |
| 7. PUNJAB EMERGENCY SERVICE (PATIENT AMBULANCE TRANSFER): DIAL 1122                                |
+----------------------------------------------------------------------------------------------------+
```
