"""TLS Certificate Generator for HorRAGor Nginx Reverse Proxy.

Generates a self-signed X.509 RSA SSL/TLS certificate and private key with Subject
Alternative Names (SAN) for localhost and local network testing:
- certs/nginx/server.key: 2048-bit RSA Private Key (PEM format)
- certs/nginx/server.crt: X.509 Public Certificate (valid for 365 days)
"""

from datetime import datetime, timedelta, timezone
import ipaddress
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

CERTS_DIR = Path("certs/nginx")
CERT_FILE = CERTS_DIR / "server.crt"
KEY_FILE = CERTS_DIR / "server.key"


def generate_self_signed_tls_cert(
    output_dir: Path = CERTS_DIR,
    days_valid: int = 365,
) -> tuple[Path, Path]:
    """Generates a self-signed TLS certificate and private key with SAN extensions."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate 2048-bit RSA Private Key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # 2. Define Subject and Issuer (Self-Signed)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "FR"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Ile-de-France"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Paris"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "HorRAGor Security Cluster"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "DevOps"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ]
    )

    # 3. Define Subject Alternative Names (SAN) for local and container networking
    san_names = [
        x509.DNSName("localhost"),
        x509.DNSName("horragor.local"),
        x509.DNSName("horragor-nginx"),
        x509.DNSName("frontend"),
        x509.DNSName("backend"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        x509.IPAddress(ipaddress.IPv6Address("::1")),
    ]

    now = datetime.now(timezone.utc)

    # 4. Build X.509 Certificate
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=days_valid))
        .add_extension(
            x509.SubjectAlternativeName(san_names),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .sign(private_key, hashes.SHA256())
    )

    # 5. Export and write Private Key (PKCS8 PEM)
    key_path = output_dir / "server.key"
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    key_path.write_bytes(key_pem)

    # 6. Export and write Public Certificate (PEM)
    cert_path = output_dir / "server.crt"
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    cert_path.write_bytes(cert_pem)

    print(f"[OK] TLS Private Key generated: {key_path}")
    print(f"[OK] TLS Public Certificate generated: {cert_path}")
    print(f"[OK] Validity: {days_valid} days | SAN: localhost, 127.0.0.1, horragor.local")

    return cert_path, key_path


if __name__ == "__main__":
    generate_self_signed_tls_cert()
