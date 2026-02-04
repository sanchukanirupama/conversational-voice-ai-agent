# Voice AI Agent Backend

This is the Python/FastAPI backend for the Voice AI Agent. It handles WebSocket connections, processes audio (STT/TTS) using OpenAI, and manages the LangGraph agent for banking logic.

## Prerequisites

- Python 3.11 or higher
- `pip` (Python package installer)
- OpenAI API Key (optional, but required for real Audio/Intelligence)

## Setup

1. **Navigate to the root project directory** (if you aren't already there):
   ```bash
   cd voice-ai-agent
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   python3 -m venv backend/venv
   source backend/venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

## Configuration

The backend looks for an `OPENAI_API_KEY` environment variable.

- **Option A**: Export it in your terminal before running:
  ```bash
  export OPENAI_API_KEY="sk-..."
  ```
- **Option B**: Create a `.env` file in the `backend/` directory (ensure `python-dotenv` loads it, or just export in shell).

**Note**: If no API Key is found, the system runs in **Mock Mode**, using simulated transcripts and simple logic.

## Running the Server

Start the FastAPI server using Uvicorn:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

- Local URL: `http://localhost:8000`
- WebSocket Endpoint: `ws://localhost:8000/ws`

## Observability (LangSmith)

To see full traces of the Agent's thought process (tools called, latency, errors):

1.  **Sign Up**: Go to [LangSmith](https://smith.langchain.com/) and create an account.
2.  **Get API Key**:
    *   Click on the **Settings** (gear icon) -> **API Keys**.
    *   Create a new Service API Key.
    *   Copy the key (starts with `lsv2...`).
3.  **Configure `.env`**:
    *   Open `backend/.env`.
    *   Paste the key: `LANGCHAIN_API_KEY=lsv2...`
    *   Ensure `LANGCHAIN_TRACING_V2=true`.
4.  **View Traces**:
    *   Restart the backend.
    *   Make a call.
    *   Go to your [LangSmith Projects](https://smith.langchain.com/projects).
    *   Look for a project named **"Voice Agent Bank ABC"**.
    *   Click it to see the trace tree of every interaction.
