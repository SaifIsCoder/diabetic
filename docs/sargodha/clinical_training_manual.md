# Diabetic Retinopathy Clinical Training Manual: Sargodha Pilot Operations

**Document Identifier:** `docs/sargodha/clinical_training_manual.md`  
**Target Program:** Supervised Clinical Pilot for Autonomous & Assistive Diabetic Retinopathy Screening  
**Target District:** Sargodha District, Punjab, Pakistan  
**Authoring Body:** Clinical AI Operations Working Group & Ophthalmic Technical Advisory Board  
**Effective Date:** 2026-11-23  
**Operational Status:** ACTIVE — CLINICAL PILOT INSTRUCTIONAL MANUAL  

---

## 1. Regulatory Status & Clinical Decision Support (CDS) Governance

### 1.1 Device Classification and Investigational Scope
The Diabetic Retinopathy Screening Platform is classified as an **Investigational Clinical Decision Support (CDS) Software as a Medical Device (SaMD)**. Under the statutory definitions of the **Drug Regulatory Authority of Pakistan (DRAP) Medical Device Rules (2017)** (Class IIb Investigational Medical Device) and the United States Food and Drug Administration (FDA) Guidance on *Clinical Decision Support Software* (Section 520(o)(1)(E) of the FD&C Act):

1. **Advisory Screening Hypothesis:** The software outputs a non-prescriptive, probabilistic triage hypothesis regarding the presence and severity of Diabetic Retinopathy (DR) and Diabetic Macular Edema (DME).
2. **Physician Primacy:** The artificial intelligence (AI) engine is strictly assistive. Ultimate diagnostic authority and therapeutic decision-making reside exclusively with licensed, PMDC-registered ophthalmologists and medical practitioners.
3. **No Independent Autonomous Discharge:** An automated finding of Grade 0 (No DR) or Grade 1 (Mild NPDR) does not supersede clinical symptoms, visual acuity deficits, or the clinical judgment of an attending physician. No patient may be discharged from diabetic ophthalmic follow-up solely on the basis of an AI assessment without human clinical validation.

```
+----------------------------------------------------------------------------------------------------+
|                                    LEGAL & REGULATORY BOUNDARY                                     |
|                                                                                                    |
|  "The retinal image analysis provided by this application represents an automated screening       |
|   hypothesis designed to support clinical workflow. It does not constitute a final medical         |
|   diagnosis. Definitive diagnosis, treatment planning, and surgical intervention remain the sole   |
|   responsibility of the credentialed human medical practitioner."                                   |
+----------------------------------------------------------------------------------------------------+
```

### 1.2 Clinical Pilot Objectives in Sargodha District
The Sargodha clinical pilot evaluates real-world point-of-care screening efficacy across the district's public, charitable, and private eye care facilities. The primary objectives are:
- Validating AI concordance against consensus grading by board-certified Pakistani ophthalmologists (Fellows of the College of Physicians and Surgeons Pakistan, FCPS).
- Shortening time-to-evaluation for vision-threatening diabetic retinopathy (VTDR, ICDR Grades 3 and 4) through established referral conduits to Dr. Faisal Masood Teaching Hospital (DHQ Sargodha), LRBT Secondary Eye Hospital Shahpur, and Niazi Medical Complex.
- Eliminating ungradable image bottlenecks through point-of-capture heuristic image quality feedback.

---

## 2. International Clinical Diabetic Retinopathy (ICDR) Grading System

Clinicians and operators must master the International Clinical Diabetic Retinopathy (ICDR) severity scale and associated morphological lesions.

```
+----------------------------------------------------------------------------------------------------+
|                         ICDR CLINICAL CLASSIFICATION & MORPHOLOGICAL MATRIX                        |
+-------+-----------------------------+--------------------------------------------------------------+
| Grade | Clinical Designation        | Hallmark Ophthalmoscopic Lesions                             |
+-------+-----------------------------+--------------------------------------------------------------+
|   0   | No Apparent DR              | No microaneurysms, hemorrhages, or vascular abnormalities.   |
+-------+-----------------------------+--------------------------------------------------------------+
|   1   | Mild Non-Proliferative DR   | Microaneurysms only.                                         |
+-------+-----------------------------+--------------------------------------------------------------+
|   2   | Moderate NPDR               | More than microaneurysms, but less than Severe NPDR:         |
|       |                             | - Scattered blot and dot hemorrhages                         |
|       |                             | - Hard exudates (lipid deposits)                             |
|       |                             | - Cotton-wool spots (nerve fiber layer infarcts)             |
+-------+-----------------------------+--------------------------------------------------------------+
|   3   | Severe NPDR                 | Meets ANY ONE of the "4-2-1" Criteria:                       |
|       |                             | - 4 quadrants: >20 intraretinal hemorrhages per quadrant     |
|       |                             | - 2 quadrants: Definite venous beading                       |
|       |                             | - 1 quadrant: Prominent Intraretinal Microvascular           |
|       |                             |   Abnormalities (IRMA)                                       |
|       |                             | AND no frank proliferative signs.                            |
+-------+-----------------------------+--------------------------------------------------------------+
|   4   | Proliferative DR (PDR)      | Neovascularization of Disc (NVD), Neovascularization         |
|       |                             | Elsewhere (NVE), Preretinal / Vitreous Hemorrhage, or        |
|       |                             | Tractional Retinal Detachment.                               |
+-------+-----------------------------+--------------------------------------------------------------+
```

### 2.1 Grade 0: No Apparent Retinopathy
- **Definition:** Absence of any fundus lesions attributable to diabetic microvascular damage.
- **Morphology:** The retinal vasculature exhibits crisp caliber, distinct branching patterns, healthy optic disc margins with physiological cupping, and an intact foveal avascular zone (FAZ) free from exudation or swelling.
- **Clinical Follow-Up:** Annual re-screening (12 months), accompanied by intensive lifestyle counseling, HbA1c optimization target (<7.0%), and systemic blood pressure management.

### 2.2 Grade 1: Mild Non-Proliferative Diabetic Retinopathy (Mild NPDR)
- **Definition:** Presence of microaneurysms only.
- **Morphology:** Tiny, circular, well-demarcated dark red dots ranging from 15 to 60 micrometers in diameter. Microaneurysms represent focal outpouchings of capillary walls caused by pericyte loss. They occur predominantly in the inner nuclear layer of the retina and are frequently clustered temporal to the fovea.
- **Differential Exclusion:** Must not exhibit flame-shaped hemorrhages, hard exudates, cotton-wool spots, or venous anomalies.
- **Clinical Follow-Up:** Re-screening within 6 to 12 months. Routine baseline visual acuity testing. If visual acuity drops below 6/12 Snellen, order baseline Optical Coherence Tomography (OCT) to rule out subclinical macular edema.

### 2.3 Grade 2: Moderate Non-Proliferative Diabetic Retinopathy (Moderate NPDR)
- **Definition:** Vascular lesions exceeding microaneurysms alone, but falling short of the threshold for Severe NPDR.
- **Morphological Lesions:**
  1. *Dot and Blot Hemorrhages:* Deep intraretinal hemorrhages located in the inner nuclear and outer plexiform layers, presenting as round, darker red spots with fuzzy borders.
  2. *Flame Hemorrhages:* Superficial hemorrhages in the nerve fiber layer with striated, feathered borders oriented along nerve axons.
  3. *Hard Exudates:* Discrete, waxy, yellow-white deposits with crisp borders, composed of lipoprotein precipitates extravasated through incompetent capillary endothelia. Frequently arranged in rings (circinate retinopathy) around leaking microaneurysms.
  4. *Cotton-Wool Spots (Soft Exudates):* Fluffy, superficial, grayish-white patches with indistinct feathered margins, representing axoplasmic stasis in the nerve fiber layer following precapillary arteriolar occlusion.
- **Clinical Follow-Up:** Comprehensive dilated examination by an ophthalmologist within 3 to 6 months. High-resolution Spectral Domain OCT (SD-OCT) of the macula to evaluate central subfield thickness (CST).

### 2.4 Grade 3: Severe Non-Proliferative Diabetic Retinopathy (Severe NPDR)
- **Definition:** Pre-proliferative state characterized by extensive capillary non-perfusion and retinal ischemia, evaluated via the validated **"4-2-1 Rule"** of the Early Treatment Diabetic Retinopathy Study (ETDRS).
- **The 4-2-1 Diagnostic Rule:** The patient qualifies for Grade 3 if the retinal fundus exhibits **any one** of the following criteria in the absence of proliferative changes:
  - **"4" — Hemorrhages/Microaneurysms:** Definite intraretinal hemorrhages and microaneurysms in each of the four retinal quadrants (typically $\ge 20$ individual discrete lesions per quadrant, benchmarked against ETDRS Standard Photograph 2A).
  - **"2" — Venous Beading:** Definite venous caliber irregularity, segmentation, and focal constriction resembling a string of sausages in two or more retinal quadrants.
  - **"1" — IRMA:** Prominent Intraretinal Microvascular Abnormalities (dilated, tortuous shunt vessels running within the retinal architecture without crossing retinal vessels or breaching the internal limiting membrane) in one or more quadrants.
- **Progression Risk:** Patients with Severe NPDR face an estimated 52% probability of progressing to vision-threatening Proliferative DR within one year if left unmonitored.
- **Clinical Follow-Up:** Urgent vitreoretinal referral within 2 to 4 weeks. Multi-quadrant Fundus Fluorescein Angiography (FFA) to map capillary non-perfusion zones and evaluate indications for prophylactic Panretinal Photocoagulation (PRP) or Anti-VEGF therapy.

### 2.5 Grade 4: Proliferative Diabetic Retinopathy (PDR)
- **Definition:** The presence of pathologic neo-angiogenesis in response to profound retinal ischemia mediated by Vascular Endothelial Growth Factor (VEGF).
- **Morphological Hallmarks:**
  1. *Neovascularization of the Disc (NVD):* Fragile, disorganized new blood vessels budding on or within 1 disc diameter of the optic nerve head. High-risk PDR is defined as NVD $\ge 1/4$ to $1/3$ of the disc area, or any NVD accompanied by preretinal or vitreous hemorrhage.
  2. *Neovascularization Elsewhere (NVE):* Sprouting of abnormal fibrovascular fronds along the main retinal vascular arcades or peripheral retina, breaching the internal limiting membrane.
  3. *Preretinal (Subhyaloid) Hemorrhage:* Boat-shaped or D-shaped accumulations of blood trapped between the retina and the posterior vitreous face, exhibiting a flat upper horizontal fluid level.
  4. *Vitreous Hemorrhage:* Frank extravasation of blood into the vitreous gel, obscuring retinal details and causing sudden, profound visual loss.
  5. *Fibrovascular Proliferation & Tractional Retinal Detachment (TRD):* Maturation of vascular complexes into contractile fibrous membranes that pull the neurosensory retina away from the underlying retinal pigment epithelium (RPE), manifesting as taut, tented, immobile retinal elevations without retinal breaks.
- **Clinical Urgency:** **Immediate Emergency Vitreoretinal Referral within 24 to 72 hours.**

### 2.6 Diabetic Macular Edema (DME) / Diabetic Maculopathy
Diabetic macular edema is the leading cause of moderate visual impairment in diabetic patients and can occur at any ICDR grade:
- **Clinically Significant Macular Edema (CSME - ETDRS Definition):**
  - Retinal thickening at or within 500 $\mu\text{m}$ of the foveal center.
  - Hard exudates at or within 500 $\mu\text{m}$ of the foveal center if associated with adjacent retinal thickening.
  - A zone of retinal thickening $\ge 1$ disc area in size, any portion of which is located within 1 disc diameter of the foveal center.
- **Center-Involved DME (CI-DME):** Retinal thickening involving the central 1-mm subfield on SD-OCT. Standard treatment consists of intravitreal Anti-VEGF pharmacotherapy (e.g., Bevacizumab 1.25 mg, Ranibizumab 0.5 mg, or Aflibercept 2.0 mg).

---

## 3. Fundus Photography Standardized Acquisition Protocol

High diagnostic accuracy requires standardized image capture. The mobile and web platforms interface with tabletop digital fundus cameras (e.g., Topcon, Canon, Zeiss) and certified portable handheld units deployed at Sargodha pilot screening desks.

```
+----------------------------------------------------------------------------------------------------+
|                         STANDARDIZED DUAL-FIELD RETINAL ACQUISITION PROTOCOL                       |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|            [Field 1: Disc-Centered]                        [Field 2: Macula-Centered]              |
|                                                                                                    |
|              +-------------------+                           +-------------------+                 |
|              |         |         |                           |         |         |                 |
|              |   (O)   |         |                           |         |   (O)   |                 |
|              |  Optic  |         |                           |         |  Optic  |                 |
|              |  Disc   |         |                           |         |  Disc   |                 |
|              |---------+---------|                           |---------+---------|                 |
|              |         |    *    |                           |         |         |                 |
|              |         |  Fovea  |                           |    *    |         |                 |
|              |         |         |                           |  Fovea  |         |                 |
|              +-------------------+                           +-------------------+                 |
|            Optic disc centered in frame.                   Fovea centered at intersection of       |
|            Captures nasal periphery and                   horizontal and vertical axes.            |
|            major vascular arcades.                        Evaluates macula and temporal vessels.   |
+----------------------------------------------------------------------------------------------------+
```

### 3.1 Field of View and Framing Specifications
- **Optical Standard:** 45-degree or 50-degree non-mydriatic or mydriatic digital fundus photography.
- **Two Standard Mandatory Fields per Eye:**
  - **Field 1 (Optic Disc-Centered):** Position the internal fixation target so the optic nerve head is precisely centered in the frame. This field optimizes visibility of the nasal retina, peripapillary region, and superior/inferior temporal vascular arcades.
  - **Field 2 (Macula-Centered):** Position the fixation target so the fovea centralis is centered at the exact crosshair of the optical frame. This field provides critical resolution for detecting foveal microaneurysms, perifoveal capillary dropout, and circinate exudate rings.

### 3.2 Environmental Conditions and Patient Positioning
1. **Ambient Lighting:** Dim examination room lighting (illuminance $< 5$ lux) to promote natural physiological pupillary dilation in non-mydriatic mode. Extinguish overhead fluorescent lamps; prevent direct sunlight or specular reflections on camera oculars.
2. **Ergonomic Alignment:**
   - Adjust chair and table height so the patient sits upright without straining neck or back.
   - Position chin firmly in the chin rest cup; ensure forehead rests flush against the padded forehead band.
   - Align the patient's external canthus with the canthal height alignment marker on the camera head armature.
3. **Patient Instruction:** Instruct the patient to keep both eyes wide open, breathe normally, and fixate steadily on the green or orange internal fixation LED target. Remind the patient to blink once immediately before image capture to restore a smooth, uniform tear film.

### 3.3 Pupillary Dilation Protocol (Mydriasis)
1. **Minimum Pupil Threshold:** Reliable non-mydriatic 45-degree imaging requires a minimum unconstricted pupil diameter of **$\ge 3.5\text{ mm}$**.
2. **Mydriatic Assessment:** If natural pupillary diameter remains $< 3.5\text{ mm}$ after 5 minutes of dark adaptation, or if dense media opacities preclude adequate illumination:
   - Verify the patient has no documented history of angle-closure glaucoma or shallow anterior chamber depths (van Herick Grade $\le 2$ on slit lamp).
   - Instill 1 drop of **Tropicamide 0.5% or 1.0%** ophthalmic solution into each eye.
   - Wait 15 to 20 minutes to achieve pharmacological dilation ($\ge 6.0\text{ mm}$).
   - Inform the patient that visual blurring for reading and photophobia will persist for 2 to 4 hours, and advise against driving or operating machinery during this period.

### 3.4 Handling Media Opacities & Cataract Artifacts
1. **Nuclear Sclerosis:** Yellow-brown nuclear cataract scatter reduces blue/green light transmission, creating a washed-out, dark yellowish tint across the image. Increase flash intensity by $+1$ to $+2$ increments while monitoring for glare saturation.
2. **Cortical & Posterior Subcapsular Spoke Opacities:** Sectoral lens spokes cast dark shadows or focal radial wedges across the retina. Instruct the patient to adjust fixation slightly ($2^\circ$ to $5^\circ$) or shift the camera objective slightly off-axis to image through clear lens apertures.
3. **Vitreous Hemorrhage / Asteroid Hyalosis:** Highly reflective suspended calcium soaps or diffuse vitreous haze cause massive backscatter. Utilize split-focus assist bars to achieve optimal retinal plane focus rather than focusing on suspended vitreous debris.

### 3.5 Operator Artifact Recognition & Rejection Criteria
Images exhibiting any of the following technical artifacts must be rejected immediately at the point of care, corrected, and re-acquired prior to patient discharge:
- **Lens Dust Spots:** Fixed, circular, translucent dark spots that remain stationary across different patients. *Resolution:* Clean the objective lens with optical-grade lens paper and 99% anhydrous isopropyl alcohol.
- **Eyelash and Lid Shadows:** Dense, dark vertical or curving fringes obscuring the upper or lower retinal fields. *Resolution:* Instruct the patient to open wide; if dermatochalasis or ptosis is present, gently elevate the upper eyelid against the orbital rim using a sterile cotton-tipped applicator (never touch the globe).
- **Corneal Reflection & Glare Halos:** Bright, crescent-shaped white or rainbow-colored flashes across the periphery, caused by camera objective misalignment relative to the corneal apex. *Resolution:* Re-center the working distance alignment dots until the crescent disappears.
- **Motion Blur & Defocus:** Blurring of fine capillary details and vessel margins caused by saccadic eye movement or poor focal tracking. Split-line focusing indicators must be crisply aligned into a single continuous bar before triggering exposure.

### 3.6 Local Heuristic Out-Of-Distribution (OOD) & Image Quality Enforcement
The application incorporates a multi-tier, offline-capable image validation engine (`gemini_validator.py` and local quality gate):
- **Brightness & Illumination Check:** Images with mean pixel brightness $< 25.0$ (severe underexposure) or $> 230.0$ (overexposed glare blowout) are flagged as ungradable.
- **Contrast & Sharpness Analysis:** Laplacian variance and high-frequency edge gradients are analyzed. Images falling below the sharpness threshold ($\text{Var}(\Delta I) < 100.0$) trigger an automated `BLUR_DETECTED` warning.
- **Entropy & Dynamic Range:** Retinal images must exhibit color channel distribution consistent with hemoglobin and melanin absorption spectra (red-channel dominant, green-channel capillary contrast). Monochromatic, corrupted, or non-ocular images (e.g. photos of walls or documents) are rejected with error code `ERR_OOD_NON_RETINAL`.

---

## 4. Step-by-Step Software Workflows: Mobile and Web Platforms

### 4.1 Clinician Authentication & Multi-Factor Access
1. **Access Point:** Navigate to the secure staging/production URL (web portal) or open the verified Expo React Native mobile application on designated clinical tablets.
2. **Credentials:** Authenticate using institutional email and password. Clinician accounts must have been previously verified via the PMDC credentialing procedure (`is_verified = TRUE`, `verification_status = 'approved'`).
3. **Session Management:** The client receives a signed JSON Web Token (JWT) from Supabase Auth. Sessions enforce automatic idle timeout after 15 minutes of inactivity in clinical environments to prevent unauthorized data exposure.

```
+----------------------------------------------------------------------------------------------------+
|                             CLINICIAN DELEGATED ACCESS & SCAN WORKFLOW                             |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|   [Patient Check-In] --------> Generates One-Time Delegation Code (e.g. "K7M9-2P4Q")               |
|                                                                                                    |
|   [Clinician Portal] --------> Calls RPC `claim_clinician_access(p_code)`                          |
|                                  | (alias: `redeem_clinician_grant(p_grant_code)`)                 |
|                                  +---> Validates: active, unexpired (<24h), unredeemed             |
|                                  +---> Binds clinician UUID to patient scan record                 |
|                                  +---> Elevates Row Level Security (RLS) access                    |
|                                                                                                    |
|   [Fundus Image Review] -----> Decrypts authenticated HTTPS image URL via Supabase Storage         |
|                                  |                                                                 |
|                                  +---> Inspects raw image via high-resolution pan/zoom viewport     |
|                                  +---> Evaluates AI Model Prediction (Grades 0–4)                  |
|                                  +---> Confirms or Reclassifies Diagnosis                          |
|                                  +---> Appends clinical rationale (`clinician_notes`)              |
|                                                                                                    |
|   [Diagnostic Record] -------> Generates HMAC-SHA256 Scan Receipt & Enforces Row Immutability      |
+----------------------------------------------------------------------------------------------------+
```

### 4.2 Delegation Grant Redemption Workflow
To comply with the Prevention of Electronic Crimes Act (PECA 2016) and avoid Broken Object-Level Authorization (BOLA), clinicians cannot arbitrarily query patient records. Patient data is accessed strictly via explicit delegation grants:
1. When a patient registers at the intake desk, the system creates an ephemeral, single-use 8-character alphanumeric delegation code (valid for 24 hours).
2. The clinician selects **"Redeem Patient Scan"** in the mobile/web interface and inputs the code.
3. The application executes the PostgreSQL stored procedure:
   ```sql
   SELECT public.claim_clinician_access(
       p_code := 'K7M92P4Q'
   );
   ```
   *(Note: The procedure `claim_clinician_access` accepts a single parameter `p_code TEXT`, deriving the clinician identity directly from `auth.uid()` in PostgreSQL to enforce anti-BOLA security. The backwards-compatible alias `public.redeem_clinician_grant(p_grant_code := 'K7M92P4Q')` is also supported.)*
4. The database atomically verifies code validity, checks that `status = 'active'` and `expires_at > NOW()`, marks the grant redeemed, binds the clinician UUID to the grant, and establishes a secure relation authorizing the clinician to view the patient's fundus scans under Row Level Security (RLS).

### 4.3 High-Resolution Retinal Image Inspection
1. The clinician opens the authenticated scan viewer.
2. **Pan & Pinch-to-Zoom:** The viewer supports fluid pan, rotate, and continuous zoom up to $400\%$ magnification, enabling granular inspection of the foveal avascular zone (FAZ), peripapillary disc margins, and peripheral vascular bifurcations.
3. **Color Channel Toggling:** Clinicians can toggle a green-channel (red-free equivalent) filter. Green-light visualization enhances optical contrast for retinal microaneurysms, hemorrhages, and nerve fiber layer defects by absorbing red background pigment reflection.

### 4.4 Diagnostic Confirmation, Reclassification & Logging
1. The interface displays the automated screening output:
   - **Predicted ICDR Grade:** Grade 0 to Grade 4.
   - **Disease Confidence Distribution:** Five-class probability distribution across all grades.
   - **Referable Status:** Non-Referable (Grades 0–1) vs. Referable Diabetic Retinopathy (Grades 2–4).
2. **Clinical Adjudication:** The clinician selects one of three actions:
   - **Confirm Prediction:** The clinician concurs with the AI grade.
   - **Reclassify Diagnosis:** If clinical findings differ (e.g., subtle IRMA observed indicating Grade 3 where AI predicted Grade 2), the clinician overrides the score, selects the definitive clinical grade, and enters explanatory rationale in `clinician_notes`.
   - **Mark Ungradable:** If poor optical clarity prevents definitive classification, the scan is flagged for immediate re-imaging or formal slit-lamp biomicroscopy.
3. **Submitting Clinical Review:** Submitting the review executes an atomic database transaction that updates the scan state, records clinician identity, captures the timestamp, and locks the review record against subsequent tampering.

### 4.5 Cryptographic Verification: HMAC-SHA256 Scan Receipts
1. To ensure medical-legal integrity and satisfy forensic compliance standards, every completed screening scan produces a deterministic, tamper-evident cryptographic receipt.
2. **Receipt Generation:** The application runtime (`app.py`) computes a deterministic HMAC-SHA256 signature over the screening artifact payload:
   $$\text{Receipt} = \text{HMAC-SHA256}(K_{\text{secret}}, \text{image\_sha256} : \text{grade} : \text{probs\_str} : \text{model\_version} : \text{patient\_str} : \text{timestamp})$$
   Here, `image_sha256` is the SHA-256 digest of raw fundus pixels, `grade` is the predicted ICDR grade (0–4), `probs_str` is the comma-separated 5-class probability vector, `model_version` identifies the deployed checkpoint (e.g., `retfound_v1`), `patient_str` binds the patient UUID (or `anonymous`), and `timestamp` records UNIX epoch seconds. The resulting hexadecimal signature is stored alongside the scan record in PostgreSQL for forensic auditability and non-repudiation.
3. **Scan Immutability:** Migration trigger `protect_scan_immutability()` prevents subsequent modification of the image file, patient linkage, or AI inference payload once written to PostgreSQL, guaranteeing non-repudiation in clinical malpractice or audit evaluations.

---

## 5. Clinical Risk Escalation & Emergency Protocol

### 5.1 Protocol for Grade 4 Severe PDR and Acute Vision Loss
Proliferative Diabetic Retinopathy with high-risk characteristics, pre-retinal/vitreous hemorrhage, or tractional retinal detachment threatens permanent, irreversible blindness within days if untreated.

```
+----------------------------------------------------------------------------------------------------+
|                               EMERGENCY CLINICAL ESCALATION PATHWAY                                |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|    AI Screening Output: Grade 4 (PDR) OR Patient Reports Acute Vision Drop / Floaters / Flashes     |
|                                              |                                                     |
|                                              v                                                     |
|    [Point-of-Care Action]                                                                          |
|    1. Operator / Screening Nurse immediately notifies on-site Attending Clinician.                 |
|    2. Clinician performs immediate dilated slit-lamp biomicroscopy.                                |
|    3. Verify presence of: NVD, Vitreous Hemorrhage, Neovascular Glaucoma (Rubeosis Iridis).         |
|                                              |                                                     |
|                                              v                                                     |
|    [Dispatch Emergency Referral Slip] (Time Window: < 24–72 Hours)                                 |
|    Generate official printed referral form with HMAC scan receipt and fundus photographic prints.  |
|                                              |                                                     |
|                     +------------------------+------------------------+                            |
|                     |                                                 |                            |
|                     v                                                 v                            |
|        [Public / Academic Pathway]                      [Charitable / Subsidized Pathway]         |
|        Dr. Faisal Masood Teaching Hospital /           LRBT Secondary Eye Hospital,               |
|        DHQ Sargodha (Eye Department OPD)                Shahpur Saddar (Vitreoretinal Unit)        |
|        Helpline: 048-9230340                           Helpline: 0486-6310965 / 0315-7280051       |
|                     |                                                 |                            |
|                     +------------------------+------------------------+                            |
|                                              |                                                     |
|                                              v                                                     |
|                                 [Private Emergency Pathway]                                        |
|                                 Niazi Welfare Foundation Teaching Hospital                         |
|                                 (Niazi Medical Complex, Club Road Sargodha)                        |
|                                 Retina Desk: 048-3727144 / 0317-1777509                            |
|                                              |                                                     |
|                                              v                                                     |
|                   [Regional Apex Center — Complex 23G/25G MIVS Vitrectomy]                         |
|                   Al-Shifa Trust Eye Hospital, Balkasar / Chakwal (0543-568000)                    |
|                   King Edward Medical University / Mayo Hospital, Lahore                           |
+----------------------------------------------------------------------------------------------------+
```

### 5.2 Verified Sargodha Referral Directory

#### 1. Public Tertiary Academic Center:
- **Institution:** Dr. Faisal Masood Teaching Hospital / Sargodha Medical College (SMC / UOS)
- **Address:** Khushab Road, near Katchery Bridge, Sargodha, Punjab 40100
- **Direct Administration / Eye Clinic Helpline:** `048-9230340`
- **Clinical Lead:** Prof. Dr. Hashim Imran, Head of Department of Ophthalmology (MBBS, FCPS)
- **Key Capabilities:** Outpatient eye clinics (OPD), general ophthalmic surgery, ultrasound B-scan, laser photocoagulation, acute ocular trauma triage.

#### 2. Specialized Charitable Vitreoretinal Center:
- **Institution:** Layton Rahmatulla Benevolent Trust (LRBT) Secondary Eye Hospital, Shahpur
- **Address:** Mehria Town, Sargodha Road, Shahpur Saddar, District Sargodha, Punjab
- **Direct Helplines:** `0486-6310965` / `0486-6310966` / Mobile: `0315-7280051`
- **Institutional Email:** `shahpur@lrbt.org.pk`
- **Key Capabilities:** 100% free care for underprivileged patients; dedicated Medical & Vitreo-Retina Unit; Optical Coherence Tomography (OCT); Fundus Fluorescein Angiography (FFA); Intravitreal Anti-VEGF injections (Bevacizumab); Argon Retinal Photocoagulation Laser.

#### 3. Private Vitreoretinal Center:
- **Institution:** Niazi Welfare Foundation Teaching Hospital / Niazi Medical Complex
- **Address:** 103 Club Road, near Club Chowk / Railway Road, Sargodha, Punjab
- **Direct Helplines:** `048-3727144` / `048-3727148` / Mobile: `0317-1777509` / `0321-6042122`
- **Clinical Lead:** Dr. Amir Qadeer Malik, Consultant Vitreo-Retinal Specialist (MBBS, FCPS, MCPS, DLO)
- **Key Capabilities:** Vitreo-retinal consultation and surgical intervention, micro-incision vitreoretinal surgery (MIVS), diabetic macular edema treatment, laser photocoagulation.

#### 4. Specialized Private Laser Center:
- **Institution:** Zaheer Laser Eye Centre
- **Address:** Block-A, Main Satellite Town Road, Satellite Town, Sargodha, Punjab
- **Direct Helplines:** `042-34500888` / `048-3210000`
- **Clinical Lead:** Dr. Bilal Zaheer Qureshi, Consultant Eye Surgeon & Vitreoretinal Specialist (MBBS, FCPS, FICO)
- **Key Capabilities:** Specialized retinal laser photocoagulation, vitreoretinal surgery, diagnostic fundus imaging, macular evaluation.

#### 5. Regional Apex Catchment Center (Complex Surgical Vitrectomy):
- **Institution:** Al-Shifa Trust Eye Hospital (Chakwal Regional Apex Hub)
- **Address:** Talagang Road, near Balkasar Interchange (M-2 Motorway), Chakwal, Punjab
- **Direct Helplines:** `0543-568000` / Apex Rawalpindi Hospital: `051-5487821` / UAN: `051-111-25-74-43`
- **Key Capabilities:** Tertiary/quaternary apex vitreoretinal referral center; 23-gauge and 25-gauge Pars Plana Vitrectomy (PPV) for complex tractional retinal detachments, severe proliferative vitreoretinopathy (PVR), silicone oil/gas endotamponade, and pediatric diabetic vitrectomy.

### 5.3 Point-of-Care Red-Flag Symptoms & Immediate Action Rules
If any patient—regardless of AI grade—reports any of the following acute symptoms, the operator must bypass routine processing and trigger an **Emergency Clinical Alert**:
1. **Sudden painless loss or severe dimming of vision in one or both eyes** (suspicion of dense vitreous hemorrhage or central retinal artery/vein occlusion).
2. **A dark curtain, veil, or shadow progressing across the visual field** (suspicion of rhegmatogenous or tractional retinal detachment).
3. **Sudden onset of persistent photopsia (flashes of light) accompanied by a shower of black floaters or cobwebs** (suspicion of acute posterior vitreous detachment with retinal tear or avulsion of neovascular fronds).
4. **Severe ocular pain, redness, nausea, and headache with halo vision around lights** (suspicion of neovascular glaucoma secondary to anterior segment ischemia with rubeosis iridis).

**Mandatory Immediate Actions:**
1. Keep the patient at the clinic under staff observation; do not discharge unassisted.
2. Provide a formal printed referral slip stamped by the on-site physician.
3. Telephonically alert the receiving eye unit (e.g. LRBT Shahpur `0486-6310965` or DHQ Sargodha `048-9230340`).
4. In cases of acute pain, systemic distress, or mobility compromise, dial the Punjab Emergency Service **Rescue 1122** for assisted ambulance transfer.
