from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

def generate_keys():
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    pem_private = private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption())
    with open("signing_key.pem", "wb") as f: f.write(pem_private)
    print("Private key saved to signing_key.pem")
    pem_public = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
    with open("verify_key.pem", "wb") as f: f.write(pem_public)
    print("Public key saved to verify_key.pem")

if __name__ == "__main__":
    generate_keys()