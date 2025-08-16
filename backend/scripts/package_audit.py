import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import hashlib
import zipfile
from app.crypto import load_private_key, sign_hash

SIGNING_KEY_PATH = "signing_key.pem"
AUDIT_LOG_PATH = "../audit_data/audit.jsonl"
REPLAY_SCRIPT_PATH = "repro/inference_replay.py"
OUTPUT_ZIP_PATH = "../audit_pack.zip"

def get_file_sha256(filepath):
    sha = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192): sha.update(chunk)
    return sha.hexdigest()

def create_docs_readme():
    os.makedirs("docs_temp", exist_ok=True)
    readme_path = "docs_temp/README.md"
    content = "# Audit Pack Verification\n\nThis audit pack contains components to verify inference requests.\n\n## Contents\n- `MANIFEST.json`: List of files and their SHA256 hashes.\n- `MANIFEST.json.sig`: Ed25519 signature of the manifest.\n- `audit/`: Contains the signed JSONL audit logs.\n- `repro/`: Contains the `inference_replay.py` script."
    with open(readme_path, "w") as f: f.write(content.strip())
    return readme_path

def main():
    print("Starting audit pack creation...")
    if not (os.path.exists(AUDIT_LOG_PATH) and os.path.exists(SIGNING_KEY_PATH)):
        print(f"Error: Audit log ('{AUDIT_LOG_PATH}') or signing key not found. Please generate logs and keys.")
        return
    docs_readme_path = create_docs_readme()
    manifest = {"files": [
        {"path": f"audit/{os.path.basename(AUDIT_LOG_PATH)}", "sha256": get_file_sha256(AUDIT_LOG_PATH)},
        {"path": f"repro/{os.path.basename(REPLAY_SCRIPT_PATH)}", "sha256": get_file_sha256(REPLAY_SCRIPT_PATH)},
        {"path": f"docs/{os.path.basename(docs_readme_path)}", "sha256": get_file_sha256(docs_readme_path)},
    ]}
    manifest_json_path = "MANIFEST.json"
    with open(manifest_json_path, "w") as f: json.dump(manifest, f, indent=2)
    private_key = load_private_key(SIGNING_KEY_PATH)
    manifest_hash_hex = get_file_sha256(manifest_json_path)
    signature = sign_hash(private_key, manifest_hash_hex)
    manifest_sig_path = "MANIFEST.json.sig"
    with open(manifest_sig_path, "w") as f: f.write(signature)
    with zipfile.ZipFile(OUTPUT_ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zf:
        files_to_zip = [
            (manifest_json_path, "MANIFEST.json"),
            (manifest_sig_path, "MANIFEST.json.sig"),
            (AUDIT_LOG_PATH, f"audit/{os.path.basename(AUDIT_LOG_PATH)}"),
            (REPLAY_SCRIPT_PATH, f"repro/{os.path.basename(REPLAY_SCRIPT_PATH)}"),
            (docs_readme_path, f"docs/{os.path.basename(docs_readme_path)}"),
        ]
        for src, dest in files_to_zip: zf.write(src, dest)
    print(f"Successfully created {OUTPUT_ZIP_PATH}")
    os.remove(manifest_json_path); os.remove(manifest_sig_path); os.remove(docs_readme_path); os.rmdir("docs_temp")
    print("Temporary files cleaned up.")

if __name__ == "__main__":
    main()