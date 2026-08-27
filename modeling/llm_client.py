"""Cliente unificado para interactuar con proveedores de LLM (Groq, Gemini, OpenAI, Ollama)."""

import os
from typing import Generator, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """Cliente unificado y de alto rendimiento para generación con LLMs y Streaming."""

    def __init__(self, provider: str = None, model_name: str = None):
        # Leer credenciales desde .env
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # Detección automática
        if provider:
            self.provider = provider.lower()
        elif self.groq_key:
            self.provider = "groq"
        elif self.gemini_key:
            self.provider = "gemini"
        elif self.openai_key:
            self.provider = "openai"
        else:
            self.provider = "none"

        self.model_name = model_name or self._default_model_for_provider()

    def _default_model_for_provider(self) -> str:
        if self.provider == "groq":
            return os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        elif self.provider == "gemini":
            return os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        elif self.provider == "openai":
            return os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        elif self.provider == "ollama":
            return os.getenv("OLLAMA_MODEL", "llama3")
        return "mock"

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> Dict[str, Any]:
        """Genera una respuesta completa con baja temperatura para evitar alucinaciones."""
        if self.provider == "groq" and self.groq_key:
            return self._generate_groq(system_prompt, user_prompt, temperature)
        elif self.provider == "gemini" and self.gemini_key:
            return self._generate_gemini(system_prompt, user_prompt, temperature)
        elif self.provider == "openai" and self.openai_key:
            return self._generate_openai(system_prompt, user_prompt, temperature)
        elif self.provider == "ollama":
            return self._generate_ollama(system_prompt, user_prompt, temperature)
        else:
            return self._generate_mock(system_prompt, user_prompt)

    def generate_stream(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> Generator[str, None, None]:
        """Genera la respuesta token por token en tiempo real (Streaming) con baja temperatura."""
        if self.provider == "groq" and self.groq_key:
            from groq import Groq
            client = Groq(api_key=self.groq_key)
            stream = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                stream=True
            )
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content.replace("¿", "")

        elif self.provider == "gemini" and self.gemini_key:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.gemini_key)
            response_stream = client.models.generate_content_stream(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature
                )
            )
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text.replace("¿", "")

        elif self.provider == "openai" and self.openai_key:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_key)
            stream = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                stream=True
            )
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content.replace("¿", "")
        else:
            mock = self._generate_mock(system_prompt, user_prompt)
            yield mock["text"]

    def _generate_groq(self, system_prompt: str, user_prompt: str, temperature: float) -> Dict[str, Any]:
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)
            completion = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )
            raw_text = completion.choices[0].message.content or ""
            return {
                "text": raw_text.replace("¿", ""),
                "provider": "Groq Cloud",
                "model": self.model_name,
                "status": "success"
            }
        except Exception as e:
            return {
                "text": f"[Error comunicando con Groq API: {e}]",
                "provider": "Groq Cloud",
                "model": self.model_name,
                "status": "error"
            }

    def _generate_gemini(self, system_prompt: str, user_prompt: str, temperature: float) -> Dict[str, Any]:
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=self.gemini_key)
            response = client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature
                )
            )
            raw_text = response.text or ""
            return {
                "text": raw_text.replace("¿", ""),
                "provider": "Google Gemini",
                "model": self.model_name,
                "status": "success"
            }
        except Exception as e:
            return {
                "text": f"[Error comunicando con Gemini API: {e}]",
                "provider": "Google Gemini",
                "model": self.model_name,
                "status": "error"
            }

    def _generate_openai(self, system_prompt: str, user_prompt: str, temperature: float) -> Dict[str, Any]:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_key)
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )
            raw_text = response.choices[0].message.content or ""
            return {
                "text": raw_text.replace("¿", ""),
                "provider": "OpenAI",
                "model": self.model_name,
                "status": "success"
            }
        except Exception as e:
            return {
                "text": f"[Error comunicando con OpenAI API: {e}]",
                "provider": "OpenAI",
                "model": self.model_name,
                "status": "error"
            }

    def _generate_ollama(self, system_prompt: str, user_prompt: str, temperature: float) -> Dict[str, Any]:
        try:
            import requests
            url = f"{self.ollama_base_url}/api/chat"
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "options": {"temperature": temperature},
                "stream": False
            }
            res = requests.post(url, json=payload, timeout=60)
            data = res.json()
            raw_text = data.get("message", {}).get("content", "") or ""
            return {
                "text": raw_text.replace("¿", ""),
                "provider": "Ollama (Local)",
                "model": self.model_name,
                "status": "success"
            }
        except Exception as e:
            return {
                "text": f"[Error conectando a Ollama: {e}]",
                "provider": "Ollama (Local)",
                "model": self.model_name,
                "status": "error"
            }

    def _generate_mock(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        return {
            "text": "hola ;) estoy funcionando en modo simulación local sin API configurada.",
            "provider": "Mock",
            "model": "local-fallback",
            "status": "mock"
        }
