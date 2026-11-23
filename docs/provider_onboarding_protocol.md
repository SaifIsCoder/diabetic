# Clinical Pilot Provider Onboarding Protocol & Ethical Governance Framework

**Document Identifier:** `docs/provider_onboarding_protocol.md`  
**Target Environment:** Sargodha District Clinical Pilot, Punjab, Pakistan  
**Author:** Provider Researcher (`worker_sprint4_research`)  
**Sprint:** Sprint 4 (Track 2: Healthcare Provider Directory & Clinical Pilot Preparation)  
**Date of Release:** 2026-11-22  
**Governance Status:** **MANDATORY HUMAN GATE ENFORCED — EXTERNAL OUTREACH BLOCKED**  

---

## 1. Governance Warning & Human Approval Gate

```
========================================================================================
                                 MANDATORY GOVERNANCE GATE
========================================================================================
ALL EXTERNAL OUTREACH, UNSOLICITED COMMUNICATIONS, PHONE CALLS, EMAILS, RECRUITMENT 
MESSAGES, PARTNERSHIP REPRESENTATIONS, OR DIRECT ENGAGEMENT WITH CLINICIANS OR 
INSTITUTIONS ARE STRICTLY PROHIBITED.

CURRENT STATUS: BLOCKED — HUMAN APPROVAL REQUIRED

NO PRODUCTION USER ACCOUNTS WITH CLINICAL PRIVILEGES (is_verified = TRUE) MAY BE CREATED 
OR ACTIVATED WITHOUT EXPLICIT SIGN-OFF FROM THE PRINCIPAL INVESTIGATOR AND PROJECT LEAD.
========================================================================================
```

This protocol outlines the institutional, legal, regulatory, and procedural steps required before any healthcare facility or clinician in Sargodha, Punjab, Pakistan can participate in prospective clinical evaluations of the Diabetic Retinopathy Autonomous Diagnostic System.

---

## 2. Pilot Scope & Clinical Objectives

### 2.1 Clinical Purpose
The clinical pilot aims to evaluate the real-world diagnostic concordance, usability, and referral efficacy of an AI-powered retinal screening tool deployed in primary healthcare centers and diabetic clinics in Sargodha District, establishing a verified referral pipeline to local tertiary ophthalmic facilities (e.g. DHQ Teaching Hospital Sargodha, LRBT Secondary Eye Hospital Shahpur, and Niazi Medical Complex).

### 2.2 Investigational Device Classification
The software functions as an **Investigational Clinical Decision Support / Triage Aid**, not an autonomous diagnostic device. Under the regulatory definitions established by the Drug Regulatory Authority of Pakistan (DRAP) Medical Device Rules (2017) and international equivalents (Software as a Medical Device - SaMD Class IIb):
1. The AI system provides a secondary screening triage recommendation.
2. It **does not replace** the clinical judgment of a licensed ophthalmologist.
3. Every fundus scan flagged as abnormal (DR Grades 1, 2, 3, or 4) or ungradable must undergo definitive review by an authorized clinician before clinical management decisions or laser/surgical interventions are initiated.

---

## 3. Institutional Review Board (IRB) & Ethical Governance

Before initiating provider recruitment or enrolling human subjects, formal ethical approvals must be granted by the designated Institutional Review Boards (IRBs) / Ethical Review Committees (ERCs).

```
+--------------------------------------------------------------------------------------------------+
|                            INSTITUTIONAL ETHICAL APPROVAL FLOWCHART                              |
+--------------------------------------------------------------------------------------------------+
|                                                                                                  |
|   1. Protocol Dossier Formulation                                                                |
|      (Investigator's Brochure, Clinical Protocol, Bilingual Patient Consent, DPIA)               |
|                                    |                                                             |
|                                    v                                                             |
|   2. Primary Institutional Ethical Review Committee (ERC)                                        |
|      * Sargodha Medical College / Dr. Faisal Masood Teaching Hospital ERC                        |
|      * University of Sargodha (UOS) Research Ethics Board                                        |
|                                    |                                                             |
|                                    v                                                             |
|   3. Multi-Center Institutional Memoranda of Understanding (MoUs)                                |
|      * Formal agreement with DHQ Teaching Hospital / Punjab Health Dept                          |
|      * Tertiary partner MoUs: LRBT Secondary Eye Hospital Shahpur & Niazi Medical Complex        |
|                                    |                                                             |
|                                    v                                                             |
|   4. Human Sign-Off & Regulatory Dossier Archival                                                |
|      (Human Gate Cleared -> Transition from BLOCKED to APPROVED)                                 |
+--------------------------------------------------------------------------------------------------+
```

### 3.1 Required Institutional Approvals
1. **Primary Academic IRB / ERC:**  
   Ethical Review Committee, Sargodha Medical College (SMC) / Dr. Faisal Masood Teaching Hospital, Sargodha.
2. **University Ethics Review Board:**  
   Institutional Bioethics Committee, University of Sargodha (UOS).
3. **Partner Institutional Permissions:**  
   Administrative approval and clinical trial data agreements with participating trust and private complexes:
   - Layton Rahmatulla Benevolent Trust (LRBT) Clinical Research Committee (for Shahpur facility).
   - Niazi Medical & Dental College Institutional Ethical Committee.
4. **Provincial Health Department Notification:**  
   Formal notification to the Chief Executive Officer (District Health Authority) Sargodha and Primary & Secondary Healthcare Department, Government of Punjab.

### 3.2 Protocol Dossier Package
The submission to the ERC must contain:
* **Clinical Investigation Plan (CIP):** Trial design, sample size calculations, inclusion/exclusion criteria, and primary endpoints (sensitivity, specificity, AUROC vs board-certified ophthalmologist consensus).
* **Investigator’s Brochure (IB):** Machine learning architecture specifications, model validation metrics on standard benchmark datasets (EyePACS, Messidor, local Pakistani fundus cohorts), error analysis, and offline safety fail-safes.
* **Data Protection & Privacy Impact Assessment (DPIA):** Cryptographic storage architecture, AES-256 encryption at rest, TLS 1.3 in transit, automated patient de-identification, and GDPR-aligned right to erasure (addressing audit findings `SEC-09`, `PRIV-03`, `PRIV-04`).
* **Bilingual Informed Consent Forms (ICFs):** Patient information sheets provided in both Urdu and English.
* **Investigator Conflict of Interest Disclosures:** Declarations of financial and academic interests by all clinical investigators.

---

## 4. Provider Onboarding: 5-Phase Framework

```
Phase 1: Human Gate Sign-off & Institutional Agreement
Phase 2: Clinician Credentialing & Primary Source Verification (PSV)
Phase 3: System Training & Clinical Safety Certification
Phase 4: Provisioning & Granting Database Privileges (is_verified = TRUE)
Phase 5: Supervised Pilot Operation & Continuous Audit
```

### Phase 1: Institutional Partnership & Regulatory Sign-off
1. The Human Principal Investigator (PI) executes the institutional research agreement with the medical director of the participating facility.
2. The facility designates a Site Lead Ophthalmologist (e.g., Head of Department or Senior Consultant).
3. Secure clinical hardware (dedicated tablet/terminal, high-resolution calibrated monitor) is deployed at the clinical screening desk.

### Phase 2: Credential Submission & Primary Source Verification (PSV)
Every candidate clinician must submit a formal Credentialing Packet containing:
1. Legal full name and National Identity Card (CNIC) copy.
2. Basic Medical Degree (MBBS) certificate and graduation institution.
3. Post-graduate ophthalmic specialization diplomas (FCPS, FRCS, MCPS, DOMS, or equivalent).
4. Valid, active Pakistan Medical & Dental Council (PMDC) Registration Certificate.
5. Current institutional appointment letter and good standing certificate from hospital administration.
6. Curriculum Vitae detailing years of ophthalmic experience.

### Phase 3: Clinical System Training & Investigator Certification
Before receiving login access, the clinician completes a mandatory 2-hour clinical orientation:
1. **Scope & Limitations:** Reviewing the investigational nature of the AI model and understanding that the AI output is an advisory screening hypothesis.
2. **Diagnostic Criteria Alignment:** Reviewing the International Clinical Diabetic Retinopathy (ICDR) scale (Grades 0–4) and standardizing clinical definitions for mild, moderate, severe NPDR, and PDR.
3. **Workflow Familiarization:** Using the web/mobile clinician portal, redeeming one-time patient access grant codes (`claim_clinician_access`), inspecting retinal fundus images, and recording clinical notes (`clinician_notes`).
4. **Safety & Adverse Event Protocols:** Handling false positives/negatives, reporting software anomalies, and executing emergency vitreoretinal referrals for Grade 4 scans.

### Phase 4: Staged Account Provisioning & Privilege Elevation
1. Clinician registers an account through the application interface (`role = 'clinician'`).
2. Per migration `003_doctor_registration_and_roles.sql`, the database trigger automatically forces initial status:
   - `is_verified = FALSE`
   - `verification_status = 'pending'`
   - `verified_at = NULL`
3. The Primary Source Verification (PSV) verification officer verifies all documents according to SOP Section 5.
4. Only upon documentary validation, an authorized administrative service role executes the promotion RPC:
   ```sql
   SELECT public.admin_set_clinician_verification(
       p_clinician_id := '<clinician-uuid>',
       p_status := 'approved'
   );
   ```
5. The clinician is now promoted to `is_verified = TRUE`, allowing them to redeem patient grants, view authorized fundus images, and submit clinical evaluations per RLS security policy `SEC-04`.

### Phase 5: Supervised Pilot Operation & Quality Assurance
1. **Concordance Monitoring:** During the initial 30 days, 100% of cases screened by the AI are independently double-read by a senior consultant ophthalmologist.
2. **Weekly Discrepancy Rounds:** A clinical panel meets weekly to evaluate any scan where the AI grade and clinician ground truth differ by $\ge 1$ grade.
3. **Annual Credential Re-Check:** PMDC licensure status is re-verified every 12 months.

---

## 5. Standard Operating Procedure (SOP): PMDC Credential Verification

**SOP Identifier:** `SOP-CLIN-001`  
**Title:** Primary Source Verification of Medical Licensure via PMDC  

### 5.1 Objective
To establish an auditable, non-repudiable procedure for validating the identity, qualifications, and active licensure of medical practitioners prior to granting clinical review privileges in the Diabetic Retinopathy system.

### 5.2 Verification Authority
All medical practitioners in Pakistan are legally regulated by the **Pakistan Medical and Dental Council (PMDC)** (under the Pakistan Medical and Dental Council Act, 2022 / former Pakistan Medical Commission). Only physicians holding an "Active / Valid" registration with recognized post-graduate ophthalmic qualifications are eligible for clinical review roles.

### 5.3 Step-by-Step Verification Procedure

```
[Step 1] Collect Document Packet (CNIC, PMDC Certificate, FCPS/Degree)
   |
   v
[Step 2] Access Official PMDC Online Verification Portal (https://pmdc.pk)
   |
   v
[Step 3] Query Practitioner Record using Registration Number / CNIC
   |
   v
[Step 4] Validate 4 Identity Anchors:
         - Exact Name Match against CNIC
         - Active Registration Status (Valid Expiry Date)
         - Recognized Medical Qualifications (MBBS + FCPS/DOMS/Ophthalmic Diploma)
         - Clean Disciplinary Record (No Suspension/Revocation)
   |
   v
[Step 5] Secondary College Verification (CPSP portal for FCPS / MCPS)
   |
   v
[Step 6] Generate PDF Verification Audit Stamp & Archive in Compliance Store
   |
   v
[Step 7] Authorize Database RPC Promotion (is_verified = TRUE)
```

#### Detailed Step Execution:
1. **Access Regulatory Portal:**  
   Navigate to the official PMDC Doctor Online Verification Portal:  
   `https://pmdc.pk` (or active subportal `https://online.pmdc.pk`).
2. **Input Query Parameters:**  
   Enter the candidate's PMDC Registration Number (e.g., `XXXXX-P` for Punjab medical graduates) or official National Identity Card (CNIC) number.
3. **Inspect Output Record:**  
   Verify that the official database returns:
   - Full legal name matching the identity document.
   - Registration status explicitly listed as **"VALID"** or **"ACTIVE"**.
   - Registration Expiry Date is in the future.
4. **Validate Specialty Qualifications:**  
   Confirm that the candidate's post-graduate qualification in Ophthalmology (e.g. FCPS Ophthalmology, MCPS, DOMS) is formally recorded under "Additional Qualifications". If querying an FCPS specialist, perform secondary lookup on the College of Physicians and Surgeons Pakistan (CPSP) verification portal (`https://www.cpsp.edu.pk`).
5. **Confirm Institutional Standing:**  
   Telephone the administration office of the claimed hospital (e.g., DHQ Teaching Hospital Sargodha administration: `048-9230340`, or Niazi Medical Complex: `048-3727144`) to confirm current active clinical privileges and employment.
6. **Audit Archival:**  
   Save an encrypted PDF screenshot of the PMDC verification page labeled `PMDC_VERIF_<LICENSE_NO>_<TIMESTAMP>.pdf` into the restricted regulatory compliance vault.
7. **Database Activation:**  
   Log the verification record with the verifier's identity, timestamp, and verification reference hash, and execute `admin_set_clinician_verification`.

---

## 6. Patient Informed Consent Protocols (Urdu & English)

Informed consent must be obtained from every patient before fundus imaging and AI screening. Consent must comply with the Declaration of Helsinki, Good Clinical Practice (GCP), and the Punjab Healthcare Commission regulations.

### 6.1 Consent Principles
1. **Voluntary Participation:** Refusal to participate in the AI screening pilot must not affect the patient's standard of care or access to eye treatment.
2. **Bilingual Presentation:** All documentation must be available in both plain Urdu (اردو) and English, read aloud to non-literate patients in the presence of an impartial witness.
3. **Explicit Risk & Limitation Disclosures:** Patients must be clearly informed that the AI algorithm is an assistive screening tool, that errors (false positives or false negatives) are possible, and that urgent referrals must be honored.
4. **Data Privacy & Storage:** Patients must be informed that anonymized retinal images will be stored securely on encrypted cloud servers and may be reviewed by expert ophthalmologists for clinical audit.

---

### 6.2 Patient Information Sheet & Consent Form Template (English)

```
========================================================================================
                 PATIENT INFORMED CONSENT FORM: CLINICAL PILOT STUDY
          AI-ASSISTED DIABETIC RETINOPATHY SCREENING IN SARGODHA DISTRICT
========================================================================================

Institution: Dr. Faisal Masood Teaching Hospital / Sargodha Medical College & Participating Centers
Principal Investigator: [Human PI Name, FCPS]
Study Reference: SMC-ERC-DR-2026-PILOT

1. PURPOSE OF THIS SCREENING
You are invited to participate in a medical study evaluating an artificial intelligence (AI) 
computer system designed to screen for Diabetic Retinopathy (eye damage caused by diabetes). 
Diabetes can damage the small blood vessels in your eyes without causing early symptoms. Early 
detection protects your eyesight.

2. WHAT WILL HAPPEN
- A digital photograph of the back of your eye (retina) will be taken using a specialized fundus 
  camera. This procedure is completely painless, safe, and takes less than 5 minutes.
- In some cases, eye drops may be used to widen your pupils. These drops may cause mild blurring 
  of vision for 2 to 4 hours.
- The computer program will analyze your photograph to detect signs of diabetic eye disease.
- A qualified eye doctor (ophthalmologist) will also review your results.
- If signs of diabetic eye damage are detected, you will receive a free, prioritized referral to 
  the Eye Department at DHQ Teaching Hospital Sargodha, LRBT Shahpur, or Niazi Medical Complex.

3. RISKS AND BENEFITS
- There is no physical danger from retinal photography.
- Benefit: You will receive early, comprehensive evaluation for diabetic eye disease at no cost.
- Limitation: The AI program is an investigational screening assistant. It does not provide a 
  final medical diagnosis. The eye doctor will make the final clinical decision.

4. CONFIDENTIALITY & DATA PROTECTION
- Your photographs and medical information will be stored securely with advanced encryption.
- Your personal identity (name, CNIC, phone number) will be separated from your eye photographs 
  during research analysis.
- You have the right to request the deletion of your photographs and data at any time without giving 
  a reason, and this will not affect your regular medical treatment in any way.

5. VOLUNTARY CONSENT
Participation is completely voluntary. You may withdraw at any time.

PATIENT STATEMENT & SIGNATURE:
"I have read (or have had read to me) the information sheet. I understand the purpose, benefits, 
and procedures. I agree to participate."

Patient Name: _______________________  CNIC / Registration: ______________________
Patient Signature / Thumbprint: _______________________ Date: ___________________
Investigator / Nurse Name: ____________________________ Signature: ______________
Witness Name (if illiterate): _________________________ Signature: ______________
========================================================================================
```

---

### 6.3 Patient Information Sheet & Consent Form Template (Urdu / اردو)

```
========================================================================================
                          مریض کا باضابطہ باخبر رضامندی فارم
         ضلع سرگودھا میں ذیابیطس سے متاثرہ پردہ بصارت (شوگر کے آنکھوں کے اثرات) کی 
                     کمپیوٹرائزڈ / مصنوعی ذہانت (AI) اسکریننگ
========================================================================================

طبی ادارہ: ڈاکٹر فیصل مسعود ٹیچنگ ہسپتال / سرگودھا میڈیکل کالج و ملحقہ مراکز
تحقیقی سربراہ: [نام نگراں ڈاکٹر صاحب / ماہر امراض چشم]
ریسرچ ریفرنس کوڈ: SMC-ERC-DR-2026-PILOT

١. معائنے کا مقصد:
آپ کو ذیابیطس (شوگر) کی وجہ سے آنکھوں کے پردے پر ہونے والے اثرات (Diabetic Retinopathy) 
کی جلد تشخیص کے ایک طبی تحقیقی منصوبے میں شرکت کی دعوت دی جاتی ہے۔ شوگر آنکھوں کے پچھلے 
حصے (پردہ بصارت) کی باریک خون کی نالیوں کو خاموشی سے نقصان پہنچا سکتی ہے۔ بروقت جانچ سے بینائی 
کو محفوظ رکھا جا سکتا ہے۔

٢. معائنے کا طریقہ کار:
- ایک خاص ڈیجیٹل کیمرے سے آپ کی آنکھ کے اندرونی پردے (Fundus) کی تصویر لی جائے گی۔
- یہ عمل بالکل محفوظ اور درد سے پاک ہے، اور اس میں صرف ۲ سے ۵ منٹ لگتے ہیں۔
- اگر ضرورت ہوئی تو آنکھ کی پتلی کو چوڑا کرنے والے قطرے ڈالے جا سکتے ہیں، جس سے ۲ سے ۴ گھنٹے تک 
  ہلکا سا دھندلا پن ہو سکتا ہے۔
- مصنوعی ذہانت (کمپیوٹر سوفٹ ویئر) آپ کی تصویر کا معائنہ کر کے شوگر کے اثرات کا پتا لگائے گا۔
- ایک مستند ماہر امراض چشم (Eye Specialist) بھی ان نتائج کا مکمل جائزہ لیں گے۔
- اگر پردے میں بیماری کی علامات پائی گئیں تو آپ کو فوری طور پر ڈی ایچ کیو ٹیچنگ ہسپتال سرگودھا، 
  ایل آر بی ٹی (LRBT) شاہ پور، یا نیازی میڈیکل کمپلیکس کے شعبہ چشم میں ترجیحی اور مفت علاج کے لیے 
  ریفرل جاری کیا جائے گا۔

٣. فوائد اور حدود:
- فائدہ: آپ کی بینائی کو شوگر کے مضر اثرات سے بچانے کے لیے ماہر ڈاکٹروں کی بروقت رہنمائی میسر آئے گی۔
- احتیاطی نکتہ: یہ کمپیوٹرائزڈ نظام ایک معاون اسکریننگ ٹول ہے۔ یہ کسی ماہر ڈاکٹر کا نعم البدل نہیں 
  ہے۔ حتمی فیصلہ ماہر امراض چشم کا ہو گا۔

٤. رازداری اور کوائف کا تحفظ:
- آپ کی تصویریں اور طبی معلومات جدید خفیہ کوڈنگ (انکرپشن) کے ذریعے محفوظ رکھی جائیں گی۔
- آپ کا نام اور شناختی کارڈ نمبر تحقیق کے دوران خفیہ رکھا جائے گا۔
- آپ کو یہ حق حاصل ہے کہ آپ کسی بھی وقت اپنا ڈیٹا یا تصویریں حذف (Delete) کرنے کی درخواست کر سکتے 
  ہیں، جس سے آپ کے علاج پر کوئی برا اثر نہیں پڑے گا۔

٥. رضا کارانہ شرکت:
اس معائنے میں شمولیت مکمل طور پر رضا کارانہ ہے۔ آپ کسی بھی وقت بغیر کسی وجہ کے انکار کر سکتے ہیں۔

مریض کا بیان اور دستخط:
"میں نے اس فارم کے تمام مندرجات کو پڑھ لیا ہے (یا مجھے پڑھ کر سنا اور سمجھا دیا گیا ہے)۔ 
میں اس طبی جائزے میں رضا کارانہ طور پر شامل ہونے کی اجازت دیتا/دیتی ہوں۔"

مریض کا نام: _______________________ قومی شناختی کارڈ نمبر: ______________________
مریض کے دستخط یا انگوٹھے کا نشان: ______________________ تاریخ: __________________
معائنہ کار ڈاکٹر/نرس کا نام: ___________________________ دستخط: __________________
گواہ کا نام (بوقت ضرورت): _____________________________ دستخط: __________________
========================================================================================
```

---

## 7. Clinical Risk Mitigation & Adverse Event Escalation

### 7.1 False Negative Mitigation (High Risk of Missed Vision-Threatening Disease)
* **Risk:** The AI model classifies a patient with proliferative retinopathy or severe macular edema as Grade 0 or Grade 1.
* **Mitigation Protocol:**
  1. Routine visual acuity testing ($< 6/12$ Snellen in either eye) automatically flags the patient for human ophthalmologist review regardless of AI grade.
  2. Any patient presenting with subjective visual symptoms (sudden vision drop, flashes, floaters, distorted lines) triggers an immediate clinical referral.
  3. A random 10% quality-assurance sample of Grade 0/1 scans is audited weekly by the lead consultant.

### 7.2 False Positive Mitigation (Patient Anxiety & Resource Burden)
* **Risk:** Artifacts (dust on camera lens, uneven illumination, camera motion blur) misclassified as microaneurysms or hemorrhages.
* **Mitigation Protocol:**
  1. Automated image quality pre-filtering (`gemini_validator.py` / local sharpness & illumination check) flags ungradable images immediately at the point of capture, requesting the operator to re-capture.
  2. Patients are informed that referral is a standard confirmatory evaluation, avoiding unnecessary panic.

### 7.3 Urgent Vitreo-Retinal Escalation (Grade 4)
* **Protocol for Urgent Findings:**
  1. When Grade 4 (PDR, pre-retinal hemorrhage, tractional detachment) is detected, the software automatically triggers an **Urgent Clinical Alert** on the clinician dashboard.
  2. The screening center coordinator contacts the designated on-call retina service at LRBT Shahpur (`0486-6310965` / `0315-7280051`) or Niazi Medical Complex (`048-3727144` / `0317-1777509`) to book an emergency evaluation within 24 to 72 hours.
  3. If advanced 23G/25G vitrectomy is indicated and unavailable locally, the patient is coordinated directly to Al-Shifa Trust Regional Hospital Chakwal (`0543-568000`) or King Edward / Mayo Hospital Lahore.

---

## 8. Swarm File Locks, Rollback Path & Governance Sign-Off

### 8.1 Assigned File Locks
* `audit/sargodha_provider_directory.md` (Assigned to Provider Researcher)
* `docs/provider_onboarding_protocol.md` (Assigned to Provider Researcher)
* `s:\unimate\diabetic\sprint_4_implementation.md` (Assigned to Provider Researcher)

### 8.2 Rollback Path
In the event of protocol revision or administrative rejection:
1. Delete `docs/provider_onboarding_protocol.md`.
2. Delete `audit/sargodha_provider_directory.md`.
3. Revert database staging seed migrations.

### 8.3 Final Governance Declaration
* **External Outreach Status:** **HALTED / BLOCKED**. Zero external communications have been transmitted.
* **Account Activation Status:** **LOCKED**. Zero live clinician accounts have been created.
* **Next Action Required:** Principal Investigator and Project Lead human review and approval before entering Track 3 or scheduling clinical pilot deployment meetings.
