"""Pipeline principal de procesamiento de textos, privacidad y embeddings."""

from database.engine import SessionLocal
from database.models import TextEntry, MentionedEntity, Source
from processing.cleaner import clean_text
from processing.anonymizer import TextAnonymizer
from processing.vector_store import ChromaStore


def run_processing_pipeline():
    """Ejecuta el pipeline completo de procesamiento para todos los textos pendientes en PostgreSQL.
    
    1. Obtiene los registros con processed == False.
    2. Limpia el texto (URLs, artefactos HTML, espacios).
    3. Detecta entidades con spaCy y anonimiza nombres de terceros según las reglas de privacidad.
    4. Guarda las entidades detectadas en la tabla mentioned_entities.
    5. Genera embeddings y los almacena en Chroma.
    6. Actualiza TextEntry con processed = True y el ID del vector en Chroma.
    """
    print("Iniciando pipeline de procesamiento y vectorización...")
    
    session = SessionLocal()
    try:
        # Obtener textos no procesados
        pending_texts = session.query(TextEntry).filter(TextEntry.processed == False).all()
        if not pending_texts:
            print("No hay textos pendientes de procesamiento.")
            return

        print(f"Se encontraron {len(pending_texts)} textos pendientes de procesar.")

        # Inicializar componentes
        anonymizer = TextAnonymizer()
        vector_store = ChromaStore()

        chroma_ids = []
        chroma_docs = []
        chroma_metadatas = []
        
        processed_count = 0
        entities_found_count = 0

        for entry in pending_texts:
            # 1. Limpieza básica
            cleaned_text = clean_text(entry.content)

            # 2. Detección de entidades y anonimización de terceros
            anonymized_text, detected_entities = anonymizer.process(cleaned_text)

            # 3. Registrar entidades detectadas en la base de datos
            for entity_name in detected_entities:
                mention = MentionedEntity(
                    text_id=entry.id,
                    entity_name=entity_name,
                    anonymized=True
                )
                session.add(mention)
                entities_found_count += 1

            # 4. Preparar datos para Chroma
            doc_id = f"text_{entry.id}"
            platform_name = entry.source.platform if entry.source else "desconocido"
            created_at_iso = entry.created_at.isoformat() if entry.created_at else ""

            chroma_ids.append(doc_id)
            chroma_docs.append(anonymized_text)
            chroma_metadatas.append({
                "text_id": entry.id,
                "platform": platform_name,
                "created_at": created_at_iso,
                "has_anonymization": len(detected_entities) > 0
            })

            # 5. Actualizar registro en PostgreSQL
            entry.processed = True
            entry.embedding_id = doc_id
            processed_count += 1

        # 6. Almacenar en Chroma
        print(f"Generando embeddings y guardando en Chroma...")
        vector_store.add_documents(
            ids=chroma_ids,
            documents=chroma_docs,
            metadatas=chroma_metadatas
        )

        # 7. Confirmar cambios en PostgreSQL
        session.commit()

        print("--- Resumen del Pipeline ---")
        print(f"• Textos procesados y vectorizados: {processed_count}")
        print(f"• Entidades de terceros detectadas y anonimizadas: {entities_found_count}")
        print(f"• Total de vectores en Chroma: {vector_store.count()}")
        print("Procesamiento completado con éxito.")

    except Exception as e:
        session.rollback()
        print(f"Error durante el procesamiento: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_processing_pipeline()
