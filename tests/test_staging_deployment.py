"""
Automated Test Suite for Milestone 3: Private Staging Deployment Configuration & Verification.

Tests:
1. Dockerfile non-root security directives (UID 1000 appuser).
2. docker-compose.staging.yml multi-service topology, network isolation, and port unbinding.
3. NGINX TLS 1.3 configuration, modern ciphers, and client max body size.
4. NGINX security headers (HSTS, CSP, nosniff, DENY, Referrer-Policy).
5. Local X.509 certificate generation with SAN extension (localhost, 127.0.0.1).
6. scripts/verify_staging.py execution with --lint-only.
7. scripts/verify_staging.py CLI arguments, return codes, and JSON report export.
8. Misconfiguration detection (linter catches bad configs and flags failure).
9. Automated mock health probes (HTTP redirect, TLS 1.3, health endpoint, security headers, predict auth).
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Generator
from unittest.mock import MagicMock, patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import pytest

from scripts.verify_staging import CheckResult, StagingVerifier
from staging.nginx.generate_certs import generate_self_signed_certificate

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def verifier(repo_root: Path) -> StagingVerifier:
    return StagingVerifier(repo_root=repo_root)


# ==============================================================================
# Test 1: Dockerfile Non-Root Directives
# ==============================================================================

def test_dockerfile_non_root_directives(verifier: StagingVerifier, repo_root: Path):
    """Test 1: Verify Dockerfile enforces unprivileged user creation and execution."""
    dockerfile = repo_root / "Dockerfile"
    assert dockerfile.is_file(), "Dockerfile must exist at repository root"

    content = dockerfile.read_text(encoding="utf-8")
    assert "useradd -m -u 1000 appuser" in content, "Dockerfile must create appuser with UID 1000"
    assert "chown -R appuser:appuser /app" in content, "Dockerfile must assign /app ownership to appuser"
    assert "USER appuser" in content, "Dockerfile must set USER appuser"

    result = verifier.lint_dockerfile()
    assert result.passed is True
    assert "UID 1000 appuser" in result.message


# ==============================================================================
# Test 2: Compose Staging Network Isolation & Configuration
# ==============================================================================

def test_compose_staging_isolation(verifier: StagingVerifier, repo_root: Path):
    """Test 2: Validate docker-compose.staging.yml services, isolation, and env vars."""
    compose_path = repo_root / "docker-compose.staging.yml"
    assert compose_path.is_file(), "docker-compose.staging.yml must exist"

    content = compose_path.read_text(encoding="utf-8")

    # Service definitions
    assert "retina-api:" in content
    assert "staging-proxy:" in content

    # Network isolation
    assert "staging-net:" in content
    assert "driver: bridge" in content

    # Non-root user in retina-api
    assert 'user: "1000:1000"' in content

    # Port 5000 is internal only (expose, not host mapped)
    assert 'expose:\n      - "5000"' in content or 'expose:\n      - 5000' in content or "expose:" in content
    assert '"5000:5000"' not in content, "Port 5000 must NOT be directly published to host"

    # Staging proxy ports
    assert '"8080:80"' in content
    assert '"8443:443"' in content

    # Mounts
    assert "./staging/nginx/nginx.conf:/etc/nginx/nginx.conf:ro" in content
    assert "./staging/nginx/conf.d:/etc/nginx/conf.d:ro" in content
    assert "./staging/nginx/certs:/etc/nginx/certs:ro" in content

    # Dependency
    assert "retina-api:" in content
    assert "condition: service_healthy" in content

    result = verifier.lint_compose()
    assert result.passed is True


# ==============================================================================
# Test 3: NGINX TLS 1.3 Configuration
# ==============================================================================

def test_nginx_tls13_configuration(verifier: StagingVerifier, repo_root: Path):
    """Test 3: Validate TLS 1.3 protocol, cipher suite string, and client max body size."""
    vhost_path = repo_root / "staging" / "nginx" / "conf.d" / "staging.conf"
    assert vhost_path.is_file(), "staging.conf must exist"

    content = vhost_path.read_text(encoding="utf-8")
    assert "ssl_protocols TLSv1.3 TLSv1.2;" in content
    assert "ssl_prefer_server_ciphers off;" in content
    assert "TLS_AES_256_GCM_SHA384" in content
    assert "client_max_body_size 16M;" in content
    assert "upstream retina_backend" in content
    assert "server retina-api:5000;" in content

    result = verifier.lint_nginx_tls()
    assert result.passed is True


# ==============================================================================
# Test 4: NGINX Security Headers
# ==============================================================================

def test_nginx_security_headers(verifier: StagingVerifier, repo_root: Path):
    """Test 4: Validate presence of HSTS, CSP, X-Frame-Options, X-Content-Type-Options."""
    vhost_path = repo_root / "staging" / "nginx" / "conf.d" / "staging.conf"
    content = vhost_path.read_text(encoding="utf-8")

    assert 'Strict-Transport-Security "max-age=63072000; includeSubDomains"' in content
    assert 'X-Content-Type-Options "nosniff"' in content
    assert 'X-Frame-Options "DENY"' in content
    assert "Content-Security-Policy \"default-src 'self';\"" in content
    assert 'Referrer-Policy "strict-origin-when-cross-origin"' in content

    result = verifier.lint_security_headers()
    assert result.passed is True


# ==============================================================================
# Test 5: Certificate Generation
# ==============================================================================

def test_certificate_generation(tmp_path: Path):
    """Test 5: Verify generate_certs.py creates valid X.509 cert with SAN for localhost and 127.0.0.1."""
    cert_path, key_path = generate_self_signed_certificate(
        output_dir=tmp_path,
        days=90,
        key_size=2048,
        cert_name="test.crt",
        key_name="test.key",
    )

    assert cert_path.is_file()
    assert key_path.is_file()

    cert_data = cert_path.read_bytes()
    cert = x509.load_pem_x509_certificate(cert_data)

    # Check Issuer / Subject
    subject_cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    assert subject_cn == "retina-staging.local"

    # Check Subject Alternative Names (SAN)
    san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
    san_values = [str(x.value) for x in san_ext.value]
    assert "localhost" in san_values
    assert "127.0.0.1" in san_values
    assert "retina-staging.local" in san_values

    # Check validity window
    now = datetime.datetime.now(datetime.timezone.utc)
    not_before = getattr(cert, "not_valid_before_utc", None) or cert.not_valid_before.replace(tzinfo=datetime.timezone.utc)
    not_after = getattr(cert, "not_valid_after_utc", None) or cert.not_valid_after.replace(tzinfo=datetime.timezone.utc)
    assert not_before <= now <= not_after


# ==============================================================================
# Test 6: Verify Staging Script Lint-Only Mode
# ==============================================================================

def test_verify_staging_lint_only(repo_root: Path):
    """Test 6: Verify scripts/verify_staging.py --lint-only runs cleanly with returncode 0."""
    script_path = repo_root / "scripts" / "verify_staging.py"
    res = subprocess.run(
        [sys.executable, str(script_path), "--lint-only"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert res.returncode == 0, f"Script failed with code {res.returncode}:\n{res.stderr}\n{res.stdout}"
    assert "FINAL VERDICT: PASSED" in res.stdout
    assert "[PASS]" in res.stdout


# ==============================================================================
# Test 7: Verify Staging CLI and JSON Report Export
# ==============================================================================

def test_verify_staging_cli_and_json_report(repo_root: Path, tmp_path: Path):
    """Test 7: Verify CLI flags and JSON report structure."""
    json_path = tmp_path / "test_report.json"
    script_path = repo_root / "scripts" / "verify_staging.py"

    res = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--lint-only",
            "--output-json",
            str(json_path),
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert res.returncode == 0
    assert json_path.is_file(), "JSON report must be written"

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["overall_status"] == "PASS"
    assert data["total_checks"] == 5
    assert data["passed_checks"] == 5
    assert data["failed_checks"] == 0
    assert len(data["checks"]) == 5


# ==============================================================================
# Test 8: Misconfiguration Detection in Linter
# ==============================================================================

def test_verify_staging_detects_misconfigurations(verifier: StagingVerifier, tmp_path: Path):
    """Test 8: Verify that invalid configurations are detected and flagged as errors."""

    # 1. Insecure TLS protocols (e.g. TLSv1.0 enabled)
    bad_nginx_tls = tmp_path / "bad_tls.conf"
    bad_nginx_tls.write_text(
        """
        upstream retina_backend { server retina-api:5000; }
        server {
            listen 443 ssl;
            ssl_protocols TLSv1.0 TLSv1.1;
            ssl_ciphers "HIGH:!aNULL:!MD5";
            client_max_body_size 16M;
            location / { proxy_pass http://retina_backend; }
        }
        """,
        encoding="utf-8",
    )
    result_tls = verifier.lint_nginx_tls(bad_nginx_tls)
    assert result_tls.passed is False
    assert any("TLSv1.3" in issue or "Insecure" in issue for issue in result_tls.details["issues"])

    # 2. Missing HSTS header
    bad_headers_conf = tmp_path / "bad_headers.conf"
    bad_headers_conf.write_text(
        """
        server {
            listen 443 ssl;
            add_header X-Content-Type-Options "nosniff";
        }
        """,
        encoding="utf-8",
    )
    result_hdr = verifier.lint_security_headers(bad_headers_conf)
    assert result_hdr.passed is False
    assert any("Strict-Transport-Security" in issue for issue in result_hdr.details["issues"])

    # 3. Dockerfile running as root
    bad_dockerfile = tmp_path / "Dockerfile.bad"
    bad_dockerfile.write_text(
        """
        FROM python:3.12-slim
        WORKDIR /app
        USER root
        CMD ["python", "app.py"]
        """,
        encoding="utf-8",
    )
    result_df = verifier.lint_dockerfile(bad_dockerfile)
    assert result_df.passed is False
    assert any("user creation" in issue or "privileged" in issue for issue in result_df.details["issues"])

    # 4. Compose exposing port 5000 publicly
    bad_compose = tmp_path / "bad_compose.yml"
    bad_compose.write_text(
        """
        services:
          retina-api:
            image: test
            ports:
              - "5000:5000"
            user: "1000:1000"
          staging-proxy:
            image: nginx
            ports:
              - "8080:80"
              - "8443:443"
            depends_on:
              - retina-api
        networks:
          staging-net:
            driver: bridge
        """,
        encoding="utf-8",
    )
    result_comp = verifier.lint_compose(bad_compose)
    assert result_comp.passed is False
    assert any("port 5000" in issue for issue in result_comp.details["issues"])


# ==============================================================================
# Test 9: Automated Mock Probes Verification
# ==============================================================================

def test_verify_staging_mock_probes(verifier: StagingVerifier):
    """Test 9: Verify automated health probe logic using mock execution without live daemon."""
    # Probe 1: HTTP redirect
    res_redirect = verifier.probe_http_redirect(mock=True)
    assert res_redirect.passed is True
    assert "301" in res_redirect.message

    # Probe 2: TLS handshake
    res_tls = verifier.probe_tls_handshake(mock=True)
    assert res_tls.passed is True
    assert "TLSv1.3" in res_tls.message

    # Probe 3: Health endpoint
    res_health = verifier.probe_health_endpoint(mock=True)
    assert res_health.passed is True
    assert res_health.details["status"] == "healthy"

    # Probe 4: Security headers
    res_headers = verifier.probe_security_headers(mock=True)
    assert res_headers.passed is True
    assert "Strict-Transport-Security" in res_headers.details

    # Probe 5: Unauthenticated predict fail-closed
    res_predict = verifier.probe_predict_endpoint(mock=True)
    assert res_predict.passed is True
    assert res_predict.details["status_code"] == 401

    # Full run with mock probes
    all_passed, results = verifier.run_all(lint_only=False, mock_probes=True)
    assert all_passed is True
    assert len(results) == 10
    assert all(r.passed for r in results)


# ==============================================================================
# Test 10: Live Probe Network Failure Graceful Handling
# ==============================================================================

def test_verify_staging_live_probes_handle_unreachable_target(verifier: StagingVerifier):
    """Test 10: Verify live probes cleanly report connection errors when containers are offline."""
    # Point to an unallocated port to test connection refusal handling
    bad_verifier = StagingVerifier(
        staging_url="https://127.0.0.1:59999",
        http_url="http://127.0.0.1:59998",
    )

    res_redirect = bad_verifier.probe_http_redirect(mock=False)
    assert res_redirect.passed is False
    assert "Failed to connect" in res_redirect.message

    res_tls = bad_verifier.probe_tls_handshake(port=59999, mock=False)
    assert res_tls.passed is False
    assert "TLS 1.3 handshake failed" in res_tls.message

    res_health = bad_verifier.probe_health_endpoint(mock=False)
    assert res_health.passed is False
    assert "Health probe request failed" in res_health.message
