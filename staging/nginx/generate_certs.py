#!/usr/bin/env python3
"""
Staging Self-Signed TLS Certificate Generator.

Generates local self-signed X.509 certificates and RSA private keys
with Subject Alternative Names (SAN) for local staging deployments.
Supports localhost, 127.0.0.1, and retina-staging.local.
"""

from __future__ import annotations

import argparse
import datetime
import ipaddress
import os
from pathlib import Path
import sys
from typing import Tuple

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def generate_self_signed_certificate(
    output_dir: str | Path = "staging/nginx/certs",
    days: int = 365,
    key_size: int = 2048,
    cert_name: str = "staging.crt",
    key_name: str = "staging.key",
    common_name: str = "retina-staging.local",
    organization: str = "Retina Staging",
    organizational_unit: str = "Clinical Deployment",
    country: str = "PK",
) -> Tuple[Path, Path]:
    """
    Generate a self-signed RSA TLS certificate and private key with SANs.

    Args:
        output_dir: Target directory for certificate and key files.
        days: Certificate validity period in days.
        key_size: RSA key bit length (default 2048).
        cert_name: Filename for the generated certificate.
        key_name: Filename for the generated private key.
        common_name: Common Name (CN) for the subject/issuer.
        organization: Organization (O) name.
        organizational_unit: Organizational Unit (OU) name.
        country: Country (C) code.

    Returns:
        Tuple of (cert_path, key_path).
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    cert_path = out_path / cert_name
    key_path = out_path / key_name

    # 1. Generate RSA private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )

    # 2. Configure Subject & Issuer
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, organizational_unit),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])

    # 3. Configure Subject Alternative Names (SAN)
    san_list = [
        x509.DNSName("localhost"),
        x509.DNSName(common_name),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
    ]
    if common_name != "localhost" and common_name != "retina-staging.local":
        san_list.append(x509.DNSName("retina-staging.local"))

    san_extension = x509.SubjectAlternativeName(san_list)

    # 4. Validity range
    now = datetime.datetime.now(datetime.timezone.utc)
    valid_from = now - datetime.timedelta(days=1)
    valid_to = now + datetime.timedelta(days=days)

    # 5. Build certificate
    cert_builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(valid_from)
        .not_valid_after(valid_to)
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([
                ExtendedKeyUsageOID.SERVER_AUTH,
                ExtendedKeyUsageOID.CLIENT_AUTH,
            ]),
            critical=False,
        )
        .add_extension(san_extension, critical=False)
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
            critical=False,
        )
    )

    certificate = cert_builder.sign(
        private_key=private_key,
        algorithm=hashes.SHA256(),
    )

    # 6. Serialize private key
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # 7. Serialize certificate
    cert_pem = certificate.public_bytes(
        encoding=serialization.Encoding.PEM,
    )

    # 8. Write to disk
    key_path.write_bytes(key_pem)
    cert_path.write_bytes(cert_pem)

    # Attempt restrictive permissions on key file where supported
    try:
        os.chmod(key_path, 0o600)
    except Exception:
        pass

    return cert_path, key_path


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate self-signed X.509 TLS certificate for private staging.",
    )
    parser.add_argument(
        "--output-dir",
        default="staging/nginx/certs",
        help="Directory to save staging.crt and staging.key (default: staging/nginx/certs)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Certificate validity duration in days (default: 365)",
    )
    parser.add_argument(
        "--key-size",
        type=int,
        default=2048,
        help="RSA key bit size (default: 2048)",
    )
    parser.add_argument(
        "--cert-name",
        default="staging.crt",
        help="Certificate file name (default: staging.crt)",
    )
    parser.add_argument(
        "--key-name",
        default="staging.key",
        help="Private key file name (default: staging.key)",
    )
    return parser.parse_args(args)


def main(args=None) -> int:
    parsed = parse_args(args)
    print(f"[*] Generating self-signed staging certificate ({parsed.key_size}-bit RSA)...")
    cert_path, key_path = generate_self_signed_certificate(
        output_dir=parsed.output_dir,
        days=parsed.days,
        key_size=parsed.key_size,
        cert_name=parsed.cert_name,
        key_name=parsed.key_name,
    )
    print(f"[+] Private key saved to:  {key_path.resolve()}")
    print(f"[+] Certificate saved to:  {cert_path.resolve()}")
    print("[+] SAN includes: localhost, retina-staging.local, 127.0.0.1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
