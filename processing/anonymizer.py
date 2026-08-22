"""Módulo de detección de entidades nombradas (NER) y anonimización de terceros con spaCy."""

import os
import json
import re
from typing import Tuple, List
import spacy

# Cargar configuración de privacidad
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "privacy_rules.json")


class TextAnonymizer:
    """Detecta y anonimiza nombres de terceros en textos para garantizar la privacidad."""

    def __init__(self, spacy_model: str = "es_core_news_md", config_path: str = CONFIG_PATH):
        self.config_path = config_path
        self.rules = self._load_rules()
        self.whitelist = {name.lower() for name in self.rules.get("whitelist_names", [])}
        self.aliases = {k.lower(): v for k, v in self.rules.get("known_aliases", {}).items()}
        self.placeholder = self.rules.get("generic_placeholder", "[PERSONA_TERCERO]")

        # Cargar modelo de spaCy
        try:
            self.nlp = spacy.load(spacy_model)
        except Exception:
            # Fallback en caso de que aún no esté disponible el modelo medio
            try:
                self.nlp = spacy.load("es_core_news_sm")
            except Exception:
                # Cargar modelo básico en blanco en español
                self.nlp = spacy.blank("es")

    def _load_rules(self) -> dict:
        """Carga las reglas de privacidad desde JSON."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Advertencia: no se pudo leer {self.config_path}: {e}")
        return {}

    def process(self, text: str) -> Tuple[str, List[str]]:
        """Analiza el texto, detecta personas (PER) y anonimiza a terceros.
        
        Retorna:
            - texto_anonimizado: str
            - entidades_detectadas: list[str] (nombres originales encontrados)
        """
        if not text.strip():
            return text, []

        doc = self.nlp(text)
        detected_entities = []
        entities_to_replace = []

        # Extraer entidades de personas
        for ent in doc.ents:
            if ent.label_ == "PER":
                raw_name = ent.text.strip()
                name_lower = raw_name.lower()

                # Ignorar si está en la lista de exclusión (tu propio nombre / clon)
                if name_lower in self.whitelist:
                    continue

                detected_entities.append(raw_name)
                entities_to_replace.append((ent.start_char, ent.end_char, raw_name))

        # Reemplazar entidades de atrás hacia adelante para no desfasar los índices de caracteres
        anonymized_text = text
        for start_idx, end_idx, name in sorted(entities_to_replace, key=lambda x: x[0], reverse=True):
            anonymized_text = (
                anonymized_text[:start_idx] +
                self.placeholder +
                anonymized_text[end_idx:]
            )

        return anonymized_text, detected_entities
