# Sprint 1 Remaining Blockers & Sprint 2 Backlog

**Target Project:** Diabetic Retinopathy Diagnostic Application (`s:/unimate/diabetic`)  
**Sprint:** Sprint 1 — Security, Privacy & Integrity Remediation  
**Status:** **ALL 10 SPRINT 1 SECURITY TARGETS RESOLVED; PRODUCTION DEPLOYMENT REMAINS BLOCKED PENDING SPRINT 2**

---

## 1. Sprint 1 Outcome

Sprint 1 successfully resolved and independently verified all 10 targeted security and data integrity vulnerabilities:
- `SEC-01` (BOLA in clinician grant claim) — **REMEDIATED**
- `SEC-02` (Fail-open JWT authentication) — **REMEDIATED**
- `ARCH-01` (Client-side scan persistence) — **REMEDIATED**
- `SEC-03` (CORS wildcard reflection) — **REMEDIATED**
- `SEC-04` (Unverified clinician scan/storage access) — **REMEDIATED**
- `SEC-06` (Unconstrained scan record mutation) — **REMEDIATED**
- `SEC-07` (Missing API rate limiting) — **REMEDIATED**
- `SEC-08` (Weak client grant code generation) — **REMEDIATED**
- `PRIV-01` (Gemini PHI transmission controls & storage DELETE) — **REMEDIATED**
- `PR-08` (Exposed API key in `.env`) — **REMEDIATED**

However, in accordance with the Execution Rules, the application **remains NOT ready for production** due to remaining clinical usability, ML pipeline, and packaging blockers scheduled for Sprint 2.

---

## 2. Active Deployment Blockers (Scheduled for Sprint 2)

| Issue ID | Module | Severity | Summary & Root Cause | Planned Sprint 2 Action |
| :--- | :--- | :---: | :--- | :--- |
| **QA-01** | `mobile/app/(tabs)/clinicians.tsx` | **Critical** | **Blind Clinician Reviews**: Inspection modal displays numeric grades but completely omits retinal image preview, blocking clinical second opinions. | Fetch and render fundus image using signed Supabase storage URL with zoom/pan inside modal. |
| **PR-01** | `Dockerfile` | **Critical** | **Container Crash on Startup**: `Dockerfile` omits `gemini_validator.py`, causing `ModuleNotFoundError` when imported by `app.py`. | Add `COPY gemini_validator.py .` to `Dockerfile`. |
| **PR-07** | `gunicorn.conf.py` | **Critical** | **Gunicorn Thread Starvation**: 4-thread micro-pool starves under slow external I/O or concurrent inference. | Configure 2 workers with 4 threads each, or decouple inference via asynchronous worker queue. |
| **ML-01** | `85.ipynb` | **Critical** | **Training Data Leakage**: Augmentation applied before dataset split; augmented siblings cross train/val/test sets. | Re-split dataset strictly at patient/image level before applying offline/online data augmentation. |
| **ARCH-06** | `app.py`, `mobile/app/(tabs)/index.tsx` | **High** | **Missing Grad-CAM**: Model returns only raw numerical scores without lesion localization. | Implement Grad-CAM heatmap extraction from DenseNet-121 and render overlay in mobile UI. |
| **ML-02** | `app.py` | **High** | **Model Architecture Mislabeling**: Model is named RETFound but runs standard DenseNet-121. | Correct system documentation, UI labels, and model references to accurately reflect DenseNet-121. |
| **ML-03** | `app.py:predict_grade` | **High** | **Omitted Input Normalization**: Model receives raw [0, 255] RGB values rather than ImageNet normalization. | Insert proper ImageNet z-score normalization (`tf.keras.applications.densenet.preprocess_input`). |
| **UX-01** | `mobile/app/(tabs)/index.tsx` | **High** | **Diagnostic Overclaiming**: UI labels automated AI output as "Diagnosis" rather than an investigational screening aid. | Revise all copy to "Automated DR Screening Assessment" and emphasize mandatory clinical confirmation. |
| **A11Y-01** | `mobile/constants/Colors.ts` | **High** | **Color Contrast Failures (WCAG 1.4.3)**: Dark mode primary buttons fail at 2.62:1; History badges fail at 2.39:1. | Adjust color tokens in `Colors.ts` to achieve minimum 4.5:1 contrast ratio. |
| **A11Y-02** | `mobile/app/(tabs)/index.tsx` | **High** | **Silent AI Prediction Delivery (WCAG 4.1.3)**: Screen reader users receive no audio notification when AI assessment completes. | Add `accessibilityLiveRegion="assertive"` and trigger `AccessibilityInfo.announceForAccessibility`. |
| **PR-14** | Application-wide | **High** | **Zero Error Monitoring / APM**: No error tracking (e.g. Sentry) or APM exists. | Integrate Sentry SDK across Flask backend and Expo mobile client. |

---

## 3. Sprint 2 Proposed Focus Areas

1. **Sprint 2A: Clinical Usability & Visual Explainability (`QA-01`, `ARCH-06`, `UX-01`)**
   - Implement retinal fundus image inspection with pinch-to-zoom inside the clinician review modal.
   - Implement Grad-CAM heatmap generation and overlay visualization in mobile screening view.
   - Refactor UI copy to strictly reflect screening aid status and anchor high-severity clinical disclaimers.

2. **Sprint 2B: Packaging, Infrastructure & Observability (`PR-01`, `PR-04`, `PR-07`, `PR-14`)**
   - Fix `Dockerfile` and `docker-compose.yml` to bundle `gemini_validator.py` and environment configurations.
   - Scale Gunicorn concurrency and configure Sentry error tracking.

3. **Sprint 2C: Performance Optimization & Mobile Ingestion (`PERF-01`, `PERF-02`, `PERF-05`)**
   - Transition backend to 7.31x faster TensorFlow Lite model.
   - Eliminate image double-decoding in preprocessing pipeline.
   - Transition mobile upload from Base64 JSON to binary multipart form data.
