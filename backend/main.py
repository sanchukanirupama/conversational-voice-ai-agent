from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.services.langsmith_config import init_langsmith
from backend.routes import websocket

# Initialize Services
init_langsmith()

app = FastAPI(title="Bank ABC Voice AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routes
app.include_router(websocket.router)

@app.get("/")
def home():
    return {"status": "Voice AI Backend Running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
