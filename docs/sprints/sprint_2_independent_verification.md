# Sprint 2 Independent Verification Report

**Document ID:** `sprint_2_independent_verification.md`  
**Reviewer:** Independent QA & Adversarial Critic (`reviewer_track2`)  
**Target Sprint:** Sprint 2 (Track 2: ML Pipeline Validation)  
**Parent Orchestrator:** `b5ad92e1-49c3-4295-b192-bc8d0d2807a3`  
**Date of Verification:** 2026-11-22  
**Final Verdict:** **APPROVE (with Track 3 Compatibility Finding)**  

---

## 1. Executive Summary & Review Scope

Under Stage D of the Autonomous Swarm Governance Protocol, this independent evaluation verifies the machine learning pipeline validation work delivered in Sprint 2. The review was conducted without reliance on coder self-certification, auditing source code, running adversarial test probes, checking for integrity violations, and testing failure modes.

### Target Defects Verified:
- **ML-01:** Training data leakage in `85.ipynb` and governance gating of model retraining.
- **ML-02:** Model architecture identity discrepancy (`retfound_model.keras` vs 304M RETFound ViT).
- **ML-03:** Input preprocessing normalization contract alignment ($[0.0, 255.0]$ raw range).
- **ML-04:** Out-of-distribution local rejection vulnerability (synthetic blank/black/white/flat gray).
- **ML-05:** Sub-threshold logit formatting and scalar confidence scoring.

---

## 2. Integrity & Adversarial Audit

As required by the Independent QA / Reviewer Mandate, the codebase was audited for common integrity violations:

| Check | Description | Status | Evidence / Observation |
| :--- | :--- | :---: | :--- |
| **Hardcoded Outputs** | Embeddings of expected test outcomes into production source | **CLEAN** | Inspected `gemini_validator.py` and `app.py`. Dynamic calculations of spatial variance, Shannon entropy, and ordinal confidence are applied to real pixel arrays. |
| **Facade Implementations** | Dummy functions that return static mock values | **CLEAN** | Full statistical and information-theoretic calculations (`np.var`, `np.std`, `np.histogram`, Shannon entropy $-\sum p \log_2 p$) are genuinely implemented in `gemini_validator.py:156-228`. |
| **Task Shortcuts** | Bypassing core logic or skipping model inference | **CLEAN** | The DenseNet-121 model is genuinely loaded via `tf.keras.models.load_model()` and executes forward passes on tensor batches. |
| **Fabricated Logs** | Fabricated test counts or logs | **CLEAN** | Test results were independently reproduced via `.venv\Scripts\pytest.exe`. Output timestamps, test names, and execution times match live run telemetry. |

---

## 3. Detailed Verification of Sprint 2 Remediations

### 3.1 Verification of ML-01: Training Data Leakage & Retraining Governance
- **Observation:** `docs/ml_pipeline.md §5` contains a comprehensive forensic audit of `85.ipynb`.
- **Finding:** Cell 2 generated 6 augmented siblings per image offline before Cell 6 split 6,594 files using random `train_test_split(test_size=0.2)`. Sibling images of identical patient eyes contaminated train ($N=4,747$), val ($N=528$), and test ($N=1,319$) partitions.
- **Governance Gate Check:** In `docs/ml_pipeline.md §6` and `sprint_2_implementation.md §2.1`, model retraining is formally designated:
  ```
  BLOCKED — HUMAN APPROVAL REQUIRED
  ```
  A complete 4-step leak-free patient-partitioned protocol is documented for future execution once unblocked by human governance.

### 3.2 Verification of ML-02: Checkpoint Architecture Identity
- **Observation:** Inspected `retfound_model.keras` and `app.py`.
- **Finding:** Checkpoint has 7,302,213 parameters (ImageNet-pretrained DenseNet-121 backbone with ordinal cumulative sigmoid head), not the 304M parameter RETFound Vision Transformer.
- **Verification:**
  - `app.py:58`: `MODEL_VERSION = "densenet121_ordinal_v1"`.
  - `GET /api/health` returns `"model_version": "densenet121_ordinal_v1"`.
  - `POST /api/predict` returns `"model_version": "densenet121_ordinal_v1"`.
  - `tests/test_model.py::test_model_architecture_and_parameters` verified:
    - Layer count $> 0$
    - Total parameters: $7,000,000 < P < 7,600,000$ (exact: 7,302,213)
    - Final activation: `sigmoid`
    - Output shape: `(None, 5)`

### 3.3 Verification of ML-03: Preprocessing Normalization Contract
- **Observation:** Inspected `app.py::predict_grade()`.
- **Finding:** Training in `85.ipynb` used raw uint8 Lanczos resized images cast to float32 in $[0.0, 255.0]$ without standard ImageNet `preprocess_input` (scaling to $[-1, 1]$ or z-score normalization).
- **Verification:**
  - `app.py:161-177` documents the invariant and maintains `np.asarray(image, dtype=np.float32)` in raw $[0.0, 255.0]$.
  - `tests/test_model.py::test_predict_grade_maintains_raw_pixel_range_contract` passed, confirming maximum pixel value exceeds $1.0$ and stays $\le 255.0$.

### 3.4 Verification of ML-04: Out-of-Distribution Local Image Rejection
- **Observation:** DenseNet-121 biases predict Grade 1 (>93% confidence) on uniform black, white, gray, and checkerboard images when Gemini validator is offline.
- **Implementation:** `gemini_validator.py:156-228` implements `validate_image_entropy_and_variance()` inside `validate_image_bytes()`.
- **Verification:**
  - Pure black (`color=(0,0,0)`): Rejected locally before API call with `InvalidImageError`.
  - Pure white (`color=(255,255,255)`): Rejected locally before API call with `InvalidImageError`.
  - Flat gray (`color=(128,128,128)`): Rejected locally before API call with `InvalidImageError`.
  - Blank black image: Rejected locally before API call with `InvalidImageError`.
  - In all cases, `classify_fundus_image` and `predict_grade` are NOT invoked.

### 3.5 Verification of ML-05: Confidence Formatting & Sub-Threshold Detection
- **Observation:** Prior to Sprint 2, sub-threshold activations ($p_i < 0.50$) defaulted to Grade 0 without low-confidence flagging or a scalar confidence score.
- **Verification:**
  - `POST /api/predict` returns:
    - `"confidence": float` ($0.0 \le C \le 1.0$)
    - `"low_confidence": bool` (`True` if $\max_i p_i < 0.50$)
    - `"scan_receipt"` and `"receipt"`
  - Tested with simulated sub-threshold activations $[0.35, 0.20, 0.10, 0.05, 0.01]$:
    - Yielded `grade: 0`, `confidence: 0.35`, `low_confidence: True`.

---

## 4. Adversarial Findings & Failure Modes

### Finding 1: Compatibility with Track 3 E2E Workflow Test Fixture (Minor / Test Harness)
- **Severity:** Minor (Cross-Sprint Test Harness Dependency)
- **Location:** `tests/test_e2e_workflows.py:362-364`
- **What:** In the full regression suite (`pytest tests/ -v`), 1 test failed: `test_workflow_image_preprocessing_pipeline`.
- **Why:** The test helper `generate_synthetic_fundus_image(color_mode="L")` creates a 100% solid flat gray block (`color=128`, spatial std = 0.0, color std = 0.0). The newly implemented OOD gate in `validate_image_entropy_and_variance` correctly rejects this flat gray block as non-informative.
- **Assessment:** This test failure confirms that the Sprint 2 rejection gate is operating strictly as designed. It does not invalidate Sprint 2 implementation. The test fixture in `tests/test_e2e_workflows.py` belongs to Track 3 (Sprint 3: Patient/Clinician E2E Workflows) and should be updated during Sprint 3 Stage C to synthesize textured grayscale fundus images (with spatial std $\ge 2.0$) or assert the expected rejection.
- **Recommendation:** Accept for Sprint 2. Queue test fixture refactoring for Track 3 (Sprint 3).

---

## 5. Formal Verdict

**Verdict:** **APPROVE**  
All Sprint 2 acceptance criteria have been verified independently. All 48 targeted tests pass cleanly. The model architecture, preprocessing contract, local OOD gate, and confidence formatting are fully implemented, verified, and documented.
