import argparse
import json
import os
import httpx
import hashlib

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

def sha256_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def replay_inference(log_file: str, request_id: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY environment variable not set.")
        return
    log_entry = None
    with open(log_file, 'r') as f:
        for line in f:
            entry = json.loads(line)
            if entry.get("request_id") == request_id:
                log_entry = entry; break
    if not log_entry:
        print(f"[ERROR] No log entry found for request_id: {request_id}")
        return
    print(f"[INFO] Found log entry for request_id: {request_id}")
    original_request = log_entry['request_body']
    original_output_hash = log_entry['output_hash']
    replay_request = {**original_request, 'temperature': 0, 'seed': 123}
    print("[INFO] Replaying request with deterministic settings...")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    with httpx.Client() as client:
        response = client.post(OPENAI_API_URL, json=replay_request, headers=headers, timeout=120)
        response.raise_for_status()
        replayed_output_body = response.content
    replayed_hash = sha256_hash(replayed_output_body)
    print(f"[INFO] Original Output Hash: {original_output_hash}")
    print(f"[INFO] Replayed Output Hash: {replayed_hash}")
    if original_output_hash == replayed_hash:
        print("[SUCCESS] Hashes match! The inference is reproducible.")
    else:
        print("[FAILURE] Hashes do not match.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay an OpenAI inference from an audit log.")
    parser.add_argument("log_file", help="Path to the audit.jsonl file.")
    parser.add_argument("--request-id", required=True, help="The request_id to replay.")
    args = parser.parse_args()
    replay_inference(args.log_file, args.request_id)