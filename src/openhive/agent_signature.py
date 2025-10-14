import base64
import json
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
    def sign(message: dict, private_key_pem: str) -> str:
        """Signs a message dictionary using an Ed25519 private key in PEM format."""
        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None
            )
            message_string = json.dumps(message, separators=(',', ':'), sort_keys=True)
            signature = private_key.sign(message_string.encode('utf-8'))
            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to sign message: {e}")

    @staticmethod
    def verify(message: dict, signature: str, public_key_pem: str) -> bool:
        """Verifies a message signature using an Ed25519 public key in PEM format."""
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8')
            )
            message_string = json.dumps(message, separators=(',', ':'), sort_keys=True)
            signature_bytes = base64.b64decode(signature)
            public_key.verify(signature_bytes, message_string.encode('utf-8'))
            return True
        except Exception:
            return False
