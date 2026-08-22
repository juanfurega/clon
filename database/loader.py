"""Script para cargar datos crudos o sintéticos desde JSON a PostgreSQL."""

import os
import json
from datetime import datetime
from dateutil import parser as date_parser

from database.engine import SessionLocal, init_db
from database.models import Source, TextEntry


def load_json_data(file_path: str = "data/sample_data.json"):
    """Carga los textos desde un archivo JSON a la base de datos PostgreSQL.
    
    1. Asegura que las tablas estén creadas (init_db).
    2. Agrupa o crea las fuentes (Source) según la plataforma.
    3. Inserta los registros de texto (TextEntry) asociados a cada fuente.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No se encontró el archivo: {file_path}")

    # Asegurar creación de tablas
    print("Verificando / creando tablas en PostgreSQL...")
    init_db()

    with open(file_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    session = SessionLocal()
    try:
        # Cache de fuentes existentes para no duplicar sources con la misma plataforma
        sources_cache = {}
        for source in session.query(Source).all():
            sources_cache[source.platform] = source

        inserted_count = 0
        for item in items:
            platform = item.get("platform", "desconocido")
            content = item.get("content", "").strip()
            if not content:
                continue

            # Obtener o crear Source
            if platform not in sources_cache:
                new_source = Source(platform=platform, raw_file_path=file_path)
                session.add(new_source)
                session.flush()  # Para obtener el new_source.id
                sources_cache[platform] = new_source
            
            source_obj = sources_cache[platform]

            # Parsear fecha
            created_at_str = item.get("created_at")
            if created_at_str:
                created_at = date_parser.parse(created_at_str)
            else:
                created_at = datetime.utcnow()

            text_entry = TextEntry(
                source_id=source_obj.id,
                content=content,
                created_at=created_at,
                processed=False,
                embedding_id=None
            )
            session.add(text_entry)
            inserted_count += 1

        session.commit()
        print(f"Éxito: Se cargaron {inserted_count} textos en PostgreSQL.")
        return inserted_count

    except Exception as e:
        session.rollback()
        print(f"Error durante la carga: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    load_json_data()
