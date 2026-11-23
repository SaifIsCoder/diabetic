# Sprint 2 Audit & Gate Check: ML Pipeline Validation

**Sprint:** Sprint 2 (Track 2)  
**Target:** AI/ML Pipeline, Inference Preprocessing, Model Identity, and Rejection Gates  
**Status:** **STAGE B — PLAN & GATE CHECK APPROVED**  
**Date:** 2026-11-22  

---

## 1. Confirmed Audit Findings & Root Causes

1. **ML-01: Training Data Leakage in `85.ipynb`**
   - *Confirmed Root Cause:* Cell 1 generated 6 augmented siblings per image offline before splitting. Sibling images crossed train/val/test splits, invalidating reported 87.72% accuracy and 0.9578 kappa metrics.
   - *Status:* **BLOCKED — HUMAN APPROVAL REQUIRED** for model retraining with fresh weights. In-sprint scope: Document split methodology, leakage analysis, and retraining protocol in `docs/ml_pipeline.md`.

2. **ML-02: Model Architecture Identity Discrepancy**
   - *Confirmed Root Cause:* Checkpoint `retfound_model.keras` is an ImageNet-initialized `DenseNet121` (7.3M parameters), not the 304M Vision Transformer foundation model `RETFound`.
   - *Status:* Reversible documentation and version identifier alignment approved. Backend `/api/health` reports `densenet121_ordinal_v1`. Model replacement with RETFound remains blocked for human approval.

3. **ML-03: Preprocessing Normalization Alignment**
   - *Confirmed Root Cause:* Training in `85.ipynb` fed raw `[0, 255]` pixel floats into DenseNet121. Applying standard ImageNet `preprocess_input` (`[-1, 1]` or z-score) breaks predictions on the current checkpoint.
   - *Status:* Keep raw `[0.0, 255.0]` inputs consistent with checkpoint weights. Document contract in `docs/ml_pipeline.md`.

4. **ML-04: Out-of-Distribution Rejection Vulnerability**
   - *Confirmed Root Cause:* Dense classification layer bias predicts Grade 1 (>93% confidence) on uniform blank/gray/checkerboard/noise images when Gemini validator is offline.
   - *Status:* Implement local heuristic variance and Shannon entropy checks in `validate_image_bytes()` in `gemini_validator.py` to reject non-informative synthetic inputs locally without requiring cloud API calls.

5. **ML-05: Sub-Threshold Logit Formatting & Missing Scalar Confidence**
   - *Confirmed Root Cause:* Sub-threshold sigmoid activations (<0.5) silently default to Grade 0 without low-confidence flagging. Scalar `confidence` is omitted from `/api/predict` response.
   - *Status:* Calculate scalar confidence based on margin/sigmoid distance, include in API JSON response, and add uncertainty flag if max sigmoid < 0.5.

---

## 2. Governance Gate Check

| Sub-task | Nature | Action / Gate Status |
| :--- | :--- | :--- |
| Retrain DenseNet121 or RETFound with leak-free splits | Destructive / Resource intensive | **BLOCKED — HUMAN APPROVAL REQUIRED** |
| Replace weights file `retfound_model.keras` | Model replacement | **BLOCKED — HUMAN APPROVAL REQUIRED** |
| Document leakage & split protocol | Documentation | **Auto-proceed** |
| Update model version string to `densenet121_ordinal_v1` | Reversible local code | **Auto-proceed** |
| Implement local heuristic variance/entropy gate in `gemini_validator.py` | Reversible local code & test | **Auto-proceed** |
| Include scalar `confidence` and threshold warning in `/api/predict` | Reversible local code & test | **Auto-proceed** |
| Automated unit tests in `tests/test_model.py` and `tests/test_gemini_validator.py` | Automated tests | **Auto-proceed** |

---

## 3. Implementation Plan & File Locks

- **Exclusive File Owner:** `ML Engineer` (`teamwork_worker`)
- **Locked Files:**
  - `gemini_validator.py`
  - `app.py`
  - `tests/test_model.py`
  - `tests/test_gemini_validator.py`
  - `docs/ml_pipeline.md`
- **Rollback Path:**
  - `git checkout -- gemini_validator.py app.py tests/test_model.py tests/test_gemini_validator.py`
  - Delete `docs/ml_pipeline.md`
