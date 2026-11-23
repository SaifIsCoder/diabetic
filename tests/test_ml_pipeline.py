"""
Automated Test Suite for Milestone 2: ML Data Leakage Resolution & Retraining Pipeline.

Covers:
1. Patient-level dataset partitioning with formal zero-overlap verification across
   train, validation, and holdout test splits.
2. Stratification fidelity preserving patient severity distributions.
3. Online data generator compliance: batch dimensions, raw [0.0, 255.0] float32 pixel contract,
   and Frank & Hall cumulative binary ordinal labels.
4. Online augmentation isolation: active solely during training, strictly disabled
   for validation and testing.
5. Retraining harness execution under --dry-run and --max-steps 1 verification modes.
6. Diagnostic evaluation module verifying exact accuracy, QWK, Referable DR sensitivity/specificity,
   and confusion matrices.
7. Ordinal encoding and decoding parity with production inference contract (app.py:283).
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import Dict, Set

import numpy as np
import pandas as pd
import pytest
from PIL import Image

from scripts.data_generator import (
    RetinalDataGenerator,
    generate_synthetic_fundus_array,
    grade_to_cumulative_ordinal,
)
from scripts.evaluate_model import decode_ordinal_predictions, evaluate_predictions, run_evaluation
from scripts.split_dataset import (
    detect_columns,
    generate_mock_patient_cohort,
    split_dataset,
)
from scripts.train_harness import (
    QuadraticWeightedKappaCallback,
    build_densenet_ordinal_model,
    run_training_pipeline,
)


REPO_ROOT = Path(__file__).resolve().parent.parent


class TestPatientLevelSplitting:
    """Verifies that dataset splitting eliminates all patient and image cross-split leakage."""

    @pytest.fixture
    def mock_cohort(self) -> pd.DataFrame:
        """Synthetic multi-image patient cohort."""
        return generate_mock_patient_cohort(num_patients=120, random_seed=42)

    def test_zero_patient_overlap_invariant(self, mock_cohort: pd.DataFrame):
        """Formally asserts that P_train, P_val, and P_test sets are 100% mutually disjoint."""
        train_df, val_df, test_df, summary = split_dataset(
            mock_cohort, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, random_seed=42
        )

        train_patients: Set[str] = set(train_df["patient_id"])
        val_patients: Set[str] = set(val_df["patient_id"])
        test_patients: Set[str] = set(test_df["patient_id"])

        # Tripartite disjointness assertions
        assert len(train_patients & val_patients) == 0, (
            f"Leakage detected between train and val: {train_patients & val_patients}"
        )
        assert len(train_patients & test_patients) == 0, (
            f"Leakage detected between train and test: {train_patients & test_patients}"
        )
        assert len(val_patients & test_patients) == 0, (
            f"Leakage detected between val and test: {val_patients & test_patients}"
        )

        # Completeness assertion: all unique patients accounted for
        total_unique = mock_cohort["patient_id"].nunique()
        assert len(train_patients | val_patients | test_patients) == total_unique
        assert summary["leak_free_verification"]["zero_leakage_verified"] is True

    def test_zero_image_overlap_invariant(self, mock_cohort: pd.DataFrame):
        """Ensures that no individual image appears in more than one partition."""
        train_df, val_df, test_df, _ = split_dataset(
            mock_cohort, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, random_seed=42
        )

        train_imgs = set(train_df["image_id"])
        val_imgs = set(val_df["image_id"])
        test_imgs = set(test_df["image_id"])

        assert len(train_imgs & val_imgs) == 0
        assert len(train_imgs & test_imgs) == 0
        assert len(val_imgs & test_imgs) == 0
        assert len(train_imgs | val_imgs | test_imgs) == len(mock_cohort)

    def test_stratification_preserves_patient_grade_proportions(self, mock_cohort: pd.DataFrame):
        """Verifies that patient severity distribution is preserved across all splits."""
        train_df, val_df, test_df, summary = split_dataset(
            mock_cohort, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, random_seed=42
        )

        # Check all 5 grades exist in train split
        train_grades = set(train_df["patient_grade"].unique())
        cohort_grades = set(mock_cohort.groupby("patient_id")["grade"].max().unique())
        assert cohort_grades.issubset(train_grades)

        # Ratios approximate target ratios within expected discrete bin tolerances
        assert 0.65 <= summary["train_split"]["patient_ratio"] <= 0.75
        assert 0.10 <= summary["val_split"]["patient_ratio"] <= 0.20
        assert 0.10 <= summary["test_split"]["patient_ratio"] <= 0.20

    def test_patient_severity_aggregation_rule(self):
        """Verifies patient_grade = max(image_grades) per patient."""
        # Patient with asymmetric grades (OD=0, OS=3) must have patient_grade=3
        asymmetric_df = pd.DataFrame([
            {"patient_id": "P_001", "image_id": "P_001_OD.jpg", "grade": 0},
            {"patient_id": "P_001", "image_id": "P_001_OS.jpg", "grade": 3},
            {"patient_id": "P_002", "image_id": "P_002_OD.jpg", "grade": 1},
            {"patient_id": "P_003", "image_id": "P_003_OD.jpg", "grade": 2},
            {"patient_id": "P_004", "image_id": "P_004_OD.jpg", "grade": 4},
        ])

        train_df, val_df, test_df, _ = split_dataset(
            asymmetric_df, train_ratio=0.50, val_ratio=0.25, test_ratio=0.25, random_seed=42
        )

        all_splits = pd.concat([train_df, val_df, test_df])
        p001_rows = all_splits[all_splits["patient_id"] == "P_001"]
        assert len(p001_rows) == 2
        # Both images must have patient_grade=3
        assert (p001_rows["patient_grade"] == 3).all()

    def test_custom_ratios_and_seeds_reproducibility(self, mock_cohort: pd.DataFrame):
        """Verifies deterministic output across runs with identical random seed."""
        t1, v1, s1, _ = split_dataset(mock_cohort, train_ratio=0.80, val_ratio=0.10, test_ratio=0.10, random_seed=123)
        t2, v2, s2, _ = split_dataset(mock_cohort, train_ratio=0.80, val_ratio=0.10, test_ratio=0.10, random_seed=123)

        assert t1["patient_id"].tolist() == t2["patient_id"].tolist()
        assert v1["patient_id"].tolist() == v2["patient_id"].tolist()
        assert s1["patient_id"].tolist() == s2["patient_id"].tolist()

    def test_invalid_ratio_sum_raises_error(self, mock_cohort: pd.DataFrame):
        """Asserts ValueError when train + val + test != 1.0."""
        with pytest.raises(ValueError, match="Split ratios must sum to 1.0"):
            split_dataset(mock_cohort, train_ratio=0.50, val_ratio=0.20, test_ratio=0.10)


class TestRetinalDataGenerator:
    """Verifies data generator batch shapes, pixel contracts, ordinal targets, and augmentation isolation."""

    @pytest.fixture
    def sample_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame({
            "image_id": [f"img_{i:02d}.jpg" for i in range(10)],
            "grade": [0, 1, 2, 3, 4, 0, 1, 2, 3, 4],
        })

    def test_batch_dimensions_and_shapes(self, sample_dataframe: pd.DataFrame):
        """Verifies X shape is (batch_size, 224, 224, 3) and y shape is (batch_size, 5)."""
        gen = RetinalDataGenerator(
            df=sample_dataframe,
            img_dir="nonexistent_dir",
            batch_size=4,
            target_size=(224, 224),
            is_training=False,
        )

        assert len(gen) == 3  # ceil(10 / 4)
        x_batch, y_batch = gen[0]

        assert x_batch.shape == (4, 224, 224, 3)
        assert y_batch.shape == (4, 5)
        assert x_batch.dtype == np.float32
        assert y_batch.dtype == np.float32

        # Last batch has remaining 2 samples
        x_last, y_last = gen[2]
        assert x_last.shape == (2, 224, 224, 3)
        assert y_last.shape == (2, 5)

    def test_raw_pixel_range_contract_ml03(self, sample_dataframe: pd.DataFrame):
        """ML-03: Verifies pixel values strictly reside in [0.0, 255.0] without ImageNet mean subtraction."""
        gen = RetinalDataGenerator(
            df=sample_dataframe,
            img_dir="nonexistent_dir",
            batch_size=4,
            is_training=False,
        )
        x_batch, _ = gen[0]

        assert x_batch.min() >= 0.0, f"Pixel underflow: min={x_batch.min()}"
        assert x_batch.max() <= 255.0, f"Pixel overflow: max={x_batch.max()}"
        # Synthetic fundus has circular aperture with non-zero pixels
        assert x_batch.max() > 100.0, "Expected fundus interior pixels > 100.0"

    def test_cumulative_binary_ordinal_target_encoding(self):
        """Verifies Frank & Hall ordinal mapping: [t0, ..., t4] where t_k = 1 if grade >= k else 0."""
        expected_mappings = {
            0: [1.0, 0.0, 0.0, 0.0, 0.0],
            1: [1.0, 1.0, 0.0, 0.0, 0.0],
            2: [1.0, 1.0, 1.0, 0.0, 0.0],
            3: [1.0, 1.0, 1.0, 1.0, 0.0],
            4: [1.0, 1.0, 1.0, 1.0, 1.0],
        }

        for grade, expected_vec in expected_mappings.items():
            encoded = grade_to_cumulative_ordinal(grade)
            assert np.array_equal(encoded, np.array(expected_vec, dtype=np.float32)), (
                f"Grade {grade} mapped to {encoded}, expected {expected_vec}"
            )

    def test_online_augmentation_strict_isolation(self, sample_dataframe: pd.DataFrame):
        """Ensures augmentation is active when is_training=True and strictly disabled when is_training=False."""
        # 1. Validation/test generator: is_training=False must return deterministic pristine images
        val_gen = RetinalDataGenerator(
            df=sample_dataframe,
            img_dir="nonexistent_dir",
            batch_size=2,
            is_training=False,
            seed=42,
        )
        x_val_1, _ = val_gen[0]
        x_val_2, _ = val_gen[0]
        # In pristine mode, consecutive reads of the same index must be bitwise identical
        np.testing.assert_array_equal(
            x_val_1,
            x_val_2,
            err_msg="Validation images varied between reads! Augmentation must be disabled when is_training=False.",
        )

        # 2. Training generator: is_training=True applies stochastic transformations
        train_gen = RetinalDataGenerator(
            df=sample_dataframe,
            img_dir="nonexistent_dir",
            batch_size=2,
            is_training=True,
            seed=42,
        )
        x_train_1, _ = train_gen[0]
        x_train_2, _ = train_gen[0]
        # At least some pixels should differ due to stochastic rotation/flip/zoom/brightness
        assert not np.array_equal(x_train_1, x_train_2), (
            "Training generator did not apply stochastic augmentation across successive batch calls."
        )

    def test_physical_image_loading_fallback(self):
        """Verifies generator correctly loads physical images when present on disk."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            img_file = tmp_path / "real_fundus_01.jpg"

            # Create test image on disk
            img = Image.new("RGB", (300, 300), color=(180, 80, 30))
            img.save(img_file)

            df = pd.DataFrame([{"image_id": "real_fundus_01.jpg", "grade": 2}])
            gen = RetinalDataGenerator(df=df, img_dir=tmp_path, batch_size=1, is_training=False)

            x_batch, y_batch = gen[0]
            assert x_batch.shape == (1, 224, 224, 3)
            # R channel should reflect ~180
            assert np.isclose(x_batch[0, 112, 112, 0], 180.0, atol=5.0)


class TestRetrainingHarness:
    """Verifies model topology, QWK callbacks, and safe dry-run execution."""

    def test_densenet_ordinal_model_topology(self):
        """Verifies model layers, output shape (None, 5), and backbone freezing."""
        model = build_densenet_ordinal_model(
            input_shape=(224, 224, 3),
            weights=None,  # Test without downloading weights
            freeze_backbone_layers=100,
        )

        assert model.output_shape == (None, 5)
        # Check layer names
        layer_names = [l.name for l in model.layers]
        assert "global_average_pooling2d" in layer_names
        assert "dense_256" in layer_names
        assert "batch_normalization" in layer_names
        assert "dense_ordinal_5" in layer_names

        # Verify backbone layers[:100] are frozen
        base_model = model.layers[0]
        for idx, layer in enumerate(base_model.layers[:100]):
            assert not layer.trainable, f"Layer {idx} ({layer.name}) should be frozen"

    def test_dry_run_execution_pipeline(self):
        """Verifies retraining harness executes cleanly under dry-run mode."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            summary = run_training_pipeline(
                output_dir=tmp_dir,
                dry_run=True,
                max_steps=1,
                epochs=1,
                batch_size=4,
                weights=None,
            )

            assert summary["status"] == "COMPLETED"
            assert summary["mode"] == "DRY_RUN"
            assert summary["epochs_run"] == 1
            assert "loss" in summary["history"]
            assert len(summary["kappa_evaluation"]) == 1

            # Check history file was created
            history_file = Path(tmp_dir) / "retraining_history.json"
            assert history_file.is_file()

            with open(history_file, "r", encoding="utf-8") as f:
                saved_summary = json.load(f)
            assert saved_summary["mode"] == "DRY_RUN"

    def test_existing_root_models_never_modified_by_harness(self):
        """Enforces guardrail: retraining harness must NEVER overwrite retfound_model.keras at root."""
        root_keras = REPO_ROOT / "retfound_model.keras"
        if root_keras.is_file():
            stat_before = root_keras.stat().st_mtime
            # Run dry-run
            with tempfile.TemporaryDirectory() as tmp_dir:
                run_training_pipeline(
                    output_dir=tmp_dir,
                    dry_run=True,
                    max_steps=1,
                    epochs=1,
                    batch_size=4,
                    weights=None,
                )
            stat_after = root_keras.stat().st_mtime
            assert stat_before == stat_after, "Root retfound_model.keras was modified!"


class TestModelEvaluation:
    """Verifies clinical diagnostic evaluation calculations and reporting."""

    def test_ordinal_decoding_parity_with_app(self):
        """Verifies decode_ordinal_predictions exactly matches app.py:283."""
        # Test edge case predictions
        test_probs = np.array([
            [0.9, 0.1, 0.1, 0.0, 0.0],  # count>=0.5 is 1 -> grade 0
            [0.9, 0.8, 0.2, 0.1, 0.0],  # count>=0.5 is 2 -> grade 1
            [0.9, 0.9, 0.8, 0.1, 0.0],  # count>=0.5 is 3 -> grade 2
            [0.9, 0.9, 0.9, 0.8, 0.1],  # count>=0.5 is 4 -> grade 3
            [0.9, 0.9, 0.9, 0.9, 0.9],  # count>=0.5 is 5 -> grade 4
            [0.2, 0.1, 0.0, 0.0, 0.0],  # count>=0.5 is 0 -> grade 0
        ])

        grades = decode_ordinal_predictions(test_probs)
        expected = np.array([0, 1, 2, 3, 4, 0])
        np.testing.assert_array_equal(grades, expected)

    def test_clinical_evaluation_metrics_computation(self):
        """Verifies exact accuracy, QWK, Referable DR sensitivity/specificity, and confusion matrix."""
        y_true = np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4])
        # Simulate slight predictions: 8 correct, 2 off by 1
        y_pred = np.array([0, 0, 1, 2, 2, 2, 3, 4, 4, 4])

        metrics = evaluate_predictions(y_true, y_pred)

        assert metrics["sample_count"] == 10
        assert metrics["exact_grade_accuracy"] == 0.8000
        assert metrics["quadratic_weighted_kappa"] > 0.85
        assert metrics["macro_f1"] > 0.70

        # Referable DR (Grade >= 2):
        # y_true >= 2: indices 4,5,6,7,8,9 (6 samples)
        # y_pred for those: 2,2,3,4,4,4 (all >= 2 -> 6 TP, 0 FN -> sensitivity = 1.0)
        ref = metrics["referable_dr_metrics"]
        assert ref["true_positives"] == 6
        assert ref["false_negatives"] == 0
        assert ref["sensitivity"] == 1.0000

        # Non-referable: indices 0,1,2,3
        # y_pred for index 3 is 2 (FP), others 0,0,1 (TN=3) -> specificity = 3/4 = 0.75
        assert ref["true_negatives"] == 3
        assert ref["false_positives"] == 1
        assert ref["specificity"] == 0.7500

        # Confusion matrix shape
        assert len(metrics["confusion_matrix"]) == 5
        assert len(metrics["confusion_matrix"][0]) == 5

    def test_run_evaluation_mock_mode_and_json_export(self):
        """Verifies evaluate_model.run_evaluation generates valid report JSON."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_json = Path(tmp_dir) / "eval_report.json"
            res = run_evaluation(output_json=str(out_json), mock=True)

            assert out_json.is_file()
            with open(out_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert "exact_grade_accuracy" in data
            assert "quadratic_weighted_kappa" in data
            assert "referable_dr_metrics" in data
            assert data["sample_count"] > 0
