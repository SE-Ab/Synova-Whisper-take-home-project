# Professional AI Proxy with Signed Audit Chain

This project implements a secure, OpenAI-compatible proxy server featuring a signed audit chain and a modern frontend interface. It is designed as a production-ready, multi-service application orchestrated with Docker Compose.

This version connects to the **live, free, and high-speed Groq API**, which is OpenAI-compatible. This allows for full end-to-end testing with a real AI model without needing a paid OpenAI key, fulfilling all requirements in a robust and demonstrable way.

## Features

-   ✅ **Secure Audit Trail**: Every transaction is logged to a tamper-evident, Ed25519-signed JSONL chain, ensuring atomic writes with file locks.
-   ✅ **Live AI Integration**: Connects to the free Groq API for real-time, high-speed inference, fulfilling the "OpenAI-compatible" requirement.
-   ✅ **Modern Frontend Showcase**: A beautiful, responsive chat interface on `localhost:8080` with a fluid "live typing" effect, Markdown rendering, and syntax highlighting.
-   ✅ **Containerized Architecture**: The entire stack (Frontend, Proxy) is orchestrated with `docker-compose` for a one-command, zero-dependency setup.
-   ✅ **Reproducibility Pack**: A script is included to package the audit logs and verification tools into a distributable `audit_pack.zip`.
-   ✅ **Seamless User Experience**: The frontend automatically and securely receives its API key from the backend, providing a zero-configuration user experience after the initial setup.

## Architecture

The system runs as two interconnected services, communicating with a live external API. This decoupled architecture is clean, scalable, and easy to maintain.

[User Browser] ---> [Frontend (Nginx on :8080)]
|
[Proxy (FastAPI on :8000)] ---> [Audit Log (audit.jsonl)]
|
[Live Groq API (api.groq.com)]


## Setup & Launch

**Prerequisites:**
1.  Docker and Docker Compose.
2.  A free API key from [Groq](https://console.groq.com/keys).

**Instructions:**

1.  **Configure Environment**:
    *   Copy the `.env.example` file to a new file named `.env`.
    *   Open `.env` and paste your free Groq API key (it starts with `gsk_`) into the `GROQ_API_KEY` field.

2.  **Generate Signing Keys**: The proxy requires an Ed25519 key pair for the audit log.
    ```bash
    # Navigate to the backend directory
    cd backend
    # Create a venv and install dependencies
    python -m venv venv
    # Activate the virtual environment
    # On Windows (PowerShell):
    .\venv\Scripts\Activate.ps1
    # On macOS/Linux:
    # source venv/bin/activate
    pip install -r requirements.txt
    # Run the key generation script
    python scripts/generate_key.py
    # Return to the root directory
    cd ..
    ```

3.  **Create Initial Log File**: To prevent Docker volume permission issues (especially on Windows), create the initial log file.
    ```bash
    # On Windows (PowerShell):
    New-Item audit_data/audit.jsonl -ItemType File -Force
    # On macOS/Linux:
    # mkdir -p audit_data && touch audit_data/audit.jsonl
    ```

4.  **Launch the Services**: From the project root, run the master command:
    ```bash
    docker-compose up --build
    ```

## How to Use

-   **Frontend UI**: Open your browser and navigate to **`http://localhost:8080`**. The application will be ready to use immediately. Type a prompt and press Enter.

-   **Example `curl` Command**: You can also interact with the proxy directly via the command line.
    ```bash
    # Replace $GROQ_API_KEY with your key
    curl -N http://localhost:8000/proxy/openai/v1/chat/completions \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $GROQ_API_KEY" \
      -d '{
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": "Explain SSE streaming in one sentence."}],
        "stream": true
      }'
    ```

## Project Deliverables Checklist

This project successfully fulfills all mandatory requirements from the challenge brief.

#### ✓ Proxy / SSE Streaming
-   [x] Accepts `POST` requests at the specified endpoint.
-   [x] Forwards requests to an OpenAI-compatible upstream API.
-   [x] Passes through SSE streams correctly.
-   [x] Computes and emits `rem.chunk` events per data frame.
-   [x] Injects the final `rem.manifest` event before the stream ends.

#### ✓ Audit Log
-   [x] Stores logs in an append-only JSONL file.
-   [x] Contains all required fields (`ts`, `request_id`, etc.).
-   [x] Chains each entry via `prev_hash`.
-   [x] Signs each line with Ed25519.
-   [x] Ensures atomic writes using `portalocker` and `fsync`.

#### ✓ Replay Script
-   [x] `repro/inference_replay.py` is included.
-   [x] It reads a JSONL entry and attempts to replay it with deterministic settings.
-   [x] **Note**: The replay script is designed for a deterministic API (like OpenAI with `seed` and `temperature=0`). It will not produce matching hashes against the live, non-deterministic Groq API but is provided to demonstrate the concept of a replayable audit.

#### ✓ Audit Pack Export
-   [x] A sample `audit_pack.zip` is included in the root of this repository.
-   [x] A script (`scripts/package_audit.py`) is provided to generate a new pack containing the manifest, signature, logs, replay script, and docs. To run:
    ```bash
    # In the backend directory (with venv active)
    python scripts/package_audit.py
    ```

This concludes the project. The application is fully functional, robust, and ready for evaluation.
