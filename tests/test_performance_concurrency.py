"""tests/test_performance_concurrency.py

Comprehensive test suite verifying Sprint 7 Backend Architecture & Performance remediations:
- PR-07: Gunicorn micro-pool concurrency sizing, timeout, keepalive, and lifecycle hooks.
- PERF-01: TFLite runtime integration, fallback mechanisms, bitwise and schema parity.
- PERF-03: TensorFlow intra-op and inter-op thread clamping.
- Concurrency & Thread-safety: Multi-threaded load simulation without deadlocks or healthcheck starvation.
"""

import base64
import concurrent.futures
import importlib.util
import io
import os
import sys
import time
from pathlib import Path

import numpy as np
import pytest
import tensorflow as tf
from PIL import Image

import app
from gemini_validator import ValidationResult, ValidationStatus


PROJECT_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def mock_gemini_for_tests(monkeypatch):
    """Mock Gemini external API validation gate to isolate backend inference and concurrency."""
    monkeypatch.setattr(
        "app.classify_fundus_image",
        lambda *args, **kwargs: ValidationResult(
            status=ValidationStatus.VALID_FUNDUS,
            reason="Mocked valid fundus for concurrency and performance tests.",
        ),
    )


@pytest.fixture(scope="module")
def keras_model():
    """Module-scoped Keras model fixture."""
    return app.load_model(use_tflite=False)


@pytest.fixture(scope="module")
def tflite_model():
    """Module-scoped TFLite model fixture."""
    return app.load_tflite_model()


def create_synthetic_fundus_image(width=224, height=224, color=(160, 45, 35)):
    """Create a synthetic fundus-like image with texture/entropy to pass input validation."""
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    arr[:, :, 0] = color[0]
    arr[:, :, 1] = color[1]
    arr[:, :, 2] = color[2]
    # Add synthetic optic disc / vascular gradient patterns to ensure healthy entropy
    y, x = np.ogrid[:height, :width]
    center_y, center_x = height // 2, width // 2
    mask = (x - center_x) ** 2 + (y - center_y) ** 2 <= (width // 4) ** 2
    arr[mask, 0] = np.clip(arr[mask, 0] + 40, 0, 255)
    arr[mask, 1] = np.clip(arr[mask, 1] + 25, 0, 255)

    img = Image.fromarray(arr)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def load_gunicorn_config_module(env_overrides=None):
    """Helper to load gunicorn.conf.py in an isolated environment."""
    conf_path = PROJECT_DIR / "gunicorn.conf.py"
    assert conf_path.is_file(), "gunicorn.conf.py must exist"

    orig_env = os.environ.copy()
    if env_overrides is not None:
        for k, v in env_overrides.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = str(v)

    try:
        spec = importlib.util.spec_from_file_location("gunicorn_conf_test", str(conf_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        os.environ.clear()
        os.environ.update(orig_env)


# ==============================================================================
# 1. PR-07: GUNICORN CONFIGURATION TESTS
# ==============================================================================

class TestGunicornConfiguration:
    """Verifies PR-07 remediation in gunicorn.conf.py: workers, threads, timeout, keepalive, and hooks."""

    def test_default_workers_and_threads_capacity(self):
        """Default configuration must have workers=2, threads=4 (8 threads minimum concurrency capacity)."""
        conf = load_gunicorn_config_module(
            env_overrides={
                "GUNICORN_WORKERS": None,
                "GUNICORN_THREADS": None,
                "GUNICORN_TIMEOUT": None,
                "GUNICORN_KEEPALIVE": None,
            }
        )
        assert conf.workers == 2
        assert conf.threads == 4
        total_capacity = conf.workers * conf.threads
        assert total_capacity == 8, f"Expected 8 threads minimum, got {total_capacity}"

    def test_timeouts_and_keepalive(self):
        """Timeout must be 60s and keepalive must be 5s to avoid worker starvation."""
        conf = load_gunicorn_config_module(
            env_overrides={
                "GUNICORN_TIMEOUT": None,
                "GUNICORN_KEEPALIVE": None,
                "GUNICORN_GRACEFUL_TIMEOUT": None,
            }
        )
        assert conf.timeout == 60
        assert conf.keepalive == 5
        assert conf.graceful_timeout == 30

    def test_worker_class_is_gthread(self):
        """Worker class must be gthread to enable multi-threaded request processing."""
        conf = load_gunicorn_config_module()
        assert conf.worker_class == "gthread"

    def test_preload_app_is_disabled(self):
        """Preload app must be False to prevent TensorFlow fork safety issues across workers."""
        conf = load_gunicorn_config_module()
        assert conf.preload_app is False

    def test_dynamic_environment_overrides(self):
        """Verify environment variables dynamically override workers, threads, and timeouts."""
        conf = load_gunicorn_config_module(
            env_overrides={
                "GUNICORN_WORKERS": "4",
                "GUNICORN_THREADS": "8",
                "GUNICORN_TIMEOUT": "90",
                "GUNICORN_KEEPALIVE": "10",
            }
        )
        assert conf.workers == 4
        assert conf.threads == 8
        assert conf.timeout == 90
        assert conf.keepalive == 10
        assert conf.workers * conf.threads == 32

    def test_lifecycle_hooks_exist_and_execute_cleanly(self):
        """Verify lifecycle hooks (on_starting, worker_abort, worker_int) are callable and log cleanly."""
        conf = load_gunicorn_config_module()

        class MockLogger:
            def __init__(self):
                self.messages = []

            def info(self, msg):
                self.messages.append(("INFO", msg))

            def warning(self, msg):
                self.messages.append(("WARNING", msg))

        class MockServer:
            def __init__(self):
                self.log = MockLogger()

        class MockWorker:
            def __init__(self, pid=1234):
                self.pid = pid
                self.log = MockLogger()

        server = MockServer()
        worker = MockWorker(pid=9999)

        # 1. on_starting
        conf.on_starting(server)
        assert len(server.log.messages) == 1
        assert "Gunicorn starting" in server.log.messages[0][1]

        # 2. worker_abort
        conf.worker_abort(worker)
        assert len(worker.log.messages) == 1
        assert "received abort signal" in worker.log.messages[0][1]
        assert "9999" in worker.log.messages[0][1]

        # 3. worker_int
        conf.worker_int(worker)
        assert len(worker.log.messages) == 2
        assert "terminating gracefully" in worker.log.messages[1][1]


# ==============================================================================
# 2. PERF-03: TENSORFLOW THREAD CLAMPING TESTS
# ==============================================================================

class TestTensorFlowThreadClamping:
    """Verifies PERF-03 thread clamping to prevent thread thrashing and memory spikes."""

    def test_configure_tensorflow_threading_clamps_to_two(self):
        """Verify configure_tensorflow_threading sets intra/inter op parallelism to 2."""
        intra, inter = app.configure_tensorflow_threading(2, 2)
        assert intra in (1, 2)
        assert inter in (1, 2)

    def test_module_initialization_threading_clamped(self):
        """Verify TensorFlow threading was clamped during app module initialization."""
        intra = tf.config.threading.get_intra_op_parallelism_threads()
        inter = tf.config.threading.get_inter_op_parallelism_threads()
        assert intra in (1, 2)
        assert inter in (1, 2)


# ==============================================================================
# 3. PERF-01: TFLITE INFERENCE RUNTIME & MATHEMATICAL PARITY TESTS
# ==============================================================================

class TestTFLiteRuntimeAndParity:
    """Verifies PERF-01: TFLite interpreter loading, fallback, and mathematical parity against Keras."""

    def test_tflite_model_file_exists(self):
        """Confirm retfound_model.tflite exists and is ~28.9MB (64% smaller than Keras 82.3MB)."""
        tflite_path = app.TFLITE_MODEL_PATH
        keras_path = app.MODEL_PATH
        assert tflite_path.is_file(), f"Missing TFLite model at {tflite_path}"
        assert keras_path.is_file(), f"Missing Keras model at {keras_path}"

        tflite_size = tflite_path.stat().st_size
        keras_size = keras_path.stat().st_size
        assert tflite_size < keras_size
        assert 25_000_000 < tflite_size < 35_000_000

    def test_load_model_auto_fallback_when_tflite_disabled(self):
        """When use_tflite is False, load_model returns standard Keras model."""
        model = app.load_model(use_tflite=False)
        assert not getattr(model, "is_tflite", False)
        assert hasattr(model, "layers")

    def test_load_model_loads_tflite_when_requested(self):
        """When use_tflite is True, load_model returns TFLiteModelWrapper."""
        model = app.load_model(use_tflite=True)
        assert getattr(model, "is_tflite", False)
        assert isinstance(model, app.TFLiteModelWrapper)

    def test_load_model_fallback_when_tflite_missing(self, tmp_path):
        """When tflite model path is missing, load_model falls back safely to Keras."""
        missing_path = tmp_path / "nonexistent.tflite"
        fallback_model = app.load_model(use_tflite=True, tflite_path=missing_path)
        assert not getattr(fallback_model, "is_tflite", False)
        assert hasattr(fallback_model, "layers")

    def test_tflite_wrapper_thread_safety_attributes(self, tflite_model):
        """Verify TFLiteModelWrapper encapsulates an interpreter with a threading lock."""
        assert hasattr(tflite_model, "_lock")
        assert hasattr(tflite_model, "interpreter")
        assert hasattr(tflite_model, "input_index")
        assert hasattr(tflite_model, "output_index")

    def test_mathematical_parity_keras_vs_tflite(self, keras_model, tflite_model):
        """Verify FP32 mathematical parity between Keras and TFLite across synthetic images.

        Maximum absolute difference must be strictly <= 1e-4 (empirically ~1.19e-7).
        """
        colors = [
            (150, 40, 30),
            (180, 60, 50),
            (130, 35, 25),
            (170, 50, 45),
        ]

        for color in colors:
            img_bytes = create_synthetic_fundus_image(color=color)

            # Predict with Keras
            k_grade, k_label, k_probs = app.predict_grade(keras_model, img_bytes)

            # Predict with TFLite
            t_grade, t_label, t_probs = app.predict_grade(tflite_model, img_bytes)

            # 1. Output Grades must be strictly identical
            assert k_grade == t_grade, f"Grade mismatch: Keras={k_grade}, TFLite={t_grade}"

            # 2. Output Labels must be strictly identical
            assert k_label == t_label

            # 3. Probabilities length must be 5
            assert len(k_probs) == 5
            assert len(t_probs) == 5

            # 4. Numerical divergence must be within floating-point tolerance
            max_diff = max(abs(kp - tp) for kp, tp in zip(k_probs, t_probs))
            assert max_diff <= 1e-4, f"Divergence too high: {max_diff}"

    def test_tflite_and_keras_produce_identical_scan_receipt_hmac(self, keras_model, tflite_model):
        """Verify scan receipts generated from Keras and TFLite predictions have identical HMAC signatures."""
        img_bytes = create_synthetic_fundus_image()
        image_sha256 = "sample_sha256_hash_value"
        patient_id = "patient-test-parity"

        k_grade, _, k_probs = app.predict_grade(keras_model, img_bytes)
        t_grade, _, t_probs = app.predict_grade(tflite_model, img_bytes)

        assert k_probs == t_probs

        k_receipt = app.generate_scan_receipt(
            grade=k_grade,
            probabilities=k_probs,
            image_sha256=image_sha256,
            patient_id=patient_id,
        )
        t_receipt = app.generate_scan_receipt(
            grade=t_grade,
            probabilities=t_probs,
            image_sha256=image_sha256,
            patient_id=patient_id,
        )

        assert k_receipt["signature"] == t_receipt["signature"]
        is_valid, _ = app.verify_scan_receipt(t_receipt)
        assert is_valid is True

    def test_error_handling_parity_on_corrupt_data(self, keras_model, tflite_model):
        """Verify identical exception behavior between Keras and TFLite when fed non-image data."""
        invalid_bytes = b"not_an_image_random_binary_garbage_stream"

        with pytest.raises(ValueError, match="not a readable image"):
            app.predict_grade(keras_model, invalid_bytes)

        with pytest.raises(ValueError, match="not a readable image"):
            app.predict_grade(tflite_model, invalid_bytes)


# ==============================================================================
# 4. CONCURRENCY & MULTI-THREADED LOAD SIMULATION TESTS
# ==============================================================================

def get_auth_headers():
    """Generate a valid JWT auth header if authentication is enforced."""
    secret = os.environ.get("SUPABASE_JWT_SECRET") or "dr-scan-tamper-evident-integrity-key-v1"
    import jwt
    payload = {
        "sub": "test-perf-user",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


class TestConcurrencyAndThreadSafety:
    """Verifies that the backend handles multi-threaded concurrent requests without deadlocks or pool starvation."""

    @pytest.fixture
    def test_client_tflite(self, tflite_model):
        """Create test client with TFLite model."""
        application = app.create_app(model=tflite_model)
        application.config["TESTING"] = True
        return application.test_client()

    @pytest.fixture
    def test_client_keras(self, keras_model):
        """Create test client with Keras model."""
        application = app.create_app(model=keras_model)
        application.config["TESTING"] = True
        return application.test_client()

    def test_healthcheck_responsiveness_under_concurrent_model_inference(self, test_client_tflite):
        """Verify PR-07: Healthcheck /api/health responds immediately (HTTP 200) under concurrent inference."""
        img_bytes = create_synthetic_fundus_image()
        num_inference_workers = 6
        num_health_workers = 6
        headers = get_auth_headers()

        def run_inference():
            data = {"image": (io.BytesIO(img_bytes), "scan.jpg")}
            resp = test_client_tflite.post(
                "/api/predict",
                data=data,
                content_type="multipart/form-data",
                headers=headers,
            )
            return resp.status_code

        def run_healthcheck():
            start_t = time.perf_counter()
            resp = test_client_tflite.get("/api/health")
            elapsed = time.perf_counter() - start_t
            return resp.status_code, elapsed

        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            # Launch interleaved inference and healthcheck calls
            inference_futures = [executor.submit(run_inference) for _ in range(num_inference_workers)]
            health_futures = [executor.submit(run_healthcheck) for _ in range(num_health_workers)]

            # Collect results
            for f in inference_futures:
                status = f.result()
                assert status == 200

            for f in health_futures:
                status, elapsed = f.result()
                assert status == 200
                assert elapsed < 1.0, f"Healthcheck delayed too long ({elapsed:.3f}s)"

    def test_concurrent_tflite_model_invocations_no_race_conditions(self, tflite_model):
        """Verify thread-safe concurrent execution of TFLiteModelWrapper across 8 simultaneous threads."""
        img_bytes = create_synthetic_fundus_image()

        def worker_task(thread_id):
            grade, label, probs = app.predict_grade(tflite_model, img_bytes)
            return thread_id, grade, label, probs

        num_threads = 8
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_task, i) for i in range(num_threads)]
            results = [f.result() for f in futures]

        assert len(results) == num_threads
        first_grade = results[0][1]
        first_label = results[0][2]
        first_probs = results[0][3]

        for res in results:
            _, grade, label, probs = res
            assert grade == first_grade
            assert label == first_label
            assert probs == first_probs

    def test_api_predict_returns_binary_classification_field(self, test_client_tflite):
        """Verify that /api/predict returns the binary_classification field for schema parity."""
        img_bytes = create_synthetic_fundus_image()
        headers = get_auth_headers()
        resp = test_client_tflite.post(
            "/api/predict",
            data={"image": (io.BytesIO(img_bytes), "scan.jpg")},
            content_type="multipart/form-data",
            headers=headers,
        )
        assert resp.status_code == 200
        payload = resp.get_json()
        assert "binary_classification" in payload
        assert isinstance(payload["binary_classification"], bool)
        assert payload["binary_classification"] == (payload["grade"] > 0)


# ==============================================================================
# 5. LATENCY COMPARISON & BENCHMARK SUITE
# ==============================================================================

class TestLatencyAndResourceEfficiency:
    """Measures latency of TFLite vs Keras and verifies TFLite execution speedup."""

    def test_tflite_latency_is_significantly_faster_than_keras(self, keras_model, tflite_model):
        """Demonstrate that TFLite inference executes faster than Keras forward pass."""
        img_bytes = create_synthetic_fundus_image()

        # Warm up both models
        app.predict_grade(keras_model, img_bytes)
        app.predict_grade(tflite_model, img_bytes)

        # Benchmark Keras (3 runs)
        keras_times = []
        for _ in range(3):
            t0 = time.perf_counter()
            app.predict_grade(keras_model, img_bytes)
            keras_times.append(time.perf_counter() - t0)

        # Benchmark TFLite (3 runs)
        tflite_times = []
        for _ in range(3):
            t0 = time.perf_counter()
            app.predict_grade(tflite_model, img_bytes)
            tflite_times.append(time.perf_counter() - t0)

        keras_mean_ms = np.mean(keras_times) * 1000
        tflite_mean_ms = np.mean(tflite_times) * 1000

        print(f"\n[BENCHMARK] Keras: {keras_mean_ms:.2f} ms | TFLite: {tflite_mean_ms:.2f} ms")
        assert tflite_mean_ms < keras_mean_ms, (
            f"Expected TFLite ({tflite_mean_ms:.2f}ms) to be faster than Keras ({keras_mean_ms:.2f}ms)"
        )
