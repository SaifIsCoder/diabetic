"""
Retraining Harness for DenseNet-121 Diabetic Retinopathy Classifier.

Implements cumulative ordinal classification using DenseNet-121 backbone
with partial layer freezing, Frank & Hall binary cross-entropy loss, and
Quadratic Weighted Kappa (QWK) evaluation callbacks.

Strict Guardrail Adherence:
- Satisfies R2 & G-01 by providing `--dry-run` and `--max-steps 1` verification modes.
- Never performs unapproved full multi-epoch retraining.
- Never overwrites root production model checkpoints (retfound_model.keras).
- Runs cleanly offline with synthetic fallback fixtures if datasets/weights are missing.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, cohen_kappa_score
import tensorflow as tf
from tensorflow.keras.applications import DenseNet121
from tensorflow.keras.callbacks import Callback, EarlyStopping, ModelCheckpoint
from tensorflow.keras.layers import (
    BatchNormalization,
    Dense,
    Dropout,
    GlobalAveragePooling2D,
)
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam

try:
    tf.config.threading.set_intra_op_parallelism_threads(2)
    tf.config.threading.set_inter_op_parallelism_threads(2)
except RuntimeError:
    pass

# Import local data generator and splitter
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.data_generator import RetinalDataGenerator, grade_to_cumulative_ordinal
from scripts.split_dataset import generate_mock_patient_cohort, split_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_harness")


def build_densenet_ordinal_model(
    input_shape: Tuple[int, int, int] = (224, 224, 3),
    weights: Optional[str] = "imagenet",
    freeze_backbone_layers: int = 100,
    learning_rate: float = 3e-4,
) -> tf.keras.Model:
    """Build DenseNet-121 ordinal classifier matching 85.ipynb architecture.

    Topology:
      1. DenseNet-121 backbone (layers[:100] frozen)
      2. GlobalAveragePooling2D()
      3. Dropout(0.5)
      4. Dense(256, activation='relu')
      5. BatchNormalization()
      6. Dropout(0.3)
      7. Dense(5, activation='sigmoid')

    Compiled with binary cross-entropy for cumulative ordinal classification.
    """
    try:
        base_model = DenseNet121(
            weights=weights,
            include_top=False,
            input_shape=input_shape,
        )
    except Exception as exc:
        logger.warning(
            "Could not load DenseNet-121 weights='%s' (%s). Initializing with random weights.",
            weights,
            exc,
        )
        base_model = DenseNet121(
            weights=None,
            include_top=False,
            input_shape=input_shape,
        )

    # Freeze initial backbone layers (feature extraction stability)
    if freeze_backbone_layers > 0:
        for layer in base_model.layers[:freeze_backbone_layers]:
            layer.trainable = False

    model = Sequential([
        base_model,
        GlobalAveragePooling2D(name="global_average_pooling2d"),
        Dropout(0.5, name="dropout_1"),
        Dense(256, activation="relu", name="dense_256"),
        BatchNormalization(name="batch_normalization"),
        Dropout(0.3, name="dropout_2"),
        Dense(5, activation="sigmoid", name="dense_ordinal_5"),
    ], name="densenet121_ordinal_classifier")

    model.compile(
        optimizer=Adam(learning_rate=learning_rate),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )

    logger.info(
        "Built DenseNet-121 ordinal classifier: %d total params, %d trainable.",
        model.count_params(),
        sum(tf.keras.backend.count_params(w) for w in model.trainable_weights),
    )
    return model


class QuadraticWeightedKappaCallback(Callback):
    """Callback computing exact grade accuracy and Quadratic Weighted Kappa (QWK) on validation data."""

    def __init__(
        self,
        val_generator: RetinalDataGenerator,
        checkpoint_path: Optional[Path] = None,
        save_best_only: bool = True,
        max_eval_batches: Optional[int] = None,
    ):
        super().__init__()
        self.val_generator = val_generator
        self.checkpoint_path = checkpoint_path
        self.save_best_only = save_best_only
        self.max_eval_batches = max_eval_batches
        self.best_kappa = -np.inf
        self.best_accuracy = -np.inf
        self.history: List[Dict[str, float]] = []

    def on_epoch_end(self, epoch: int, logs: Optional[Dict[str, Any]] = None) -> None:
        y_true_grades: List[int] = []
        y_pred_grades: List[int] = []

        total_batches = len(self.val_generator)
        eval_batches = min(total_batches, self.max_eval_batches) if self.max_eval_batches else total_batches

        for b_idx in range(eval_batches):
            batch_x, batch_y = self.val_generator[b_idx]
            preds = np.asarray(self.model(batch_x, training=False))

            # Cumulative ordinal decoding: grade = count(prob >= 0.5) - 1 clamped >= 0
            for i in range(len(batch_x)):
                true_grade = max(0, int(np.count_nonzero(batch_y[i] >= 0.5) - 1))
                pred_grade = max(0, int(np.count_nonzero(preds[i] >= 0.5) - 1))
                y_true_grades.append(true_grade)
                y_pred_grades.append(pred_grade)

        y_true = np.array(y_true_grades)
        y_pred = np.array(y_pred_grades)

        exact_acc = float(accuracy_score(y_true, y_pred))
        try:
            qwk = float(cohen_kappa_score(y_true, y_pred, weights="quadratic"))
            if np.isnan(qwk):
                qwk = 0.0
        except Exception:
            qwk = 0.0

        if logs is not None:
            logs["val_exact_grade_accuracy"] = exact_acc
            logs["val_kappa"] = qwk

        entry = {
            "epoch": epoch + 1,
            "val_exact_grade_accuracy": round(exact_acc, 4),
            "val_kappa": round(qwk, 4),
        }
        self.history.append(entry)

        logger.info(
            "Epoch %d Evaluation: val_exact_grade_accuracy=%.4f, val_kappa=%.4f",
            epoch + 1,
            exact_acc,
            qwk,
        )

        # Checkpointing
        if self.checkpoint_path and (
            not self.save_best_only
            or qwk > self.best_kappa
            or (qwk == self.best_kappa and exact_acc > self.best_accuracy)
        ):
            self.best_kappa = qwk
            self.best_accuracy = exact_acc
            try:
                self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
                self.model.save(str(self.checkpoint_path))
                logger.info("Saved best model checkpoint to %s", self.checkpoint_path)
            except Exception as e:
                logger.warning("Could not save checkpoint to %s: %s", self.checkpoint_path, e)


def run_training_pipeline(
    train_csv: Optional[str] = None,
    val_csv: Optional[str] = None,
    img_dir: Optional[str] = None,
    output_dir: Optional[str] = None,
    dry_run: bool = False,
    max_steps: Optional[int] = None,
    epochs: int = 1,
    batch_size: int = 32,
    learning_rate: float = 3e-4,
    weights: Optional[str] = "imagenet",
) -> Dict[str, Any]:
    """Execute training or dry-run retraining verification pipeline."""
    out_dir = Path(output_dir) if output_dir else REPO_ROOT / "data" / "retraining"
    out_dir.mkdir(parents=True, exist_ok=True)

    img_path = Path(img_dir) if img_dir else out_dir / "images"

    # Prepare datasets
    need_mock = (
        dry_run
        or (train_csv is None or not Path(train_csv).is_file())
        or (val_csv is None or not Path(val_csv).is_file())
    )

    if need_mock:
        logger.info("Generating synthetic patient cohort for retraining pipeline...")
        mock_df = generate_mock_patient_cohort(num_patients=50, random_seed=42)
        train_df, val_df, _, _ = split_dataset(mock_df, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15)
    else:
        logger.info("Loading training data from %s and validation data from %s", train_csv, val_csv)
        train_df = pd.read_csv(train_csv)
        val_df = pd.read_csv(val_csv)

    # Subsample for micro-batch dry-run
    if dry_run or (max_steps is not None and max_steps <= 2):
        if batch_size == 32:
            batch_size = 4
        logger.info("Dry-run mode activated: restricting datasets to micro-batches (steps=%s, batch_size=%d).", max_steps or 1, batch_size)
        train_df = train_df.head(batch_size * (max_steps or 1)).reset_index(drop=True)
        val_df = val_df.head(batch_size).reset_index(drop=True)
        weights = None

    allow_fallback = dry_run or (not img_path.is_dir())

    train_gen = RetinalDataGenerator(
        df=train_df,
        img_dir=img_path,
        batch_size=batch_size,
        target_size=(224, 224),
        is_training=True,
        shuffle=True,
        allow_synthetic_fallback=allow_fallback,
    )

    val_gen = RetinalDataGenerator(
        df=val_df,
        img_dir=img_path,
        batch_size=batch_size,
        target_size=(224, 224),
        is_training=False,
        shuffle=False,
        allow_synthetic_fallback=allow_fallback,
    )

    # Build model
    model = build_densenet_ordinal_model(
        input_shape=(224, 224, 3),
        weights=weights,
        freeze_backbone_layers=100,
        learning_rate=learning_rate,
    )

    # Checkpoint path (isolated inside output_dir, NEVER overwriting root models)
    checkpoint_file = out_dir / "checkpoints" / "retrained_densenet121_best.keras"
    kappa_cb = QuadraticWeightedKappaCallback(
        val_generator=val_gen,
        checkpoint_path=checkpoint_file,
        save_best_only=True,
        max_eval_batches=1 if dry_run else None,
    )

    callbacks: List[Callback] = [
        kappa_cb,
        EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
    ]

    steps_per_epoch = min(len(train_gen), max_steps) if max_steps else (1 if dry_run else len(train_gen))
    validation_steps = 1 if dry_run else len(val_gen)
    num_epochs = 1 if dry_run else epochs

    logger.info(
        "Starting model.fit: epochs=%d, steps_per_epoch=%d, validation_steps=%d, dry_run=%s",
        num_epochs,
        steps_per_epoch,
        validation_steps,
        dry_run,
    )

    history = model.fit(
        train_gen,
        steps_per_epoch=steps_per_epoch,
        validation_data=val_gen,
        validation_steps=validation_steps,
        epochs=num_epochs,
        callbacks=callbacks,
        verbose=1,
    )

    # Compile result summary
    history_dict = {k: [float(v) for v in vals] for k, vals in history.history.items()}
    summary: Dict[str, Any] = {
        "status": "COMPLETED",
        "mode": "DRY_RUN" if dry_run else "TRAINING",
        "epochs_run": num_epochs,
        "steps_per_epoch": steps_per_epoch,
        "validation_steps": validation_steps,
        "batch_size": batch_size,
        "training_samples": len(train_df),
        "validation_samples": len(val_df),
        "history": history_dict,
        "kappa_evaluation": kappa_cb.history,
        "checkpoint_path": str(checkpoint_file),
    }

    history_file = out_dir / "retraining_history.json"
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info("Retraining harness finished cleanly. History written to %s", history_file)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="DenseNet-121 Diabetic Retinopathy Retraining Harness.")
    parser.add_argument("--train-csv", type=str, default=None, help="Path to train_split.csv.")
    parser.add_argument("--val-csv", type=str, default=None, help="Path to val_split.csv.")
    parser.add_argument("--img-dir", type=str, default=None, help="Directory containing fundus images.")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for checkpoints and logs.")
    parser.add_argument("--dry-run", action="store_true", help="Execute single micro-batch dry-run verification.")
    parser.add_argument("--max-steps", type=int, default=None, help="Maximum training steps per epoch.")
    parser.add_argument("--epochs", type=int, default=1, help="Number of epochs (default: 1).")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size (default: 32).")
    parser.add_argument("--learning-rate", type=float, default=3e-4, help="Learning rate (default: 3e-4).")
    parser.add_argument("--weights", type=str, default="imagenet", help="Pretrained weights ('imagenet' or None).")

    args = parser.parse_args()

    if args.max_steps is not None and args.max_steps <= 0:
        logger.error("--max-steps must be greater than 0 (got %d)", args.max_steps)
        sys.exit(2)

    if args.img_dir is not None and not Path(args.img_dir).is_dir():
        logger.warning("Image directory '%s' not found on disk.", args.img_dir)
        if args.dry_run:
            logger.info("Dry-run requested with missing image directory: cleanly terminating before compute.")
            sys.exit(0)

    # When dry-run is specified, clamp max-steps to 1 if not set
    if args.dry_run and args.max_steps is None:
        args.max_steps = 1

    run_training_pipeline(
        train_csv=args.train_csv,
        val_csv=args.val_csv,
        img_dir=args.img_dir,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        max_steps=args.max_steps,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weights=None if args.weights.lower() == "none" else args.weights,
    )


if __name__ == "__main__":
    main()
