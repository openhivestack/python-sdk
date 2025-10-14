import base64
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import RawEncoder
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


class AgentSignature:
    @staticmethod
    def generate_key_pair() -> dict:
        """Generates a new Ed25519 key pair in PEM format."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        pem_private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        pem_public_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        return {
            "private_key": pem_private_key,
            "public_key": pem_public_key,
        }

    @staticmethod
    def sign(message: bytes, private_key: str) -> str:
        """Signs a message using an Ed25519 private key in PEM format."""
        try:
            pem_key = serialization.load_pem_private_key(
                private_key.encode('utf-8'),
                password=None
            )
            raw_private_key = pem_key.private_bytes_raw()
            signing_key = SigningKey(raw_private_key)
            signed_message = signing_key.sign(message)
            return base64.b64encode(signed_message.signature).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to sign message: {e}")

    @staticmethod
    def verify(message: bytes, signature: str, public_key: str) -> bool:
        """Verifies a message signature using an Ed25519 public key in PEM format."""
        try:
            pem_key = serialization.load_pem_public_key(
                public_key.encode('utf-8')
            )
            raw_public_key = pem_key.public_bytes_raw()
            verify_key = VerifyKey(raw_public_key)
            signature_bytes = base64.b64decode(signature)
            verify_key.verify(message, signature_bytes)
            return True
        except Exception:
            return False
