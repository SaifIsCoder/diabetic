# Machine Learning Pipeline Architecture & Validation Specification

**System:** Diabetic Retinopathy Diagnostic System  
**Pipeline Track:** Track 2 — ML Pipeline Validation (Sprint 2)  
**Model Version:** `densenet121_ordinal_v1`  
**Checkpoint Path:** `retfound_model.keras`  
**Document Status:** Production Audited & Locked  
**Date:** 2026-11-22  

---

## 1. Executive Summary & Model Identity Discrepancy (ML-02)

During the Phase 0 audit and Sprint 2 deep verification, a major discrepancy was identified between the checkpoint filename (`retfound_model.keras`) and the underlying deep neural network architecture.

| Attribute | Documented / Assumed Claim | Actual Verified Architecture |
| :--- | :--- | :--- |
| **Model Type** | RETFound (Vision Transformer foundation model) | DenseNet-121 (Densely Connected Convolutional Network) |
| **Foundation Origin** | Nature 2023 304M ViT-Large | ImageNet-initialized torchvision / tf.keras weights |
| **Parameter Count** | ~304,000,000 parameters | 7,302,213 parameters (~7.3M) |
| **Model Head** | Multi-class projection head | 2-layer Dense MLP with Sigmoidal Ordinal Output |
| **Version Identifier** | Inconsistent / `retfound` | `densenet121_ordinal_v1` |

### Governance Resolution:
1. **Model Version String Alignment:** The backend API (`/api/health`, `/api/predict`, and scan receipts) explicitly and uniformly reports `densenet121_ordinal_v1`.
2. **Model Replacement Gate:** Full replacement of the weights with true RETFound (304M parameters) or retraining on large-scale clinical cohorts is designated as **BLOCKED — HUMAN APPROVAL REQUIRED** due to substantial compute requirements and model weight licensing.

---

## 2. Neural Network Architecture Specification

The current inference checkpoint (`retfound_model.keras`) was trained in `85.ipynb`. It employs an ImageNet-pretrained DenseNet-121 backbone coupled to an ordinal classification head.

### 2.1 Layer-by-Layer Topology

```
Input Image [224, 224, 3] (float32, [0.0, 255.0])
       │
       ▼
DenseNet-121 Base (Pretrained on ImageNet, layers[:100] frozen)
  Output: [None, 7, 7, 1024] (7,037,504 parameters)
       │
       ▼
GlobalAveragePooling2D() -> [None, 1024]
       │
       ▼
Dropout(rate=0.5)
       │
       ▼
Dense(units=256, activation="relu") -> [None, 256] (262,400 parameters)
       │
       ▼
BatchNormalization() -> [None, 256] (1,024 parameters)
       │
       ▼
Dropout(rate=0.3)
       │
       ▼
Dense(units=5, activation="sigmoid") -> [None, 5] (1,285 parameters)
```

### 2.2 Parameter Breakdown

| Parameter Group | Count | Size (MB) |
| :--- | :--- | :--- |
| **Total Parameters** | 7,302,213 | ~27.86 MB |
| **Trainable Parameters** | 6,413,381 | ~24.47 MB |
| **Non-Trainable Parameters** | 888,832 | ~3.39 MB |

---

## 3. Ordinal Cumulative Sigmoid Classification

Diabetic retinopathy grading is fundamentally an ordinal clinical task:
- Grade 0: No Diabetic Retinopathy
- Grade 1: Mild Non-Proliferative Diabetic Retinopathy (NPDR)
- Grade 2: Moderate Non-Proliferative Diabetic Retinopathy (NPDR)
- Grade 3: Severe Non-Proliferative Diabetic Retinopathy (NPDR)
- Grade 4: Proliferative Diabetic Retinopathy (PDR)

Standard categorical softmax cross-entropy treats misclassifications symmetrically (e.g. classifying Grade 4 as Grade 0 carries the same loss penalty as classifying Grade 4 as Grade 3). To enforce clinical monotonicity, `85.ipynb` implemented **cumulative multi-label ordinal regression**.

### 3.1 Target Encoding
Each training label $y \in \{0, 1, 2, 3, 4\}$ was transformed into a cumulative 5-bit vector $\mathbf{t} = [t_0, t_1, t_2, t_3, t_4]$ where:
$$t_i = \mathbb{I}(y \ge i)$$

Thus:
- Grade 0 $\rightarrow [1, 0, 0, 0, 0]$
- Grade 1 $\rightarrow [1, 1, 0, 0, 0]$
- Grade 2 $\rightarrow [1, 1, 1, 0, 0]$
- Grade 3 $\rightarrow [1, 1, 1, 1, 0]$
- Grade 4 $\rightarrow [1, 1, 1, 1, 1]$

### 3.2 Loss Function & Training
The model was compiled with independent binary cross-entropy loss across the 5 sigmoid units:
$$\mathcal{L} = -\frac{1}{5} \sum_{i=0}^4 \left[ t_i \log p_i + (1 - t_i) \log (1 - p_i) \right]$$
where $p_i = \sigma(z_i)$ represents the estimated probability $P(\text{Grade} \ge i)$.

### 3.3 Inference Decision Rule
In `app.py::predict_grade()`, the discrete predicted grade is determined by counting how many cumulative thresholds meet or exceed $0.5$:
$$\text{Grade} = \max\left(0, \sum_{i=0}^4 \mathbb{I}(p_i \ge 0.5) - 1\right)$$

### 3.4 Scalar Confidence & Uncertainty Quantification (ML-05)
Prior to Sprint 2, the API silently defaulted sub-threshold activations ($p_i < 0.5$) to Grade 0 without low-confidence flagging or exposing a scalar confidence. Under Sprint 2 remediation:
- **Low Confidence Flag:** `"low_confidence": bool` is set to `True` whenever $\max_i p_i < 0.50$.
- **Scalar Confidence:** A calibrated scalar confidence $C \in [0.0, 1.0]$ is computed:
  - If $\max_i p_i < 0.50$: $C = \max_i p_i$ (reflecting sub-threshold uncertainty).
  - If Grade = 0: $C = \max(p_0 \cdot (1 - p_1), 1 - p_1)$.
  - If Grade = 4: $C = p_4$.
  - If Grade $g \in \{1, 2, 3\}$: $C = p_g \cdot (1 - p_{g+1})$.

---

## 4. Preprocessing & Normalization Contract (ML-03)

### 4.1 Strict Invariant
```python
# PREPROCESSING SPECIFICATION
image = source.convert("RGB").resize((224, 224), resample=Image.Resampling.LANCZOS)
batch = np.asarray(image, dtype=np.float32)[np.newaxis, ...]
# batch values remain strictly in [0.0, 255.0]
```

### 4.2 Why Standard Preprocessing Is Strictly Prohibited
Most DenseNet-121 implementations expect inputs normalized via `tf.keras.applications.densenet.preprocess_input` (scaling pixels to $[-1, 1]$ or z-score standardization). However, examination of `85.ipynb` (Cell 4) confirmed that images were resized via PIL and converted directly to uint8 arrays without division by 255.0 or zero-centering.

Applying `preprocess_input` shifts input pixel distributions away from the training distribution, causing severe logit corruption and false predictions on the current checkpoint weights (`retfound_model.keras`).

**Contract Requirement:** Input tensors MUST retain raw float32 values in $[0.0, 255.0]$. No preprocessing transforms beyond RGB conversion and 224x224 Lanczos resizing may be introduced without retraining.

---

## 5. Training Data Leakage Analysis in `85.ipynb` (ML-01)

### 5.1 Confirmed Root Cause
In `85.ipynb`:
1. **Original Balancing (Cell 2):** 1,180 original fundus images were selected from `DR_grading.csv` (236 images per grade).
2. **Offline Augmentation Before Split (Cell 2):** For each original image, 6 augmented siblings were generated offline using `ImageDataGenerator` (zoom, horizontal/vertical flips) and written to disk (`working/ddr-equal/aug_images`), yielding 6,594 image files.
3. **Naive Image-Level Train/Test Split (Cell 6):**
   ```python
   # 85.ipynb Cell 6 - FATAL FLAW:
   x_train_full, x_test, y_train_full, y_test = train_test_split(
       x_train, y_train_multi, test_size=0.2, random_state=2019
   )
   ```
4. **Flaw Mechanism:** Because `train_test_split` operated on the 6,594 augmented image files, augmented copies of the **exact same original retinal photograph** were partitioned randomly into training ($N=4,747$), validation ($N=528$), and test ($N=1,319$) sets.

### 5.2 Clinical & Statistical Impact
- **Severe Data Leakage:** The holdout test set was contaminated with augmented variants of images present in the training set.
- **Metric Invalidation:** The reported test performance (accuracy: 87.72%, quadratic weighted kappa: 0.9578) is an artifact of memorizing patient-specific retinal vasculature patterns and cannot be generalized to unseen patients.
- **Regulatory Risk:** Deploying models trained under cross-split leakage into a clinical pilot poses immediate patient safety risks.

---

## 6. Retraining & Remediation Protocol (ML-01 Governance Gate)

**Current Status:** **BLOCKED — HUMAN APPROVAL REQUIRED**

Retraining the model or swapping weights in production is a destructive, non-reversible operation requiring explicit human review and authorization.

### 6.1 Required Protocol When Unblocked
When approved by human governance, retraining MUST strictly adhere to the following protocol:

```
Step 1: Patient-Level Partitioning
  Source: Raw DR_grading dataset (patient ID / subject ID grouped)
  Split: 70% Train, 15% Validation, 15% Holdout Test
  CRITICAL: All images (left/right eyes, multiple visits) of Patient X must
  reside exclusively in one split. Zero patient overlap across splits.
       │
       ▼
Step 2: Strict Augmentation Ordering
  - Holdout Test Set: 100% PRISTINE, UN-AUGMENTED original images only.
  - Validation Set: 100% PRISTINE, UN-AUGMENTED original images only.
  - Training Set: Apply online augmentation on-the-fly during batch generation.
    NEVER persist augmented images to disk before splitting.
       │
       ▼
Step 3: Normalized Preprocessing Pipeline
  Fit normalization/scaling parameters exclusively on the training partition.
  If adopting RETFound or modern ViT, enforce exact model-specific normalization.
       │
       ▼
Step 4: Clinical Validation Suite
  Evaluate holdout test set across:
  - Quadratic Weighted Kappa (QWK) with 95% bootstrap confidence intervals.
  - Referable DR Classification (Grade >= 2): Sensitivity, Specificity, ROC-AUC.
  - Error slice analysis across demographic subgroups.
```

---

## 7. Out-of-Distribution & Local Heuristic Image Validation (ML-04)

Standard deep convolutional classifiers without out-of-distribution (OOD) rejection exhibit pathological overconfidence on uninformative synthetic images. DenseNet-121 predicts Grade 1 (>93% confidence) on uniform black, white, gray, and checkerboard images due to dense layer bias.

To prevent diagnostic hallucinations, a multi-tier defense is enforced:

```
[Uploaded Image]
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ Tier 1: Local Heuristic Variance & Entropy Gate        │
│ (gemini_validator.py::validate_image_bytes)            │
│  - Dimension limits (100x100 to 8000x8000)             │
│  - Extreme intensity checks (pure black, pure white)   │
│  - Flat gray / uniform achromatic detection            │
│  - Shannon entropy & combined variance thresholds      │
│  -> Rejects blank/flat/noise LOCALLY with HTTP 400     │
└───────────────────────┬────────────────────────────────┘
                        │ Valid local entropy/variance
                        ▼
┌────────────────────────────────────────────────────────┐
│ Tier 2: Multimodal Gemini Triage Classifier            │
│ (gemini_validator.py::classify_fundus_image)           │
│  - Verifies presence of retinal anatomy (optic disc,   │
│    macula, retinal vasculature)                        │
│  - Rejects selfies, external eyes, documents, X-rays   │
│  -> Rejects non-fundus / uncertain with HTTP 400       │
└───────────────────────┬────────────────────────────────┘
                        │ Verified Retinal Fundus
                        ▼
┌────────────────────────────────────────────────────────┐
│ Tier 3: DenseNet-121 Inference Model                   │
│ (app.py::predict_grade)                                │
│  - Raw [0.0, 255.0] Lanczos input                      │
│  - Ordinal sigmoid activations                         │
│  - Scalar confidence & low-confidence uncertainty flag │
└────────────────────────────────────────────────────────┘
```

### 7.1 Tier 1 Thresholds
- `MIN_VARIANCE_THRESHOLD = 10.0`: Rejects images where combined spatial and color channel variance is below 10.0.
- `MIN_ENTROPY_THRESHOLD = 0.5`: Rejects images where Shannon entropy across color channels is below 0.5 bits.
- `Achromatic Flatness Gate`: Rejects images where spatial standard deviation < 2.0 and color standard deviation < 2.0.

This guarantees that uninformative, corrupted, or synthetic non-fundus inputs are rejected deterministically before any cloud API call or model inference occurs.
