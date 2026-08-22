"""Módulo de limpieza de texto para el clon digital."""

import re
import html


def clean_text(text: str) -> str:
    """Limpia ruido común de redes sociales y texto digital sin perder el tono personal.
    
    1. Desescapa entidades HTML (&amp;, &lt;, etc.).
    2. Elimina URLs completas y acortadas (t.co, http://, https://).
    3. Normaliza espacios en blanco y saltos de línea repetidos.
    4. Mantiene puntuación, mayúsculas y emojis característicos del estilo de escritura.
    """
    if not text:
        return ""

    # 1. Desescapar HTML
    cleaned = html.unescape(text)

    # 2. Eliminar URLs (ej. https://t.co/xyz, http://...)
    url_pattern = r"https?://\S+|www\.\S+"
    cleaned = re.sub(url_pattern, "", cleaned)

    # 3. Eliminar caracteres de control invisibles excepto saltos de línea estándar
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", cleaned)

    # 4. Normalizar espacios múltiples
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    # Normalizar saltos de línea excesivos (más de 2 consecutivos)
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)

    return cleaned.strip()
