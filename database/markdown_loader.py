"""Cargador automático de archivos Markdown (.md) hacia PostgreSQL."""

import os
import glob
import re
from datetime import datetime
from typing import List, Dict, Any

from database.engine import SessionLocal, init_db
from database.models import Source, TextEntry

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def parse_markdown_sections(content: str) -> List[str]:
    """Divide un archivo Markdown en bloques de texto independientes por encabezados o separadores.
    
    Criterios de división:
    1. Encabezados de nivel 1, 2 o 3 (# Título, ## Subtítulo, ### Tema).
    2. Separadores horizontales (--- o ***).
    """
    if not content.strip():
        return []

    # Dividir por encabezados (# , ## , ### ) o por separadores (---)
    pattern = r"(?m)^(?:#{1,3}\s+.+|---|\*\*\*)$"
    matches = list(re.finditer(pattern, content))
    
    if not matches:
        # Si no hay encabezados, todo el archivo es un único fragmento
        clean = content.strip()
        return [clean] if clean else []

    sections = []
    
    # Texto previo al primer encabezado (si existe)
    if matches[0].start() > 0:
        preamble = content[:matches[0].start()].strip()
        if preamble:
            sections.append(preamble)

    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        chunk = content[start:end].strip()
        if chunk and chunk not in ["---", "***"]:
            sections.append(chunk)

    return sections


def load_markdown_files(data_folder: str = DATA_DIR, specific_file: str = None) -> int:
    """Escanea la carpeta data/ buscando archivos .md y carga sus secciones a PostgreSQL.
    
    Args:
        data_folder: Carpeta donde buscar archivos Markdown.
        specific_file: Opcional, ruta a un archivo .md específico.
        
    Returns:
        int: Total de secciones/textos cargados.
    """
    print("=" * 60)
    print("📂 CARGADOR DE ARCHIVOS MARKDOWN A POSTGRESQL")
    print("=" * 60)
    
    # Asegurar que las tablas existan
    init_db()

    if specific_file:
        if not os.path.exists(specific_file):
            print(f"❌ Error: El archivo {specific_file} no existe.")
            return 0
        md_files = [specific_file]
    else:
        # Buscar automáticamente todos los archivos .md en data/
        search_pattern = os.path.join(data_folder, "*.md")
        md_files = glob.glob(search_pattern)

    if not md_files:
        print(f"ℹ️ No se encontraron archivos .md en la carpeta: {data_folder}")
        print("💡 Crea tus archivos Markdown (ej: data/biografia.md, data/reflexiones.md) y vuelve a ejecutar este comando.")
        return 0

    print(f"🔍 Archivos Markdown encontrados: {len(md_files)}")
    for f in md_files:
        print(f"  • {os.path.basename(f)}")

    session = SessionLocal()
    total_inserted = 0

    try:
        # Cache de fuentes existentes
        sources_cache = {s.platform: s for s in session.query(Source).all()}

        for file_path in md_files:
            file_name = os.path.basename(file_path)
            # El nombre del archivo (sin .md) se usa como plataforma/fuente
            platform = os.path.splitext(file_name)[0]

            if platform not in sources_cache:
                new_source = Source(platform=platform, raw_file_path=file_path)
                session.add(new_source)
                session.flush()
                sources_cache[platform] = new_source

            source_obj = sources_cache[platform]

            # Leer contenido del Markdown
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            sections = parse_markdown_sections(content)
            file_inserted = 0

            # Obtener contenidos ya existentes en esta fuente para no duplicar
            existing_contents = {
                t.content for t in session.query(TextEntry.content).filter(TextEntry.source_id == source_obj.id).all()
            }

            for section in sections:
                clean_section = section.strip()
                if not clean_section or clean_section in existing_contents:
                    continue

                text_entry = TextEntry(
                    source_id=source_obj.id,
                    content=clean_section,
                    created_at=datetime.utcnow(),
                    processed=False,
                    embedding_id=None
                )
                session.add(text_entry)
                existing_contents.add(clean_section)
                file_inserted += 1
                total_inserted += 1

            print(f"  ✅ '{file_name}': {file_inserted} nuevas secciones cargadas.")

        session.commit()
        print("-" * 60)
        print(f"🎉 Éxito: Se cargaron {total_inserted} textos nuevos en PostgreSQL (processed=False).")
        print("📌 Siguiente paso: Ejecuta 'python -m processing.pipeline' para procesar los textos y vectorizarlos en Chroma.")
        return total_inserted

    except Exception as e:
        session.rollback()
        print(f"❌ Error durante la carga de Markdown: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    load_markdown_files()
