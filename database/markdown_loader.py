"""Cargador automático de archivos Markdown (.md) hacia PostgreSQL con preservación de contexto de títulos."""

import os
import glob
import re
from datetime import datetime
from typing import List

from database.engine import SessionLocal, init_db
from database.models import Source, TextEntry

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def parse_markdown_sections(content: str) -> List[str]:
    """Divide un archivo Markdown en bloques de texto independientes por encabezados o separadores,
    preservando el título principal del documento para dar contexto semántico a cada sección.
    """
    if not content.strip():
        return []

    lines = content.splitlines()
    main_title = ""
    sections = []
    current_header = ""
    current_lines = []

    for line in lines:
        stripped = line.strip()
        
        # Detectar título H1 principal
        if stripped.startswith("# ") and not main_title:
            main_title = stripped.replace("# ", "").strip()
            continue

        # Detectar encabezados de sección (## o ###) o divisores (---)
        if re.match(r"^(?:#{1,3}\s+.+|---|\*\*\*)$", stripped):
            if current_lines:
                body = "\n".join(current_lines).strip()
                if body:
                    prefix = f"[{main_title}] " if main_title else ""
                    header_str = f"{current_header}\n\n" if current_header else ""
                    full_chunk = f"{prefix}{header_str}{body}".strip()
                    sections.append(full_chunk)
                current_lines = []
            
            if not stripped.startswith("---") and not stripped.startswith("***"):
                current_header = stripped
            else:
                current_header = ""
        else:
            current_lines.append(line)

    # Última sección
    if current_lines:
        body = "\n".join(current_lines).strip()
        if body:
            prefix = f"[{main_title}] " if main_title else ""
            header_str = f"{current_header}\n\n" if current_header else ""
            full_chunk = f"{prefix}{header_str}{body}".strip()
            sections.append(full_chunk)

    return sections


def load_markdown_files(data_folder: str = DATA_DIR, specific_file: str = None) -> int:
    """Escanea la carpeta data/ buscando archivos .md y carga sus secciones a PostgreSQL."""
    print("=" * 60)
    print("[CARGADOR DE ARCHIVOS MARKDOWN A POSTGRESQL]")
    print("=" * 60)
    
    init_db()

    if specific_file:
        if not os.path.exists(specific_file):
            print(f"[!] Error: El archivo {specific_file} no existe.")
            return 0
        md_files = [specific_file]
    else:
        search_pattern = os.path.join(data_folder, "*.md")
        md_files = glob.glob(search_pattern)

    if not md_files:
        print(f"[i] No se encontraron archivos .md en la carpeta: {data_folder}")
        return 0

    print(f"[i] Archivos Markdown encontrados: {len(md_files)}")
    for f in md_files:
        print(f"  * {os.path.basename(f)}")

    session = SessionLocal()
    total_inserted = 0

    try:
        sources_cache = {s.platform: s for s in session.query(Source).all()}

        for file_path in md_files:
            file_name = os.path.basename(file_path)
            platform = os.path.splitext(file_name)[0]

            if platform not in sources_cache:
                new_source = Source(platform=platform, raw_file_path=file_path)
                session.add(new_source)
                session.flush()
                sources_cache[platform] = new_source

            source_obj = sources_cache[platform]

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            sections = parse_markdown_sections(content)
            file_inserted = 0

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

            print(f"  [OK] '{file_name}': {file_inserted} nuevas secciones cargadas.")

        session.commit()
        print("-" * 60)
        print(f"[EXITO] Se cargaron {total_inserted} textos nuevos en PostgreSQL (processed=False).")
        return total_inserted

    except Exception as e:
        session.rollback()
        print(f"[ERROR] durante la carga de Markdown: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    load_markdown_files()
