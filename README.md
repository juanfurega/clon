# Cuequi — Clon Digital Conversacional & Arquitectura RAG

**Cuequi** es un sistema de Inteligencia Artificial conversacional de extremo a extremo diseñado para replicar la identidad, memoria biográfica, modismos lingüísticos y patrones de razonamiento de una persona real a partir de su huella digital y textos personales.

El proyecto implementa una arquitectura desacoplada basada en **RAG (Retrieval-Augmented Generation)**, pipelines de anonimización de privacidad con **spaCy**, indexación semántica en **ChromaDB**, orquestación multi-proveedor de LLMs de ultra-baja latencia (**Groq Cloud / Google Gemini**) y una interfaz web moderna en tiempo real mediante **Server-Sent Events (SSE)**.

## Arquitectura del Sistema

El proyecto está estructurado en 4 capas principales:

```
clon/
├── database/           # Capa 1: Persistencia relacional, modelos y loaders
├── processing/         # Capa 2: Pipeline de NLP, anonimización PII y embeddings
├── modeling/           # Capa 3: Motor RAG, cliente multi-LLM y control de idiolecto
├── interface/          # Capa 4: API REST/SSE (FastAPI) e interfaz Web reactiva
├── config/             # Reglas de privacidad y whitelists de entidades
├── data/               # Fuentes de datos, registros de chat y base vectorial
└── tests/              # Pruebas unitarias y de integración
```

---

## Stack Tecnológico

| Componente | Tecnología | Justificación y Rol Técnico |
| :--- | :--- | :--- |
| **Lenguaje** | `Python 3.11+ / 3.14` | Ecosistema estándar para ingeniería de datos y ML. |
| **Base Relacional** | `PostgreSQL` + `SQLAlchemy 2.0` | Registro de fuentes crudas, textos sin procesar, auditoría de entidades y estado de vectorización. |
| **Base Vectorial** | `ChromaDB` | Almacenamiento y consulta de embeddings para recuperación semántica por similitud. |
| **NLP & Privacidad** | `spaCy` | Named Entity Recognition (NER) para detectar y anonimizar terceros antes del embedding, auditando con reglas en `config/privacy_rules.json`. |
| **Embeddings** | `sentence-transformers` | Representación semántica de textos. |
| **LLM Inference** | `Groq Cloud` / `Google Gemini` | Inferencia acelerada por LPU para respuestas en tiempo real. Soporte configurable con fallback. |
| **API & Streaming** | `FastAPI` + `Uvicorn` + `SSE` | Arquitectura no bloqueante con streaming de tokens en tiempo real (Server-Sent Events) y gestión persistente de sesiones de chat. |
| **Frontend** | `HTML5`, `Vanilla CSS` moderno & `JS nativo` | Interfaz limpia, responsiva, modo oscuro con micro-animaciones, avatar y sin frameworks externos. |

---

## Uso

### Prerrequisitos
* **Python 3.11 o superior**
* **PostgreSQL** en ejecución (local o remoto)
* **API Key de Groq Cloud** (o Google Gemini)

### 1. Clonar el repositorio y configurar el entorno
```bash
git clone https://github.com/juanfurega/clon.git
cd clon

# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# (Linux / macOS)
# source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Descargar modelo de lenguaje en español de spaCy
python -m spacy download es_core_news_md
```

### 2. Configurar variables de entorno
Crea un archivo `.env` en la raíz del proyecto tomando como base `.env.example`:
```env
# Base de Datos PostgreSQL
DATABASE_URL=postgresql://postgres:tu_password@localhost:5432/clon_db

# Proveedor LLM (groq, gemini, openai)
LLM_PROVIDER=groq
GROQ_API_KEY=tu_api_key_de_groq
GROQ_MODEL=openai/gpt-oss-120b

# Fallback opcional a Google Gemini
GEMINI_API_KEY=tu_api_key_de_gemini
GEMINI_MODEL=gemini-3.6-flash
```

### 3. Ingesta y vectorización de datos
El cargador escanea automáticamente cualquier archivo `.md` ubicado dentro de `data/`:
```bash
# Paso A: Cargar las secciones a PostgreSQL
python -m database.markdown_loader

# Paso B: Limpiar con spaCy, anonimizar y generar embeddings en ChromaDB
python -m processing.pipeline
```

### 4. Iniciar la aplicación
```bash
python run_app.py
```

La interfaz estará en **`http://localhost:8000`**.

---

## Estructura del Proyecto

```text
├── config/
│   └── privacy_rules.json         # Reglas de anonimización NER y whitelist
├── data/
│   ├── *.md                       # Archivos temáticos (identidad, valores, chats)
│   └── chroma/                    # Directorio persistente de vectores ChromaDB
├── database/
│   ├── engine.py                  # Conexión SQLAlchemy y SessionLocal
│   ├── models.py                  # Esquema relacional (Source, TextEntry, MentionedEntity)
│   ├── loader.py                  # Cargador de datos crudos JSON
│   └── markdown_loader.py         # Parser y cargador de Markdown por secciones
├── interface/
│   ├── api.py                     # Endpoints FastAPI, Streaming SSE y estadísticas
│   ├── session_manager.py         # Manejador multi-sesión con persistencia en JSON
│   └── static/                    # Frontend nativo (HTML, CSS, JS)
├── modeling/
│   ├── llm_client.py              # Cliente unificado multi-LLM (Groq, Gemini, OpenAI)
│   ├── prompt_templates.py        # System prompt enriquecido + Few-Shot conversacional
│   └── rag_engine.py              # Orquestador RAG (Chroma + Context Formatter + LLM)
├── processing/
│   ├── cleaner.py                 # Sanitización y normalización de texto
│   ├── anonymizer.py              # Pipeline spaCy NER con preservación de lista blanca
│   ├── vector_store.py            # Wrapper de ChromaDB y Sentence-Transformers
│   └── pipeline.py                # Pipeline end-to-end de procesamiento por lotes
├── run_app.py                     # Entrypoint de arranque con auto-apertura de navegador
├── iniciar_cuequi.bat              # Acceso directo de ejecución en Windows
└── requirements.txt               # Dependencias de producción
```

---

## Roadmap Técnico

- [x] Arquitectura RAG desacoplada con Chroma y PostgreSQL.
- [x] Pipeline de anonimización NER con listas blancas configurables.
- [x] Streaming de tokens en tiempo real con SSE en FastAPI.
- [x] In-Context Few-Shot learning para replicación de idiolecto.
- [ ] **Tool Calling / Function Calling:** Extender la capa de modelado con agentes capaces de ejecutar acciones (consultar calendarios, enviar correos, interactuar con APIs externas).
- [ ] **Despliegue Containerizado:** Dockerfile y `docker-compose.yml` para orquestación de app, PostgreSQL y ChromaDB en un entorno de producción.

---

## Notas de desarrollo

Este proyecto fue desarrollado con asistencia de herramientas de generación de código basadas en IA (Codex & Cursor), utilizadas como acelerador dentro de un proceso de diseño e iteración propio: definición del modelo de datos, revisión de la lógica y validación funcional.
