#!/usr/bin/env python3
"""
Automated Staging Verification & Configuration Linter.

Performs:
1. Static configuration linting:
   - Dockerfile non-root directives (UID 1000 appuser).
   - Docker Compose staging schema, service definitions, and network isolation.
   - NGINX TLS 1.3 protocol and modern cipher suites.
   - Security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options).
   - Self-signed TLS certificate validity and Subject Alternative Names (SAN).
2. Automated health probes:
   - HTTP redirect to HTTPS.
   - TLS 1.3 handshake negotiation.
   - Container / proxy health check (/api/health).
   - Security response headers verification.
   - Predictive endpoint authentication (fail-closed verification).

Supports offline/CI execution via --lint-only and mock probe modes.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import datetime
import json
from pathlib import Path
import re
import socket
import ssl
import sys
from typing import Any, Dict, List, Optional, Tuple
import urllib.parse
import warnings

import requests
import urllib3

# Suppress insecure request warnings for self-signed staging certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class CheckResult:
    """Represents the outcome of a single verification check or probe."""
    name: str
    category: str  # "static_lint" or "health_probe"
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class StagingVerifier:
    """Comprehensive verifier for private staging infrastructure."""

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        dockerfile_path: Optional[Path] = None,
        compose_path: Optional[Path] = None,
        nginx_conf_path: Optional[Path] = None,
        cert_path: Optional[Path] = None,
        key_path: Optional[Path] = None,
        staging_url: str = "https://localhost:8443",
        http_url: str = "http://localhost:8080",
    ):
        self.repo_root = repo_root or Path(__file__).resolve().parent.parent
        self.dockerfile_path = dockerfile_path or (self.repo_root / "Dockerfile")
        self.compose_path = compose_path or (self.repo_root / "docker-compose.staging.yml")
        self.nginx_conf_path = nginx_conf_path or (self.repo_root / "staging" / "nginx" / "conf.d" / "staging.conf")
        self.cert_path = cert_path or (self.repo_root / "staging" / "nginx" / "certs" / "staging.crt")
        self.key_path = key_path or (self.repo_root / "staging" / "nginx" / "certs" / "staging.key")
        self.staging_url = staging_url.rstrip("/")
        self.http_url = http_url.rstrip("/")

        self.results: List[CheckResult] = []

    # --------------------------------------------------------------------------
    # Static Configuration Linting
    # --------------------------------------------------------------------------

    def lint_dockerfile(self, path: Optional[Path] = None) -> CheckResult:
        """Verify Dockerfile enforces non-root execution and security hardening."""
        target = path or self.dockerfile_path
        if not target.is_file():
            return CheckResult(
                name="dockerfile_non_root",
                category="static_lint",
                passed=False,
                message=f"Dockerfile not found at {target}",
            )

        content = target.read_text(encoding="utf-8")
        issues: List[str] = []

        # 1. Check useradd for non-root user (UID 1000 or appuser)
        has_useradd = bool(re.search(r"useradd\s+.*(?:-u\s+1000|appuser)", content))
        if not has_useradd:
            issues.append("Missing unprivileged user creation directive ('useradd -m -u 1000 appuser')")

        # 2. Check ownership assignment (chown)
        has_chown = bool(re.search(r"chown\s+-R\s+appuser:appuser\s+/app", content))
        if not has_chown:
            issues.append("Missing directory ownership assignment ('chown -R appuser:appuser /app')")

        # 3. Check USER directive switches away from root
        user_matches = re.findall(r"^\s*USER\s+([^\s]+)", content, re.MULTILINE)
        if not user_matches:
            issues.append("Missing 'USER' instruction in Dockerfile")
        else:
            final_user = user_matches[-1].strip()
            if final_user in ("root", "0"):
                issues.append(f"Final USER instruction is privileged: '{final_user}'")
            elif final_user not in ("appuser", "1000", "1000:1000"):
                issues.append(f"Unexpected non-root user: '{final_user}' (expected 'appuser' or '1000')")

        passed = len(issues) == 0
        message = (
            "Dockerfile non-root user directives verified (UID 1000 appuser)"
            if passed
            else f"Dockerfile non-root verification failed: {'; '.join(issues)}"
        )
        return CheckResult(
            name="dockerfile_non_root",
            category="static_lint",
            passed=passed,
            message=message,
            details={"issues": issues, "dockerfile": str(target)},
        )

    def lint_compose(self, path: Optional[Path] = None) -> CheckResult:
        """Verify docker-compose.staging.yml enforces network isolation, port masking, and non-root."""
        target = path or self.compose_path
        if not target.is_file():
            return CheckResult(
                name="compose_staging_isolation",
                category="static_lint",
                passed=False,
                message=f"Compose staging file not found at {target}",
            )

        content = target.read_text(encoding="utf-8")
        issues: List[str] = []

        # Check for service 'retina-api'
        if not re.search(r"^\s*retina-api:\s*$", content, re.MULTILINE):
            issues.append("Missing service 'retina-api'")

        # Check for service 'staging-proxy'
        if not re.search(r"^\s*staging-proxy:\s*$", content, re.MULTILINE):
            issues.append("Missing service 'staging-proxy'")

        # Check network declaration and usage
        if "staging-net" not in content:
            issues.append("Dedicated network 'staging-net' is not declared or attached")

        # Verify retina-api non-root execution
        retina_block_match = re.search(
            r"retina-api:.*?(?=\n\s*[a-zA-Z0-9_-]+:\s*$|\Z)",
            content,
            re.DOTALL,
        )
        retina_block = retina_block_match.group(0) if retina_block_match else ""

        if not re.search(r"user:\s*[\"']?(?:1000:1000|1000|appuser)[\"']?", retina_block):
            issues.append("retina-api service must declare non-root user ('user: \"1000:1000\"')")

        # Verify retina-api does NOT publish port 5000 to public host
        # Allowed: expose: ["5000"]
        # Disallowed: ports: - "5000:5000" or host port mappings
        if re.search(r"ports:\s*\n(?:\s*-\s*[\"']?\d+:\d+[\"']?\s*\n)*\s*-\s*[\"']?(?:\d+:)?5000[\"']?", retina_block):
            issues.append("retina-api directly publishes port 5000 to host. Backend must remain internal on staging-net")

        # Verify staging-proxy ports map 8080 and 8443
        proxy_block_match = re.search(
            r"staging-proxy:.*?(?=\n\s*[a-zA-Z0-9_-]+:\s*$|\Z)",
            content,
            re.DOTALL,
        )
        proxy_block = proxy_block_match.group(0) if proxy_block_match else ""

        if not re.search(r"[\"']8080:80[\"']", proxy_block):
            issues.append("staging-proxy must map port '8080:80'")
        if not re.search(r"[\"']8443:443[\"']", proxy_block):
            issues.append("staging-proxy must map port '8443:443'")

        # Verify staging-proxy depends_on retina-api
        if "retina-api" not in proxy_block or "depends_on:" not in proxy_block:
            issues.append("staging-proxy must define depends_on targeting retina-api")

        # Verify environment variables forwarded in retina-api
        critical_vars = [
            "PORT=5000",
            "RETINA_MODEL_PATH",
            "RETINA_TFLITE_PATH",
            "USE_TFLITE",
            "SUPABASE_JWT_SECRET",
            "SCAN_HMAC_SECRET",
        ]
        for v in critical_vars:
            if v not in retina_block:
                issues.append(f"retina-api missing critical environment variable forwarding: {v}")

        passed = len(issues) == 0
        message = (
            "docker-compose.staging.yml schema and network isolation verified"
            if passed
            else f"docker-compose.staging.yml validation failed: {'; '.join(issues)}"
        )
        return CheckResult(
            name="compose_staging_isolation",
            category="static_lint",
            passed=passed,
            message=message,
            details={"issues": issues, "compose_file": str(target)},
        )

    def lint_nginx_tls(self, path: Optional[Path] = None) -> CheckResult:
        """Verify NGINX virtual host configuration enforces TLS 1.3, modern ciphers, and body size."""
        target = path or self.nginx_conf_path
        if not target.is_file():
            return CheckResult(
                name="nginx_tls13_config",
                category="static_lint",
                passed=False,
                message=f"NGINX configuration file not found at {target}",
            )

        content = target.read_text(encoding="utf-8")
        issues: List[str] = []

        # 1. ssl_protocols check
        proto_match = re.search(r"ssl_protocols\s+([^;]+);", content)
        if not proto_match:
            issues.append("Missing 'ssl_protocols' directive")
        else:
            protos = proto_match.group(1).split()
            if "TLSv1.3" not in protos:
                issues.append("ssl_protocols must explicitly enable 'TLSv1.3'")
            disallowed = {"SSLv2", "SSLv3", "TLSv1", "TLSv1.0", "TLSv1.1"}
            found_disallowed = disallowed.intersection(protos)
            if found_disallowed:
                issues.append(f"Insecure legacy protocols detected: {', '.join(found_disallowed)}")

        # 2. Modern ciphers check
        cipher_match = re.search(r"ssl_ciphers\s+[\"']?([^\"';]+)[\"']?;", content)
        if not cipher_match:
            issues.append("Missing 'ssl_ciphers' directive")
        else:
            ciphers = cipher_match.group(1)
            if "TLS_AES_256_GCM_SHA384" not in ciphers and "ECDHE" not in ciphers:
                issues.append("ssl_ciphers does not include recommended modern cipher suites")

        # 3. client_max_body_size check (must be at least 16M for retinal images)
        body_match = re.search(r"client_max_body_size\s+([0-9]+)([kKmMgG]?);", content)
        if not body_match:
            issues.append("Missing 'client_max_body_size' directive")
        else:
            num = int(body_match.group(1))
            unit = body_match.group(2).upper()
            bytes_val = num * 1024 * 1024 if unit == "M" else (num * 1024 if unit == "K" else num)
            if bytes_val < 16 * 1024 * 1024:
                issues.append(f"client_max_body_size ({num}{unit}) is under required 16M threshold")

        # 4. Upstream target
        if "retina-api:5000" not in content and "http://retina_backend" not in content:
            issues.append("Proxy configuration does not route to retina-api:5000 backend")

        passed = len(issues) == 0
        message = (
            "NGINX TLS 1.3, modern ciphers, and client_max_body_size verified"
            if passed
            else f"NGINX TLS configuration failed: {'; '.join(issues)}"
        )
        return CheckResult(
            name="nginx_tls13_config",
            category="static_lint",
            passed=passed,
            message=message,
            details={"issues": issues, "nginx_conf": str(target)},
        )

    def lint_security_headers(self, path: Optional[Path] = None) -> CheckResult:
        """Verify NGINX virtual host defines mandatory security headers."""
        target = path or self.nginx_conf_path
        if not target.is_file():
            return CheckResult(
                name="nginx_security_headers",
                category="static_lint",
                passed=False,
                message=f"NGINX configuration file not found at {target}",
            )

        content = target.read_text(encoding="utf-8")
        issues: List[str] = []

        # 1. HSTS
        hsts_match = re.search(r"add_header\s+Strict-Transport-Security\s+[\"']([^\"']+)[\"']", content, re.IGNORECASE)
        if not hsts_match:
            issues.append("Missing Strict-Transport-Security (HSTS) header")
        else:
            hsts_val = hsts_match.group(1)
            if "max-age=" not in hsts_val:
                issues.append("HSTS header missing max-age parameter")
            if "includeSubDomains" not in hsts_val:
                issues.append("HSTS header missing includeSubDomains parameter")

        # 2. X-Content-Type-Options
        if not re.search(r"add_header\s+X-Content-Type-Options\s+[\"']?nosniff[\"']?", content, re.IGNORECASE):
            issues.append("Missing or invalid X-Content-Type-Options: nosniff header")

        # 3. X-Frame-Options
        if not re.search(r"add_header\s+X-Frame-Options\s+[\"']?(?:DENY|SAMEORIGIN)[\"']?", content, re.IGNORECASE):
            issues.append("Missing or invalid X-Frame-Options: DENY header")

        # 4. Content-Security-Policy
        if not re.search(r"add_header\s+Content-Security-Policy\s+[\"']([^\"']+)[\"']", content, re.IGNORECASE):
            issues.append("Missing Content-Security-Policy (CSP) header")

        # 5. Referrer-Policy
        if not re.search(r"add_header\s+Referrer-Policy\s+[\"']([^\"']+)[\"']", content, re.IGNORECASE):
            issues.append("Missing Referrer-Policy header")

        passed = len(issues) == 0
        message = (
            "NGINX security headers verified (HSTS, nosniff, DENY, CSP, Referrer-Policy)"
            if passed
            else f"NGINX security headers linting failed: {'; '.join(issues)}"
        )
        return CheckResult(
            name="nginx_security_headers",
            category="static_lint",
            passed=passed,
            message=message,
            details={"issues": issues, "nginx_conf": str(target)},
        )

    def lint_certificates(
        self,
        cert_path: Optional[Path] = None,
        key_path: Optional[Path] = None,
    ) -> CheckResult:
        """Verify presence, validity, and SAN extension of staging TLS certificate."""
        c_path = cert_path or self.cert_path
        k_path = key_path or self.key_path

        if not c_path.is_file():
            return CheckResult(
                name="certificate_validity",
                category="static_lint",
                passed=False,
                message=f"Staging TLS certificate not found at {c_path}",
                details={"cert_path": str(c_path)},
            )

        try:
            from cryptography import x509

            cert_data = c_path.read_bytes()
            cert = x509.load_pem_x509_certificate(cert_data)

            issues: List[str] = []

            # Check validity dates
            now = datetime.datetime.now(datetime.timezone.utc)
            # Use getattr for compatibility with different cryptography versions
            not_before = getattr(cert, "not_valid_before_utc", None) or cert.not_valid_before.replace(tzinfo=datetime.timezone.utc)
            not_after = getattr(cert, "not_valid_after_utc", None) or cert.not_valid_after.replace(tzinfo=datetime.timezone.utc)

            if now < not_before:
                issues.append(f"Certificate is not yet valid (valid from {not_before})")
            if now > not_after:
                issues.append(f"Certificate has expired (expired on {not_after})")

            # Check Subject Alternative Names (SAN)
            try:
                san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
                san_names = [str(name.value) for name in san_ext.value]
                if "localhost" not in san_names:
                    issues.append("Certificate SAN missing 'localhost'")
                if "127.0.0.1" not in san_names:
                    issues.append("Certificate SAN missing '127.0.0.1'")
            except x509.ExtensionNotFound:
                issues.append("Certificate missing required SubjectAlternativeName extension")

            # Check private key existence if specified
            if k_path and not k_path.is_file():
                issues.append(f"Private key file not found at {k_path}")

            passed = len(issues) == 0
            message = (
                f"Staging TLS certificate verified (SAN: {', '.join(san_names)}, valid until {not_after.strftime('%Y-%m-%d')})"
                if passed
                else f"Certificate verification failed: {'; '.join(issues)}"
            )
            return CheckResult(
                name="certificate_validity",
                category="static_lint",
                passed=passed,
                message=message,
                details={
                    "issues": issues,
                    "cert_path": str(c_path),
                    "valid_until": str(not_after),
                },
            )
        except Exception as exc:
            return CheckResult(
                name="certificate_validity",
                category="static_lint",
                passed=False,
                message=f"Failed to parse certificate: {exc}",
                details={"error": str(exc)},
            )

    # --------------------------------------------------------------------------
    # Automated Health Probes
    # --------------------------------------------------------------------------

    def probe_http_redirect(
        self,
        http_url: Optional[str] = None,
        mock: bool = False,
    ) -> CheckResult:
        """Probe 1: Verify HTTP port 80/8080 issues 301 redirect to HTTPS."""
        url = (http_url or self.http_url) + "/"

        if mock:
            return CheckResult(
                name="probe_http_redirect",
                category="health_probe",
                passed=True,
                message="[MOCK] HTTP redirect verified (301 to HTTPS 8443)",
                details={"status_code": 301, "location": "https://localhost:8443/"},
            )

        try:
            res = requests.get(url, allow_redirects=False, timeout=5)
            if res.status_code in (301, 302, 307, 308):
                location = res.headers.get("Location", "")
                if location.startswith("https://"):
                    return CheckResult(
                        name="probe_http_redirect",
                        category="health_probe",
                        passed=True,
                        message=f"HTTP redirect verified: HTTP {res.status_code} -> {location}",
                        details={"status_code": res.status_code, "location": location},
                    )
                return CheckResult(
                    name="probe_http_redirect",
                    category="health_probe",
                    passed=False,
                    message=f"HTTP redirect location does not use HTTPS: '{location}'",
                    details={"status_code": res.status_code, "location": location},
                )
            return CheckResult(
                name="probe_http_redirect",
                category="health_probe",
                passed=False,
                message=f"Expected redirect status (301/308), got {res.status_code}",
                details={"status_code": res.status_code},
            )
        except requests.RequestException as exc:
            return CheckResult(
                name="probe_http_redirect",
                category="health_probe",
                passed=False,
                message=f"Failed to connect to HTTP staging port ({url}): {exc}",
                details={"error": str(exc)},
            )

    def probe_tls_handshake(
        self,
        host: str = "127.0.0.1",
        port: int = 8443,
        mock: bool = False,
    ) -> CheckResult:
        """Probe 2: Verify TLS 1.3 handshake negotiation against proxy."""
        if mock:
            return CheckResult(
                name="probe_tls_handshake",
                category="health_probe",
                passed=True,
                message="[MOCK] TLS 1.3 handshake verified (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384)",
                details={"version": "TLSv1.3", "cipher": "TLS_AES_256_GCM_SHA384"},
            )

        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ctx.minimum_version = ssl.TLSVersion.TLSv1_3
            ctx.maximum_version = ssl.TLSVersion.TLSv1_3

            with socket.create_connection((host, port), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname="localhost") as ssock:
                    version = ssock.version()
                    cipher = ssock.cipher()
                    if version == "TLSv1.3":
                        return CheckResult(
                            name="probe_tls_handshake",
                            category="health_probe",
                            passed=True,
                            message=f"TLS 1.3 handshake negotiated successfully (protocol: {version}, cipher: {cipher[0] if cipher else 'unknown'})",
                            details={"version": version, "cipher": cipher},
                        )
                    return CheckResult(
                        name="probe_tls_handshake",
                        category="health_probe",
                        passed=False,
                        message=f"Negotiated TLS version is {version}, expected TLSv1.3",
                        details={"version": version, "cipher": cipher},
                    )
        except Exception as exc:
            return CheckResult(
                name="probe_tls_handshake",
                category="health_probe",
                passed=False,
                message=f"TLS 1.3 handshake failed on {host}:{port}: {exc}",
                details={"error": str(exc)},
            )

    def probe_health_endpoint(
        self,
        base_url: Optional[str] = None,
        mock: bool = False,
    ) -> CheckResult:
        """Probe 3: Verify container healthcheck endpoint (/api/health) returns 200."""
        target_url = (base_url or self.staging_url) + "/api/health"

        if mock:
            return CheckResult(
                name="probe_health_endpoint",
                category="health_probe",
                passed=True,
                message="[MOCK] Container health probe returned HTTP 200 (status: healthy)",
                details={"status_code": 200, "status": "healthy"},
            )

        try:
            res = requests.get(target_url, verify=False, timeout=5)
            if res.status_code == 200:
                data = res.json()
                status_val = data.get("status")
                if status_val == "healthy":
                    return CheckResult(
                        name="probe_health_endpoint",
                        category="health_probe",
                        passed=True,
                        message=f"Health probe succeeded at {target_url} (HTTP 200, status: 'healthy')",
                        details={"status_code": res.status_code, "body": data},
                    )
                return CheckResult(
                    name="probe_health_endpoint",
                    category="health_probe",
                    passed=False,
                    message=f"Health check status is '{status_val}', expected 'healthy'",
                    details={"status_code": res.status_code, "body": data},
                )
            return CheckResult(
                name="probe_health_endpoint",
                category="health_probe",
                passed=False,
                message=f"Health endpoint returned HTTP {res.status_code}",
                details={"status_code": res.status_code, "text": res.text[:200]},
            )
        except requests.RequestException as exc:
            return CheckResult(
                name="probe_health_endpoint",
                category="health_probe",
                passed=False,
                message=f"Health probe request failed at {target_url}: {exc}",
                details={"error": str(exc)},
            )

    def probe_security_headers(
        self,
        base_url: Optional[str] = None,
        mock: bool = False,
    ) -> CheckResult:
        """Probe 4: Verify proxy transmits security headers on HTTPS responses."""
        target_url = (base_url or self.staging_url) + "/api/health"

        if mock:
            return CheckResult(
                name="probe_security_headers",
                category="health_probe",
                passed=True,
                message="[MOCK] Security response headers verified (HSTS, nosniff, DENY, CSP)",
                details={
                    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                },
            )

        try:
            res = requests.get(target_url, verify=False, timeout=5)
            headers = res.headers
            issues: List[str] = []

            if "Strict-Transport-Security" not in headers:
                issues.append("Missing Strict-Transport-Security header in response")
            if headers.get("X-Content-Type-Options", "").lower() != "nosniff":
                issues.append("Missing or invalid X-Content-Type-Options header")
            if headers.get("X-Frame-Options", "").upper() != "DENY":
                issues.append("Missing or invalid X-Frame-Options header (expected DENY)")

            passed = len(issues) == 0
            message = (
                "Proxy transmitted verified security response headers"
                if passed
                else f"Missing security headers: {'; '.join(issues)}"
            )
            return CheckResult(
                name="probe_security_headers",
                category="health_probe",
                passed=passed,
                message=message,
                details={"issues": issues, "headers": dict(headers)},
            )
        except requests.RequestException as exc:
            return CheckResult(
                name="probe_security_headers",
                category="health_probe",
                passed=False,
                message=f"Security headers probe failed at {target_url}: {exc}",
                details={"error": str(exc)},
            )

    def probe_predict_endpoint(
        self,
        base_url: Optional[str] = None,
        mock: bool = False,
    ) -> CheckResult:
        """Probe 5: Verify /api/predict fails closed (HTTP 401) when unauthenticated."""
        target_url = (base_url or self.staging_url) + "/api/predict"

        if mock:
            return CheckResult(
                name="probe_predict_auth_fail_closed",
                category="health_probe",
                passed=True,
                message="[MOCK] /api/predict fail-closed authentication verified (HTTP 401)",
                details={"status_code": 401},
            )

        try:
            # Send POST without Authorization header to confirm 401
            res = requests.post(target_url, json={}, verify=False, timeout=5)
            if res.status_code == 401:
                return CheckResult(
                    name="probe_predict_auth_fail_closed",
                    category="health_probe",
                    passed=True,
                    message=f"/api/predict authenticated endpoint correctly failed closed (HTTP 401 Unauthorized)",
                    details={"status_code": 401},
                )
            return CheckResult(
                name="probe_predict_auth_fail_closed",
                category="health_probe",
                passed=False,
                message=f"/api/predict did not fail closed on unauthenticated request: HTTP {res.status_code}",
                details={"status_code": res.status_code, "text": res.text[:200]},
            )
        except requests.RequestException as exc:
            return CheckResult(
                name="probe_predict_auth_fail_closed",
                category="health_probe",
                passed=False,
                message=f"Predict probe request failed at {target_url}: {exc}",
                details={"error": str(exc)},
            )

    # --------------------------------------------------------------------------
    # Orchestrator
    # --------------------------------------------------------------------------

    def run_all(
        self,
        lint_only: bool = False,
        mock_probes: bool = False,
    ) -> Tuple[bool, List[CheckResult]]:
        """Run all linting checks and optional health probes."""
        self.results = []

        # 1. Static Configuration Linting
        self.results.append(self.lint_dockerfile())
        self.results.append(self.lint_compose())
        self.results.append(self.lint_nginx_tls())
        self.results.append(self.lint_security_headers())
        self.results.append(self.lint_certificates())

        # 2. Automated Health Probes (if not lint-only)
        if not lint_only:
            # Parse host and port for TLS handshake
            parsed_staging = urllib.parse.urlparse(self.staging_url)
            host = parsed_staging.hostname or "127.0.0.1"
            port = parsed_staging.port or 8443

            self.results.append(self.probe_http_redirect(mock=mock_probes))
            self.results.append(self.probe_tls_handshake(host=host, port=port, mock=mock_probes))
            self.results.append(self.probe_health_endpoint(mock=mock_probes))
            self.results.append(self.probe_security_headers(mock=mock_probes))
            self.results.append(self.probe_predict_endpoint(mock=mock_probes))

        all_passed = all(r.passed for r in self.results)
        return all_passed, self.results

    def generate_report(self) -> Dict[str, Any]:
        """Generate a structured dictionary report of verification results."""
        return {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "overall_status": "PASS" if all(r.passed for r in self.results) else "FAIL",
            "total_checks": len(self.results),
            "passed_checks": sum(1 for r in self.results if r.passed),
            "failed_checks": sum(1 for r in self.results if not r.passed),
            "checks": [asdict(r) for r in self.results],
        }


def format_console_report(results: List[CheckResult], overall_passed: bool) -> str:
    """Format check results as a human-readable console table."""
    lines: List[str] = []
    lines.append("=" * 80)
    lines.append("   DIABETIC RETINOPATHY PRIVATE STAGING DEPLOYMENT VERIFICATION REPORT")
    lines.append("=" * 80)
    lines.append(f"{'STATUS':<8} | {'CATEGORY':<14} | {'CHECK NAME':<30} | {'DETAILS'}")
    lines.append("-" * 80)

    for r in results:
        status_tag = "[PASS]" if r.passed else "[FAIL]"
        lines.append(f"{status_tag:<8} | {r.category:<14} | {r.name:<30} | {r.message}")

    lines.append("-" * 80)
    verdict = "PASSED (ALL CHECKS SATISFIED)" if overall_passed else "FAILED (SEE ISSUES ABOVE)"
    lines.append(f"FINAL VERDICT: {verdict}")
    lines.append("=" * 80)
    return "\n".join(lines)


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify and lint private staging deployment configuration and health.",
    )
    parser.add_argument(
        "--lint-only",
        action="store_true",
        help="Run static configuration linting only, skipping live health probes.",
    )
    parser.add_argument(
        "--mock-probes",
        action="store_true",
        help="Execute simulated health probes without requiring live running Docker containers.",
    )
    parser.add_argument(
        "--staging-url",
        default="https://localhost:8443",
        help="Target HTTPS staging base URL (default: https://localhost:8443)",
    )
    parser.add_argument(
        "--http-url",
        default="http://localhost:8080",
        help="Target HTTP staging redirect URL (default: http://localhost:8080)",
    )
    parser.add_argument(
        "--cert-path",
        default=None,
        help="Path to staging TLS certificate (default: staging/nginx/certs/staging.crt)",
    )
    parser.add_argument(
        "--key-path",
        default=None,
        help="Path to staging TLS private key (default: staging/nginx/certs/staging.key)",
    )
    parser.add_argument(
        "--compose-file",
        default=None,
        help="Path to staging docker-compose file (default: docker-compose.staging.yml)",
    )
    parser.add_argument(
        "--dockerfile",
        default=None,
        help="Path to Dockerfile (default: Dockerfile)",
    )
    parser.add_argument(
        "--nginx-conf",
        default=None,
        help="Path to NGINX configuration (default: staging/nginx/conf.d/staging.conf)",
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Optional path to write verification report JSON.",
    )
    return parser.parse_args(args)


def main(args=None) -> int:
    parsed = parse_args(args)

    verifier = StagingVerifier(
        dockerfile_path=Path(parsed.dockerfile) if parsed.dockerfile else None,
        compose_path=Path(parsed.compose_file) if parsed.compose_file else None,
        nginx_conf_path=Path(parsed.nginx_conf) if parsed.nginx_conf else None,
        cert_path=Path(parsed.cert_path) if parsed.cert_path else None,
        key_path=Path(parsed.key_path) if parsed.key_path else None,
        staging_url=parsed.staging_url,
        http_url=parsed.http_url,
    )

    all_passed, results = verifier.run_all(
        lint_only=parsed.lint_only,
        mock_probes=parsed.mock_probes,
    )

    report_text = format_console_report(results, all_passed)
    print(report_text)

    if parsed.output_json:
        out_path = Path(parsed.output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        report_data = verifier.generate_report()
        out_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
        print(f"[+] Report JSON exported to: {out_path.resolve()}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
