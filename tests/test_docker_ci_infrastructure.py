"""
Automated Regression Suite for Sprint 8: Staging Infrastructure, Docker & CI/CD.

Tests:
1. Dockerfile hardening, missing file copies (PR-01), port 5000 and dynamic healthcheck (PR-02).
2. Docker Compose environment forwarding (PR-04), port mapping, and concurrency alignment (SEC-05).
3. Pytest discovery configuration (CP-04) and safe non-destructive import of test_supabase.py.
4. Environment variable consistency across .env and .env.example.
5. Deployment architecture documentation completeness (SEC-05).
"""

import importlib
from pathlib import Path
import re
import subprocess
import sys
from unittest.mock import MagicMock, patch
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestDockerfileInfrastructure:
    """Verifies Dockerfile configuration, file copies, ports, and healthchecks."""

    @pytest.fixture(autouse=True)
    def load_dockerfile(self):
        self.dockerfile_path = REPO_ROOT / "Dockerfile"
        assert self.dockerfile_path.is_file(), "Dockerfile must exist at repository root"
        self.dockerfile_content = self.dockerfile_path.read_text(encoding="utf-8")

    def test_dockerfile_copies_gemini_validator_pr01(self):
        """PR-01: Verify Dockerfile explicitly copies gemini_validator.py."""
        assert re.search(
            r"COPY\s+gemini_validator\.py\s+\.",
            self.dockerfile_content,
        ), "Dockerfile must copy gemini_validator.py to prevent ModuleNotFoundError on container startup"

    def test_dockerfile_copies_tflite_model_pr01(self):
        """PR-01: Verify Dockerfile copies retfound_model.tflite for dual-engine inference."""
        assert re.search(
            r"COPY\s+retfound_model\.tflite\s+\.",
            self.dockerfile_content,
        ), "Dockerfile must copy retfound_model.tflite to support TFLite runtime in container"

    def test_dockerfile_copies_core_application_files(self):
        """Verify all core application source files are copied into the container."""
        assert re.search(r"COPY\s+retfound_model\.keras\s+\.", self.dockerfile_content)
        assert re.search(r"COPY\s+app\.py\s+\.", self.dockerfile_content)
        assert re.search(r"COPY\s+gunicorn\.conf\.py\s+\.", self.dockerfile_content)

    def test_dockerfile_standardizes_port_5000_pr02(self):
        """PR-02: Verify Dockerfile standardizes on port 5000 via ENV and EXPOSE."""
        assert re.search(
            r"PORT=5000",
            self.dockerfile_content,
        ), "Dockerfile must set default ENV PORT=5000"
        assert re.search(
            r"EXPOSE\s+5000",
            self.dockerfile_content,
        ), "Dockerfile must EXPOSE 5000 instead of legacy port 7860"

    def test_dockerfile_dynamic_healthcheck_directive_pr02(self):
        """PR-02: Verify HEALTHCHECK uses dynamic PORT expansion with 5000 fallback."""
        assert "HEALTHCHECK" in self.dockerfile_content
        match = re.search(
            r"CMD\s+curl\s+-f\s+http://localhost:\$\{PORT:-5000\}/api/health\s+\|\|\s+exit\s+1",
            self.dockerfile_content,
        )
        assert match is not None, (
            "Dockerfile HEALTHCHECK must use dynamic port: "
            "CMD curl -f http://localhost:${PORT:-5000}/api/health || exit 1"
        )

    def test_dockerfile_non_root_security_hardening(self):
        """Verify container creates and runs as an unprivileged user."""
        assert "useradd" in self.dockerfile_content
        assert re.search(r"USER\s+appuser", self.dockerfile_content)

    def test_dockerfile_wsgi_entrypoint(self):
        """Verify CMD invokes Gunicorn with gunicorn.conf.py and app factory."""
        assert re.search(
            r'CMD\s*\["gunicorn",\s*"--config",\s*"gunicorn\.conf\.py",\s*"app:create_app\(\)"\]',
            self.dockerfile_content,
        )


class TestDockerComposeConfiguration:
    """Verifies docker-compose.yml configuration, environment forwarding, and port mappings."""

    @pytest.fixture(autouse=True)
    def load_compose(self):
        self.compose_path = REPO_ROOT / "docker-compose.yml"
        assert self.compose_path.is_file(), "docker-compose.yml must exist at repository root"
        self.compose_content = self.compose_path.read_text(encoding="utf-8")

    def test_docker_compose_port_mapping_5000(self):
        """Verify docker-compose maps host port 5000 to container port 5000."""
        assert re.search(
            r'-\s*"5000:5000"',
            self.compose_content,
        ), "docker-compose.yml must expose port mapping 5000:5000"

    def test_docker_compose_forwards_all_required_variables_pr04(self):
        """PR-04: Verify all critical runtime environment variables are forwarded."""
        required_vars = [
            "PORT=5000",
            "RETINA_MODEL_PATH=/app/retfound_model.keras",
            "RETINA_TFLITE_PATH=${RETINA_TFLITE_PATH:-/app/retfound_model.tflite}",
            "USE_TFLITE=${USE_TFLITE:-0}",
            "GEMINI_API_KEY=${GEMINI_API_KEY:-}",
            "ENABLE_GEMINI_VALIDATION=${ENABLE_GEMINI_VALIDATION:-true}",
            "GEMINI_MODEL=${GEMINI_MODEL:-gemini-3.1-flash-lite}",
            "GEMINI_TIMEOUT_SECONDS=${GEMINI_TIMEOUT_SECONDS:-15}",
            "SUPABASE_JWT_SECRET=${SUPABASE_JWT_SECRET:-}",
            "SCAN_HMAC_SECRET=${SCAN_HMAC_SECRET:-}",
            "ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-*}",
            "GUNICORN_WORKERS=${GUNICORN_WORKERS:-2}",
            "GUNICORN_THREADS=${GUNICORN_THREADS:-4}",
            "LOG_LEVEL=${LOG_LEVEL:-info}",
        ]

        for var_def in required_vars:
            assert var_def in self.compose_content, f"Missing required env var in docker-compose.yml: {var_def}"

    def test_docker_compose_threads_concurrency_default_is_four(self):
        """PR-04: Verify GUNICORN_THREADS defaults to 4 in docker-compose.yml."""
        assert "${GUNICORN_THREADS:-4}" in self.compose_content, (
            "docker-compose.yml GUNICORN_THREADS must default to 4 (Sprint 7 concurrency tuning)"
        )

    def test_docker_compose_healthcheck_targets_port_5000(self):
        """Verify Compose healthcheck queries port 5000."""
        assert "http://localhost:5000/api/health" in self.compose_content


class TestPytestAndCIConfiguration:
    """Verifies pytest.ini and CI runner discovery behavior (CP-04)."""

    @pytest.fixture(autouse=True)
    def load_pytest_ini(self):
        self.ini_path = REPO_ROOT / "pytest.ini"
        assert self.ini_path.is_file(), "pytest.ini must exist at repository root"
        self.ini_content = self.ini_path.read_text(encoding="utf-8")

    def test_pytest_ini_configures_testpaths(self):
        """CP-04: Verify pytest.ini restricts testpaths to tests/."""
        assert re.search(r"testpaths\s*=\s*tests", self.ini_content)

    def test_pytest_ini_norecursedirs_excludes_sensitive_directories(self):
        """CP-04: Verify norecursedirs ignores mobile, .venv, node_modules, supabase, audit, docs."""
        match = re.search(r"norecursedirs\s*=\s*(.+)", self.ini_content)
        assert match is not None, "norecursedirs directive must be present"
        excluded = match.group(1).split()
        for folder in ["mobile", ".venv", "node_modules", "supabase", "audit", "docs"]:
            assert folder in excluded, f"Folder {folder} must be excluded in norecursedirs"

    def test_pytest_ini_strict_markers_and_options(self):
        """CP-04: Verify addopts includes --strict-markers and -ra -q."""
        assert "--strict-markers" in self.ini_content
        assert "-ra" in self.ini_content

    def test_bare_pytest_collection_cleanliness(self):
        """CP-04: Verify bare pytest collects tests cleanly with zero collection errors."""
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert res.returncode == 0, f"pytest collection failed with return code {res.returncode}:\n{res.stderr}\n{res.stdout}"
        assert "INTERNALERROR" not in res.stderr
        assert "INTERNALERROR" not in res.stdout
        assert "error" not in res.stderr.lower()


class TestSupabaseDiagnosticModule:
    """Verifies root test_supabase.py behaves safely without import side effects (CP-04)."""

    def test_test_supabase_import_has_zero_side_effects(self):
        """CP-04: Importing test_supabase must not call requests or sys.exit."""
        # Unload if already imported
        if "test_supabase" in sys.modules:
            del sys.modules["test_supabase"]

        with patch("requests.get") as mock_get, patch("sys.exit") as mock_exit:
            import test_supabase  # noqa: F401

            assert mock_get.call_count == 0, "Importing test_supabase must not make network requests"
            assert mock_exit.call_count == 0, "Importing test_supabase must not call exit()"

    def test_test_supabase_defines_run_diagnostics(self):
        """CP-04: test_supabase must provide a callable run_diagnostics function."""
        import test_supabase

        assert hasattr(test_supabase, "run_diagnostics")
        assert callable(test_supabase.run_diagnostics)

    def test_run_diagnostics_handles_missing_credentials_gracefully(self):
        """CP-04: run_diagnostics must return False and not raise SystemExit when unconfigured."""
        import test_supabase

        with patch.dict("os.environ", {}, clear=True), patch("pathlib.Path.is_file", return_value=False):
            # Should safely return False without abruptly calling sys.exit
            result = test_supabase.run_diagnostics()
            assert result is False


class TestEnvironmentFilesConsistency:
    """Verifies .env and .env.example variable definitions and consistency."""

    def test_env_and_env_example_set_gunicorn_threads_to_four(self):
        """Verify both .env and .env.example configure GUNICORN_THREADS=4."""
        for filename in [".env", ".env.example"]:
            filepath = REPO_ROOT / filename
            assert filepath.is_file(), f"{filename} must exist"
            content = filepath.read_text(encoding="utf-8")
            assert re.search(r"^GUNICORN_THREADS=4", content, re.MULTILINE), (
                f"{filename} must set GUNICORN_THREADS=4"
            )

    def test_env_files_define_tflite_variables(self):
        """Verify both .env and .env.example define USE_TFLITE and RETINA_TFLITE_PATH."""
        for filename in [".env", ".env.example"]:
            filepath = REPO_ROOT / filename
            content = filepath.read_text(encoding="utf-8")
            assert "USE_TFLITE=" in content
            assert "RETINA_TFLITE_PATH=" in content

    def test_env_files_document_gemini_variables(self):
        """Verify Gemini validation variables are documented in .env and .env.example."""
        for filename in [".env", ".env.example"]:
            filepath = REPO_ROOT / filename
            content = filepath.read_text(encoding="utf-8")
            assert "GEMINI_API_KEY=" in content
            assert "ENABLE_GEMINI_VALIDATION=" in content
            assert "GEMINI_MODEL=" in content
            assert "GEMINI_TIMEOUT_SECONDS=" in content


class TestDeploymentDocumentation:
    """Verifies docs/deployment.md covers staging, TLS, and localtunnel remediation."""

    @pytest.fixture(autouse=True)
    def load_doc(self):
        self.doc_path = REPO_ROOT / "docs" / "deployment.md"
        assert self.doc_path.is_file(), "docs/deployment.md must exist"
        self.doc_content = self.doc_path.read_text(encoding="utf-8")

    def test_deployment_doc_covers_localtunnel_remediation_sec05(self):
        """SEC-05: Verify documentation explicitly details elimination of loca.lt tunnels."""
        assert "loca.lt" in self.doc_content
        assert "SEC-05" in self.doc_content
        assert "HIPAA" in self.doc_content

    def test_deployment_doc_covers_tls_reverse_proxies(self):
        """Verify documentation provides TLS 1.3 reverse proxy configurations."""
        assert "TLS 1.3" in self.doc_content
        assert "nginx" in self.doc_content.lower()
        assert "caddy" in self.doc_content.lower()

    def test_deployment_doc_covers_cloud_staging_blueprints(self):
        """Verify documentation provides staging blueprints for AWS, GCP, or Azure."""
        assert "Fargate" in self.doc_content or "Cloud Run" in self.doc_content


class TestRenderBlueprintSpecification:
    """Verifies render.yaml Blueprint specification, Docker service config, and security."""

    @pytest.fixture(autouse=True)
    def load_render_yaml(self):
        self.render_path = REPO_ROOT / "render.yaml"
        assert self.render_path.is_file(), "render.yaml Blueprint must exist at repository root"
        self.render_content = self.render_path.read_text(encoding="utf-8")

    def test_render_yaml_valid_yaml_structure(self):
        """Verify render.yaml contains services declaration and web service block."""
        assert "services:" in self.render_content
        assert re.search(r"type:\s*web", self.render_content)
        assert re.search(r"name:\s*diabetic-retinopathy-api", self.render_content)

    def test_render_yaml_docker_web_service_configuration(self):
        """Verify web service uses docker runtime, correct dockerfile path, and health check."""
        assert re.search(r"runtime:\s*docker", self.render_content)
        assert re.search(r"dockerfilePath:\s*\./Dockerfile", self.render_content)
        assert re.search(r"healthCheckPath:\s*/health", self.render_content) or re.search(
            r"healthCheckPath:\s*/api/health", self.render_content
        )

    def test_render_yaml_declares_critical_env_vars(self):
        """Verify required runtime environment variables are declared in render.yaml."""
        required_keys = [
            "FLASK_ENV",
            "PORT",
            "RETINA_MODEL_PATH",
            "GUNICORN_WORKERS",
            "GUNICORN_THREADS",
            "GUNICORN_TIMEOUT",
            "GEMINI_API_KEY",
            "SUPABASE_JWT_SECRET",
        ]
        for key in required_keys:
            pattern = rf"key:\s*{key}"
            assert re.search(pattern, self.render_content), f"render.yaml must declare envVar '{key}'"

    def test_render_yaml_marks_secrets_as_sync_false(self):
        """Verify sensitive credentials have sync: false to prevent repository secret exposure."""
        secret_keys = ["GEMINI_API_KEY", "SUPABASE_JWT_SECRET", "SCAN_HMAC_SECRET"]
        for key in secret_keys:
            pattern = rf"-\s*key:\s*{key}\s*\n\s*sync:\s*false"
            assert re.search(pattern, self.render_content), (
                f"Secret '{key}' in render.yaml must have 'sync: false' to prevent exposing secrets"
            )

    def test_render_deployment_guide_completeness(self):
        """Verify docs/render_deployment_guide.md covers sizing, migrations, and mobile connection."""
        guide_path = REPO_ROOT / "docs" / "render_deployment_guide.md"
        assert guide_path.is_file(), "docs/render_deployment_guide.md must exist"
        guide_content = guide_path.read_text(encoding="utf-8")
        assert "Standard" in guide_content
        assert "OOM" in guide_content
        assert "retinal-scans" in guide_content
        assert "001_initial_schema.sql" in guide_content
        assert "005_privacy_and_account_deletion.sql" in guide_content
        assert "EXPO_PUBLIC_INFERENCE_API_URL" in guide_content
