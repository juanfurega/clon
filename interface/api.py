"""Servidor web y API REST para la interfaz conversacional del clon digital (Cuequi)."""

import os
import json
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from modeling.rag_engine import CloneRAGEngine
from interface.session_manager import SessionManager
from database.engine import SessionLocal
from database.models import TextEntry

app = FastAPI(title="Cuequi — Clon Digital API", version="1.0.0")

# Inicializar motor RAG con nombre de clon Cuequi
rag_engine = CloneRAGEngine(author_name="Juan")
session_manager = SessionManager()

# Directorio estático y uploads
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ClearRequest(BaseModel):
    session_id: str


@app.get("/")
async def serve_index():
    """Sirve la interfaz web principal."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Cuequi API activa. Abre /static/index.html"}


# ================= GESTIÓN DE SESIONES / HISTORIAL =================

@app.get("/api/sessions")
async def list_sessions():
    """Obtiene la lista de todas las conversaciones guardadas."""
    return session_manager.list_sessions()


@app.post("/api/sessions/new")
async def create_new_session():
    """Crea una nueva conversación."""
    new_id = session_manager.create_session()
    return {"session_id": new_id, "title": "Nueva conversación"}


@app.get("/api/sessions/{session_id}")
async def get_session_details(session_id: str):
    """Obtiene el historial completo de una conversación."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return session


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Elimina una conversación."""
    session_manager.delete_session(session_id)
    return {"status": "deleted", "session_id": session_id}


# ================= CHAT Y STREAMING =================

@app.post("/api/chat/stream")
async def chat_stream_endpoint(req: ChatRequest):
    """Procesa un mensaje y transmite la respuesta token por token."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    history = session_manager.get_history(req.session_id)

    def event_generator():
        full_response = []
        for event in rag_engine.ask_stream(question=req.message, conversation_history=history):
            if event["type"] == "chunk":
                full_response.append(event["content"])
            yield f"data: {json.dumps(event)}\n\n"
        
        complete_text = "".join(full_response)
        session_manager.add_message(req.session_id, role="user", content=req.message)
        session_manager.add_message(
            req.session_id,
            role="assistant",
            content=complete_text,
            metadata={"model": rag_engine.llm_client.model_name}
        )

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/avatar/upload")
async def upload_avatar(file: UploadFile = File(...)):
    """Permite subir una foto de perfil personalizada para Cuequi."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen válida.")

    avatar_path = os.path.join(UPLOADS_DIR, "avatar.png")
    with open(avatar_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"status": "success", "avatar_url": "/static/uploads/avatar.png"}


@app.get("/api/avatar")
async def get_avatar_status():
    """Verifica si existe un avatar cargado."""
    avatar_path = os.path.join(UPLOADS_DIR, "avatar.png")
    exists = os.path.exists(avatar_path)
    return {
        "exists": exists,
        "avatar_url": "/static/uploads/avatar.png" if exists else None
    }


@app.get("/api/stats")
async def stats_endpoint():
    """Retorna métricas del sistema."""
    total_texts = 0
    try:
        db = SessionLocal()
        total_texts = db.query(TextEntry).count()
        db.close()
    except Exception:
        pass

    total_vectors = rag_engine.vector_store.count()
    active_model = rag_engine.llm_client.provider.upper()

    return {
        "total_texts": total_texts,
        "total_vectors": total_vectors,
        "active_model": active_model
    }


@app.post("/api/clear")
async def clear_endpoint(req: ClearRequest):
    """Limpia el historial de una sesión."""
    session_manager.clear_session(req.session_id)
    return {"status": "cleared", "session_id": req.session_id}


if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor de Cuequi en http://localhost:8000 ...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
