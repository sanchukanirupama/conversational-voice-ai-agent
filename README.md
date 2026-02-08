# 🎙️ AI Voice Banking Agent

A full-stack AI-powered voice banking assistant built with **Next.js**, **FastAPI**, **LangGraph**, and **OpenAI**. The agent handles real-time voice conversations, processes banking requests, and autonomously resolves customer issues using intelligent tool selection.

![Architecture](https://img.shields.io/badge/Architecture-LangGraph-blue)
![Frontend](https://img.shields.io/badge/Frontend-Next.js%2016-black)
![Backend](https://img.shields.io/badge/Backend-FastAPI-green)
![AI](https://img.shields.io/badge/AI-OpenAI-orange)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [How It Works](#-how-it-works)
- [LangGraph Flow](#-langgraph-flow)
- [LangSmith Observability](#-langsmith-observability)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Development](#-development)

---

## ✨ Features

### Voice Capabilities
- 🎤 **Voice Activity Detection (VAD)** - Intelligent speech detection with automatic silence handling
- 🗣️ **Real-time STT** - OpenAI Whisper for accurate transcription

### Banking Features
- 💳 **Card Management** - Block/freeze cards, report lost/stolen
- 💰 **Account Services** - Balance checks, transaction history
- 🔐 **Identity Verification** - Secure customer authentication
- 📝 **Address Updates** - Profile management
- 📞 **Smart Call Routing** - Intent classification and flow routing
- 🤖 **Autonomous Problem Solving** - Agent uses tools to resolve issues

### Agent Intelligence
- 🧠 **LangGraph Orchestration** - Stateful conversation flow
- 🛠️ **Tool-based Actions** - Real database operations via LangChain tools
- 🎯 **Context-aware Routing** - Dynamic flow selection based on user intent
- 📊 **LangSmith Tracing** - Full observability into agent decisions

---

## 🏗️ Architecture

### Communication Flow

```
1. User Speech Detection (Frontend)
   ↓
2. VAD captures audio → Base64 encoding
   ↓
3. WebSocket sends audio to backend
   ↓
4. OpenAI Whisper transcribes audio
   ↓
5. LangGraph Agent processes request
   │
   ├─▶ Router Node: Classify intent
   ├─▶ Gate Node: Check verification status
   ├─▶ Executor Node: Generate response + tool calls
   └─▶ Tool Node: Execute actions (DB queries, card blocking, etc.)
   ↓
6. OpenAI TTS generates audio response
   ↓
7. WebSocket sends audio back to frontend
   ↓
8. Frontend plays audio → VAD resumes listening
```

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 16 (React 19, TypeScript)
- **UI**: Tailwind CSS 4, Framer Motion
- **Audio**: Web Audio API, MediaRecorder API
- **WebSocket**: Native WebSocket API

### Backend
- **Framework**: FastAPI
- **AI Orchestration**: LangGraph
- **LLM**: OpenAI GPT-4
- **Voice**: OpenAI Whisper (STT) + TTS
- **Database**: SQLite
- **Observability**: LangSmith


---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- **LangSmith API Key** (Optional, for observability - [Sign up here](https://smith.langchain.com/))

### 1. Clone the Repository

```bash
git clone <repository-url>
cd voice-ai-agent
```

### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Edit .env and add your API keys:
# OPENAI_API_KEY=sk-...
# LANGCHAIN_API_KEY=lsv2_...  (optional)
# LANGCHAIN_TRACING_V2=true   (optional)
```

### 3. Frontend Setup

```bash
# Open a new terminal
cd client

# Install dependencies
npm install

# Configure environment (if needed)
cp .env.example .env.local

# Edit .env.local if you need to change the backend URL
# NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 4. Run Both Services

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd client
npm run dev
```

### 5. Open the Application

🌐 **Frontend**: [http://localhost:3000](http://localhost:3000)

🔧 **Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs)

📊 **Admin Dashboard**: [http://localhost:3000/admin/login](http://localhost:3000/admin/login)
- Username: `admin`
- Password: `admin123`

---

## 🔄 How It Works

### Voice Input Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. VAD (Voice Activity Detection)                          │
│     • Analyzes audio frequency in real-time (60fps)         │
│     • Threshold: Volume > 40 (0-255 scale)                  │
│     • Detects speech start automatically                    │
│     • Waits 1 second of silence before finalizing           │
└─────────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Audio Capture & Encoding                                │
│     • MediaRecorder captures WebM audio                     │
│     • Minimum duration: 800ms                               │
│     • Minimum size: 3000 bytes                              │
│     • Converts to Base64 data URL                           │
└─────────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  3. WebSocket Transmission                                  │
│     • Sends: { type: "audio", data: "data:audio/webm..." } │
│     • Frontend → Backend via WS connection                  │
└─────────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Speech-to-Text (Backend)                                │
│     • OpenAI Whisper API transcription                      │
│     • Hallucination filtering (removes "Thanks for          │
│       watching!", etc.)                                     │
│     • Minimum audio size: 1000 bytes                        │
└─────────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  5. LangGraph Agent Processing (See detailed flow below)    │
└─────────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Text-to-Speech                                          │
│     • OpenAI TTS with "alloy" voice                         │
│     • Base64 encoded MP3                                    │
└─────────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  7. Audio Playback & VAD Resume                             │
│     • Frontend decodes and plays audio                      │
│     • VAD gate opens when playback ends                     │
│     • Listens for next user input                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧠 LangGraph Flow

### Agent Architecture

The agent uses **LangGraph** to orchestrate a stateful conversation flow with multiple decision nodes:

```
                    START
                      │
                      ▼
        ┌─────────────────────────┐
        │     Router Node         │
        │  • Classifies user      │
        │    intent using LLM     │
        │  • Returns flow name    │
        │    (card_atm_issues,    │
        │     account_servicing,  │
        │     general, etc.)      │
        └─────────────────────────┘
                      │
                      ▼
        ┌─────────────────────────┐
        │   Verification Gate     │
        │  • Checks if flow       │
        │    requires ID verify   │
        │  • If required & not    │
        │    verified → injects   │
        │    verification prompt  │
        └─────────────────────────┘
                      │
                      ▼
        ┌─────────────────────────┐
        │    Flow Executor        │
        │  • Selects tools for    │
        │    the current flow     │
        │  • Binds system prompt  │
        │  • Generates response   │
        │  • May call tools       │
        └─────────────────────────┘
                      │
                      ▼
                  Decision
            ┌─────────┴─────────┐
            │                   │
         Tools?               No Tools
            │                   │
            ▼                   ▼
     ┌────────────┐          END
     │ Tool Node  │
     │ • Executes │
     │   tools    │
     │ • Returns  │
     │   results  │
     └────────────┘
            │
            └──────▶ Loop back to Router
```

### Routing Flows

The system supports multiple conversation flows:

1. **card_atm_issues** - Card blocking, lost/stolen reports
2. **account_servicing** - Balance checks, statements
3. **account_opening** - New account inquiries (escalates to human)
4. **digital_app_support** - App login issues (escalates)
5. **transfers_payments** - Payment issues (escalates)
6. **account_closure** - Closure requests (escalates)
7. **general** - Greetings, unclear intent

Each flow has:
- **Required tools**: Available actions for the agent
- **Verification requirement**: Whether ID check is mandatory
- **Max questions**: Escalation threshold
- **Flow instructions**: Specific conversation patterns

---

## 📊 LangSmith Observability

LangSmith provides full visibility into agent behavior:

### Setup

1. **Create Account**: [smith.langchain.com](https://smith.langchain.com/)

2. **Get API Key**:
   - Settings → API Keys → Create Service API Key
   - Copy the key (starts with `lsv2_...`)

3. **Configure Backend**:
   ```bash
   # backend/.env
   LANGCHAIN_API_KEY=lsv2_...
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=Voice-Agent-Bank-ABC
   ```

4. **Restart Backend**:
   ```bash
   uvicorn backend.main:app --reload
   ```


---

## 📁 Project Structure

```
voice-ai-agent/
│
├── backend/                      # Python FastAPI backend
│   ├── agent/                    # LangGraph agent logic
│   │   ├── config.py            # Flow configuration loader
│   │   ├── graph.py             # LangGraph workflow builder
│   │   ├── nodes.py             # Router, Gate, Executor nodes
│   │   ├── state.py             # AgentState type definition
│   │   └── tools_registry.py   # Tool definitions & registry
│   │
│   ├── routes/                  # FastAPI endpoints
│   │   ├── websocket.py        # WebSocket handler
│   │   ├── admin.py            # Admin API endpoints
│   │   └── health.py           # Health check
│   │
│   ├── services/                # Business logic
│   │   ├── audio.py            # STT/TTS with OpenAI
│   │   └── router.py           # Intent classification
│   │
│   ├── data/                    # Configuration & database
│   │   ├── unified_configuration.json  # Agent prompts & flows
│   │   └── voice_agent.db      # SQLite database
│   │
│   ├── tools/                   # Database operations
│   │   └── db_operations.py
│   │
│   ├── config.py               # Settings management
│   ├── main.py                 # FastAPI app entry point
│   └── requirements.txt        # Python dependencies
│
├── client/                      # Next.js frontend
│   ├── app/                     # Next.js 13+ app directory
│   │   ├── hooks/              # React hooks
│   │   │   ├── useVoiceAgent.ts      # Main WebSocket logic
│   │   │   └── useAudioRecorder.ts   # VAD engine
│   │   │
│   │   ├── components/         # React components
│   │   │   └── VoiceOrb.tsx   # Voice visualization
│   │   │
│   │   ├── admin/              # Admin dashboard
│   │   │   ├── login/
│   │   │   └── dashboard/
│   │   │
│   │   ├── page.tsx            # Main voice UI
│   │   └── layout.tsx          # Root layout
│   │
│   ├── components/ui/          # UI components
│   │   ├── siri-waveform.tsx  # Audio visualization
│   │   └── retro-grid.tsx     # Background effect
│   │
│   ├── utils/                   # Helper functions
│   │   └── audio.ts            # Audio utilities
│   │
│   └── package.json            # Node dependencies
│
└── README.md                    # This file
```

---

## ⚙️ Configuration

### Backend Environment Variables

```bash
# backend/.env

# Required
OPENAI_API_KEY=sk-...                    # OpenAI API key

# Optional - LangSmith Observability
LANGCHAIN_API_KEY=lsv2_...               # LangSmith API key
LANGCHAIN_TRACING_V2=true                # Enable tracing
LANGCHAIN_PROJECT=Voice-Agent-Bank-ABC   # Project name

# Voice Settings
STT_MODEL=whisper-1                      # Speech-to-text model
STT_LANGUAGE=en                          # Language code
TTS_MODEL=tts-1                          # Text-to-speech model
TTS_VOICE=alloy                          # Voice selection
```

### Frontend Environment Variables

```bash
# client/.env.local

NEXT_PUBLIC_WS_URL=ws://localhost:8000   # Backend WebSocket URL
```

### Agent Configuration

Edit `backend/data/unified_configuration.json` to customize:

- System prompts and personality
- Routing flows and tools
- Verification prompts
- Escalation strategies
- Flow-specific instructions

---

## 🔧 Development

### Running in Development Mode

```bash
# Backend (with auto-reload)
cd backend
uvicorn backend.main:app --reload

# Frontend (with hot reload)
cd client
npm run dev
```

### Testing Voice Features

1. **Microphone Access**: Browser will prompt on first visit
2. **Click the microphone button** to start a call
3. **Speak clearly** - VAD will detect speech automatically
4. **Wait 1 second after speaking** - Automatic silence detection
5. **Watch the console** - Logs show VAD events and transcripts

### Common VAD Parameters (Tunable)

```typescript
// client/app/hooks/useAudioRecorder.ts

const THRESHOLD = 40;           // Volume threshold (0-255)
const SILENCE_DURATION = 1000;  // ms silence before finalizing
const MIN_SPEECH_DURATION = 800; // Minimum speech duration
const MIN_BLOB_SIZE = 3000;     // Minimum audio size (bytes)
```

---

## 👨‍💻 Author

**Sanchuka Nirupama**
