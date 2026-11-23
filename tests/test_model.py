import io
import pytest
import numpy as np
from PIL import Image
import app


@pytest.fixture(scope="module")
def model():
    return app.load_model()


def test_model_loaded(model):
    assert model is not None
    assert len(model.layers) > 0


def test_predict_grade_dummy_image(model):
    # Create synthetic RGB image
    img = Image.new("RGB", (256, 256), color=(180, 50, 40))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    image_bytes = buffer.getvalue()

    grade, label, probabilities = app.predict_grade(model, image_bytes)

    assert isinstance(grade, int)
    assert 0 <= grade <= 4
    assert label in app.GRADE_LABELS.values()
    assert isinstance(probabilities, list)
    assert len(probabilities) == 5
    for p in probabilities:
        assert 0.0 <= p <= 1.0


def test_predict_invalid_image(model):
    with pytest.raises(ValueError, match="not a readable image"):
        app.predict_grade(model, b"not_an_image_binary_data")


def test_all_zeros_threshold_edge_case(monkeypatch, model):
    # Mock model output to return all zeroes [0.0, 0.0, 0.0, 0.0, 0.0]
    # to verify that grade defaults safely to 0 instead of -1
    class MockModelZero:
        def __call__(self, batch, training=False):
            return np.zeros((1, 5), dtype=np.float32)

    img = Image.new("RGB", (224, 224), color=(0, 0, 0))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    grade, label, probabilities = app.predict_grade(MockModelZero(), buffer.getvalue())
    assert grade == 0
    assert label == "No diabetic retinopathy"
    assert probabilities == [0.0, 0.0, 0.0, 0.0, 0.0]


def test_model_version_constant():
    assert app.MODEL_VERSION == "densenet121_ordinal_v1"


def test_model_architecture_and_parameters(model):
    # Verify model is DenseNet-121 based with 7.3M total parameters
    total_params = model.count_params()
    assert 7_000_000 < total_params < 7_600_000
    assert model.output_shape == (None, 5)
    # Verify final activation is sigmoid
    final_layer = model.layers[-1]
    assert hasattr(final_layer, "activation")
    assert final_layer.activation.__name__ == "sigmoid"


def test_predict_grade_maintains_raw_pixel_range_contract(model):
    """Verify inference preserves raw [0.0, 255.0] inputs and does NOT apply preprocess_input."""
    class ModelWrapper:
        def __init__(self, inner):
            self.inner = inner
            self.captured_batches = []

        def __call__(self, batch, training=False):
            self.captured_batches.append(np.asarray(batch))
            return self.inner(batch, training=training)

    wrapper = ModelWrapper(model)
    img = Image.new("RGB", (224, 224), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    app.predict_grade(wrapper, buf.getvalue())

    assert len(wrapper.captured_batches) == 1
    batch = wrapper.captured_batches[0]
    assert batch.shape == (1, 224, 224, 3)
    assert batch.dtype == np.float32
    # Verify pixels are in raw [0.0, 255.0] range (not normalized to [-1, 1] or [0, 1])
    assert float(np.max(batch)) > 1.0
    assert float(np.max(batch)) <= 255.0
    assert float(np.min(batch)) >= 0.0


def test_local_rejection_of_blank_white_black_and_flat_images():
    """Verify local rejection of blank, pure white, pure black, and flat images."""
    from gemini_validator import validate_image_bytes, InvalidImageError

    # 1. Pure black
    black = Image.new("RGB", (200, 200), color=(0, 0, 0))
    buf = io.BytesIO()
    black.save(buf, format="PNG")
    with pytest.raises(InvalidImageError, match="insufficient visual entropy/variance for a fundus photo"):
        validate_image_bytes(buf.getvalue())

    # 2. Pure white
    white = Image.new("RGB", (200, 200), color=(255, 255, 255))
    buf = io.BytesIO()
    white.save(buf, format="JPEG")
    with pytest.raises(InvalidImageError, match="insufficient visual entropy/variance for a fundus photo"):
        validate_image_bytes(buf.getvalue())

    # 3. Flat gray
    gray = Image.new("RGB", (200, 200), color=(128, 128, 128))
    buf = io.BytesIO()
    gray.save(buf, format="PNG")
    with pytest.raises(InvalidImageError, match="insufficient visual entropy/variance for a fundus photo"):
        validate_image_bytes(buf.getvalue())

    # 4. Blank
    blank = Image.new("RGB", (200, 200), color=(0, 0, 0))
    buf = io.BytesIO()
    blank.save(buf, format="JPEG")
    with pytest.raises(InvalidImageError, match="insufficient visual entropy/variance for a fundus photo"):
        validate_image_bytes(buf.getvalue())
