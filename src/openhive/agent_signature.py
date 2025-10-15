import base64
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from typing import Dict, Any
import canonicaljson

# Define consistent types for keys and payloads
JSONObject = Dict[str, Any]
KeyBase64Url = str
KeyDict = Dict[str, KeyBase64Url]


class AgentSignature:
    """
    Handles Ed25519 key generation, signing, and verification using 
    canonical JSON serialization. Key material is consistently handled as 
    Base64URL-encoded raw bytes (SPKI/PKCS#8 formats).
    """

    # Helper to decode a Base64URL string (handling missing padding)
    @staticmethod
    def _to_buffer(data_b64url: str) -> bytes:
        padding = '=' * (4 - (len(data_b64url) % 4))
        return base64.urlsafe_b64decode(data_b64url + padding)

    # Helper to encode bytes to Base64URL string (removing padding)
    @staticmethod
    def _to_base64(data_bytes: bytes) -> str:
        return base64.urlsafe_b64encode(data_bytes).decode().rstrip("=")

    @staticmethod
    def canonicalize(payload: JSONObject) -> bytes:
        """
        Converts a JSON object into its canonical byte representation.

        :param payload: The JSON object (dict) to canonicalize.
        :return: The canonical JSON string encoded as UTF-8 bytes.
        """
        # canonicaljson.encode_canonical_json handles deterministic key sorting,
        # consistent whitespace, and UTF-8 encoding, returning bytes directly.
        return canonicaljson.encode_canonical_json(payload)

    @staticmethod
    def generate_key_pair() -> KeyDict:
        """
        Generates a new Ed25519 key pair, returning Base64URL-encoded DER keys.
        
        The returned keys are:
        - privateKey: PKCS#8 DER bytes, Base64URL-encoded.
        - publicKey: SPKI DER bytes, Base64URL-encoded.

        :return: A dictionary with 'privateKey' and 'publicKey' strings.
        """
        private_key = ed25519.Ed25519PrivateKey.generate()
        
        # 1. Export private key as PKCS#8 DER bytes
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # 2. Export public key as SPKI DER bytes
        public_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # 3. Return keys in the exact dictionary structure
        return {
            'privateKey': AgentSignature._to_base64(private_bytes),
            'publicKey': AgentSignature._to_base64(public_bytes)
        }

    @staticmethod
    def _load_private_key(private_key_b64url: KeyBase64Url) -> serialization.load_der_private_key:
        private_bytes = AgentSignature._to_buffer(private_key_b64url)
        return serialization.load_der_private_key(private_bytes, password=None)

    @staticmethod
    def _load_public_key(public_key_b64url: KeyBase64Url) -> serialization.load_der_public_key:
        public_bytes = AgentSignature._to_buffer(public_key_b64url)
        return serialization.load_der_public_key(public_bytes)

    @staticmethod
    def sign(message: JSONObject, private_key: KeyBase64Url) -> str:
        """Signs a canonicalized JSON object."""
        data_to_sign = AgentSignature.canonicalize(message)
        
        private_key = AgentSignature._load_private_key(private_key)
        signature = private_key.sign(data_to_sign)
        
        return AgentSignature._to_base64(signature)

    @staticmethod
    def verify(message: JSONObject, signature: str, public_key: KeyBase64Url) -> bool:
        """Verifies a signature against a canonicalized JSON object."""
        try:
            data_to_verify = AgentSignature.canonicalize(message)
            public_key = AgentSignature._load_public_key(public_key)
            signature = AgentSignature._to_buffer(signature)
            
            public_key.verify(signature, data_to_verify)
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            # Handle key decoding/loading errors
            print(f"An error occurred during verification: {e}")
            return False
