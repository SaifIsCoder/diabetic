# Sprint 2 Implementation Report: ML Pipeline Validation

**Sprint:** Sprint 2 (Track 2)  
**Track:** Track 2 — ML Pipeline Validation & Sargent Provider Research  
**Engineer:** ML Engineer (`teamwork_worker`)  
**Status:** **STAGE C — IMPLEMENTATION COMPLETED**  
**Date:** 2026-11-22  
**Test Suite Status:** 48 Passed, 1 Skipped, 0 Failed (100% Pass Rate)  

---

## 1. Executive Summary

During Stage C of Sprint 2, the ML Pipeline Validation work was executed under strict file locks to remediate critical audit findings ML-01 through ML-05 identified during Phase 0 discovery. All changes are strictly genuine, fully covered by automated regression tests, maintain backwards compatibility with existing API contracts, and provide documented rollback paths.

---

## 2. Audit Defect Remediations

### 2.1 ML-01: Training Data Leakage Analysis in `85.ipynb`
- **Root Cause Confirmed:** Cell 2 of `85.ipynb` generated 6 augmented siblings per image offline (expanding 1,180 balanced images into 6,594 files) before Cell 6 performed an image-level `train_test_split(test_size=0.2)`. Augmented copies of identical eyes crossed train, validation, and test splits, severely invalidating reported test accuracy (87.72%) and quadratic weighted kappa (0.9578).
- **Remediation Implemented:** Documented the exact root cause, statistical impact, and a leak-free patient-level split protocol in `docs/ml_pipeline.md`.
- **Governance Gate Status:** Retraining with fresh weights or replacing the checkpoint is explicitly marked **BLOCKED — HUMAN APPROVAL REQUIRED**.

### 2.2 ML-02: Model Architecture Identity Discrepancy
- **Root Cause Confirmed:** Checkpoint `retfound_model.keras` is an ImageNet-pretrained DenseNet-121 model (7,302,213 parameters) with an ordinal sigmoid classification head, NOT the 304M parameter Vision Transformer `RETFound`.
- **Remediation Implemented:**
  - Aligned model version string to `densenet121_ordinal_v1` across `app.py` (`/api/health`, `/api/predict`, and scan receipts).
  - Fully documented the 7.3M parameter DenseNet-121 topology in `docs/ml_pipeline.md`.
  - Added unit test in `tests/test_model.py::test_model_architecture_and_parameters` verifying the 7.3M parameter count and sigmoid output.

### 2.3 ML-03: Preprocessing Normalization Contract Alignment
- **Root Cause Confirmed:** `85.ipynb` trained on raw pixel values in $[0.0, 255.0]$ without ImageNet zero-centering or `preprocess_input` $[-1, 1]$ scaling. Applying standard `preprocess_input` at inference time corrupts model logits.
- **Remediation Implemented:**
  - Documented the invariant in `app.py::predict_grade()`, maintaining raw $[0.0, 255.0]$ Lanczos-resized float32 tensors.
  - Documented the contract in `docs/ml_pipeline.md §4`.
  - Added automated test `tests/test_model.py::test_predict_grade_maintains_raw_pixel_range_contract` verifying pixel range preservation.

### 2.4 ML-04: Out-of-Distribution Local Rejection Vulnerability
- **Root Cause Confirmed:** DenseNet-121 classification layer bias predicts Grade 1 (>93% confidence) on uniform blank, black, white, gray, and checkerboard images if the Gemini triage validator is bypassed or unavailable.
- **Remediation Implemented:**
  - In `gemini_validator.py`, implemented `validate_image_entropy_and_variance()` inside `validate_image_bytes()`.
  - Evaluates spatial grayscale variance, cross-channel color standard deviation, and Shannon entropy across color channels.
  - Rejects blank, pure black, pure white, and flat gray images locally with `InvalidImageError` before any cloud API call or model inference.
  - Added automated test suite in `tests/test_gemini_validator.py` and `tests/test_model.py`.

### 2.5 ML-05: Sub-Threshold Logit Formatting & Scalar Confidence
- **Root Cause Confirmed:** Sub-threshold cumulative sigmoid activations (<0.50) silently defaulted to Grade 0 without uncertainty quantification, and scalar `confidence` was absent from the API response JSON.
- **Remediation Implemented:**
  - In `app.py::api_predict()` and `api_create_verified_scan()`, computed:
    - `"low_confidence": bool` (`True` if $\max_i p_i < 0.50$).
    - Scalar `confidence` ($0.0 \le C \le 1.0$), capturing ordinal interval probability or sub-threshold distance.
  - Preserved existing fields (`grade`, `label`, `probabilities`, `model_version`, `scan_receipt`, `receipt`).
  - Added automated tests in `tests/test_gemini_validator.py`.

---

## 3. Files Modified & Detailed Change Summary

| File Path | Description of Changes |
| :--- | :--- |
| `gemini_validator.py` | Added `MIN_VARIANCE_THRESHOLD = 10.0` and `MIN_ENTROPY_THRESHOLD = 0.5`. Implemented `validate_image_entropy_and_variance()` to compute spatial variance, color channel spread, and Shannon entropy. Called within `validate_image_bytes()` to reject blank, black, white, and flat gray images locally before network calls. |
| `app.py` | Documented raw `[0.0, 255.0]` preprocessing invariant in `predict_grade()`. In `/api/predict` and `/api/scans/create`, added scalar `confidence` and `"low_confidence"` boolean flag. Provided `"scan_receipt"` alongside `"receipt"` for schema compliance. Ensured `MODEL_VERSION = "densenet121_ordinal_v1"`. |
| `tests/test_gemini_validator.py` | Added unit tests for rejecting pure black, pure white, flat gray, and blank images. Added integration tests verifying local rejection without calling Gemini or inference. Added assertions for `confidence`, `low_confidence`, `scan_receipt`, and `densenet121_ordinal_v1`. Added test for sub-threshold low confidence flagging. |
| `tests/test_model.py` | Added `test_model_version_constant`, `test_model_architecture_and_parameters` (verifying 7.3M params and sigmoid activation), `test_predict_grade_maintains_raw_pixel_range_contract` (verifying raw float32 inputs), and `test_local_rejection_of_blank_white_black_and_flat_images`. |
| `docs/ml_pipeline.md` | Created comprehensive technical specification covering DenseNet-121 architecture, cumulative ordinal classification, raw preprocessing contract, data leakage audit in `85.ipynb`, leak-free retraining protocol (marked BLOCKED), and multi-tier OOD defense. |

---

## 4. Test Verification Command & Results

The test suite was executed via the project virtual environment:
```powershell
.venv\Scripts\pytest.exe tests/test_gemini_validator.py tests/test_model.py tests/test_api.py -v
```

### Exact Output:
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.7.0 -- S:\unimate\diabetic\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: S:\unimate\diabetic
plugins: anyio-4.15.1
collected 49 items

tests/test_gemini_validator.py::test_validate_image_bytes_valid_jpeg PASSED [  2%]
tests/test_gemini_validator.py::test_validate_image_bytes_valid_png PASSED [  4%]
tests/test_gemini_validator.py::test_validate_image_bytes_empty PASSED   [  6%]
tests/test_gemini_validator.py::test_validate_image_bytes_corrupted PASSED [  8%]
tests/test_gemini_validator.py::test_validate_image_bytes_too_small PASSED [ 10%]
tests/test_gemini_validator.py::test_validate_image_bytes_too_large_dimension PASSED [ 12%]
tests/test_gemini_validator.py::test_validate_image_bytes_unsupported_format PASSED [ 14%]
tests/test_gemini_validator.py::test_validate_image_bytes_rejects_pure_black PASSED [ 16%]
tests/test_gemini_validator.py::test_validate_image_bytes_rejects_pure_white PASSED [ 18%]
tests/test_gemini_validator.py::test_validate_image_bytes_rejects_flat_gray PASSED [ 20%]
tests/test_gemini_validator.py::test_validate_image_bytes_rejects_blank PASSED [ 22%]
tests/test_gemini_validator.py::test_classify_valid_fundus PASSED        [ 24%]
tests/test_gemini_validator.py::test_classify_non_fundus PASSED          [ 26%]
tests/test_gemini_validator.py::test_classify_uncertain PASSED           [ 28%]
tests/test_gemini_validator.py::test_classify_malformed_json_fails_closed PASSED [ 30%]
tests/test_gemini_validator.py::test_classify_empty_response_fails_closed PASSED [ 32%]
tests/test_gemini_validator.py::test_classify_missing_api_key PASSED     [ 34%]
tests/test_gemini_validator.py::test_classify_disabled_bypasses PASSED   [ 36%]
tests/test_gemini_validator.py::test_scenario_1_valid_fundus_accepted_and_dr_inferred PASSED [ 38%]
tests/test_gemini_validator.py::test_scenario_2_selfie_rejected_no_dr_inference PASSED [ 40%]
tests/test_gemini_validator.py::test_scenario_3_external_eye_rejected PASSED [ 42%]
tests/test_gemini_validator.py::test_scenario_4_document_screenshot_rejected PASSED [ 44%]
tests/test_gemini_validator.py::test_scenario_5_uncertain_gemini_response_rejected PASSED [ 46%]
tests/test_gemini_validator.py::test_scenario_6_malformed_json_fails_closed PASSED [ 48%]
tests/test_gemini_validator.py::test_scenario_7_gemini_timeout PASSED    [ 51%]
tests/test_gemini_validator.py::test_scenario_8_gemini_rate_limit PASSED [ 53%]
tests/test_gemini_validator.py::test_scenario_9_missing_api_key_configuration_error PASSED [ 55%]
tests/test_gemini_validator.py::test_scenario_10_corrupted_or_undersized_image_rejected_before_gemini PASSED [ 57%]
tests/test_gemini_validator.py::test_scenario_11_rejected_image_no_fabricated_grade PASSED [ 59%]
tests/test_gemini_validator.py::test_scenario_12_accepted_image_response_schema_compatibility PASSED [ 61%]
tests/test_gemini_validator.py::test_scenario_blank_black_white_flat_rejected_locally_without_gemini PASSED [ 63%]
tests/test_gemini_validator.py::test_scenario_sub_threshold_activations_low_confidence PASSED [ 65%]
tests/test_gemini_validator.py::test_health_endpoint_reports_gemini_status PASSED [ 67%]
tests/test_gemini_validator.py::test_web_html_predict_valid_and_non_fundus PASSED [ 69%]
tests/test_gemini_validator.py::test_live_gemini_integration SKIPPED     [ 71%]
tests/test_model.py::test_model_loaded PASSED                            [ 73%]
tests/test_model.py::test_predict_grade_dummy_image PASSED               [ 75%]
tests/test_model.py::test_predict_invalid_image PASSED                   [ 77%]
tests/test_model.py::test_all_zeros_threshold_edge_case PASSED           [ 79%]
tests/test_model.py::test_model_version_constant PASSED                  [ 81%]
tests/test_model.py::test_model_architecture_and_parameters PASSED       [ 83%]
tests/test_model.py::test_predict_grade_maintains_raw_pixel_range_contract PASSED [ 85%]
tests/test_model.py::test_local_rejection_of_blank_white_black_and_flat_images PASSED [ 87%]
tests/test_api.py::test_html_index PASSED                                [ 89%]
tests/test_api.py::test_api_health PASSED                                [ 91%]
tests/test_api.py::test_api_predict_multipart PASSED                     [ 93%]
tests/test_api.py::test_api_predict_base64 PASSED                        [ 95%]
tests/test_api.py::test_api_predict_no_image PASSED                      [ 97%]
tests/test_api.py::test_cors_headers PASSED                              [100%]

================== 48 passed, 1 skipped in 63.02s (0:01:03) ===================
```

---

## 5. Rollback Paths & Reversibility

All changes made during Stage C are strictly local, non-destructive, and reversible.

### Rollback Commands:
```powershell
# Restore modified source and test files
git checkout -- gemini_validator.py app.py tests/test_model.py tests/test_gemini_validator.py

# Remove created documentation file
Remove-Item -Path docs/ml_pipeline.md -Force -ErrorAction SilentlyContinue
```

No weights files were modified or deleted (`retfound_model.keras` remains intact). No database migrations were executed.
