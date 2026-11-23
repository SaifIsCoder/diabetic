"""
Online Retinal Data Generator Module.

Provides contamination-free, leak-free online data generation for diabetic
retinopathy classification.

Key Specifications:
1. Online-only augmentation: Augmentation is applied exclusively on-the-fly to
   training batches. Validation and test batches remain 100% pristine.
2. Pixel range contract: Returns raw float32 pixel values in [0.0, 255.0] matching
   inference pipeline (ML-03 contract: NO ImageNet mean subtraction or [-1, 1] normalization).
3. Ordinal targets: Produces cumulative binary ordinal vectors [t0, t1, t2, t3, t4]
   where t_k = 1 if grade >= k else 0 (Frank & Hall ordinal formulation).
4. Synthetic fallback: Generates synthetic retinal fundus fixtures when physical image files
   are absent from disk (allowing test execution under R2 and R5 guardrails).
"""

from __future__ import annotations

import io
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from PIL import Image, ImageEnhance, ImageOps
import tensorflow as tf


def grade_to_cumulative_ordinal(grade: int) -> np.ndarray:
    """Convert an integer DR grade (0-4) to a 5-element cumulative binary ordinal vector.

    For grade k:
      target = [1 if grade >= i else 0 for i in range(5)]
    Example:
      Grade 0 -> [1, 0, 0, 0, 0]
      Grade 1 -> [1, 1, 0, 0, 0]
      Grade 2 -> [1, 1, 1, 0, 0]
      Grade 3 -> [1, 1, 1, 1, 0]
      Grade 4 -> [1, 1, 1, 1, 1]
    """
    int_grade = int(grade)
    if not (0 <= int_grade <= 4):
        raise ValueError(f"DR grade must be between 0 and 4 (got {grade})")

    target = np.zeros(5, dtype=np.float32)
    for i in range(int_grade + 1):
        target[i] = 1.0
    return target


def generate_synthetic_fundus_array(
    seed: int,
    target_size: Tuple[int, int] = (224, 224),
) -> np.ndarray:
    """Generate a realistic synthetic fundus image array with raw pixel range [0.0, 255.0].

    Features a dark ocular background, circular fundus aperture, retinal orange-red hue,
    optic disc brightness, and simulated vascular gradients.
    """
    h, w = target_size
    rng = np.random.RandomState(seed % (2**31 - 1))

    # Coordinate grids
    y, x = np.ogrid[:h, :w]
    center_y, center_x = h / 2.0, w / 2.0
    radius = min(h, w) * 0.45

    # Circular mask for ocular aperture
    dist_from_center = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
    aperture_mask = dist_from_center <= radius

    # Base retinal color (orange-reddish fundus: R ~ 180-220, G ~ 70-110, B ~ 20-50)
    img = np.zeros((h, w, 3), dtype=np.float32)

    # Gradient across fundus
    radial_falloff = 1.0 - np.clip(dist_from_center / radius, 0.0, 1.0) * 0.35

    base_r = (190.0 + rng.uniform(-15.0, 15.0)) * radial_falloff
    base_g = (85.0 + rng.uniform(-10.0, 10.0)) * radial_falloff
    base_b = (25.0 + rng.uniform(-5.0, 5.0)) * radial_falloff

    img[..., 0] = base_r
    img[..., 1] = base_g
    img[..., 2] = base_b

    # Add optic disc (bright yellowish circle at nasal position)
    disc_x = center_x + radius * 0.45 * (1 if rng.rand() > 0.5 else -1)
    disc_y = center_y + rng.uniform(-15.0, 15.0)
    disc_dist = np.sqrt((x - disc_x) ** 2 + (y - disc_y) ** 2)
    disc_mask = disc_dist < (radius * 0.18)

    img[disc_mask, 0] = np.clip(img[disc_mask, 0] + 55.0, 0.0, 255.0)
    img[disc_mask, 1] = np.clip(img[disc_mask, 1] + 50.0, 0.0, 255.0)
    img[disc_mask, 2] = np.clip(img[disc_mask, 2] + 25.0, 0.0, 255.0)

    # Mask outside aperture to black
    img[~aperture_mask] = 0.0

    # Add gentle noise
    noise = rng.normal(0.0, 3.0, (h, w, 3)).astype(np.float32)
    img = np.clip(img + noise, 0.0, 255.0)

    return img.astype(np.float32)


class RetinalDataGenerator(tf.keras.utils.Sequence):
    """Keras Sequence data generator providing leak-free, online-augmented retinal fundus batches.

    Features:
    - Online augmentation strictly isolated to training mode (is_training=True).
    - Un-augmented pristine evaluation in validation and test mode (is_training=False).
    - Raw float32 pixel values in [0.0, 255.0] (ML-03 inference contract).
    - Cumulative binary ordinal target encoding.
    - Automatic synthetic fallback for missing disk images.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        img_dir: Union[str, Path],
        batch_size: int = 32,
        target_size: Tuple[int, int] = (224, 224),
        is_training: bool = False,
        shuffle: bool = True,
        seed: int = 42,
        allow_synthetic_fallback: bool = False,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        if len(df) == 0:
            raise ValueError("Input dataframe contains 0 samples (empty).")

        self.df = df.copy().reset_index(drop=True)
        self.img_dir = Path(img_dir) if img_dir else Path(".")
        self.batch_size = max(1, int(batch_size))
        self.target_size = target_size
        self.is_training = is_training
        self.shuffle = shuffle
        self.seed = seed
        self.allow_synthetic_fallback = allow_synthetic_fallback
        self.rng = np.random.RandomState(seed)

        # Detect column names
        cols = self.df.columns.tolist()
        self.image_col = next(
            (c for c in ["image_id", "id_code", "image_path", "filename", "file_name", "image"] if c in cols),
            cols[0],
        )
        self.grade_col = next(
            (c for c in ["grade", "diagnosis", "dr_grade", "severity", "label"] if c in cols),
            cols[1] if len(cols) > 1 else cols[0],
        )

        self.indices = np.arange(len(self.df))
        if self.shuffle and self.is_training:
            self.rng.shuffle(self.indices)

    def __len__(self) -> int:
        """Number of batches per epoch."""
        return int(math.ceil(len(self.df) / self.batch_size))

    def on_epoch_end(self) -> None:
        """Shuffle indices at end of each epoch if in training mode."""
        if self.shuffle and self.is_training:
            self.rng.shuffle(self.indices)

    def _apply_augmentation(self, image: Image.Image) -> Image.Image:
        """Apply stochastic online augmentation during training.

        Includes rotation, horizontal/vertical flips, zoom, and brightness/contrast adjustments.
        """
        # Horizontal flip
        if self.rng.rand() > 0.5:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)

        # Vertical flip
        if self.rng.rand() > 0.5:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)

        # Random rotation (-15 to +15 degrees)
        angle = self.rng.uniform(-15.0, 15.0)
        image = image.rotate(angle, resample=Image.Resampling.BILINEAR, fillcolor=(0, 0, 0))

        # Random zoom / crop (0.88 to 1.12)
        zoom_factor = self.rng.uniform(0.88, 1.12)
        w, h = image.size
        crop_w = int(w / zoom_factor)
        crop_h = int(h / zoom_factor)
        if zoom_factor > 1.0:
            left = max(0, (w - crop_w) // 2)
            top = max(0, (h - crop_h) // 2)
            image = image.crop((left, top, left + crop_w, top + crop_h)).resize(
                self.target_size, resample=Image.Resampling.LANCZOS
            )
        elif zoom_factor < 1.0:
            new_w = int(w * zoom_factor)
            new_h = int(h * zoom_factor)
            resized = image.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", self.target_size, (0, 0, 0))
            offset_x = (w - new_w) // 2
            offset_y = (h - new_h) // 2
            canvas.paste(resized, (offset_x, offset_y))
            image = canvas

        # Brightness adjustment (0.85 to 1.15)
        brightness_factor = self.rng.uniform(0.85, 1.15)
        image = ImageEnhance.Brightness(image).enhance(brightness_factor)

        # Contrast adjustment (0.85 to 1.15)
        contrast_factor = self.rng.uniform(0.85, 1.15)
        image = ImageEnhance.Contrast(image).enhance(contrast_factor)

        return image

    def _load_image(self, row_idx: int) -> np.ndarray:
        """Load single image from disk or generate synthetic fallback array."""
        image_name = str(self.df.iloc[row_idx][self.image_col])
        full_path = self.img_dir / image_name

        if not full_path.is_file():
            for ext in [".jpg", ".jpeg", ".png"]:
                candidate = self.img_dir / f"{image_name}{ext}"
                if candidate.is_file():
                    full_path = candidate
                    break

        if full_path.is_file():
            try:
                with Image.open(full_path) as img:
                    img = img.convert("RGB")
                    if self.is_training:
                        img = self._apply_augmentation(img)
                    img = img.resize(self.target_size, resample=Image.Resampling.LANCZOS)
                    arr = np.asarray(img, dtype=np.float32)
                    return np.clip(arr, 0.0, 255.0)
            except Exception:
                if not self.allow_synthetic_fallback:
                    raise IOError(f"Could not read retinal image file: {full_path}")

        # If image directory exists on disk but file is missing, fail closed unless fallback allowed
        if self.img_dir.is_dir() and not self.allow_synthetic_fallback:
            raise FileNotFoundError(f"Retinal image file not found on disk: {full_path}")

        # Synthetic fallback (used when directory is nonexistent or fallback explicitly allowed)
        arr = generate_synthetic_fundus_array(seed=self.seed + row_idx, target_size=self.target_size)
        if self.is_training:
            pil_img = Image.fromarray(np.uint8(np.clip(arr, 0.0, 255.0)))
            pil_img = self._apply_augmentation(pil_img)
            arr = np.asarray(pil_img, dtype=np.float32)
        return np.clip(arr, 0.0, 255.0)

    def __getitem__(self, index: int) -> Tuple[np.ndarray, np.ndarray]:
        """Fetch batch (X, y) at given batch index.

        Returns:
          X: float32 numpy array with shape (batch_size, 224, 224, 3) in range [0.0, 255.0].
          y: float32 numpy array with shape (batch_size, 5) representing cumulative ordinal targets.
        """
        start_idx = index * self.batch_size
        end_idx = min(start_idx + self.batch_size, len(self.df))
        batch_indices = self.indices[start_idx:end_idx]
        actual_batch_size = len(batch_indices)

        batch_x = np.empty((actual_batch_size, self.target_size[0], self.target_size[1], 3), dtype=np.float32)
        batch_y = np.empty((actual_batch_size, 5), dtype=np.float32)

        for i, row_idx in enumerate(batch_indices):
            batch_x[i] = self._load_image(row_idx)
            raw_grade = int(self.df.iloc[row_idx][self.grade_col])
            batch_y[i] = grade_to_cumulative_ordinal(raw_grade)

        return batch_x, batch_y
