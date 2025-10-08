import base64
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import RawEncoder


class Crypto:
    @staticmethod
    def generate_key_pair() -> dict:
        """Generates a new Ed25519 key pair."""
        signing_key = SigningKey.generate()
        return {
            "private_key": signing_key.encode(encoder=RawEncoder),
            "public_key": signing_key.verify_key.encode(encoder=RawEncoder),
        }

    @staticmethod
    def sign(message: bytes, private_key: bytes) -> str:
        """Signs a message using an Ed25519 private key."""
        signing_key = SigningKey(private_key)
        signed_message = signing_key.sign(message)
        return base64.b64encode(signed_message.signature).decode('utf-8')

    @staticmethod
    def verify(message: bytes, signature: str, public_key: bytes) -> bool:
        """Verifies a message signature using an Ed25519 public key."""
        try:
            verify_key = VerifyKey(public_key)
            signature_bytes = base64.b64decode(signature)
            verify_key.verify(message, signature_bytes)
            return True
        except Exception:
            return False
