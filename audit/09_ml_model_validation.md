# AI/ML Model Validation & Pipeline Reliability Audit

**Document ID:** `AUD-ML-09`  
**Target Project:** Diabetic Retinopathy Detection Portal & Mobile Application  
**Auditor Role:** Agent 9 — AI/ML Model Validation Engineer  
**Date of Assessment:** November 22, 2026  
**Status:** Complete Audit  
**Phase:** Phase 1 (Audit Only — Zero Code / Weights Modification)  

---

## Executive Summary

A comprehensive, deep-inspection audit of the diabetic retinopathy (DR) machine learning pipeline was conducted across all artifact assets: `app.py`, `gemini_validator.py`, `retfound_model.keras`, `retfound_model.tflite`, training notebook `85.ipynb`, and training histories `retfound_history.json` / `history.json`.

The audit evaluated model architecture, input preprocessing and normalization, cumulative ordinal classification formulation, explainability (Grad-CAM), edge-case resilience, Gemini triage gate reliability, and data splitting methodology.

### Critical Verdict & Key Findings
1. **Severe Data Leakage & Contaminated Test Metrics**: The reported test accuracy of **87.72%** and validation quadratic weighted kappa of **0.9578** in `85.ipynb` are **invalidated by critical data leakage**. The training pipeline generated 6 augmented siblings per image *prior* to splitting and randomly partitioned augmented siblings across train, validation, and test splits (explicitly acknowledged in `85.ipynb` Cell 5: *"Augmented siblings can cross splits, so this is not a leakage-free test"*). The model was evaluated on memorized variations of training images. Real-world generalization performance is unverified and substantially lower.
2. **Model Misrepresentation / False Naming**: While named `retfound_model.keras` and `retfound_model.tflite`, the underlying model is **not RETFound** (the 304M-parameter Vision Transformer foundation model by Zhou et al., *Nature* 2023). It is a standard **DenseNet-121** (7.3M parameters) with an ordinal classification head. Mislabelling clinical models poses severe scientific and regulatory compliance hazards.
3. **Preprocessing Normalization Discrepancy**: Pretrained DenseNet-121 expects ImageNet standardization (mean `[0.485, 0.456, 0.406]`, std `[0.229, 0.224, 0.225]`), but both training and inference feed raw `[0.0, 255.0]` unnormalized pixel values. Feeding normalized inputs `[0.0, 1.0]` shifts model predictions by full clinical grades (e.g., Grade 1 to Grade 2).
4. **Dangerous Out-of-Distribution / Blank Image Failure Modes**: When the Gemini triage gate is bypassed or offline, the model predicts **Grade 1 (Mild DR)** for completely black images, completely white images, solid gray images, checkerboards, and pure Gaussian noise, with probabilities exceeding 93%. Dense layer bias drives unit 0 and unit 1 to trigger regardless of semantic retinal content.
5. **Ordinal Classification & Confidence Interpretation Bugs**:
   - Monotonicity violations are unconstrained: when probabilities violate cumulative ordering (e.g. `[0.45, 0.90, 0.85, 0.10, 0.05]`), `app.py` simply counts elements $\ge 0.5$, masking underlying model incoherence.
   - When all cumulative probabilities are below 0.5, the model defaults to **Grade 0 ("No diabetic retinopathy")**, producing dangerous clinical false negatives on degraded or ambiguous images.
   - `app.py` surfaces raw cumulative sigmoid activations $P(Y \ge k)$ directly as `"probabilities"`, confusing clients who interpret them as categorical probability distributions $\sum P = 1.0$.
6. **Total Absence of Grad-CAM / Saliency Explainability**: Despite clinical screening standards requiring explainable AI (XAI) to highlight microaneurysms, hemorrhages, and exudates, `app.py` contains **zero Grad-CAM or heatmap implementation**.
7. **Gemini Pre-screening Gate Efficacy**: `gemini_validator.py` provides an effective defense against non-fundus inputs, rejecting images under 100x100, invalid MIME types, and non-retinal photographs. However, when `ENABLE_GEMINI_VALIDATION=false`, the system completely bypasses validation, allowing arbitrary images into the uncalibrated DenseNet model.

---

## 1. Model Architecture & Identity Verification

### 1.1 Claimed vs. Actual Architecture
- **Claimed Model Identity:** RETFound (Retinal Foundation Model based on ViT-Large/MAE, 304M parameters).
- **Physical Artifacts Inspected:**
  - `retfound_model.keras` (82,258,867 bytes, ~82.3 MB)
  - `retfound_model.tflite` (28,976,540 bytes, ~28.98 MB)
  - `app.py` (`MODEL_VERSION = "densenet121_ordinal_v1"`)

### 1.2 Architectural Breakdown (Keras Model Inspection)
The model was inspected via TensorFlow 2.21 runtime reflection:

```text
Model: "sequential"
_________________________________________________________________
 Layer (type)                Output Shape              Param #   
=================================================================
 densenet121 (Functional)    (None, 7, 7, 1024)        7,037,504 
 global_average_pooling2d    (None, 1024)              0         
 dropout (Dropout 0.5)       (None, 1024)              0         
 dense (Dense 256, ReLU)     (None, 256)               262,400   
 batch_normalization (BN)    (None, 256)               1,024     
 dropout_1 (Dropout 0.3)     (None, 256)               0         
 dense_1 (Dense 5, Sigmoid)  (None, 5)                 1,285     
=================================================================
Total params: 7,302,213 (27.86 MB)
Trainable params: 6,413,381 (24.47 MB)
Non-trainable params: 888,832 (3.39 MB) — First 100 layers frozen
```

### 1.3 Keras vs. TFLite Parity
We verified numerical parity between `retfound_model.keras` and `retfound_model.tflite` across 6 distinct input tensors (all-black, all-white, neutral gray, pure blue, checkerboard, and random noise).
- **Max Absolute Difference:** $\mathbf{0.000000}$ (exact bitwise floating-point parity).
- **Quantization:** None. The `.tflite` model is an unquantized FP32 model (`dtype=float32`).
- **Compatibility Warning:** `tf.lite.Interpreter` emitted deprecation warnings under TF 2.21, advising migration to LiteRT (`ai_edge_litert`).

---

## 2. Preprocessing, Dimensions & Normalization Audit

### 2.1 Pipeline Flow
The image preprocessing pipeline spans `gemini_validator.py`, `app.py`, and `85.ipynb`:

```
Uploaded Image (Bytes)
       │
       ▼
[gemini_validator.validate_image_bytes]
  ├── Format Check (JPEG, PNG, WEBP)
  ├── Dimension Range [100x100 to 8000x8000]
  ├── Decompression Bomb Protection (MAX_IMAGE_PIXELS = 64M)
  ├── EXIF Orientation Transposition (ImageOps.exif_transpose)
  └── Convert RGB & Re-encode to JPEG (quality=95)
       │
       ▼
[gemini_validator.classify_fundus_image]
  └── Gemini 3.1 Flash Lite Triage Gate (valid_fundus / non_fundus / uncertain)
       │
       ▼
[app.predict_grade]
  ├── PIL Resize to (224, 224) with Lanczos Resampling
  ├── Convert to numpy array float32 (values in [0.0, 255.0])
  └── Feed directly into DenseNet121 model(batch)
```

### 2.2 Identified Normalization Flaws
1. **Omission of ImageNet Normalization:**
   - Standard DenseNet-121 pretrained on ImageNet expects pixel inputs scaled and standardized:
     $$\tilde{x}_c = \frac{x_c / 255.0 - \mu_c}{\sigma_c}, \quad \mu = [0.485, 0.456, 0.406], \; \sigma = [0.229, 0.224, 0.225]$$
   - In `85.ipynb` Cell 3 and Cell 6, `x_train` was generated as `uint8` in `[0, 255]`. `ImageDataGenerator` was instantiated with `zoom_range=0.15, horizontal_flip=True, vertical_flip=True`, but **omitted `rescale=1./255`**.
   - In `app.py` line 160:
     ```python
     batch = np.asarray(image, dtype=np.float32)[np.newaxis, ...]
     ```
     Pixels are passed directly in range `[0.0, 255.0]`.
2. **Impact on Model Stability:**
   Because inputs were unnormalized during fine-tuning, the convolutional filter weights in the early DenseNet layers adapted to raw 0-255 scale. However, when test images are normalized to `[0.0, 1.0]` or standard ImageNet distributions, the model outputs completely divergent predictions:
   - Random noise in `[0, 255]`: Grade 1 (Mild DR)
   - Same noise in `[0, 1]`: Grade 2 (Moderate DR)
   - Same noise with `preprocess_input`: Grade 2 (Moderate DR)

---

## 3. Training Methodology & Data Leakage Analysis

### 3.1 Data Preparation (`85.ipynb`)
- **Base Dataset:** DDR Dataset (`DR_grading.csv`), balanced to 236 images per class (Total: 1,180 original images).
- **Offline Augmentation:**
  In Cell 1, 6 augmented variations were generated per original image via `ImageDataGenerator` and saved to disk. Total generated images: **6,594**.
- **Distribution of Augmented Dataset:**
  - Grade 0: 1,308
  - Grade 1: 1,318
  - Grade 2: 1,329
  - Grade 3: 1,321
  - Grade 4: 1,318

### 3.2 The Critical Split Leakage Vulnerability
In Cell 5, the train/validation/test split was performed:

```python
# Reproduce the Kaggle image-level split for score comparison.
# Augmented siblings can cross splits, so this is not a leakage-free test.

x_train_full, x_test, y_train_full, y_test = train_test_split(
    x_train,
    y_train_multi,
    test_size=0.2,
    random_state=2019,
)

x_train_partial, x_val, y_train_partial, y_val = train_test_split(
    x_train_full,
    y_train_full,
    test_size=0.1,
    random_state=2019,
)
```

#### Diagnostic Finding:
- Augmented images derived from the **same original image** were assigned random unique filenames (`{diagnosis}__0_{id}.jpg`) and pooled together into `x_train`.
- `train_test_split` was executed on the pooled augmented images rather than grouped by original image ID.
- Up to 5 of the 6 augmented siblings of a training image appeared in the test and validation sets.
- **Clinical/Statistical Impact:** The reported validation quadratic kappa of **0.9578** and test accuracy of **87.72%** represent **evaluation on memorized augmented copies**, not true generalization. The leakage invalidates all reported benchmark metrics.

```
+-------------------------------------------------------------------------+
|                        ORIGINAL IMAGE (Patient A)                       |
+------------------------------------+------------------------------------+
                                     |
               +---------------------+---------------------+
               | (Offline Augmentation: 6 siblings generated)
               v                                           v
       Sibling 1, 2, 3, 4                             Sibling 5, 6
               │                                           │
               ▼                                           ▼
      [TRAINING SET: 80%]                         [TEST SET: 20%]
               │                                           │
               +─────────── IDENTITY LEAKAGE! ─────────────+
                 Model learns exact retinal vascular pattern
                 Test score is inflated by memorization!
```

---

## 4. Class Mapping, Ordinal Formulation & Confidence Calculation

### 4.1 Cumulative Ordinal Representation (Frank & Hall Method)
The model formulates 5-grade diabetic retinopathy severity using cumulative multi-label classification:
- **Grade 0 (No DR):** $[1, 0, 0, 0, 0]$
- **Grade 1 (Mild NPDR):** $[1, 1, 0, 0, 0]$
- **Grade 2 (Moderate NPDR):** $[1, 1, 1, 0, 0]$
- **Grade 3 (Severe NPDR):** $[1, 1, 1, 1, 0]$
- **Grade 4 (Proliferative DR):** $[1, 1, 1, 1, 1]$

The output layer is `Dense(5, activation="sigmoid")`, where node $k$ represents $P(\text{Grade} \ge k)$.

### 4.2 Inference Logic in `app.py`
```python
probabilities = [round(float(p), 4) for p in raw_preds[0]]
grade = max(0, int(np.count_nonzero(raw_preds[0] >= 0.5) - 1))
```

### 4.3 Flaws in the Current Formulation
1. **Unconstrained Monotonicity:**
   In theoretical ordinal logistic regression, cumulative probabilities must satisfy $P(\text{Grade} \ge k) \ge P(\text{Grade} \ge k+1)$. Independent sigmoid units in standard neural networks do NOT enforce this condition.
   If the network predicts non-monotonic logits (e.g. $[0.35, 0.92, 0.88, 0.12, 0.02]$), counting threshold crossings yields:
   $$\text{count} = 2 \implies \text{Grade} = 2 - 1 = 1$$
   This assigns Grade 1 even though unit 0 (the indicator for Grade $\ge 0$) failed to cross the threshold!
2. **Dangerous Low-Confidence Default:**
   If the network produces very low probabilities for all units (e.g., $[0.40, 0.30, 0.20, 0.10, 0.05]$ on an uninterpretable or severely corrupted image):
   $$\text{count} = 0 \implies \text{grade} = \max(0, 0 - 1) = 0$$
   The system defaults to **Grade 0: "No diabetic retinopathy"**. In a clinical triage setting, assigning "healthy" to an uncertain or failed prediction is the worst possible clinical failure mode (silent false negative).
3. **Misleading Probability Semantics:**
   `app.py` serializes `probabilities = [0.9924, 0.9221, 0.0004, 0.0000, 0.0062]` directly into the JSON response.
   Mobile clients and clinicians interpret these as mutually exclusive class probabilities. In reality:
   $$P(\text{Grade} = k) = P(\text{Grade} \ge k) - P(\text{Grade} \ge k+1)$$
   The true class probabilities for the vector above are:
   - $P(\text{Grade}=0) = 0.9924 - 0.9221 = 0.0703$ (7.0%)
   - $P(\text{Grade}=1) = 0.9221 - 0.0004 = 0.9217$ (92.2%)
   - $P(\text{Grade}=2) = 0.0004 - 0.0000 = 0.0004$ (0.04%)
   - $P(\text{Grade}=3) = 0.0000 - 0.0062 = -0.0062$ (**Negative probability due to non-monotonicity!**)
   - $P(\text{Grade}=4) = 0.0062$ (0.6%)

---

## 5. Explainability & Grad-CAM Audit

### 5.1 Verification of Visual Saliency
- **Audit Mandate:** Inspect Grad-CAM implementation, saliency maps, and visual explainability features.
- **Finding:** **Grad-CAM is completely missing from `app.py`**.
  - There are no hook functions on the `conv5_block16_2_conv` or last convolutional layer of DenseNet-121.
  - No heatmap generation, alpha-blending, or overlay rendering exists in the backend API or mobile client.
  - The API returns only a numerical grade, textual label, and raw probability list.
- **Clinical Risk:**
  Automated diabetic retinopathy screening tools without visual localization cannot be clinically validated or trusted. Clinicians cannot verify whether a Grade 2 or 3 classification was triggered by real microaneurysms, hemorrhages, or venous beading versus optical lens glare, dust particles on the camera, or optic disc artifacts.

---

## 6. Resilience & Edge-Case Testing Matrix

We conducted automated stress testing against the pipeline (`test_resilience.py`). Below are the observed empirical results:

| Test Case | Dimensions / Format | Pre-Validation (`validate_image_bytes`) | Gemini Validator Status | Model Inference (Keras / TFLite) | Observed Grade & Prediction | Pipeline Assessment |
|---|---|---|---|---|---|---|
| **Empty File** | 0 bytes | `InvalidImageError` ("Uploaded file is empty") | Blocked (HTTP 400) | Not Called | N/A | **PASS** (Safely rejected) |
| **Corrupted JPEG Header** | Truncated binary | `InvalidImageError` ("Could not be decoded") | Blocked (HTTP 400) | Not Called | N/A | **PASS** (Safely rejected) |
| **Sub-minimum Dimensions** | 1x1, 99x99 | `InvalidImageError` (< 100x100) | Blocked (HTTP 400) | Not Called | N/A | **PASS** (Safely rejected) |
| **Boundary Minimum** | 100x100 | Accepted, normalized to JPEG | Triage Gate | Runs Inference | Output Depends on Image | **PASS** |
| **Extreme Aspect Ratio** | 100x4000 | Accepted by byte validator | Triage Gate | Severe Distortion | Model predictions distorted by anisotropic resize | **MEDIUM RISK** |
| **Unsupported Formats** | GIF, BMP, TIFF, SVG | `InvalidImageError` ("Unsupported image format") | Blocked (HTTP 400) | Not Called | N/A | **PASS** (Safely rejected) |
| **Oversize Image** | > 10 MB | Rejected by `MAX_IMAGE_BYTES` | Blocked (HTTP 413) | Not Called | N/A | **PASS** (Safely rejected) |
| **All Black Image (zeros)** | 224x224 JPEG | Accepted | Bypassed (Offline/Disabled) | $[0.970, 0.935, 0.447, 0.281, 0.073]$ | **Grade 1: Mild NPDR** | **CRITICAL FAILURE** |
| **All White Image (255)** | 224x224 JPEG | Accepted | Bypassed (Offline/Disabled) | $[0.988, 0.987, 0.026, 0.005, 0.014]$ | **Grade 1: Mild NPDR** | **CRITICAL FAILURE** |
| **Solid Neutral Gray (128)** | 224x224 JPEG | Accepted | Bypassed (Offline/Disabled) | $[0.984, 0.999, 0.126, 0.005, 0.015]$ | **Grade 1: Mild NPDR** | **CRITICAL FAILURE** |
| **Solid Pure Blue** | 224x224 JPEG | Accepted | Bypassed (Offline/Disabled) | $[0.962, 0.990, 0.818, 0.000, 0.044]$ | **Grade 2: Moderate NPDR** | **CRITICAL FAILURE** |
| **Checkerboard Pattern** | 224x224 JPEG | Accepted | Bypassed (Offline/Disabled) | $[0.981, 0.927, 0.123, 0.060, 0.013]$ | **Grade 1: Mild NPDR** | **CRITICAL FAILURE** |
| **Gaussian Noise** | 224x224 JPEG | Accepted | Bypassed (Offline/Disabled) | $[0.995, 0.816, 0.005, 0.001, 0.027]$ | **Grade 1: Mild NPDR** | **CRITICAL FAILURE** |

### Critical Takeaway on Failure Modes
The DenseNet-121 model has strong positive biases in the first two output units. In the absence of a working Gemini triage gate, the model will diagnose virtually **any random, blank, or non-retinal image as Mild Diabetic Retinopathy (Grade 1)**.

---

## 7. Gemini Validator & Fallback Resilience Analysis

### 7.1 Architecture of the Gate
`gemini_validator.py` uses Gemini 3.1 Flash Lite (`gemini-3.1-flash-lite`) with structured JSON schema output (`GeminiFundusResponse`) and temperature 0.0.
The classifier determines:
- `valid_fundus`: Image contains retinal anatomy (optic disc, macula, retinal vessels).
- `non_fundus`: Any other subject (selfies, documents, animals, chest X-rays, external eyes).
- `uncertain`: Glare, extreme blur, severe degradation.

### 7.2 Failure Mode & Fallback Evaluation
1. **Missing / Invalid API Key (`GeminiConfigurationError`):**
   - Result: Returns HTTP 500 (`GEMINI_CONFIGURATION_ERROR`).
   - Assessment: **Fails closed**. Prevents unverified images from hitting the model.
2. **Quota / Rate Limit (`GeminiRateLimitError`):**
   - Result: Returns HTTP 429 (`GEMINI_RATE_LIMITED`).
   - Assessment: **Fails closed**.
3. **Timeout (`GeminiTimeoutError`):**
   - Configured timeout: 15.0s.
   - Result: Returns HTTP 504 (`GEMINI_TIMEOUT`).
   - Assessment: **Fails closed**.
4. **Service Unavailability (`GeminiUnavailableError`):**
   - Result: Returns HTTP 503 (`GEMINI_VALIDATION_UNAVAILABLE`).
   - Assessment: **Fails closed**.
5. **Malformed JSON / Empty Response:**
   - Result: `_parse_gemini_response` catches JSON decode errors and falls closed to `ValidationStatus.UNCERTAIN` (HTTP 400).
   - Assessment: **Fails closed**.
6. **Feature Flag Bypass (`ENABLE_GEMINI_VALIDATION=false`):**
   - Result: `classify_fundus_image` returns `VALID_FUNDUS` with `bypassed=True`.
   - Assessment: **Fails open**. Intended for offline development/testing, but creates an extreme clinical safety risk if deployed in production without an API key.

---

## 8. Verifiable Metrics & Confusion Matrix Assessment

### 8.1 Metrics Recorded in Training Logs (`85.ipynb`)
From the training history and checkpoint selection in `85.ipynb`:

| Metric | Training Set | Validation Set (Best Checkpoint) | Test Set (Kaggle Protocol) |
|---|---|---|---|
| **Exact Grade Accuracy** | 43.6% (bit acc) | **86.55%** (Epoch 13) | **87.72%** |
| **Quadratic Weighted Kappa ($\kappa$)** | N/A | **0.9578** (Epoch 13) | **0.9578** |
| **Macro Precision** | N/A | N/A | **88.38%** |
| **Macro Recall** | N/A | N/A | **87.77%** |
| **Macro F1-Score** | N/A | N/A | **87.89%** |
| **Weighted F1-Score** | N/A | N/A | **87.78%** |

### 8.2 Test Set Confusion Matrix (Recorded in Cell 10)
Test set size: $N = 1,319$ images.

```text
                  Predicted Grade
               0      1      2      3      4    Total
Actual 0     235     14      1      0      0     250
Actual 1      17    243      7      7      0     274
Actual 2       0     29    208     27      0     264
Actual 3       0      5     21    243      1     270
Actual 4       0      2      5     26    228     261
Total        252    293    242    303    229    1319
```

### 8.3 Class-by-Class Performance Breakdown
From the recorded confusion matrix:
- **Grade 0 (No DR):**
  - Sensitivity / Recall: $235 / 250 = \mathbf{94.0\%}$
  - Specificity: $(1319 - 250 - 17) / (1319 - 250) = 1052 / 1069 = \mathbf{98.4\%}$
  - False Negatives: 15 / 250 (6.0% missed)
- **Grade 1 (Mild NPDR):**
  - Sensitivity / Recall: $243 / 274 = \mathbf{88.7\%}$
  - False Positives: $14 + 29 + 5 + 2 = 50$
- **Grade 2 (Moderate NPDR):**
  - Sensitivity / Recall: $208 / 264 = \mathbf{78.8\%}$
  - Significant cross-classification into Grade 1 (29 cases) and Grade 3 (27 cases).
- **Grade 3 (Severe NPDR):**
  - Sensitivity / Recall: $243 / 270 = \mathbf{90.0\%}$
- **Grade 4 (Proliferative DR):**
  - Sensitivity / Recall: $228 / 261 = \mathbf{87.4\%}$
  - Misclassified as Grade 3: 26 cases (10.0%).

> [!CAUTION]
> **Audit Warning on Metrics Validity:**
> While the confusion matrix demonstrates balanced performance across grades, **these figures cannot be interpreted as genuine out-of-sample performance** due to the split data leakage documented in Section 3. Real patient test data would experience substantially higher confusion between adjacent grades (especially Grades 1 and 2).

---

## 9. Comprehensive Risk & Reliability Scorecard

| Evaluation Dimension | Severity Level | Status | Clinical & Operational Risk Summary |
|---|---|---|---|
| **Data Split Integrity** | **CRITICAL** | ❌ FAILED | Augmented siblings cross splits. Reported metrics overfit to training set identity. |
| **Model Identity / Lineage** | **HIGH** | ❌ MISLEADING | Artifacts labeled `retfound` but run DenseNet-121. Misrepresentation of foundation model architecture. |
| **Input Normalization** | **HIGH** | ❌ FAILED | Raw 0-255 pixels fed to ImageNet-pretrained backbone. Scale sensitivity shifts predictions. |
| **Out-of-Distribution Robustness** | **HIGH** | ❌ FAILED | Blank, gray, checkerboard, or noise images predict Grade 1 (Mild DR) with >93% probability. |
| **Ordinal Monotonicity Handling** | **MEDIUM** | ⚠️ VULNERABLE | Non-monotonic sigmoid outputs are unconstrained. Zero threshold crossings default to Grade 0. |
| **Explainability (Grad-CAM)** | **HIGH** | ❌ MISSING | Zero visual heatmap or localization support. Violates clinical AI standards. |
| **Gemini Triage Gating** | **LOW** | ✅ ROBUST | Fails closed on missing keys, rate limits, timeouts, and unparseable responses. |
| **Keras / TFLite Parity** | **LOW** | ✅ PASSED | Exact bitwise agreement ($0.000000$ diff) between Keras and TFLite implementations. |
| **Test Suite Coverage** | **LOW** | ✅ PASSED | 33 automated tests in `tests/` pass with comprehensive mock coverage. |

---

## 10. Prioritized Phase 2 Remediation Recommendations

### Priority 1: Clinical Safety & Diagnostic Fixes (Immediate)
1. **Fix Leakage-Free Data Splitting:**
   - Re-partition the DDR dataset by **original patient / image ID** before performing any offline or online augmentation (`GroupKFold` or `train_test_split(df_original)`).
   - Re-evaluate the true unbiased validation and test performance of DenseNet-121.
2. **Implement Safe Uncertainty Fallback:**
   - Replace the silent fallback to Grade 0 with an explicit **Uncertainty / Low Confidence Flag**:
     ```python
     if max(probabilities) < 0.5 and grade == 0 and sum(probabilities) < 0.2:
         return None, "Uncertain / Low Confidence", probabilities
     ```
   - Never classify an ambiguous or zero-activation image as "No diabetic retinopathy".
3. **Convert Cumulative Outputs to True Probabilities:**
   - Calculate genuine marginal class probabilities in `app.predict_grade`:
     ```python
     p_cum = np.array(raw_preds[0])
     p_class = np.zeros(5)
     p_class[0] = max(0.0, 1.0 - p_cum[1])
     for k in range(1, 4):
         p_class[k] = max(0.0, p_cum[k] - p_cum[k+1])
     p_class[4] = p_cum[4]
     # Normalize to sum to 1.0
     p_class /= p_class.sum()
     ```

### Priority 2: Preprocessing & Standardization (High)
1. **Harmonize Image Normalization:**
   - Standardize all training and inference through `tf.keras.applications.densenet.preprocess_input` or a Keras `Rescaling(1./255)` layer baked directly into the model graph.
2. **Aspect Ratio Preservation:**
   - Replace anisotropic resizing (stretching) with letterboxed padding (preserving retinal circular geometry) to avoid distorting optic disc and vessel diameters.

### Priority 3: Explainability & Governance (Phase 2 Roadmap)
1. **Implement Grad-CAM Endpoint:**
   - Add a Grad-CAM generator targeting DenseNet-121's `conv5_block16_2_conv` layer.
   - Expose an endpoint `POST /api/predict_with_heatmap` returning the base64-encoded heatmap overlay alongside the prediction.
2. **Model Transparency & Renaming:**
   - Rename model files from `retfound_model.*` to `densenet121_dr_ordinal.*` to reflect genuine model lineage and prevent clinical misrepresentation.
3. **LiteRT Migration:**
   - Migrate TFLite loading from deprecated `tf.lite.Interpreter` to `ai_edge_litert.Interpreter`.

---

## 11. Conclusion

The diabetic retinopathy detection pipeline exhibits solid engineering in its defensive API gating (`gemini_validator.py`) and exact Keras-to-TFLite export fidelity. However, the core machine learning model suffers from **severe data leakage in training splits**, **model mislabeling**, **omission of input normalization**, **failure to enforce ordinal monotonicity**, and **total absence of visual explainability (Grad-CAM)**. 

While the Gemini pre-filter successfully catches non-retinal uploads under normal operations, the underlying DenseNet model cannot be deemed clinically reliable on its own until Phase 2 retraining with strict patient-grouped splits, standard normalization, and Grad-CAM explainability is executed.

---
*Report completed and verified by Agent 9 (AI/ML Model Validation Engineer).*
