# Proyecto: Clonación Digital

## Estructura de carpetas adoptada

```
clon/
├── database/           # Capa de base de datos relacional
├── collection/         # Capa de recolección de datos
├── processing/         # Capa de procesamiento y embeddings
├── modeling/           # Capa de modelado (RAG + system prompt)
├── interface/          # Capa de interacción (desacoplada)
├── config/             # Configuración
├── data/               # Datos crudos (JSON/NDJSON)
└── tests/              # Tests
```

Mapeo con las 4 capas conceptuales: `collection/` = Recolección, `processing/` = Procesamiento, `modeling/` = Modelado, `interface/` = Interacción y Memoria. `database/` y `config/` son soporte transversal.

## Estado del proyecto

- [x] Esqueleto inicial
- [x] Esquema de base de datos
- [ ] Implementación de recolección
- [ ] Implementación de procesamiento
- [ ] Implementación de modelado
- [ ] Interfaz conversacional

## Objetivo del proyecto

Construir un modelo de IA personal que reproduzca mi forma de pensar, escribir y responder, entrenado a partir de mi huella digital (redes sociales, escritos personales, reflexiones). Objetivo inmediato: proyecto personal exploratorio. Objetivo a largo plazo (secundario, no bloqueante): que el sistema pueda funcionar como un legado conversacional para seres queridos.

Existe además una extensión futura, no prioritaria por ahora: que el clon pueda actuar como agente (redactar/enviar emails, agendar) en lugar de solo responder preguntas. **Fuera de scope por ahora — no implementar.** Se menciona solo para que el diseño de arquitectura no lo bloquee más adelante. Si en el futuro se retoma, debe diseñarse como una capa aparte (no dentro de `modeling/`, que es exclusivamente RAG + system prompt).

## Arquitectura general (4 capas)

1. **Capa de Recolección de datos**: ingesta de posts, mensajes y textos personales.
2. **Capa de Procesamiento**: limpieza de texto + generación de embeddings para búsqueda semántica.
3. **Capa de Modelado**: lógica que hace que el modelo de lenguaje responda "como yo".
4. **Capa de Interacción y Memoria**: interfaz conversacional con memoria persistente entre sesiones.

Estas capas deben quedar razonablemente desacopladas entre sí (cada una es reemplazable sin romper las demás).

## Stack técnico definido

| Componente | Herramienta | Notas |
|---|---|---|
| Lenguaje | Python | Ya tengo experiencia |
| Recolección | `requests`, `tweepy` (X), `instaloader`, APIs oficiales (Twitter/X API, Instagram Graph API, Meta Graph API) | Guardar en JSON o NDJSON |
| Base relacional | PostgreSQL (local) | Ya tengo experiencia con SQL/SQLAlchemy |
| Base vectorial | Chroma (local) | Open-source, corre local, sin costo de hosting |
| NLP / limpieza | spaCy | Buen soporte en español |
| Embeddings | `sentence-transformers` (local) | Alternativa: APIs con capa gratuita (Cohere, Google) si el hardware es limitado |
| Orquestación / RAG | LlamaIndex (preferido sobre LangChain para este caso: "preguntar sobre mis propios documentos") | |
| Interfaz | **Por definir** — ver nota abajo | |
| Modelo de lenguaje | API con capa gratuita/económica, o modelo open-source local (a definir) | |

### Nota importante — Interfaz aún no decidida

**Streamlit todavía NO está confirmado como la interfaz definitiva.** El documento original lo sugiere para un prototipo rápido (ya tengo experiencia previa con él), pero quiero mantener esta decisión abierta. Al diseñar el proyecto:

- No acoplar la lógica de negocio (capas 1-3) a Streamlit.
- Dejar la capa de interacción como un módulo separado que pueda montarse sobre Streamlit, FastAPI, u otra alternativa sin reescribir el resto del sistema.

## Enfoque de "modelado" elegido

De tres opciones posibles (RAG, fine-tuning con LoRA/QLoRA, system prompt enriquecido), la estrategia recomendada para arrancar es:

**Combinar system prompt enriquecido + RAG**, escalando el uso de RAG a medida que crece el volumen de datos personales. Fine-tuning queda descartado para esta primera etapa (mayor costo y complejidad; se reevalúa más adelante si el proyecto está validado).

**Esta decisión ya está tomada y no debería reabrirse sin pedirlo explícitamente.** Si en algún momento se sugiere fine-tuning o LoRA como alternativa "más robusta", la respuesta por defecto es no implementarlo todavía — corresponde a `modeling/` en una etapa posterior, no a esta.

## Roadmap sugerido (orden de implementación)

El orden de trabajo debe seguir esta secuencia — no avanzar a un módulo sin tener el anterior funcional:

1. **`collection/`** (semana 1-2): exportar y organizar datos personales (redes sociales, escritos) en JSON/NDJSON, guardados en `data/`.
2. **`database/`** (semana 3): modelar el esquema en PostgreSQL y cargar metadatos.
3. **`processing/`** (semana 4): generar embeddings de los textos y guardarlos en Chroma.
4. **`modeling/`** (semana 5): armar un prototipo con LlamaIndex + system prompt enriquecido.
5. **`interface/`** (semana 5-6): exponer el prototipo en una interfaz simple, sin acoplarla a los módulos anteriores.
6. **Iteración** (semana 6+): mejorar el prompt, sumar más datos, evaluar si vale la pena avanzar a fine-tuning (ver nota en sección de Modelado).

## Consideraciones de datos

- Priorizar exportación oficial de datos ("Descargar mis datos" en Instagram/X) sobre scraping.
- **Requisito de `processing/`**: filtrar o anonimizar menciones a terceros (familiares, amigos) que aparezcan en los datos de origen antes de generar embeddings, ya que no dieron consentimiento para ser parte del entrenamiento. Esto debe quedar como un paso explícito del pipeline de limpieza, no como algo opcional.

## Consideraciones de diseño para el posible uso futuro como legado digital (no bloqueante ahora, pero a tener en cuenta en el diseño)

- El sistema debería poder identificarse siempre como una simulación (no debe poder hacerse pasar por la persona real sin aclararlo).
- Dejar espacio en el modelo de datos para: metadatos de consentimiento, permisos de acceso, y un flag de "activo/retirado".
- Restringir el acceso a usuarios adultos.

Estos puntos no son una capa técnica nueva — son reglas de negocio que conviene poder implementar sobre la arquitectura ya definida (permisos en la base de datos, metadatos, flags), sin necesidad de rediseñar nada ahora.

## Resumen de decisiones abiertas para el agente

- [ ] Interfaz final: Streamlit vs. otra opción (mantener desacoplada mientras tanto).
- [ ] Proveedor de modelo de lenguaje: API con capa gratuita vs. modelo open-source local.
- [ ] Alcance inicial del agente de acciones (email, calendario) — **fuera de scope por ahora**.
