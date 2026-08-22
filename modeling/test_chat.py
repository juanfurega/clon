"""Script interactivo en consola para probar el clon digital con RAG."""

import sys
from modeling.rag_engine import CloneRAGEngine


def main():
    print("=" * 60)
    print("🤖 INICIANDO CLON DIGITAL PERSONAL (MODO CONSOLA)")
    print("=" * 60)
    
    engine = CloneRAGEngine(author_name="Juan")
    history = []

    print(f"• Proveedor de LLM detectado: {engine.llm_client.provider.upper()} ({engine.llm_client.model_name})")
    print(f"• Vectores disponibles en Chroma: {engine.vector_store.count()}")
    print("• Escribe tu mensaje o 'salir' para terminar.\n")

    while True:
        try:
            user_input = input("Tú: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["salir", "exit", "quit"]:
                print("Hasta luego!")
                break

            print("\n🔍 Buscando memorias y generando respuesta...")
            result = engine.ask(question=user_input, conversation_history=history)

            print(f"\n🧠 Clon ({result['model']}):")
            print(result["response"])

            # Mostrar fuentes recuperadas para depuración y transparencia
            print("\n📚 [Memorias recuperadas de Chroma]:")
            for i, doc in enumerate(result["retrieved_documents"], 1):
                meta = result["sources_metadata"][i - 1] if i - 1 < len(result["sources_metadata"]) else {}
                platform = meta.get("platform", "nota")
                print(f"  [{i}] ({platform}): {doc[:90]}...")
            print("-" * 60 + "\n")

            # Guardar en historial
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": result["response"]})

        except KeyboardInterrupt:
            print("\nSesión finalizada.")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
