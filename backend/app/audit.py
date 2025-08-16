import portalocker
import json
import os
from datetime import datetime, timezone
from app.schemas import AuditLogEntry
from app.crypto import load_private_key, get_canonical_json, sha256_hash, sign_hash

class AuditLogger:
    def __init__(self, log_file: str, key_path: str, signer_id: str):
        self.log_file = log_file
        self.private_key = load_private_key(key_path)
        self.signer_id = signer_id

    def _get_last_hash_from_disk(self) -> str | None:
        """Safely reads the log file from disk to get the last hash."""
        if not os.path.exists(self.log_file) or os.path.getsize(self.log_file) == 0:
            return None
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in reversed(lines):
                    stripped_line = line.strip()
                    if stripped_line:
                        return json.loads(stripped_line)['hash']
            return None
        except (IOError, json.JSONDecodeError, KeyError, IndexError):
            return None

    def log(self, request_id: str, request_body: dict, response_body: bytes):
        """
        Logs a transaction using a safe, explicit read-then-write pattern,
        locking the file by its path.
        """
        # This is the most reliable locking pattern.
        # It locks the file path, performs all operations, then unlocks.
        with portalocker.Lock(self.log_file, 'a', timeout=5) as f:
            # Step 1: Get the previous hash *inside the lock*.
            prev_hash = self._get_last_hash_from_disk()

            # Step 2: Construct the full log entry in memory.
            entry_data = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
                "request_body": request_body,
                "input_hash": sha256_hash(json.dumps(request_body, sort_keys=True).encode()),
                "output_hash": sha256_hash(response_body),
                "prev_hash": prev_hash,
                "signer_id": self.signer_id,
            }
            
            temp_entry = AuditLogEntry(**entry_data, hash="", sig="")
            entry_hash = sha256_hash(get_canonical_json(temp_entry))
            signature = sign_hash(self.private_key, entry_hash)
            final_entry = AuditLogEntry(**entry_data, hash=entry_hash, sig=signature)
            
            # Step 3: Append the new entry to the file handle provided by portalocker.
            f.write(final_entry.model_dump_json() + "\n")
            f.flush()
            os.fsync(f.fileno())