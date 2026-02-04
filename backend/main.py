from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import base64

from backend.agent import app_graph
from backend.config import settings
from backend.services.audio import generate_audio, transcribe_audio
from langchain_core.messages import HumanMessage

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audio payloads smaller than this cannot contain real speech.
# Checked before hitting Whisper to avoid hallucinations on noise/silence fragments.
MIN_AUDIO_BYTES = 1000


@app.get("/")
def home():
    return {"status": "Voice AI Backend Running"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket Connected")

    session_state = {
        "messages": [],
        "customer_id": None,
        "is_verified": False,
    }

    loop = asyncio.get_running_loop()

    try:
        # Send greeting with TTS audio
        greeting_text = settings.GREETING_MESSAGE
        greeting_audio = await loop.run_in_executor(None, generate_audio, greeting_text)

        await websocket.send_text(json.dumps({
            "type": "audio",
            "content": greeting_text,
            "audio": greeting_audio,
        }))

        while True:
            data = await websocket.receive_text()

            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                payload = {"type": "text", "text": data}

            user_text = ""

            if payload.get("type") == "audio":
                audio_b64 = payload.get("data", "")
                if audio_b64:
                    if "," in audio_b64:
                        audio_b64 = audio_b64.split(",")[1]

                    audio_bytes = base64.b64decode(audio_b64)

                    # Guard: skip payloads too small to contain speech
                    if len(audio_bytes) < MIN_AUDIO_BYTES:
                        print(f"Skipped audio: only {len(audio_bytes)} bytes")
                        continue

                    user_text = await loop.run_in_executor(None, transcribe_audio, audio_bytes)
                    print(f"Transcribed: {user_text}")
            else:
                user_text = payload.get("text", "")

            if not user_text:
                continue

            print(f"User: {user_text}")

            # Invoke the LangGraph agent
            session_state["messages"].append(HumanMessage(content=user_text))
            final_state = await app_graph.ainvoke(session_state)

            last_msg = final_state["messages"][-1]
            response_text = last_msg.content
            session_state = final_state

            print(f"Agent: {response_text}")

            if not response_text:
                continue

            # Generate TTS audio and send as a single message.
            # One message per turn keeps the frontend transcript clean and
            # lets the client release its response-pending lock reliably.
            audio_content = await loop.run_in_executor(None, generate_audio, response_text)

            await websocket.send_text(json.dumps({
                "type": "audio",
                "content": response_text,
                "audio": audio_content,
            }))

    except WebSocketDisconnect:
        print("WebSocket Disconnected")
