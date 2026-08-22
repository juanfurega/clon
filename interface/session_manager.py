"""Gestor de sesiones persistentes y memoria conversacional entre sesiones."""

import os
import json
import time
from typing import Dict, List, Any

SESSIONS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "chat_sessions.json")


class SessionManager:
    """Administra el historial de conversaciones y estado de sesiones de chat persistentes."""

    def __init__(self, storage_path: str = SESSIONS_FILE):
        self.storage_path = storage_path
        self._sessions: Dict[str, Dict[str, Any]] = self._load_storage()

    def _load_storage(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error cargando sesiones desde {self.storage_path}: {e}")
        return {}

    def _save_storage(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error guardando sesiones en {self.storage_path}: {e}")

    def create_session(self, title: str = "Nueva conversación") -> str:
        """Crea una nueva sesión vacía."""
        session_id = "session_" + str(int(time.time() * 1000)) + "_" + os.urandom(3).hex()
        self._sessions[session_id] = {
            "id": session_id,
            "title": title,
            "created_at": time.time(),
            "updated_at": time.time(),
            "messages": []
        }
        self._save_storage()
        return session_id

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Obtiene la lista de mensajes de una sesión."""
        session = self._sessions.get(session_id)
        if session:
            return session.get("messages", [])
        return []

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Obtiene la metadata y mensajes de una sesión."""
        return self._sessions.get(session_id, None)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """Lista todas las sesiones ordenadas por fecha de actualización descendente."""
        sessions_list = list(self._sessions.values())
        sessions_list.sort(key=lambda s: s.get("updated_at", 0), reverse=True)
        return [
            {
                "id": s["id"],
                "title": s.get("title", "Conversación"),
                "created_at": s.get("created_at"),
                "updated_at": s.get("updated_at"),
                "message_count": len(s.get("messages", []))
            }
            for s in sessions_list
        ]

    def add_message(self, session_id: str, role: str, content: str, metadata: dict = None):
        """Agrega un mensaje y actualiza el título automáticamente si es el primer mensaje."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "id": session_id,
                "title": "Conversación",
                "created_at": time.time(),
                "updated_at": time.time(),
                "messages": []
            }

        session = self._sessions[session_id]
        
        # Si es el primer mensaje del usuario, usarlo como título de la conversación
        if role == "user" and (not session["messages"] or session.get("title") == "Nueva conversación"):
            clean_title = content.strip().replace("\n", " ")
            session["title"] = (clean_title[:32] + "...") if len(clean_title) > 32 else clean_title

        entry = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        session["messages"].append(entry)
        session["updated_at"] = time.time()
        self._save_storage()

    def clear_session(self, session_id: str):
        """Limpia los mensajes de una sesión pero conserva la sesión."""
        if session_id in self._sessions:
            self._sessions[session_id]["messages"] = []
            self._sessions[session_id]["updated_at"] = time.time()
            self._save_storage()

    def delete_session(self, session_id: str):
        """Elimina por completo una sesión."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._save_storage()
