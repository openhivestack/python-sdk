import base64
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import RawEncoder
import json


class AgentSignature:
    @staticmethod
    def generate_key_pair() -> dict:
        """Generates a new Ed25519 key pair, returning keys as Base64 strings."""
        signing_key = SigningKey.generate()
        private_key_bytes = signing_key.encode(encoder=RawEncoder)
        public_key_bytes = signing_key.verify_key.encode(encoder=RawEncoder)
        
        return {
            "private_key": base64.b64encode(private_key_bytes).decode('utf-8'),
            "public_key": base64.b64encode(public_key_bytes).decode('utf-8'),
        }

    @staticmethod
    def sign(message: dict, private_key: bytes) -> str:
        """Signs a message dictionary using raw Ed25519 private key bytes."""
        signing_key = SigningKey(private_key)
        message_string = json.dumps(message, separators=(',', ':'), sort_keys=True)
        signed_message = signing_key.sign(message_string.encode('utf-8'))
        return base64.b64encode(signed_message.signature).decode('utf-8')

    @staticmethod
    def verify(message: dict, signature: str, public_key: bytes) -> bool:
        """Verifies a message signature using raw Ed25519 public key bytes."""
        try:
            verify_key = VerifyKey(public_key)
            signature_bytes = base64.b64decode(signature)
            message_string = json.dumps(message, separators=(',', ':'), sort_keys=True)
            verify_key.verify(message_string.encode('utf-8'), signature_bytes)
            return True
        except Exception:
            return False
