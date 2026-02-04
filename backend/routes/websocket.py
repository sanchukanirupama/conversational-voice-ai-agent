import json
import asyncio
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.agent import app_graph, generate_contextual_response
from backend.config import settings
from backend.services.audio import generate_audio, transcribe_audio
from langchain_core.messages import HumanMessage

router = APIRouter()

# Audio payloads smaller than this cannot contain real speech.
MIN_AUDIO_BYTES = 1000
MAX_SILENCE_NUDGES = 2

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket Connected")
    
    # Initialize session state (mock)
    session_state = {
        "messages": [],
        "customer_id": None, 
        "is_verified": False,
        "is_call_over": False
    }

    loop = asyncio.get_running_loop()
    silence_count = 0

    try:
        # Send Greeting with Audio
        greeting_text = settings.PROMPTS.get("greeting", settings.GREETING_MESSAGE)
        
        # Generate Audio in ThreadPool
        greeting_audio = await loop.run_in_executor(None, generate_audio, greeting_text)
        
        await websocket.send_text(json.dumps({
            "type": "audio", 
            "content": greeting_text, 
            "audio": greeting_audio
        }))

        while True:
            # Wait for any message from frontend (audio or timeout signal)
            data = await websocket.receive_text()
            
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                payload = {"type": "text", "text": data}

            # Handle Timeout Signal from Frontend
            if payload.get("type") == "timeout":
                print("Frontend reported Idle Timeout.")
                silence_count += 1
                
                if silence_count > MAX_SILENCE_NUDGES:
                    print("Max silence reached. Ending call.")
                    closing_text = await generate_contextual_response(session_state["messages"], "closing_silence")
                    closing_audio = await loop.run_in_executor(None, generate_audio, closing_text)
                    await websocket.send_text(json.dumps({
                        "type": "audio",
                        "content": closing_text,
                        "audio": closing_audio
                    }))
                    # Allow playback time then close
                    await asyncio.sleep(len(closing_text) * 0.1) 
                    break
                
                # Send Nudge
                nudge_text = await generate_contextual_response(session_state["messages"], "nudge")
                nudge_audio = await loop.run_in_executor(None, generate_audio, nudge_text)
                await websocket.send_text(json.dumps({
                    "type": "audio",
                    "content": nudge_text,
                    "audio": nudge_audio
                }))
                continue

            # Reset silence count on any valid user input
            silence_count = 0
            user_text = ""
            
            if payload.get("type") == "audio":
                audio_b64 = payload.get("data", "")
                if audio_b64:
                    if "," in audio_b64:
                        audio_b64 = audio_b64.split(",")[1]
                    
                    audio_bytes = base64.b64decode(audio_b64)
                    
                    # Guard: skip payloads too small to contain speech
                    if len(audio_bytes) < MIN_AUDIO_BYTES:
                        continue
                        
                    # Run Transcribe in Thread
                    user_text = await loop.run_in_executor(None, transcribe_audio, audio_bytes)
                    print(f"Transcribed: {user_text}")
            else:
                 user_text = payload.get("text", "")
            
            if not user_text or not user_text.strip():
                continue

            print(f"User: {user_text}")
            
            # Invoke Agent
            session_state["messages"].append(HumanMessage(content=user_text))
            
            # Run graph
            final_state = await app_graph.ainvoke(
                session_state,
                config={
                    "run_name": "BankAgentConversation",
                    "tags": ["voice_agent_websocket"],
                    "metadata": {"customer_id": session_state.get("customer_id", "unknown")}
                }
            )
            
            # Get latest response
            last_msg = final_state["messages"][-1]
            response_text = last_msg.content
            
            # Update session state
            session_state = final_state
            
            print(f"Agent: {response_text}")
            
            # Fallback for silent disconnects: Ensure we say goodbye if the agent didn't
            if not response_text and final_state.get("is_call_over"):
                response_text = await generate_contextual_response(session_state["messages"], "closing_goodbye")
            
            # Send Text First (Low Latency feedback)
            if not response_text:
                if final_state.get("is_call_over"):
                    break
                continue

            # Generate and Send Audio (Combined turn)
            audio_content = await loop.run_in_executor(None, generate_audio, response_text)
            
            await websocket.send_text(json.dumps({
                "type": "audio", 
                "content": response_text, 
                "audio": audio_content
            }))

            # Check if we should end the call
            if final_state.get("is_call_over"):
                print("Call termination detected. Closing connection.")
                # Give a small buffer for the frontend to play the audio
                await asyncio.sleep(0.5) 
                break

    except WebSocketDisconnect:
        print("WebSocket Disconnected")
    finally:
        try:
            await websocket.close()
        except:
            pass
