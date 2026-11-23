# Sprint 2 Test Execution & Verification Report

**Sprint:** Sprint 2 (Track 2: ML Pipeline Validation)  
**Executed By:** Independent QA / Reviewer (`reviewer_track2`)  
**Date:** 2026-11-22  
**Test Environment:** Windows (PowerShell), Python 3.12.10, pytest-9.1.1, TensorFlow 2.18 / Keras  

---

## 1. Executive Summary

This report documents the independent test execution for Sprint 2 (Track 2: Machine Learning Pipeline Validation), covering remediations for defects **ML-01**, **ML-02**, **ML-03**, **ML-04**, and **ML-05**. 

Testing was performed using isolated, automated test runners in the project virtual environment (`.venv\Scripts\pytest.exe`) and direct Python validation scripts without coder self-certification.

### Summary Metrics
| Test Scope | Target Files | Collected | Passed | Failed | Skipped | Pass Rate |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Sprint 2 Targeted Suite** | `tests/test_gemini_validator.py`<br>`tests/test_model.py`<br>`tests/test_api.py` | 49 | 48 | 0 | 1 (`live_gemini`) | **100%** |
| **Full Regression Suite** | `tests/` (All test suites) | 131 | 129 | 1 (`test_e2e_workflows.py`) | 1 (`live_gemini`) | **99.2%** |

---

## 2. Targeted Sprint 2 Test Suite Execution

### Command:
```powershell
.venv\Scripts\pytest.exe tests/test_gemini_validator.py tests/test_model.py tests/test_api.py -v
```

### Exact Verbatim Output:
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

================== 48 passed, 1 skipped in 63.97s (0:01:03) ===================
```

---

## 3. Full Repository Regression Suite Execution

### Command:
```powershell
.venv\Scripts\pytest.exe tests/ -v
```

### Summary Results:
- **Total Tests Collected:** 131 items
- **Passed:** 129
- **Skipped:** 1 (`test_live_gemini_integration` — skipped due to offline mock testing environment without live `GEMINI_API_KEY`)
- **Failed:** 1 (`tests/test_e2e_workflows.py::test_workflow_image_preprocessing_pipeline`)
- **Exit Code:** 1
- **Duration:** 101.60 seconds

### Failure Investigation:
- **Test:** `tests/test_e2e_workflows.py::test_workflow_image_preprocessing_pipeline`
- **Failure Traceback:**
  ```
  tests/test_e2e_workflows.py:363: in test_workflow_image_preprocessing_pipeline
      sanitized_bytes, _ = validate_image_bytes(gray_bytes)
  gemini_validator.py:283: in validate_image_bytes
      validate_image_entropy_and_variance(rgb_img)
  gemini_validator.py:217: in validate_image_entropy_and_variance
      raise InvalidImageError(
  E   gemini_validator.InvalidImageError: Image has insufficient visual entropy/variance for a fundus photo (flat gray or uniform image detected; spatial std=0.00, color std=0.00).
  ```
- **Root Cause Analysis:**  
  `test_e2e_workflows.py` (authored during Phase 0 / Sprint 1 as part of Track 3 E2E workflow baseline) defined a synthetic test helper `generate_synthetic_fundus_image(color_mode="L")` which creates a 100% solid flat gray block `Image.new("L", (width, height), color=128)` with zero spatial variance (`spatial std=0.00`) and zero color variation (`color std=0.00`).
  
  In Sprint 2, remediation for defect `ML-04` introduced strict local rejection of uniform/flat gray images in `validate_image_entropy_and_variance()` to prevent DenseNet-121 from hallucinating Grade 1 (>93% confidence) on uninformative synthetic gray inputs.
  
  Therefore, the failure in `test_workflow_image_preprocessing_pipeline` is not a regression in model logic, but rather an unadapted synthetic test fixture in Track 3 (`test_e2e_workflows.py`) that generates a flat uniform gray square. A genuine grayscale fundus photo (e.g. red-free imaging with visible vessels) possesses spatial standard deviation $\ge 2.0$ and Shannon entropy $\ge 0.5$ and passes validation.

---

## 4. Independent Verification of Specific Sprint 2 Criteria

### 4.1 Local Image Rejection (ML-04)
Independent execution confirmed that non-informative synthetic inputs are rejected before network or inference calls:
- Pure black image (`color=(0, 0, 0)`): Rejected locally with `InvalidImageError` (`max intensity=0.0, mean=0.0`).
- Pure white image (`color=(255, 255, 255)`): Rejected locally with `InvalidImageError` (`min intensity=255.0, mean=255.0`).
- Flat gray image (`color=(128, 128, 128)`): Rejected locally with `InvalidImageError` (`spatial std=0.00, color std=0.00`).
- Blank image: Rejected locally with `InvalidImageError`.

### 4.2 Endpoint Health Model Version (ML-02)
- Request: `GET /api/health`
- Response Payload:
  ```json
  {
    "auth_enforced": false,
    "gemini_configured": false,
    "gemini_validation_enabled": true,
    "model_loaded": true,
    "model_version": "densenet121_ordinal_v1",
    "rate_limiting_enabled": true,
    "scan_integrity_verification": true,
    "status": "healthy"
  }
  ```
- Verified: `model_version` is uniformly `"densenet121_ordinal_v1"`.

### 4.3 Prediction Confidence & Sub-Threshold Formatting (ML-05)
- Standard inference on fundus photograph:
  - `confidence`: `0.5052` (type: `float`, range $0.0 \le C \le 1.0$).
  - `low_confidence`: `False` (type: `bool`).
  - `model_version`: `"densenet121_ordinal_v1"`.
  - `scan_receipt` and `receipt`: present with valid HMAC SHA-256 signature.
- Sub-threshold inference simulation (all probabilities $< 0.50$, e.g. $[0.35, 0.20, 0.10, 0.05, 0.01]$):
  - `grade`: `0`.
  - `confidence`: `0.35` (type: `float`).
  - `low_confidence`: `True` (type: `bool`).
  - Backward compatibility: preserves `grade`, `label`, `probabilities`, and `receipt` intact.

### 4.4 Documentation Validation (ML-01, ML-02, ML-03)
- Inspected `docs/ml_pipeline.md`:
  - DenseNet-121 architecture (7,302,213 parameters, ordinal sigmoid head) is accurately detailed.
  - Data leakage in `85.ipynb` (cross-split contamination from pre-split augmentation) is formally documented with mathematical and clinical impact.
  - Model retraining protocol is explicitly labeled **`BLOCKED — HUMAN APPROVAL REQUIRED`** with step-by-step patient-partitioned retraining guidelines.
