import portalocker
import json
import os
from datetime import datetime, timezone
from app.schemas import AuditLogEntry
from app.crypto import load_private_key, get_canonical_json, sha256_hash, sign_hash
from threading import Lock

class AuditLogger:
    def __init__(self, log_file: str, key_path: str, signer_id: str):
        self.log_file = log_file
        self.private_key = load_private_key(key_path)
        self.signer_id = signer_id
        self.state_lock = Lock()
        self.last_known_hash = self._initialize_last_hash()

    def _initialize_last_hash(self) -> str | None:
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            if not os.path.exists(self.log_file):
                return None
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in reversed(lines):
                    stripped_line = line.strip()
                    if stripped_line:
                        return json.loads(stripped_line)['hash']
            return None
        except Exception as e:
            print(f"Could not initialize last hash from log file: {e}")
            return None

    def log(self, request_id: str, request_body: dict, response_body: bytes):
        try:
            with self.state_lock:
                prev_hash = self.last_known_hash
                entry_data = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "request_id": request_id,
                    "request_body": request_body,
                    "input_hash": sha256_hash(json.dumps(request_body, sort_keys=True).encode()),
                    "output_hash": sha256_hash(response_body),
                    "prev_hash": prev_hash,
                    "signer_id": self.signer_id,
                }
                temp_entry = AuditLogEntry(**entry_data, hash="placeholder", sig="placeholder")
                entry_hash = sha256_hash(get_canonical_json(temp_entry))
                signature = sign_hash(self.private_key, entry_hash)
                final_entry = AuditLogEntry(**entry_data, hash=entry_hash, sig=signature)
                with open(self.log_file, "a", encoding='utf-8') as f:
                    f.write(final_entry.model_dump_json() + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                self.last_known_hash = entry_hash
        except Exception as e:
            print(f"CRITICAL ERROR during audit logging: {e}")