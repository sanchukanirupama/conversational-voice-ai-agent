import asyncio
import websockets
import json
import sys

async def test_agent_flow():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # 1. Receive Greeting
        greeting = await websocket.recv()
        print(f"Received: {greeting}")
        assert "Welcome" in greeting

        # 2. Ask for Balance (Intent)
        print("Sending: Check my balance")
        await websocket.send(json.dumps({"text": "Check my balance"}))
        
        response = await websocket.recv()
        print(f"Received: {response}")
        # Agent should ask for identity
        resp_data = json.loads(response)
        content = resp_data['content']
        # Depending on LLM response, it should mention identity or ID/PIN
        # We can't strictly assert exact text, but we can check if it calls tool or asks question.
        # Since we are mocking the client, we just expect a response.
        
        # 3. Provide Identity (Verification)
        print("Sending Identity: cust_001 / 1234")
        await websocket.send(json.dumps({"text": "My ID is cust_001 and PIN is 1234"}))
        
        response = await websocket.recv()
        print(f"Received: {response}")
        
        # 4. Agent should now provide balance or say verified
        # It might take two turns depending on how the Agent is structured (Verify -> then Action)
        # But let's check if we get a subsequent response or if we need to ask again.
        # If the agent is smart, it might proceed to fulfilling the request if it remembers the context.
        # If not, we might need to ask "What is my balance?" again.
        
        # Let's send a follow up just in case:
        print("Sending: What is my balance now?")
        await websocket.send(json.dumps({"text": "What is my balance?"}))
        
        response = await websocket.recv()
        print(f"Received: {response}")
        resp_data = json.loads(response)
        assert "$2500.5" in resp_data['content'] or "2,500.50" in resp_data['content']

if __name__ == "__main__":
    try:
        asyncio.run(test_agent_flow())
        print("Verification Successful!")
    except Exception as e:
        print(f"Verification Failed: {e}")
        sys.exit(1)
