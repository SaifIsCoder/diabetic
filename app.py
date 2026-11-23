import base64
import hashlib
import hmac
import io
import os
import threading
import time
from pathlib import Path

import jwt
import numpy as np
import tensorflow as tf
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from PIL import Image, UnidentifiedImageError


def configure_tensorflow_threading(intra_threads: int = 2, inter_threads: int = 2) -> tuple[int, int]:
    """Configure TensorFlow CPU thread pools to prevent thread contention and memory spikes (PERF-03)."""
    try:
        tf.config.threading.set_intra_op_parallelism_threads(intra_threads)
        tf.config.threading.set_inter_op_parallelism_threads(inter_threads)
    except RuntimeError:
        # Ops already initialized in running environment
        pass
    try:
        return (
            tf.config.threading.get_intra_op_parallelism_threads(),
            tf.config.threading.get_inter_op_parallelism_threads(),
        )
    except Exception:
        return (intra_threads, inter_threads)


# Clamp TensorFlow threading immediately upon module initialization (PERF-03)
configure_tensorflow_threading(2, 2)

from gemini_validator import (
    classify_fundus_image,
    validate_image_bytes,
    FundusValidationError,
    InvalidImageError,
    NonFundusImageError,
    UncertainFundusImageError,
    GeminiConfigurationError,
    GeminiRateLimitError,
    GeminiTimeoutError,
    GeminiUnavailableError,
    ValidationStatus,
    is_validation_enabled,
    get_gemini_api_key,
)


PROJECT_DIR = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_DIR / ".env")
except ImportError:
    env_file = PROJECT_DIR / ".env"
    if env_file.is_file():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v

MODEL_PATH = Path(
    os.environ.get("RETINA_MODEL_PATH", PROJECT_DIR / "retfound_model.keras")
)
TFLITE_MODEL_PATH = Path(
    os.environ.get("RETINA_TFLITE_PATH", PROJECT_DIR / "retfound_model.tflite")
)
IMAGE_SIZE = (224, 224)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MODEL_VERSION = "densenet121_ordinal_v1"

GRADE_LABELS = {
    0: "No diabetic retinopathy",
    1: "Mild non-proliferative diabetic retinopathy",
    2: "Moderate non-proliferative diabetic retinopathy",
    3: "Severe non-proliferative diabetic retinopathy",
    4: "Proliferative diabetic retinopathy",
}

PAGE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Diabetic Retinopathy Diagnostic Portal</title>
    <style>
      :root {
        --primary: #007A87;
        --navy: #0F1E36;
        --accent: #00B4D8;
        --bg: #F4F8FA;
        --surface: #FFFFFF;
        --text: #0B1A2C;
        --muted: #5A6E85;
      }
      body { font: 16px system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text);
             margin: 0; padding: 2.5rem 1rem; }
      main { max-width: 680px; margin: auto; padding: 2.5rem; background: var(--surface);
             border-radius: 16px; box-shadow: 0 10px 30px rgba(15, 30, 54, 0.08); border: 1px solid #E2E8F0; }
      .header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem; }
      .badge { background: #E0F2FE; color: var(--primary); padding: 0.25rem 0.6rem; border-radius: 9999px;
               font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }
      h1 { margin: 0; font-size: 1.6rem; color: var(--navy); }
      p { line-height: 1.6; color: var(--muted); }
      input, button { font: inherit; }
      .upload-box { border: 2px dashed #CBD5E1; padding: 2rem; border-radius: 12px; text-align: center;
                    margin: 1.5rem 0; cursor: pointer; transition: border-color 0.2s; }
      .upload-box:hover { border-color: var(--primary); }
      input[type="file"] { display: block; margin: 1rem auto 0; }
      button { border: 0; border-radius: 10px; padding: .85rem 1.5rem; width: 100%;
               background: var(--primary); color: white; cursor: pointer; font-weight: 600;
               font-size: 1rem; transition: background 0.2s; }
      button:hover { background: #006670; }
      button:disabled { opacity: .65; cursor: wait; }
      .result, .error, .notice { margin-top: 1.5rem; padding: 1.25rem; border-radius: 12px; }
      .result { background: #F0FDF4; border: 1px solid #BBF7D0; }
      .error { background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }
      .notice { background: #FFFBEB; font-size: .88rem; color: #92400E; border: 1px solid #FDE68A; }
      .grade { font-size: 1.25rem; font-weight: 700; color: #166534; }
      .api-link { margin-top: 1.5rem; text-align: center; font-size: 0.85rem; color: var(--muted); }
      .api-link a { color: var(--primary); font-weight: 600; text-decoration: none; }
    </style>
  </head>
  <body>
    <main>
      <div class="header">
        <span class="badge">Clinical AI Screening</span>
      </div>
      <h1>Diabetic Retinopathy Grading</h1>
      <p>Upload a retinal fundus photograph to receive an AI-assisted severity grading (Grades 0 to 4).</p>
      <form action="/predict" method="post" enctype="multipart/form-data"
            onsubmit="this.querySelector('button').disabled = true;
                      this.querySelector('button').textContent = 'Analyzing Retinal Image…';">
        <div class="upload-box">
          <label for="image">Select Retinal Fundus Photograph (JPEG or PNG)</label>
          <input id="image" name="image" type="file" accept="image/*" required>
        </div>
        <button type="submit">Run Diagnostic Inference</button>
      </form>
      {% if result %}
      <section class="result" aria-live="polite">
        <div class="grade">Grade {{ result.grade }}: {{ result.label }}</div>
      </section>
      {% endif %}
      {% if error %}
      <section class="error" role="alert">{{ error }}</section>
      {% endif %}
      <section class="notice">
        <strong>Clinical Screening Notice:</strong> Research prototype only. This prediction is an automated screening aid and not a medical diagnosis or substitute for an examination by a qualified ophthalmologist.
      </section>
      <div class="api-link">
        API ready: <code>POST /api/predict</code> &nbsp;|&nbsp; <code>GET /api/health</code>
      </div>
    </main>
  </body>
</html>
"""


def is_tflite_enabled() -> bool:
    """Check whether TFLite runtime is requested via environment variable."""
    return os.environ.get("USE_TFLITE", "false").lower() in ("true", "1", "yes")


class TFLiteModelWrapper:
    """Thread-safe wrapper around tf.lite.Interpreter providing a callable interface

    matching Keras model calling conventions: model(batch, training=False).
    Guarantees thread-safe inference under concurrent WSGI worker threads (PERF-01, PR-07).
    """

    def __init__(self, model_path: Path | str, num_threads: int = 2):
        self.model_path = Path(model_path)
        self.num_threads = num_threads
        self._lock = threading.Lock()
        self.interpreter = tf.lite.Interpreter(
            model_path=str(self.model_path),
            num_threads=self.num_threads,
        )
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.input_index = self.input_details[0]["index"]
        self.output_index = self.output_details[0]["index"]
        self.is_tflite = True

    def __call__(self, batch, training: bool = False):
        batch_np = np.asarray(batch, dtype=np.float32)
        with self._lock:
            self.interpreter.set_tensor(self.input_index, batch_np)
            self.interpreter.invoke()
            output = self.interpreter.get_tensor(self.output_index)
        return output.copy()


def load_tflite_model(
    model_path: Path = TFLITE_MODEL_PATH, num_threads: int = 2
) -> TFLiteModelWrapper:
    """Load TFLite interpreter wrapped for thread-safe inference."""
    if not Path(model_path).is_file():
        raise FileNotFoundError(f"TFLite model file not found: {model_path}")
    return TFLiteModelWrapper(model_path, num_threads=num_threads)


def load_model(
    model_path: Path = MODEL_PATH,
    use_tflite: bool | None = None,
    tflite_path: Path = TFLITE_MODEL_PATH,
):
    """Load inference model: either TFLite interpreter or Keras model.

    If use_tflite is True (or USE_TFLITE env var is enabled) and tflite model exists,
    loads TFLite with thread-safe wrapper.
    If TFLite model is missing or fails to load, falls back safely to Keras model.
    """
    enable_tflite = is_tflite_enabled() if use_tflite is None else use_tflite

    # If an explicit .tflite model path is provided directly
    if str(model_path).endswith(".tflite"):
        return load_tflite_model(Path(model_path))

    if enable_tflite:
        target_tflite = Path(tflite_path)
        if target_tflite.is_file():
            try:
                return load_tflite_model(target_tflite)
            except Exception:
                # Auto-fallback to Keras if TFLite initialization fails
                pass
        # Auto-fallback to Keras if TFLite file does not exist

    if not Path(model_path).is_file():
        raise FileNotFoundError(
            f"Model file not found: {model_path}. "
            "Set RETINA_MODEL_PATH to the trained .keras model."
        )
    return tf.keras.models.load_model(model_path, compile=False)


def predict_grade(model, image_bytes):
    """Predict diabetic retinopathy severity grade (0-4) using DenseNet-121 ordinal classifier.

    PREPROCESSING CONTRACT (ML-03):
    Training in 85.ipynb fed raw [0.0, 255.0] pixel floats into DenseNet121.
    Standard ImageNet preprocess_input (e.g. [-1, 1] scaling or z-score normalization)
    was NOT applied during training and MUST NOT be applied at inference time on current
    checkpoint weights (retfound_model.keras).
    Input images are converted to standard RGB, resized to (224, 224) via Lanczos resampling,
    and cast to float32 retaining the raw [0.0, 255.0] dynamic range.
    """
    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            image = source.convert("RGB").resize(
                IMAGE_SIZE,
                resample=Image.Resampling.LANCZOS,
            )
            batch = np.asarray(image, dtype=np.float32)[np.newaxis, ...]
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("The uploaded file is not a readable image.") from exc

    raw_preds = np.asarray(model(batch, training=False))
    if raw_preds.shape != (1, len(GRADE_LABELS)):
        raise RuntimeError(
            "The loaded model returned an unexpected output shape: "
            f"{raw_preds.shape}"
        )

    probabilities = [round(float(p), 4) for p in raw_preds[0]]
    grade = max(0, int(np.count_nonzero(raw_preds[0] >= 0.5) - 1))
    if grade not in GRADE_LABELS:
        raise RuntimeError(f"The model returned an invalid grade: {grade}")
    return grade, GRADE_LABELS[grade], probabilities


DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:8081",
    "http://localhost:19006",
    "http://localhost:3000",
    "http://localhost:5000",
    "http://127.0.0.1:8081",
    "http://127.0.0.1:19006",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5000",
]

RATE_LIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
RATE_LIMIT_HEALTH = os.environ.get("RATE_LIMIT_HEALTH", "60 per minute")
RATE_LIMIT_PREDICT = os.environ.get("RATE_LIMIT_PREDICT", "10 per minute")
RATE_LIMIT_VERIFY = os.environ.get("RATE_LIMIT_VERIFY", "30 per minute")


def get_predict_rate_limit() -> str:
    from flask import current_app
    if current_app and current_app.testing and not os.environ.get("ENFORCE_PREDICT_RATE_LIMIT"):
        return os.environ.get("RATE_LIMIT_PREDICT_TEST", "1000 per minute")
    return os.environ.get("RATE_LIMIT_PREDICT", "10 per minute")


def get_health_rate_limit() -> str:
    from flask import current_app
    if current_app and current_app.testing and not os.environ.get("ENFORCE_HEALTH_RATE_LIMIT"):
        return os.environ.get("RATE_LIMIT_HEALTH_TEST", "1000 per minute")
    return os.environ.get("RATE_LIMIT_HEALTH", "60 per minute")


def get_allowed_origins() -> list[str]:
    env_origins = os.environ.get("ALLOWED_ORIGINS")
    if env_origins:
        parsed = [o.strip() for o in env_origins.split(",") if o.strip()]
        if parsed:
            return parsed
    return list(DEFAULT_ALLOWED_ORIGINS)


def is_production() -> bool:
    env = (
        os.environ.get("FLASK_ENV")
        or os.environ.get("ENV")
        or os.environ.get("APP_ENV")
        or "development"
    ).lower()
    return env in ("production", "prod")


def is_auth_enforced() -> bool:
    return (
        is_production()
        or bool(os.environ.get("SUPABASE_JWT_SECRET"))
        or os.environ.get("REQUIRE_AUTH", "").lower() in ("true", "1", "yes")
    )


def get_scan_hmac_secret() -> bytes:
    key = (
        os.environ.get("SCAN_HMAC_SECRET")
        or os.environ.get("SUPABASE_JWT_SECRET")
        or "dr-scan-tamper-evident-integrity-key-v1"
    )
    return key.encode("utf-8")


def generate_scan_receipt(
    grade: int,
    probabilities: list,
    image_sha256: str,
    patient_id: str | None = None,
    model_version: str = MODEL_VERSION,
) -> dict:
    timestamp = int(time.time())
    probs_str = ",".join(f"{p:.4f}" for p in probabilities)
    patient_str = str(patient_id) if patient_id else "anonymous"
    message = f"{image_sha256}:{grade}:{probs_str}:{model_version}:{patient_str}:{timestamp}"
    signature = hmac.new(
        get_scan_hmac_secret(),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "image_sha256": image_sha256,
        "grade": grade,
        "probabilities": probabilities,
        "model_version": model_version,
        "patient_id": patient_str,
        "timestamp": timestamp,
        "signature": signature,
    }


def verify_scan_receipt(
    receipt: dict,
    max_age_seconds: int = 86400,
) -> tuple[bool, str]:
    required_fields = ["image_sha256", "grade", "model_version", "timestamp", "signature"]
    for field in required_fields:
        if field not in receipt:
            return False, f"Missing required receipt field: {field}"

    try:
        timestamp = int(receipt["timestamp"])
    except (ValueError, TypeError):
        return False, "Invalid timestamp in receipt"

    now = int(time.time())
    if now - timestamp > max_age_seconds:
        return False, "Receipt has expired"
    if timestamp > now + 300:
        return False, "Receipt timestamp is in the future"

    grade = receipt["grade"]
    model_version = receipt.get("model_version", MODEL_VERSION)
    patient_str = receipt.get("patient_id", "anonymous")
    image_sha256 = receipt["image_sha256"]
    signature = receipt["signature"]

    probabilities = receipt.get("probabilities", [])
    probs_str = ",".join(f"{p:.4f}" for p in probabilities) if probabilities else ""

    message = f"{image_sha256}:{grade}:{probs_str}:{model_version}:{patient_str}:{timestamp}"
    expected_sig = hmac.new(
        get_scan_hmac_secret(),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if hmac.compare_digest(expected_sig, signature):
        return True, "Scan receipt verified successfully"

    # Also check alternate signature without probabilities
    message_alt = f"{image_sha256}:{grade}::{model_version}:{patient_str}:{timestamp}"
    expected_alt = hmac.new(
        get_scan_hmac_secret(),
        message_alt.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if hmac.compare_digest(expected_alt, signature):
        return True, "Scan receipt verified successfully"

    return False, "Invalid cryptographic signature: scan receipt has been tampered with"


def get_rate_limit_key() -> str:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        parts = auth_header.split(" ", 1)
        if len(parts) > 1 and parts[1].strip():
            token = parts[1].strip()
            try:
                unverified = jwt.decode(token, options={"verify_signature": False})
                if "sub" in unverified and unverified["sub"]:
                    return f"user:{unverified['sub']}"
            except Exception:
                pass

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
        if client_ip:
            return f"ip:{client_ip}"

    client_ip = request.headers.get("X-Client-IP") or request.headers.get("X-Real-IP")
    if client_ip:
        return f"ip:{client_ip.strip()}"

    return f"ip:{get_remote_address()}"


limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[],
    storage_uri=RATE_LIMIT_STORAGE_URI,
)


def verify_auth_token():
    """Verify Supabase JWT authentication token.

    SEC-02 Remediation: Enforces fail-closed token verification.
    In production mode or when auth is configured/required, requests without
    a valid Bearer JWT are strictly rejected.
    Never falls back to unauthenticated bypass if secret is missing in prod mode.
    """
    secret = os.environ.get("SUPABASE_JWT_SECRET")
    auth_enforced = is_auth_enforced()

    if not auth_enforced:
        # Development/testing bypass only when auth is not configured and not in production
        return True, None

    if not secret:
        # SEC-02 Fail-closed: In production or when auth is enforced, missing secret must reject
        return False, "Authentication configuration error: SUPABASE_JWT_SECRET is required"

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return False, "Missing or invalid Authorization header"

    parts = auth_header.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        return False, "Missing or invalid Authorization header"

    token = parts[1].strip()
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return True, payload
    except jwt.ExpiredSignatureError:
        return False, "Token has expired"
    except jwt.InvalidAudienceError:
        return False, "Invalid token audience"
    except jwt.PyJWTError as exc:
        return False, f"Invalid token: {exc}"


def create_app(model=None):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
    app.config.setdefault(
        "RATELIMIT_ENABLED",
        os.environ.get("RATELIMIT_ENABLED", "true").lower() in ("true", "1", "yes"),
    )

    # Initialize rate limiter with application
    limiter.init_app(app)

    # SEC-03: Enable CORS with strict whitelist of allowed origins (no wildcard reflection with credentials)
    allowed_origins = get_allowed_origins()
    CORS(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        methods=["GET", "POST", "OPTIONS"],
    )

    loaded_model = model if model is not None else load_model()

    # Browser Web UI
    @app.get("/")
    def index():
        return render_template_string(PAGE)

    @app.post("/predict")
    @limiter.limit(get_predict_rate_limit)
    def predict_html():
        uploaded = request.files.get("image")
        if uploaded is None or not uploaded.filename:
            return render_template_string(
                PAGE, error="Choose an image file before submitting."
            ), 400

        raw_bytes = uploaded.read(MAX_UPLOAD_BYTES + 1)
        if len(raw_bytes) > MAX_UPLOAD_BYTES:
            return render_template_string(
                PAGE, error="The image is too large. Maximum upload size is 10 MB."
            ), 413

        try:
            sanitized_bytes, mime_type = validate_image_bytes(raw_bytes)
        except InvalidImageError as exc:
            return render_template_string(PAGE, error=str(exc)), 400

        try:
            val_result = classify_fundus_image(sanitized_bytes, mime_type=mime_type)
        except GeminiConfigurationError:
            return render_template_string(
                PAGE, error="Image validation configuration error on server."
            ), 500
        except GeminiRateLimitError:
            return render_template_string(
                PAGE, error="Validation rate limit exceeded. Please try again shortly."
            ), 429
        except GeminiTimeoutError:
            return render_template_string(
                PAGE, error="Validation request timed out. Please try again."
            ), 504
        except GeminiUnavailableError:
            return render_template_string(
                PAGE, error="Image validation service is temporarily unavailable."
            ), 503

        if val_result.status == ValidationStatus.NON_FUNDUS:
            return render_template_string(
                PAGE,
                error=f"Validation Rejected: The uploaded image does not appear to be a retinal fundus photograph ({val_result.reason}).",
            ), 400

        if val_result.status == ValidationStatus.UNCERTAIN:
            return render_template_string(
                PAGE,
                error=f"Validation Notice: Unable to verify retinal image clarity ({val_result.reason}). Please upload a clear fundus photograph.",
            ), 400

        try:
            grade, label, _probs = predict_grade(
                loaded_model, sanitized_bytes
            )
        except ValueError as exc:
            return render_template_string(PAGE, error=str(exc)), 400
        except Exception as exc:
            return render_template_string(PAGE, error=f"Internal error: {exc}"), 500

        return render_template_string(
            PAGE,
            result={"grade": grade, "label": label},
        )

    # API Endpoints
    @app.get("/api/health")
    @app.get("/health")
    @limiter.limit(get_health_rate_limit)
    def api_health():
        is_tflite = getattr(loaded_model, "is_tflite", False) or isinstance(loaded_model, TFLiteModelWrapper)
        return jsonify(
            {
                "status": "healthy",
                "model_loaded": True,
                "model_version": MODEL_VERSION,
                "inference_engine": "tflite" if is_tflite else "keras",
                "tflite_enabled": is_tflite,
                "auth_enforced": is_auth_enforced(),
                "gemini_validation_enabled": is_validation_enabled(),
                "gemini_configured": bool(get_gemini_api_key()),
                "rate_limiting_enabled": True,
                "scan_integrity_verification": True,
            }
        ), 200

    @app.post("/api/predict")
    @limiter.limit(get_predict_rate_limit)
    def api_predict():
        # Optional JWT authentication verification
        is_authenticated, auth_error = verify_auth_token()
        if not is_authenticated:
            return jsonify({"success": False, "error": auth_error}), 401

        image_bytes = None

        # Case 1: Multipart form upload
        if "image" in request.files:
            file = request.files["image"]
            if file.filename:
                image_bytes = file.read(MAX_UPLOAD_BYTES + 1)
        elif "file" in request.files:
            file = request.files["file"]
            if file.filename:
                image_bytes = file.read(MAX_UPLOAD_BYTES + 1)

        # Case 2: Base64 JSON payload
        elif request.is_json and request.json and "image" in request.json:
            raw_base64 = request.json["image"]
            if "," in raw_base64:
                raw_base64 = raw_base64.split(",", 1)[1]
            try:
                image_bytes = base64.b64decode(raw_base64)
            except Exception as exc:
                return jsonify(
                    {
                        "success": False,
                        "error": f"Invalid base64 encoding: {exc}",
                        "error_code": "INVALID_IMAGE",
                    }
                ), 400

        if not image_bytes:
            return jsonify(
                {
                    "success": False,
                    "error": "No image provided. Send a multipart file ('image') or base64 JSON.",
                    "error_code": "INVALID_IMAGE",
                }
            ), 400

        if len(image_bytes) > MAX_UPLOAD_BYTES:
            return jsonify(
                {
                    "success": False,
                    "error": "Image exceeds 10 MB limit.",
                    "error_code": "INVALID_IMAGE",
                }
            ), 413

        # Step 1: Pre-validate image bytes and dimensions before any external API call
        try:
            sanitized_bytes, mime_type = validate_image_bytes(image_bytes)
        except InvalidImageError as exc:
            return jsonify(
                {
                    "success": False,
                    "error": str(exc),
                    "error_code": "INVALID_IMAGE",
                }
            ), 400

        # Step 2: Call Gemini fundus validation gate
        try:
            val_result = classify_fundus_image(sanitized_bytes, mime_type=mime_type)
        except GeminiConfigurationError:
            return jsonify(
                {
                    "success": False,
                    "error": "Image validation service configuration error.",
                    "error_code": "GEMINI_CONFIGURATION_ERROR",
                }
            ), 500
        except GeminiRateLimitError:
            return jsonify(
                {
                    "success": False,
                    "error": "Image validation service rate limit exceeded. Please try again shortly.",
                    "error_code": "GEMINI_RATE_LIMITED",
                }
            ), 429
        except GeminiTimeoutError:
            return jsonify(
                {
                    "success": False,
                    "error": "Image validation service timed out. Please try again.",
                    "error_code": "GEMINI_TIMEOUT",
                }
            ), 504
        except GeminiUnavailableError:
            return jsonify(
                {
                    "success": False,
                    "error": "Image validation service is currently unavailable.",
                    "error_code": "GEMINI_VALIDATION_UNAVAILABLE",
                }
            ), 503

        # Step 3: Handle non-fundus classification
        if val_result.status == ValidationStatus.NON_FUNDUS:
            return jsonify(
                {
                    "success": False,
                    "error": "The uploaded image does not appear to be a retinal fundus photograph.",
                    "error_code": "NON_FUNDUS_IMAGE",
                    "reason": val_result.reason,
                    "validation_status": "non_fundus",
                }
            ), 400

        # Step 4: Handle uncertain classification
        if val_result.status == ValidationStatus.UNCERTAIN:
            return jsonify(
                {
                    "success": False,
                    "error": "Unable to verify if the uploaded image is a suitable retinal fundus photograph. Please upload a clear fundus photograph.",
                    "error_code": "FUNDUS_CLASSIFICATION_UNCERTAIN",
                    "reason": val_result.reason,
                    "validation_status": "uncertain",
                }
            ), 400

        # Step 5: Valid fundus image -> invoke existing DenseNet-121 inference pipeline
        try:
            grade, label, probabilities = predict_grade(loaded_model, sanitized_bytes)
        except ValueError as exc:
            return jsonify(
                {
                    "success": False,
                    "error": str(exc),
                    "error_code": "INVALID_IMAGE",
                }
            ), 400
        except Exception as exc:
            return jsonify(
                {
                    "success": False,
                    "error": f"Inference failed: {exc}",
                    "error_code": "INFERENCE_FAILED",
                }
            ), 500

        # Compute scalar confidence and low-confidence uncertainty flag (ML-05)
        max_prob = max(probabilities) if probabilities else 0.0
        low_confidence = bool(max_prob < 0.50)

        if low_confidence:
            confidence = round(float(max_prob), 4)
        else:
            if grade == 0:
                p1 = probabilities[1] if len(probabilities) > 1 else 0.0
                confidence = round(float(max(probabilities[0] * (1.0 - p1), 1.0 - p1)), 4)
            elif grade == 4:
                confidence = round(float(probabilities[4]), 4)
            else:
                p_curr = probabilities[grade]
                p_next = probabilities[grade + 1] if grade + 1 < len(probabilities) else 0.0
                confidence = round(float(p_curr * (1.0 - p_next)), 4)

        confidence = round(float(np.clip(confidence, 0.0, 1.0)), 4)

        # Binary classification flag (ML / schema parity: Grade 0 vs Grade >= 1)
        binary_classification = bool(grade > 0)

        # Compute SHA-256 digest of sanitized image bytes
        image_sha256 = hashlib.sha256(sanitized_bytes).hexdigest()

        # Extract patient ID from verified JWT if authenticated
        patient_id = auth_error.get("sub") if (is_authenticated and isinstance(auth_error, dict)) else None

        # Generate cryptographic integrity receipt (ARCH-01)
        receipt = generate_scan_receipt(
            grade=grade,
            probabilities=probabilities,
            image_sha256=image_sha256,
            patient_id=patient_id,
            model_version=MODEL_VERSION,
        )

        return jsonify(
            {
                "success": True,
                "grade": grade,
                "label": label,
                "confidence": confidence,
                "low_confidence": low_confidence,
                "probabilities": probabilities,
                "binary_classification": binary_classification,
                "model_version": MODEL_VERSION,
                "validation": val_result.to_dict(),
                "receipt": receipt,
                "scan_receipt": receipt,
            }
        ), 200

    @app.post("/api/scans/verify-receipt")
    @app.post("/api/scans/verify")
    @limiter.limit(RATE_LIMIT_VERIFY)
    def api_verify_receipt():
        # Optional JWT authentication verification
        is_authenticated, auth_error = verify_auth_token()
        if not is_authenticated:
            return jsonify({"success": False, "error": auth_error}), 401

        if not request.is_json:
            return jsonify(
                {
                    "success": False,
                    "error": "Request body must be JSON.",
                    "error_code": "INVALID_PAYLOAD",
                }
            ), 400

        body = request.get_json()
        receipt = body.get("receipt", body)
        is_valid, message = verify_scan_receipt(receipt)
        if not is_valid:
            return jsonify(
                {
                    "success": False,
                    "valid": False,
                    "error": message,
                    "error_code": "TAMPERED_SCAN_RECEIPT",
                }
            ), 400

        return jsonify(
            {
                "success": True,
                "valid": True,
                "message": message,
                "verified_receipt": receipt,
            }
        ), 200

    @app.post("/api/scans/create")
    @app.post("/api/scans")
    @limiter.limit(get_predict_rate_limit)
    def api_create_verified_scan():
        is_authenticated, auth_error = verify_auth_token()
        if not is_authenticated:
            return jsonify({"success": False, "error": auth_error}), 401

        patient_id = (
            auth_error.get("sub")
            if (is_authenticated and isinstance(auth_error, dict))
            else (request.form.get("patient_id") or (request.json.get("patient_id") if request.is_json else None))
        )
        eye = request.form.get("eye") or (request.json.get("eye") if request.is_json else "OU")
        patient_notes = request.form.get("patient_notes") or (
            request.json.get("patient_notes") if request.is_json else ""
        )

        image_bytes = None
        if "image" in request.files:
            file = request.files["image"]
            if file.filename:
                image_bytes = file.read(MAX_UPLOAD_BYTES + 1)
        elif "file" in request.files:
            file = request.files["file"]
            if file.filename:
                image_bytes = file.read(MAX_UPLOAD_BYTES + 1)
        elif request.is_json and request.json and "image" in request.json:
            raw_base64 = request.json["image"]
            if "," in raw_base64:
                raw_base64 = raw_base64.split(",", 1)[1]
            try:
                image_bytes = base64.b64decode(raw_base64)
            except Exception as exc:
                return jsonify(
                    {
                        "success": False,
                        "error": f"Invalid base64 encoding: {exc}",
                        "error_code": "INVALID_IMAGE",
                    }
                ), 400

        if not image_bytes:
            return jsonify(
                {
                    "success": False,
                    "error": "No image provided. Send a multipart file ('image') or base64 JSON.",
                    "error_code": "INVALID_IMAGE",
                }
            ), 400

        if len(image_bytes) > MAX_UPLOAD_BYTES:
            return jsonify(
                {
                    "success": False,
                    "error": "Image exceeds 10 MB limit.",
                    "error_code": "INVALID_IMAGE",
                }
            ), 413

        try:
            sanitized_bytes, mime_type = validate_image_bytes(image_bytes)
        except InvalidImageError as exc:
            return jsonify(
                {
                    "success": False,
                    "error": str(exc),
                    "error_code": "INVALID_IMAGE",
                }
            ), 400

        try:
            val_result = classify_fundus_image(sanitized_bytes, mime_type=mime_type)
        except GeminiConfigurationError:
            return jsonify(
                {
                    "success": False,
                    "error": "Image validation service configuration error.",
                    "error_code": "GEMINI_CONFIGURATION_ERROR",
                }
            ), 500
        except GeminiRateLimitError:
            return jsonify(
                {
                    "success": False,
                    "error": "Image validation service rate limit exceeded. Please try again shortly.",
                    "error_code": "GEMINI_RATE_LIMITED",
                }
            ), 429
        except GeminiTimeoutError:
            return jsonify(
                {
                    "success": False,
                    "error": "Image validation service timed out. Please try again.",
                    "error_code": "GEMINI_TIMEOUT",
                }
            ), 504
        except GeminiUnavailableError:
            return jsonify(
                {
                    "success": False,
                    "error": "Image validation service is currently unavailable.",
                    "error_code": "GEMINI_VALIDATION_UNAVAILABLE",
                }
            ), 503

        if val_result.status == ValidationStatus.NON_FUNDUS:
            return jsonify(
                {
                    "success": False,
                    "error": "The uploaded image does not appear to be a retinal fundus photograph.",
                    "error_code": "NON_FUNDUS_IMAGE",
                    "reason": val_result.reason,
                }
            ), 400

        if val_result.status == ValidationStatus.UNCERTAIN:
            return jsonify(
                {
                    "success": False,
                    "error": "Unable to verify if the uploaded image is a suitable retinal fundus photograph.",
                    "error_code": "FUNDUS_CLASSIFICATION_UNCERTAIN",
                    "reason": val_result.reason,
                }
            ), 400

        try:
            grade, label, probabilities = predict_grade(loaded_model, sanitized_bytes)
        except ValueError as exc:
            return jsonify(
                {
                    "success": False,
                    "error": str(exc),
                    "error_code": "INVALID_IMAGE",
                }
            ), 400
        except Exception as exc:
            return jsonify(
                {
                    "success": False,
                    "error": f"Inference failed: {exc}",
                    "error_code": "INFERENCE_FAILED",
                }
            ), 500

        # Compute scalar confidence and low-confidence uncertainty flag (ML-05)
        max_prob = max(probabilities) if probabilities else 0.0
        low_confidence = bool(max_prob < 0.50)

        if low_confidence:
            confidence = round(float(max_prob), 4)
        else:
            if grade == 0:
                p1 = probabilities[1] if len(probabilities) > 1 else 0.0
                confidence = round(float(max(probabilities[0] * (1.0 - p1), 1.0 - p1)), 4)
            elif grade == 4:
                confidence = round(float(probabilities[4]), 4)
            else:
                p_curr = probabilities[grade]
                p_next = probabilities[grade + 1] if grade + 1 < len(probabilities) else 0.0
                confidence = round(float(p_curr * (1.0 - p_next)), 4)

        confidence = round(float(np.clip(confidence, 0.0, 1.0)), 4)

        binary_classification = bool(grade > 0)
        image_sha256 = hashlib.sha256(sanitized_bytes).hexdigest()
        receipt = generate_scan_receipt(
            grade=grade,
            probabilities=probabilities,
            image_sha256=image_sha256,
            patient_id=patient_id,
            model_version=MODEL_VERSION,
        )

        canonical_scan = {
            "patient_id": patient_id,
            "eye": eye,
            "grade": grade,
            "label": label,
            "confidence": confidence,
            "low_confidence": low_confidence,
            "probabilities": probabilities,
            "binary_classification": binary_classification,
            "model_version": MODEL_VERSION,
            "patient_notes": patient_notes,
            "image_sha256": image_sha256,
            "validation": val_result.to_dict(),
            "receipt": receipt,
            "scan_receipt": receipt,
        }

        return jsonify(
            {
                "success": True,
                "scan": canonical_scan,
                "confidence": confidence,
                "low_confidence": low_confidence,
                "binary_classification": binary_classification,
                "receipt": receipt,
                "scan_receipt": receipt,
            }
        ), 201

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify(
            {
                "success": False,
                "error": f"Rate limit exceeded: {e.description}",
                "error_code": "RATE_LIMIT_EXCEEDED",
            }
        ), 429

    @app.errorhandler(413)
    def upload_too_large(_error):
        if request.path.startswith("/api/"):
            return jsonify(
                {
                    "success": False,
                    "error": "Maximum upload size is 10 MB.",
                    "error_code": "INVALID_IMAGE",
                }
            ), 413
        return render_template_string(
            PAGE, error="The image is too large. Maximum upload size is 10 MB."
        ), 413

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
