"""
Pytest configuration and synthetic fixtures for E2E opaque-box test suite.

Features:
- Dynamic marker registration for strict-marker compliance.
- Ephemeral synthetic fixtures (MockPatientCohort, MockFundusFactory,
  MockStagingEnvironment, MockModelCheckpoint, MarkdownLinterFixture).
- Zero real patient health data (zero PHI).
- Zero external WAN calls or paid cloud provisioning.
"""

from __future__ import annotations

import datetime
import ipaddress
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def pytest_configure(config: pytest.Config) -> None:
    """Dynamically register custom E2E markers to satisfy --strict-markers."""
    config.addinivalue_line("markers", "e2e: End-to-end opaque-box tests")
    config.addinivalue_line("markers", "tier1: Tier 1 Feature coverage tests")
    config.addinivalue_line("markers", "tier2: Tier 2 Boundary and corner case tests")
    config.addinivalue_line("markers", "tier3: Tier 3 Pairwise cross-feature integration tests")
    config.addinivalue_line("markers", "tier4: Tier 4 Real-world clinical workflow scenarios")


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the absolute Path to repository root."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def python_exe() -> str:
    """Return the active Python interpreter executable path."""
    return sys.executable


# ==============================================================================
# Fixture 1: MockPatientCohort
# ==============================================================================

class MockPatientCohort:
    """Generates synthetic patient metadata cohorts with multi-image distributions."""

    @staticmethod
    def generate_dataframe(
        num_patients: int = 50,
        random_seed: int = 42,
        min_images_per_patient: int = 1,
        max_images_per_patient: int = 4,
    ) -> pd.DataFrame:
        """Create a synthetic pandas DataFrame containing patient metadata."""
        rng = np.random.default_rng(random_seed)
        rows: List[Dict[str, Any]] = []

        # Grounding DR distribution (60% 0, 15% 1, 15% 2, 6% 3, 4% 4)
        grade_probs = [0.60, 0.15, 0.15, 0.06, 0.04]

        for p_idx in range(1, num_patients + 1):
            patient_id = f"SYN-P{p_idx:04d}"
            patient_grade = int(rng.choice([0, 1, 2, 3, 4], p=grade_probs))
            img_count = int(rng.integers(min_images_per_patient, max_images_per_patient + 1))

            for img_i in range(img_count):
                eye = "OD" if img_i % 2 == 0 else "OS"
                field = "macular" if img_i < 2 else "peripheral"
                # Sub-grade can be equal or slightly less than max patient grade
                if patient_grade > 0 and rng.random() > 0.6:
                    img_grade = int(rng.integers(0, patient_grade + 1))
                else:
                    img_grade = patient_grade

                # Ensure at least one image has the max patient_grade
                if img_i == img_count - 1 and img_count > 1:
                    max_so_far = max([r["diagnosis"] for r in rows if r["patient_id"] == patient_id] or [0])
                    if max_so_far < patient_grade:
                        img_grade = patient_grade

                image_id = f"{patient_id}_{eye}_{field}_{img_i}"
                rows.append({
                    "image_id": image_id,
                    "patient_id": patient_id,
                    "eye": eye,
                    "field": field,
                    "diagnosis": img_grade,
                })

        return pd.DataFrame(rows)

    @classmethod
    def generate_csv(
        cls,
        target_path: Path,
        num_patients: int = 50,
        random_seed: int = 42,
        min_images_per_patient: int = 1,
        max_images_per_patient: int = 4,
    ) -> Path:
        """Create and write synthetic patient metadata CSV to target_path."""
        df = cls.generate_dataframe(
            num_patients=num_patients,
            random_seed=random_seed,
            min_images_per_patient=min_images_per_patient,
            max_images_per_patient=max_images_per_patient,
        )
        target_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(target_path, index=False)
        return target_path


@pytest.fixture
def mock_patient_cohort() -> type[MockPatientCohort]:
    """Factory fixture for generating synthetic patient metadata cohorts."""
    return MockPatientCohort


# ==============================================================================
# Fixture 2: MockFundusFactory
# ==============================================================================

class MockFundusFactory:
    """Generates synthetic retinal fundus images and OOD artifacts in [0.0, 255.0]."""

    @staticmethod
    def create_fundus_array(
        shape: Tuple[int, int, int] = (224, 224, 3),
        grade: int = 0,
        random_seed: Optional[int] = None,
    ) -> np.ndarray:
        """Generate a realistic circular ocular fundus model in float32 [0.0, 255.0]."""
        rng = np.random.default_rng(random_seed)
        h, w, c = shape
        arr = np.zeros((h, w, c), dtype=np.float32)

        y, x = np.ogrid[:h, :w]
        center_y, center_x = h / 2.0, w / 2.0
        radius = min(h, w) * 0.45
        dist_from_center = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
        ocular_mask = dist_from_center <= radius

        # Reddish-orange fundus base
        arr[..., 0] = 180.0  # R
        arr[..., 1] = 60.0   # G
        arr[..., 2] = 30.0   # B

        # Radial falloff
        falloff = 1.0 - 0.4 * (dist_from_center / (radius + 1e-5))
        arr = arr * falloff[..., None]

        # Optic disc (yellowish-bright circle offset to one side)
        disc_x, disc_y = int(center_x - radius * 0.4), int(center_y)
        dist_disc = np.sqrt((x - disc_x) ** 2 + (y - disc_y) ** 2)
        disc_mask = dist_disc <= (radius * 0.15)
        arr[disc_mask, 0] = 235.0
        arr[disc_mask, 1] = 210.0
        arr[disc_mask, 2] = 140.0

        # Macula (dark oval near center)
        macula_x, macula_y = int(center_x + radius * 0.2), int(center_y)
        dist_macula = np.sqrt((x - macula_x) ** 2 + (y - macula_y) ** 2)
        macula_mask = dist_macula <= (radius * 0.12)
        arr[macula_mask, 0] = 110.0
        arr[macula_mask, 1] = 35.0
        arr[macula_mask, 2] = 20.0

        # Simulate micro-lesions for grades > 0
        if grade > 0:
            num_lesions = grade * 8
            for _ in range(num_lesions):
                lx = int(rng.uniform(center_x - radius * 0.7, center_x + radius * 0.7))
                ly = int(rng.uniform(center_y - radius * 0.7, center_y + radius * 0.7))
                if 0 <= lx < w and 0 <= ly < h and ocular_mask[ly, lx]:
                    # Microaneurysm/hemorrhage (deep red) or exudate (bright yellow)
                    if rng.random() > 0.4 and grade >= 2:
                        arr[max(0, ly - 2):ly + 3, max(0, lx - 2):lx + 3] = [240.0, 230.0, 100.0]
                    else:
                        arr[max(0, ly - 1):ly + 2, max(0, lx - 1):lx + 2] = [80.0, 10.0, 10.0]

        # Add subtle random retinal noise
        noise = rng.normal(0, 3.0, (h, w, c)).astype(np.float32)
        arr = arr + noise

        # Zero out outside ocular mask
        arr[~ocular_mask] = 0.0

        return np.clip(arr, 0.0, 255.0)

    @classmethod
    def create_fundus_image(
        cls,
        shape: Tuple[int, int, int] = (224, 224, 3),
        grade: int = 0,
        random_seed: Optional[int] = None,
    ) -> Image.Image:
        """Create a PIL Image of a synthetic fundus."""
        arr = cls.create_fundus_array(shape=shape, grade=grade, random_seed=random_seed)
        return Image.fromarray(arr.astype(np.uint8))

    @classmethod
    def save_fundus_file(
        cls,
        filepath: Path,
        shape: Tuple[int, int, int] = (224, 224, 3),
        grade: int = 0,
        image_format: str = "JPEG",
    ) -> Path:
        """Generate and save synthetic fundus image to disk."""
        img = cls.create_fundus_image(shape=shape, grade=grade)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        img.save(filepath, format=image_format)
        return filepath

    @staticmethod
    def create_ood_array(
        ood_type: str = "uniform_gray",
        shape: Tuple[int, int, int] = (224, 224, 3),
        random_seed: Optional[int] = None,
    ) -> np.ndarray:
        """Generate Out-of-Distribution (OOD) test arrays."""
        rng = np.random.default_rng(random_seed)
        h, w, c = shape

        if ood_type == "uniform_gray":
            return np.full((h, w, c), 128.0, dtype=np.float32)
        elif ood_type == "pure_black":
            return np.zeros((h, w, c), dtype=np.float32)
        elif ood_type == "pure_white":
            return np.full((h, w, c), 255.0, dtype=np.float32)
        elif ood_type == "noise":
            return rng.uniform(0.0, 255.0, (h, w, c)).astype(np.float32)
        elif ood_type == "checkerboard":
            arr = np.zeros((h, w, c), dtype=np.float32)
            block = max(1, h // 8)
            for i in range(h):
                for j in range(w):
                    if ((i // block) + (j // block)) % 2 == 0:
                        arr[i, j] = 255.0
            return arr
        else:
            return np.full((h, w, c), 128.0, dtype=np.float32)

    @classmethod
    def save_ood_file(
        cls,
        filepath: Path,
        ood_type: str = "uniform_gray",
        shape: Tuple[int, int, int] = (224, 224, 3),
        image_format: str = "JPEG",
    ) -> Path:
        """Generate and save OOD test image to disk."""
        arr = cls.create_ood_array(ood_type=ood_type, shape=shape)
        img = Image.fromarray(arr.astype(np.uint8))
        filepath.parent.mkdir(parents=True, exist_ok=True)
        img.save(filepath, format=image_format)
        return filepath


@pytest.fixture
def mock_fundus_factory() -> type[MockFundusFactory]:
    """Factory fixture for generating synthetic fundus and OOD image artifacts."""
    return MockFundusFactory


# ==============================================================================
# Fixture 3: MockStagingEnvironment
# ==============================================================================

class MockStagingEnvironment:
    """Manages ephemeral mock private staging configurations and SAN SSL certs."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.cert_dir = self.base_dir / "staging" / "nginx" / "certs"
        self.conf_dir = self.base_dir / "staging" / "nginx" / "conf.d"
        self.cert_path = self.cert_dir / "staging.crt"
        self.key_path = self.cert_dir / "staging.key"
        self.dockerfile_path = self.base_dir / "Dockerfile"
        self.compose_path = self.base_dir / "docker-compose.staging.yml"
        self.nginx_conf_path = self.conf_dir / "staging.conf"

    def setup(self) -> "MockStagingEnvironment":
        """Scaffold staging configuration files and generate local test SAN certs."""
        self.cert_dir.mkdir(parents=True, exist_ok=True)
        self.conf_dir.mkdir(parents=True, exist_ok=True)

        # 1. Generate local SAN SSL certificate via cryptography
        self._generate_test_certificates()

        # 2. Write compliant Dockerfile
        self.dockerfile_path.write_text(
            """FROM python:3.12-slim
WORKDIR /app
RUN useradd -m -u 1000 appuser
COPY . /app
RUN chown -R appuser:appuser /app
USER appuser
ENV PORT=5000
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:${PORT:-5000}/api/health || exit 1
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:create_app()"]
""",
            encoding="utf-8",
        )

        # 3. Write compliant docker-compose.staging.yml
        self.compose_path.write_text(
            """version: '3.8'
services:
  retina-api:
    build:
      context: .
      dockerfile: Dockerfile
    user: "1000:1000"
    networks:
      - staging-net
    environment:
      - PORT=5000
      - FLASK_ENV=staging
      - RETINA_MODEL_PATH=/app/retfound_model.keras
      - RETINA_TFLITE_PATH=/app/retfound_model.tflite
      - USE_TFLITE=true
      - SUPABASE_JWT_SECRET=test_secret
      - SCAN_HMAC_SECRET=test_hmac
    expose:
      - "5000"

  staging-proxy:
    image: nginx:alpine
    ports:
      - "8080:80"
      - "8443:443"
    volumes:
      - ./staging/nginx/conf.d:/etc/nginx/conf.d:ro
      - ./staging/nginx/certs:/etc/nginx/certs:ro
    networks:
      - staging-net
    depends_on:
      - retina-api

networks:
  staging-net:
    driver: bridge
""",
            encoding="utf-8",
        )

        # 4. Write compliant NGINX staging.conf
        self.nginx_conf_path.write_text(
            """server {
    listen 80;
    server_name localhost retina-staging.local;
    return 301 https://$host:8443$request_uri;
}

server {
    listen 443 ssl;
    server_name localhost retina-staging.local;

    ssl_certificate /etc/nginx/certs/staging.crt;
    ssl_certificate_key /etc/nginx/certs/staging.key;

    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;

    client_max_body_size 16M;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Content-Security-Policy "default-src 'self'" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://retina-api:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
""",
            encoding="utf-8",
        )
        return self

    def _generate_test_certificates(self) -> None:
        """Create valid SAN certificate using cryptography module."""
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "PK"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Retina Mock Staging"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        san = x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.DNSName("retina-staging.local"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ])

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
            .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365))
            .add_extension(san, critical=False)
            .sign(key, hashes.SHA256())
        )

        self.key_path.write_bytes(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        self.cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


@pytest.fixture
def mock_staging_env(tmp_path: Path) -> MockStagingEnvironment:
    """Fixture providing a self-contained mock staging deployment environment."""
    env = MockStagingEnvironment(tmp_path)
    return env.setup()


# ==============================================================================
# Fixture 4: MockModelCheckpoint
# ==============================================================================

@pytest.fixture
def mock_model_checkpoint(tmp_path: Path) -> Path:
    """Generate a lightweight Keras functional model checkpoint (<100KB)."""
    import tensorflow as tf
    from tensorflow.keras import layers, models

    # Build ultra-lightweight dummy model matching (224, 224, 3) -> (5, sigmoid)
    inputs = layers.Input(shape=(224, 224, 3), name="input_retina")
    x = layers.GlobalAveragePooling2D()(inputs)
    outputs = layers.Dense(5, activation="sigmoid", name="ordinal_output")(x)
    model = models.Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])

    checkpoint_path = tmp_path / "mock_dense121_ordinal.keras"
    model.save(checkpoint_path)
    return checkpoint_path


# ==============================================================================
# Fixture 5: MarkdownLinterFixture
# ==============================================================================

class MarkdownLinterFixture:
    """Parser checking zero placeholder tokens, structure, and bilingual content."""

    PLACEHOLDER_PATTERNS = [
        re.compile(r"\[TBD\]", re.IGNORECASE),
        re.compile(r"\[Insert[^\]]*\]", re.IGNORECASE),
        re.compile(r"\[Date\]", re.IGNORECASE),
        re.compile(r"\bTODO\b"),
        re.compile(r"\bFIXME\b"),
        re.compile(r"<<<"),
        re.compile(r">>>"),
        re.compile(r"\bXXX\b"),
    ]

    URDU_UNICODE_PATTERN = re.compile(r"[\u0600-\u06FF]")

    @classmethod
    def scan_file(cls, filepath: Path) -> Dict[str, Any]:
        """Scan a markdown document and return structural and lint statistics."""
        if not filepath.is_file():
            raise FileNotFoundError(f"Markdown file does not exist: {filepath}")

        content = filepath.read_text(encoding="utf-8")
        placeholders_found = []
        for pat in cls.PLACEHOLDER_PATTERNS:
            matches = pat.findall(content)
            if matches:
                placeholders_found.extend(matches)

        headings_h1 = len(re.findall(r"^#\s+.+", content, re.MULTILINE))
        headings_h2 = len(re.findall(r"^##\s+.+", content, re.MULTILINE))
        headings_h3 = len(re.findall(r"^###\s+.+", content, re.MULTILINE))
        has_urdu = bool(cls.URDU_UNICODE_PATTERN.search(content))
        has_english = bool(re.search(r"[a-zA-Z]{4,}", content))

        return {
            "path": str(filepath),
            "size_bytes": len(content.encode("utf-8")),
            "line_count": len(content.splitlines()),
            "placeholder_count": len(placeholders_found),
            "placeholders": placeholders_found,
            "headings_h1": headings_h1,
            "headings_h2": headings_h2,
            "headings_h3": headings_h3,
            "has_urdu": has_urdu,
            "has_english": has_english,
            "is_bilingual": has_urdu and has_english,
        }

    @classmethod
    def assert_zero_placeholders(cls, filepath: Path) -> None:
        """Assert that the specified file contains zero placeholder tokens."""
        result = cls.scan_file(filepath)
        assert result["placeholder_count"] == 0, (
            f"Found {result['placeholder_count']} placeholder tokens in {filepath}: "
            f"{result['placeholders'][:10]}"
        )


@pytest.fixture
def markdown_linter() -> type[MarkdownLinterFixture]:
    """Fixture providing Markdown placeholder scanning and lint verification."""
    return MarkdownLinterFixture
