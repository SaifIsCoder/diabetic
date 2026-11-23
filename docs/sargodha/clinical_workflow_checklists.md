# Clinical Point-of-Care Workflow Checklists: Sargodha Retinal Pilot

**Document Identifier:** `docs/sargodha/clinical_workflow_checklists.md`  
**Target Environment:** Sargodha District Pilot Screening Desks (DHQ Sargodha, LRBT Shahpur, Niazi Medical Complex)  
**Standard Operating Procedure:** `SOP-CLIN-002` (Clinical Point-of-Care Operations)  
**Effective Date:** 2026-11-23  
**Status:** PRODUCTION-GRADE POINT-OF-CARE OPERATIONAL CHECKLISTS — ZERO PLACEHOLDERS  

---

## Checklist 1: Patient Reception & Intake Desk Checklist

**Assigned Staff:** Reception Officer / Clinical Intake Nurse  
**Station:** Clinical Registration & Intake Counter  
**Execution Frequency:** Once per patient encounter upon arrival  

```
+----+-----------------------------------------------------------------------------------------+-----------+
| #  | Operational Task & Verification Requirement                                             | Status    |
+----+-----------------------------------------------------------------------------------------+-----------+
| 1  | PATIENT IDENTITY & ELIGIBILITY VERIFICATION                                             |           |
|    | [ ] Verify National Identity Card (CNIC) or official hospital Medical Record (MR) number.| [ ] PASS  |
|    | [ ] Confirm patient age is >= 18 years.                                                 | [ ] PASS  |
|    | [ ] Confirm verified diagnosis of Diabetes Mellitus (Type 1 or Type 2).                  | [ ] PASS  |
|    | [ ] Check exclusion criteria: confirm absence of active infectious conjunctivitis,       | [ ] PASS  |
|    |     acute ocular chemical injury, or cognitive inability to participate.                 |           |
+----+-----------------------------------------------------------------------------------------+-----------+
| 2  | BILINGUAL INFORMED CONSENT DOCUMENTATION                                                |           |
|    | [ ] Present the official bilingual Informed Consent Form (Urdu or English per patient).  | [ ] PASS  |
|    | [ ] Provide verbal explanation of AI assistive role, physician primacy, and PECA privacy.| [ ] PASS  |
|    | [ ] Obtain patient physical signature OR verified thumbprint (Male: Left, Female: Right).| [ ] PASS  |
|    | [ ] For non-literate patients, ensure impartial witness signs and records CNIC.          | [ ] PASS  |
|    | [ ] File the original paper consent in the on-site compliance binder.                    | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 3  | MEDICAL & OPHTHALMIC HISTORY INTAKE                                                     |           |
|    | [ ] Record diabetes duration (in years) and current treatment (Insulin / Oral agents).   | [ ] PASS  |
|    | [ ] Record most recent HbA1c value (if available within last 90 days) and date.          | [ ] PASS  |
|    | [ ] Document history of hypertension, cardiovascular disease, and renal impairment.      | [ ] PASS  |
|    | [ ] Inquire into prior ocular interventions: cataract surgery, retinal laser, injections.| [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 4  | BASELINE VISUAL ACUITY ASSESSMENT                                                        |           |
|    | [ ] Test distance visual acuity for Right Eye (OD) using Snellen / ETDRS chart at 6m.    | [ ] PASS  |
|    | [ ] Test distance visual acuity for Left Eye (OS) using Snellen / ETDRS chart at 6m.     | [ ] PASS  |
|    | [ ] Record whether testing was performed with habitual spectacles (Pinhole if <6/12).   | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 5  | PATIENT QUEUE REGISTRATION & DELEGATION GRANT ISSUANCE                                   |           |
|    | [ ] Create new screening session in the intake tablet application.                      | [ ] PASS  |
|    | [ ] System generates unique 8-character delegation grant code (e.g., "K7M9-2P4Q").      | [ ] PASS  |
|    | [ ] Print or write the delegation grant code clearly on the patient routing slip.        | [ ] PASS  |
|    | [ ] Escort patient to photography station waiting area with dark sunglasses reminder.    | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
```

---

## Checklist 2: Fundus Photography Operator Checklist

**Assigned Staff:** Certified Ophthalmic Technician / Camera Operator  
**Station:** Retinal Photography Suite  
**Equipment:** Digital Non-Mydriatic/Mydriatic Fundus Camera & Clinical Capture Terminal  
**Execution Frequency:** Once per patient imaging session  

```
+----+-----------------------------------------------------------------------------------------+-----------+
| #  | Operational Task & Verification Requirement                                             | Status    |
+----+-----------------------------------------------------------------------------------------+-----------+
| 1  | PRE-EXAMINATION ROOM & EQUIPMENT SETUP                                                   |           |
|    | [ ] Dim ambient examination room lighting to < 5 lux (non-mydriatic dark adaptation).    | [ ] PASS  |
|    | [ ] Inspect camera objective lens using penlight; confirm zero dust spots or smudges.    | [ ] PASS  |
|    | [ ] Power on fundus camera and launch certified clinical image acquisition software.     | [ ] PASS  |
|    | [ ] Confirm tablet/PC connection to secure local staging server.                         | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 2  | PATIENT POSITIONING & ERGONOMIC ALIGNMENT                                                |           |
|    | [ ] Adjust electric instrument table and chin rest height to match patient stature.      | [ ] PASS  |
|    | [ ] Instruct patient to rest chin securely in chin cup and forehead flush against band.  | [ ] PASS  |
|    | [ ] Align patient's lateral canthus with the canthal height reference line on upright.   | [ ] PASS  |
|    | [ ] Instruct patient on fixation target (look steadily at the internal green light dot). | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 3  | PUPILLARY DIAMETER & DILATION ASSESSMENT                                                 |           |
|    | [ ] Measure unconstricted pupil diameter using camera infrared alignment monitor.        | [ ] PASS  |
|    | [ ] Confirm pupil diameter is >= 3.5 mm.                                                 | [ ] PASS  |
|    | [ ] If pupil < 3.5 mm after 3 minutes dark adaptation:                                   |           |
|    |     - Confirm no history of angle-closure glaucoma or shallow anterior chamber.          | [ ] PASS  |
|    |     - Administer 1 drop of Tropicamide 0.5% or 1.0% in each eye upon physician order.    | [ ] PASS  |
|    |     - Allow 15-20 minutes for full dilation (>= 6.0 mm) before proceeding.               | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 4  | STANDARDIZED DUAL-FIELD RETINAL CAPTURE                                                  |           |
|    | [ ] RIGHT EYE (OD) - FIELD 1: Capture 45-degree Optic Disc Centered fundus image.        | [ ] PASS  |
|    | [ ] RIGHT EYE (OD) - FIELD 2: Capture 45-degree Macula Centered fundus image.            | [ ] PASS  |
|    | [ ] LEFT EYE (OS) - FIELD 1: Capture 45-degree Optic Disc Centered fundus image.         | [ ] PASS  |
|    | [ ] LEFT EYE (OS) - FIELD 2: Capture 45-degree Macula Centered fundus image.          | [ ] PASS  |
|    | [ ] Align split-line focusing indicators to form one continuous line before exposure.    | [ ] PASS  |
|    | [ ] Prompt patient to blink once, open wide, and immediately fire camera shutter flash.   | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 5  | POINT-OF-CAPTURE QUALITY & OOD HEURISTIC VALIDATION                                      |           |
|    | [ ] Verify image sharpness: retinal vessels around disc and macula are crisp.           | [ ] PASS  |
|    | [ ] Verify absence of blink / eyelid cutoff obscuring more than 10% of retinal area.     | [ ] PASS  |
|    | [ ] Verify absence of bright white/orange crescent corneal reflection glare halos.       | [ ] PASS  |
|    | [ ] Confirm local heuristic engine passes image (No `ERR_OOD_NON_RETINAL` or blur flag). | [ ] PASS  |
|    | [ ] If rejected by quality check: re-align patient immediately and capture repeat image.  | [ ] PASS  |
|    | [ ] Upload validated image set to staging storage and route patient to Review Station.   | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
```

---

## Checklist 3: Clinician Image Review & Diagnostic Confirmation Checklist

**Assigned Staff:** Licensed Consultant Ophthalmologist (PMDC-registered)  
**Station:** Clinician Diagnostic Workstation / Secure Review Terminal  
**Execution Frequency:** Once per patient screening encounter  

```
+----+-----------------------------------------------------------------------------------------+-----------+
| #  | Operational Task & Verification Requirement                                             | Status    |
+----+-----------------------------------------------------------------------------------------+-----------+
| 1  | CLINICIAN AUTHENTICATION & ACCESS DELEGATION                                             |           |
|    | [ ] Log into clinical portal using institutional credentials and verified MFA.          | [ ] PASS  |
|    | [ ] Confirm active PMDC verification status (`is_verified = TRUE`).                      | [ ] PASS  |
|    | [ ] Input patient's 8-character delegation grant code (redeem via `claim_clinician_access`).| [ ] PASS  |
|    | [ ] Confirm cryptographic authorization grants access to patient fundus images via RLS.  | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 2  | SYSTEMATIC FUNDUS IMAGE INSPECTION                                                       |           |
|    | [ ] Inspect Field 1 (Disc-centered) for:                                                 |           |
|    |     - Optic disc margins, neuroretinal rim, cupping, and Neovascularization of Disc (NVD)| [ ] PASS  |
|    |     - Vascular caliber, arteriolar attenuation, venous beading, and peripapillary leaks. | [ ] PASS  |
|    | [ ] Inspect Field 2 (Macula-centered) for:                                               |           |
|    |     - Foveal avascular zone (FAZ) integrity and macular capillary non-perfusion.        | [ ] PASS  |
|    |     - Microaneurysms, dot/blot hemorrhages, and circinate rings of hard exudates.        | [ ] PASS  |
|    | [ ] Pan across all 4 retinal quadrants at >= 200% zoom using high-resolution viewer.     | [ ] PASS  |
|    | [ ] Toggle red-free (green-channel) optical filter to verify subtle microaneurysms/IRMA. | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 3  | AI MODEL PREDICTION EVALUATION & ADJUDICATION                                            |           |
|    | [ ] Review the AI screening classification (ICDR Grade 0, 1, 2, 3, or 4).               | [ ] PASS  |
|    | [ ] Evaluate predicted probabilities across all 5 clinical classes.                      | [ ] PASS  |
|    | [ ] Formulate independent human expert diagnostic judgment.                              | [ ] PASS  |
|    | [ ] CLINICAL DECISION ACTION:                                                            |           |
|    |     [ ] Option A: Concur with AI classification (Click "Confirm Prediction").            | [ ] PASS  |
|    |     [ ] Option B: Override AI classification (Select correct grade 0–4 & record notes).  | [ ] PASS  |
|    |     [ ] Option C: Mark scan Ungradable (Specify optical reason: media opacity/cataract). | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 4  | CLINICAL NOTES & MACULOPATHY DOCUMENTATION                                               |           |
|    | [ ] Document presence or absence of Diabetic Macular Edema (CSME / CI-DME).              | [ ] PASS  |
|    | [ ] Enter clinical rationale and specific management recommendations in `clinician_notes`| [ ] PASS  |
|    | [ ] Check that mandatory HMAC-SHA256 scan receipt is generated and immutability enforced.| [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 5  | PATIENT DISPOSITION & FOLLOW-UP ASSIGNMENT                                               |           |
|    | [ ] Assign verified follow-up interval based on definitive clinical grade:               |           |
|    |     - Grade 0: Routine re-screening in 12 months.                                        | [ ] PASS  |
|    |     - Grade 1: Re-screening in 6 to 12 months with metabolic review.                    | [ ] PASS  |
|    |     - Grade 2: Slit-lamp biomicroscopy & macular OCT in 3 to 6 months.                   | [ ] PASS  |
|    |     - Grade 3: Urgent vitreoretinal referral within 2 to 4 weeks.                        | [ ] PASS  |
|    |     - Grade 4: IMMEDIATE EMERGENCY VITREORETINAL REFERRAL WITHIN 24–72 HOURS (Checklist 4) | [ ] PASS  |
|    | [ ] Digitally sign review record; print finalized bilingual report for patient.          | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
```

---

## Checklist 4: Emergency Severe DR Escalation Protocol Checklist

**Assigned Staff:** Lead Clinician, Screening Coordinator & Referral Desk Nurse  
**Trigger Criteria:** ICDR Grade 4 (PDR), Vitreous Hemorrhage, Tractional Retinal Detachment, Rubeosis Iridis, or Acute Sudden Vision Drop  
**Target Action Window:** Referral dispatch within 2 hours; Specialist evaluation within 24 to 72 hours  

```
+----+-----------------------------------------------------------------------------------------+-----------+
| #  | Operational Task & Verification Requirement                                             | Status    |
+----+-----------------------------------------------------------------------------------------+-----------+
| 1  | IMMEDIATE CLINICAL ALERT & ON-SITE STABILIZATION                                        |           |
|    | [ ] Retinal software raises high-priority visual banner: "EMERGENCY CLINICAL ESCALATION".| [ ] PASS  |
|    | [ ] Screening technician immediately notifies the attending on-site physician.           | [ ] PASS  |
|    | [ ] Physician performs urgent slit-lamp biomicroscopy with 90D/78D lens.                 | [ ] PASS  |
|    | [ ] Evaluate anterior chamber angle for neovascularization of the iris (Rubeosis Iridis).| [ ] PASS  |
|    | [ ] Measure intraocular pressure (IOP) via Goldmann applanation or non-contact tonometer.| [ ] PASS  |
|    | [ ] Retain patient on-site in quiet, upright position; avoid strenuous movement.         | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 2  | EMERGENCY REFERRAL PACKET FORMULATION                                                    |           |
|    | [ ] Print high-resolution full-color fundus photographs of both eyes.                   | [ ] PASS  |
|    | [ ] Print official Emergency Vitreoretinal Referral Slip including:                      | [ ] PASS  |
|    |     - Patient Name, CNIC, MR Number, Contact Phone, and Resident Address.               |           |
|    |     - Baseline Visual Acuity, Intraocular Pressure, and Systemic Diabetic History.       |           |
|    |     - Confirmed Grade 4 lesions: NVD, NVE, Vitreous Hemorrhage, or Retinal Detachment.   |           |
|    |     - Cryptographic HMAC-SHA256 Scan Receipt signature for authenticity verification.    |           |
|    | [ ] Attending physician physically signs and applies PMDC license rubber stamp.         | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 3  | TELEPHONIC HOSPITAL NOTIFICATION & DIRECT ESCALATION                                     |           |
|    | [ ] Contact designated on-call retina service coordinator based on patient circumstance: |           |
|    |     - Option 1 (Public Tertiary): Dr. Faisal Masood Teaching Hospital (048-9230340).     | [ ] PASS  |
|    |     - Option 2 (Charitable 100% Free): LRBT Eye Hospital Shahpur (0486-6310965).        | [ ] PASS  |
|    |     - Option 3 (Private Tertiary): Niazi Medical Complex (048-3727144 / 0317-1777509).  | [ ] PASS  |
|    |     - Option 4 (Regional Apex Vitrectomy): Al-Shifa Trust Chakwal (0543-568000).        | [ ] PASS  |
|    | [ ] Transmit patient details and confirm specialist evaluation slot within 24–72 hours.  | [ ] PASS  |
|    | [ ] Record receiving coordinator's name and confirmed appointment time in emergency log. | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 4  | PATIENT & CAREGIVER CRISIS COUNSELING                                                    |           |
|    | [ ] Verbally explain urgency to patient and family in clear Urdu: sight is in jeopardy.  | [ ] PASS  |
|    | [ ] Provide written pre-procedure instructions: avoid lifting heavy objects, avoid        | [ ] PASS  |
|    |     straining, maintain head elevation at 30-45 degrees while resting in bed.            |           |
|    | [ ] Emphasize that emergency laser or anti-VEGF injection can prevent permanent blindness.| [ ] PASS  |
|    | [ ] Verify patient has safe private transport or coordinate with Rescue 1122 if disabled.| [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 5  | CLOSED-LOOP REFERRAL TRACKING & FOLLOW-UP                                                |           |
|    | [ ] Log encounter in "Sargodha Pilot Emergency Escalation Registry".                     | [ ] PASS  |
|    | [ ] Schedule automated 48-hour telephonic check by screening nurse to confirm arrival.   | [ ] PASS  |
|    | [ ] Obtain written counter-referral slip from tertiary surgeon to close audit loop.      | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
```

---

## Checklist 5: Device Disinfection, Infection Control & Shift Turnover Checklist

**Assigned Staff:** Screening Operator & Infection Control Lead  
**Station:** Fundus Photography Suite & Patient Waiting Area  
**Execution Frequency:** Disinfection between every patient; Technical audit at end of shift  

```
+----+-----------------------------------------------------------------------------------------+-----------+
| #  | Operational Task & Verification Requirement                                             | Status    |
+----+-----------------------------------------------------------------------------------------+-----------+
| 1  | PER-PATIENT SURFACE DISINFECTION (Mandatory between every patient encounter)             |           |
|    | [ ] Perform 6-step hand hygiene using alcohol-based hand rub or antimicrobial soap.      | [ ] PASS  |
|    | [ ] Wipe patient chin rest cup thoroughly using a 70% Isopropyl Alcohol disinfectant wipe.| [ ] PASS  |
|    | [ ] Wipe patient forehead rest cushion thoroughly using a 70% Isopropyl Alcohol wipe.    | [ ] PASS  |
|    | [ ] Wipe patient hand grips and side positioning handles with disinfectant wipe.         | [ ] PASS  |
|    | [ ] Allow alcohol to air dry completely for at least 60 seconds (ensuring germicidal kill)| [ ] PASS  |
|    | [ ] Replace chin rest paper liner (if utilizing disposable paper stack model).           | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 2  | OPTICAL LENS CARE & CAMERA HYGIENE                                                       |           |
|    | [ ] Inspect camera front objective lens for aerosol droplets, sebum, or dust particles.  | [ ] PASS  |
|    | [ ] Never spray disinfectant or alcohol directly onto the camera objective lens.         | [ ] PASS  |
|    | [ ] If lens cleaning is required: use dry optical lens air-blower first to remove grit.   | [ ] PASS  |
|    | [ ] Wipe lens using lint-free optical lens tissue moistened with certified lens cleaner, | [ ] PASS  |
|    |     starting from center and spiraling gently outward in smooth circular strokes.        |           |
|    | [ ] Place protective objective lens cap immediately when camera is not in active use.    | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 3  | SHIFT-END DATA SYNCHRONIZATION & SYSTEM AUDIT                                            |           |
|    | [ ] Verify all queued retinal images have successfully synchronized to staging storage.  | [ ] PASS  |
|    | [ ] Confirm 0 pending unsynchronized scan records in local SQLite / offline storage.    | [ ] PASS  |
|    | [ ] Check secure HTTPS / TLS 1.3 connection status to backend API server.                | [ ] PASS  |
|    | [ ] Verify available local SSD storage space is >= 10 GB on clinical acquisition PC.     | [ ] PASS  |
|    | [ ] Ensure no temporary unencrypted patient image files remain in desktop trash/temp.    | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 4  | INVENTORY & CONSUMABLE AUDIT                                                             |           |
|    | [ ] Check stock of Tropicamide 0.5% / 1.0% eye drops (discard bottles opened > 28 days). | [ ] PASS  |
|    | [ ] Check supply of 70% Isopropyl Alcohol wipes, lens tissue, and disposable dark glasses| [ ] PASS  |
|    | [ ] Verify supply of bilingual consent forms and emergency referral slips (min 50 sets).| [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
| 5  | SHIFT TURNOVER LOG & HANDOFF ATTESTATION                                                 |           |
|    | [ ] Record total patient encounters completed during shift: ________ patients.           | [ ] PASS  |
|    | [ ] Record total pharmacological dilations performed: ________ patients.                 | [ ] PASS  |
|    | [ ] Record total Emergency Grade 4 referrals dispatched: ________ patients.              | [ ] PASS  |
|    | [ ] Record any hardware, software, or optical anomalies in the physical station logbook. | [ ] PASS  |
|    | [ ] Outgoing operator signs daily logbook; incoming operator countersigns at handoff.    | [ ] PASS  |
+----+-----------------------------------------------------------------------------------------+-----------+
```
