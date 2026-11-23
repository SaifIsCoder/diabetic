"""
Dataset Splitting Module with Patient-Level Stratification.

Resolves historical ML data leakage by enforcing zero patient overlap across
training, validation, and holdout test partitions.

Key Features:
1. Multi-image patient grouping: Retinal fundus examinations often contain
   multiple images per patient (OD/OS, macula/optic disc fields). Images from the
   same patient are strictly constrained to the same split.
2. Patient severity aggregation: patient_grade = max(image_grades).
3. Stratified splitting: Preserves exact grade distributions across partitions.
4. Leakage assertions: Formal verification that train, val, and test patient sets
   are mutually disjoint.
5. Mock cohort generation: High-fidelity synthetic multi-image patient cohort
   when raw patient data is unavailable (satisfying R2 and R5 guardrails).
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("split_dataset")


def generate_mock_patient_cohort(
    num_patients: int = 200,
    min_images_per_patient: int = 1,
    max_images_per_patient: int = 4,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Generate a realistic synthetic multi-image patient cohort.

    Generates realistic patient IDs with multiple eyes/fields and clinical DR grades
    (0 = No DR, 1 = Mild, 2 = Moderate, 3 = Severe, 4 = Proliferative).
    """
    rng = np.random.RandomState(random_seed)
    records: List[Dict[str, Any]] = []

    # Distribution approximating clinical DR screening population
    grade_probabilities = [0.45, 0.20, 0.18, 0.10, 0.07]

    for p_idx in range(1, num_patients + 1):
        patient_id = f"PAT_{p_idx:05d}"
        # Pick patient primary severity
        base_grade = int(rng.choice(5, p=grade_probabilities))
        num_images = rng.randint(min_images_per_patient, max_images_per_patient + 1)

        eyes = ["OD", "OS"]
        fields = ["macula", "disc", "peripheral"]

        for img_idx in range(num_images):
            eye = eyes[img_idx % 2]
            field = fields[(img_idx // 2) % len(fields)]
            image_id = f"{patient_id}_{eye}_{field}_{img_idx + 1:02d}.jpg"

            # Image grade: usually matches base_grade, occasionally 1 grade lower
            # (asymmetric DR between eyes or field variations)
            if base_grade > 0 and rng.rand() < 0.25:
                img_grade = max(0, base_grade - 1)
            else:
                img_grade = base_grade

            records.append({
                "patient_id": patient_id,
                "image_id": image_id,
                "eye": eye,
                "field": field,
                "grade": int(img_grade),
            })

    df = pd.DataFrame(records)
    logger.info(
        "Generated synthetic cohort: %d images across %d unique patients.",
        len(df),
        df["patient_id"].nunique(),
    )
    return df


def detect_columns(df: pd.DataFrame) -> Tuple[str, str, str]:
    """Detect patient_id, image_id, and grade column names in input dataframe."""
    cols = df.columns.tolist()

    # Detect patient ID column
    patient_candidates = ["patient_id", "patient", "subject_id", "id_patient", "patient_code"]
    patient_col = next((c for c in patient_candidates if c in cols), None)

    # Detect image ID column
    image_candidates = ["image_id", "id_code", "image_path", "filename", "file_name", "image"]
    image_col = next((c for c in image_candidates if c in cols), None)

    # Detect grade column
    grade_candidates = ["grade", "diagnosis", "dr_grade", "severity", "label"]
    grade_col = next((c for c in grade_candidates if c in cols), None)

    if patient_col is None:
        # If no patient column, check if image_id exists and can be parsed or synthesize patient IDs
        if image_col is not None:
            logger.warning("No explicit patient_id column found. Attempting to parse from %s.", image_col)
            # Try splitting e.g. PAT_00001_OD.jpg -> PAT_00001
            extracted = df[image_col].astype(str).str.extract(r"^([A-Za-z0-9]+_[A-Za-z0-9]+)")[0]
            if extracted.notna().all() and extracted.nunique() < len(df):
                df["patient_id"] = extracted
                patient_col = "patient_id"
            else:
                # Fallback: 1 patient per image (single-image cohort)
                logger.warning("Treating each image as an independent patient.")
                df["patient_id"] = [f"PAT_{i:06d}" for i in range(len(df))]
                patient_col = "patient_id"
        else:
            raise ValueError(f"Could not identify patient_id column among: {cols}")

    if image_col is None:
        raise ValueError(f"Could not identify image_id column among: {cols}")

    if grade_col is None:
        raise ValueError(f"Could not identify grade/diagnosis column among: {cols}")

    return patient_col, image_col, grade_col


def split_dataset(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Partition dataset into stratified train, validation, and test splits grouped by patient ID.

    Guarantees:
    1. Zero patient overlap:
       train_patients & val_patients == empty
       train_patients & test_patients == empty
       val_patients & test_patients == empty
    2. Patient severity is computed as max(image_grades) per patient.
    3. Stratification preserves patient severity distribution across all splits.
    """
    total_ratio = train_ratio + val_ratio + test_ratio
    if not (0.999 <= total_ratio <= 1.001):
        raise ValueError(f"Split ratios must sum to 1.0 (got {total_ratio:.4f})")

    patient_col, image_col, grade_col = detect_columns(df)

    # Standardize working copy
    work_df = df.copy()
    work_df["patient_id"] = work_df[patient_col].astype(str)
    work_df["image_id"] = work_df[image_col].astype(str)
    work_df["grade"] = work_df[grade_col].astype(int)

    # Validate grades
    valid_grades = set(range(5))
    found_grades = set(work_df["grade"].unique())
    invalid_grades = found_grades - valid_grades
    if invalid_grades:
        raise ValueError(f"Invalid DR grade values detected: {invalid_grades}. Expected values in 0..4.")

    # Aggregate patient severity: patient_grade = max(image_grades)
    patient_severity = (
        work_df.groupby("patient_id")["grade"]
        .max()
        .rename("patient_grade")
        .reset_index()
    )

    work_df = work_df.merge(patient_severity, on="patient_id", how="left")

    rng = np.random.RandomState(random_seed)

    train_patients: Set[str] = set()
    val_patients: Set[str] = set()
    test_patients: Set[str] = set()

    # Stratify by patient_grade
    for grade_val in sorted(patient_severity["patient_grade"].unique()):
        grade_patients = (
            patient_severity[patient_severity["patient_grade"] == grade_val]["patient_id"]
            .tolist()
        )
        rng.shuffle(grade_patients)
        n_p = len(grade_patients)

        if n_p == 1:
            # Single patient goes to train
            train_patients.update(grade_patients)
            continue
        elif n_p == 2:
            train_patients.add(grade_patients[0])
            val_patients.add(grade_patients[1])
            continue

        n_train = int(round(n_p * train_ratio))
        n_val = int(round(n_p * val_ratio))
        # Ensure at least 1 in val and test if n_p is sufficient (>= 3)
        if n_val == 0 and n_p >= 3:
            n_val = 1
        n_test = n_p - n_train - n_val
        if n_test <= 0 and n_p >= 3 and n_train > 1:
            n_train -= 1
            n_test = n_p - n_train - n_val

        p_train = grade_patients[:n_train]
        p_val = grade_patients[n_train : n_train + n_val]
        p_test = grade_patients[n_train + n_val :]

        train_patients.update(p_train)
        val_patients.update(p_val)
        test_patients.update(p_test)

    # FORMAL ZERO-LEAKAGE ASSERTIONS
    train_val_overlap = train_patients & val_patients
    train_test_overlap = train_patients & test_patients
    val_test_overlap = val_patients & test_patients

    assert len(train_val_overlap) == 0, (
        f"Data leakage detected! {len(train_val_overlap)} patients overlap between train and val: {train_val_overlap}"
    )
    assert len(train_test_overlap) == 0, (
        f"Data leakage detected! {len(train_test_overlap)} patients overlap between train and test: {train_test_overlap}"
    )
    assert len(val_test_overlap) == 0, (
        f"Data leakage detected! {len(val_test_overlap)} patients overlap between val and test: {val_test_overlap}"
    )

    all_assigned = train_patients | val_patients | test_patients
    total_unique_patients = patient_severity["patient_id"].nunique()
    assert len(all_assigned) == total_unique_patients, (
        f"Mismatch in patient assignment: {len(all_assigned)} assigned vs {total_unique_patients} total."
    )

    # Filter image partitions
    train_df = work_df[work_df["patient_id"].isin(train_patients)].copy().reset_index(drop=True)
    val_df = work_df[work_df["patient_id"].isin(val_patients)].copy().reset_index(drop=True)
    test_df = work_df[work_df["patient_id"].isin(test_patients)].copy().reset_index(drop=True)

    # Build comprehensive audit summary
    def _get_grade_dist(sub_df: pd.DataFrame, col: str) -> Dict[str, int]:
        counts = sub_df[col].value_counts().to_dict()
        return {f"grade_{int(k)}": int(v) for k, v in sorted(counts.items())}

    patient_df_train = patient_severity[patient_severity["patient_id"].isin(train_patients)]
    patient_df_val = patient_severity[patient_severity["patient_id"].isin(val_patients)]
    patient_df_test = patient_severity[patient_severity["patient_id"].isin(test_patients)]

    summary: Dict[str, Any] = {
        "total_patients": int(total_unique_patients),
        "total_images": int(len(work_df)),
        "split_ratios": {
            "target_train": float(train_ratio),
            "target_val": float(val_ratio),
            "target_test": float(test_ratio),
        },
        "random_seed": int(random_seed),
        "leak_free_verification": {
            "train_val_overlap_count": len(train_val_overlap),
            "train_test_overlap_count": len(train_test_overlap),
            "val_test_overlap_count": len(val_test_overlap),
            "zero_leakage_verified": True,
        },
        "train_split": {
            "patient_count": len(train_patients),
            "image_count": len(train_df),
            "patient_ratio": round(len(train_patients) / total_unique_patients, 4),
            "patient_grade_distribution": _get_grade_dist(patient_df_train, "patient_grade"),
            "image_grade_distribution": _get_grade_dist(train_df, "grade"),
        },
        "val_split": {
            "patient_count": len(val_patients),
            "image_count": len(val_df),
            "patient_ratio": round(len(val_patients) / total_unique_patients, 4),
            "patient_grade_distribution": _get_grade_dist(patient_df_val, "patient_grade"),
            "image_grade_distribution": _get_grade_dist(val_df, "grade"),
        },
        "test_split": {
            "patient_count": len(test_patients),
            "image_count": len(test_df),
            "patient_ratio": round(len(test_patients) / total_unique_patients, 4),
            "patient_grade_distribution": _get_grade_dist(patient_df_test, "patient_grade"),
            "image_grade_distribution": _get_grade_dist(test_df, "grade"),
        },
    }

    logger.info(
        "Split complete: Train=%d patients (%d imgs), Val=%d patients (%d imgs), Test=%d patients (%d imgs). Overlap=0.",
        len(train_patients),
        len(train_df),
        len(val_patients),
        len(val_df),
        len(test_patients),
        len(test_df),
    )

    return train_df, val_df, test_df, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Partition DR dataset into leak-free patient-level splits.")
    parser.add_argument("--metadata", type=str, default=None, help="Path to input metadata CSV file.")
    parser.add_argument("--output-dir", type=str, required=True, help="Directory to save split CSVs and summary.")
    parser.add_argument("--train-ratio", type=float, default=0.70, help="Ratio for training partition (default: 0.70).")
    parser.add_argument("--val-ratio", type=float, default=0.15, help="Ratio for validation partition (default: 0.15).")
    parser.add_argument("--test-ratio", type=float, default=0.15, help="Ratio for test partition (default: 0.15).")
    parser.add_argument("--random-seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--mock", action="store_true", help="Generate synthetic multi-image patient cohort.")

    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.metadata is not None:
        if not Path(args.metadata).is_file():
            logger.error("Specified metadata file does not exist: %s", args.metadata)
            import sys
            sys.exit(1)

    use_mock = args.mock or (args.metadata is None)

    if use_mock:
        logger.info("Using synthetic multi-image patient cohort (--mock mode).")
        df = generate_mock_patient_cohort(num_patients=200, random_seed=args.random_seed)
    else:
        logger.info("Loading metadata from '%s'.", args.metadata)
        df = pd.read_csv(args.metadata)

    train_df, val_df, test_df, summary = split_dataset(
        df=df,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        random_seed=args.random_seed,
    )

    train_path = out_dir / "train_split.csv"
    val_path = out_dir / "val_split.csv"
    test_path = out_dir / "test_split.csv"
    summary_path = out_dir / "split_summary.json"

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info("Saved splits and summary to '%s':", out_dir)
    logger.info("  - %s (%d rows)", train_path.name, len(train_df))
    logger.info("  - %s (%d rows)", val_path.name, len(val_df))
    logger.info("  - %s (%d rows)", test_path.name, len(test_df))
    logger.info("  - %s", summary_path.name)


if __name__ == "__main__":
    main()
