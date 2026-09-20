"""RSA Key Management for JWT RS256 signing and verification.

Generates and persists 2048-bit RSA key pairs to the `certs/` folder:
- `certs/jwt_private.pem`: Private key used ONLY by the backend to sign JWTs.
- `certs/jwt_public.pem`: Public key used to verify signatures.
"""

from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# Dedicated directory for cryptographic keys
CERTS_DIR = Path("certs")
PRIVATE_KEY_PATH = CERTS_DIR / "jwt_private.pem"
PUBLIC_KEY_PATH = CERTS_DIR / "jwt_public.pem"


def generate_rsa_keypair() -> tuple[str, str]:
    """Generates a 2048-bit RSA key pair and persists them to certs/ in PEM format."""
    CERTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Generate RSA Private Key (2048 bits, public exponent 65537 - NIST standard)
    private_key_obj = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # 2. Export Private Key to PKCS8 PEM format (unencrypted on disk, gitignored)
    private_pem = private_key_obj.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    # 3. Export Public Key to SubjectPublicKeyInfo PEM format
    public_pem = private_key_obj.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    # 4. Save to disk so keys persist across server restarts
    PRIVATE_KEY_PATH.write_text(private_pem, encoding="utf-8")
    PUBLIC_KEY_PATH.write_text(public_pem, encoding="utf-8")

    return private_pem, public_pem


def get_rsa_keys() -> tuple[str, str]:
    """Loads the RSA private and public keys, auto-generating them if missing."""
    if not PRIVATE_KEY_PATH.exists() or not PUBLIC_KEY_PATH.exists():
        return generate_rsa_keypair()

    private_pem = PRIVATE_KEY_PATH.read_text(encoding="utf-8")
    public_pem = PUBLIC_KEY_PATH.read_text(encoding="utf-8")
    return private_pem, public_pem
