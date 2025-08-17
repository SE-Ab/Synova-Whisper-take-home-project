import json
import hashlib
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from pydantic import BaseModel

def load_private_key(path: str) -> ed25519.Ed25519PrivateKey:
    """Loads a private key from a PEM file."""
    with open(path, "rb") as key_file:
        return serialization.load_pem_private_key(key_file.read(), password=None)

def sha256_hash(data: bytes) -> str:
    """Computes the SHA-256 hash of byte data."""
    return hashlib.sha256(data).hexdigest()

def get_canonical_json(data: BaseModel) -> bytes:
    """
    Returns the canonical JSON representation for hashing, compatible with Pydantic V2.
    This is essential for creating verifiable signatures.
    """

    model_dict = data.model_dump(exclude={'sig'})

    return json.dumps(model_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')

def sign_hash(private_key: ed25519.Ed25519PrivateKey, data_hash: str) -> str:
    """Signs a hash string using the private key."""
    return private_key.sign(data_hash.encode('utf-8')).hex()