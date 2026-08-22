"""Motor RAG que conecta la base vectorial Chroma con el System Prompt y el LLM."""

from typing import Generator, Dict, Any
from processing.vector_store import ChromaStore
from modeling.prompt_templates import build_system_prompt, format_rag_context
from modeling.llm_client import LLMClient


class CloneRAGEngine:
    """Motor conversacional para el clon digital con recuperación aumentada por datos."""

    def __init__(self, author_name: str = "Juan", llm_provider: str = None, model_name: str = None):
        self.author_name = author_name
        self.vector_store = ChromaStore()
        self.llm_client = LLMClient(provider=llm_provider, model_name=model_name)
        self.system_prompt = build_system_prompt(author_name=author_name)

    def _prepare_rag_prompt(self, question: str, n_context_chunks: int = 3, conversation_history: list = None):
        """Busca en Chroma y construye el prompt enriquecido."""
        # 1. Recuperación semántica en Chroma
        chroma_res = self.vector_store.query(query_text=question, n_results=n_context_chunks)
        
        retrieved_docs = chroma_res.get("documents", [[]])[0]
        retrieved_metas = chroma_res.get("metadatas", [[]])[0]

        # 2. Formatear el contexto RAG
        context_str = format_rag_context(retrieved_docs, retrieved_metas)

        # 3. Formatear historial si existe
        history_str = ""
        if conversation_history:
            history_lines = []
            for turn in conversation_history[-4:]:
                role = "Interlocutor" if turn.get("role") == "user" else "Clon"
                history_lines.append(f"{role}: {turn.get('content')}")
            history_str = f"### HISTORIAL DE LA CONVERSACIÓN:\n" + "\n".join(history_lines) + "\n\n"

        # 4. Construir el prompt aumentado
        augmented_user_prompt = f"""{history_str}### MEMORIAS Y FRAGMENTOS RECUPERADOS (Base de conocimiento):
{context_str}

### MENSAJE DEL INTERLOCUTOR:
{question}

Responde al interlocutor como el clon de {self.author_name}, utilizando tus memorias si son pertinentes y manteniendo siempre tu tono de voz."""

        return augmented_user_prompt, retrieved_docs, retrieved_metas

    def ask(self, question: str, n_context_chunks: int = 3, conversation_history: list = None) -> Dict[str, Any]:
        """Procesa una pregunta y retorna la respuesta completa."""
        augmented_prompt, docs, metas = self._prepare_rag_prompt(question, n_context_chunks, conversation_history)
        llm_output = self.llm_client.generate(
            system_prompt=self.system_prompt,
            user_prompt=augmented_prompt
        )

        return {
            "response": llm_output.get("text", ""),
            "retrieved_documents": docs,
            "sources_metadata": metas,
            "provider": llm_output.get("provider", "desconocido"),
            "model": llm_output.get("model", "desconocido"),
            "status": llm_output.get("status", "success")
        }

    def ask_stream(self, question: str, n_context_chunks: int = 3, conversation_history: list = None) -> Generator[Dict[str, Any], None, None]:
        """Procesa una pregunta y retorna un generador de streaming token por token."""
        augmented_prompt, docs, metas = self._prepare_rag_prompt(question, n_context_chunks, conversation_history)
        
        # 1. Emitir metadatos y documentos recuperados de inicio
        yield {
            "type": "metadata",
            "retrieved_documents": docs,
            "sources_metadata": metas,
            "provider": self.llm_client.provider,
            "model": self.llm_client.model_name
        }

        # 2. Emitir tokens en tiempo real
        for chunk in self.llm_client.generate_stream(system_prompt=self.system_prompt, user_prompt=augmented_prompt):
            yield {
                "type": "chunk",
                "content": chunk
            }

        yield {"type": "done"}
