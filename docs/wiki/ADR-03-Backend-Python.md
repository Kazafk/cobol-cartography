# ADR-03 - Backend : Python / FastAPI

> Registre : [[ADR-Register]]

**Statut** : Propos�
**Date** : � compl�ter
**D�cideurs** : `architect-reviewer`, `fastapi-developer`

## Contexte

Le backend orchestre le pipeline d'indexation (invoque le parser Java), g�re le graphe SQLite, sert les API REST pour l'extension VS Code, et h�bergera la couche RAG/IA.

## Options �valu�es

| Option | Avantages | Inconv�nients |
|--------|-----------|---------------|
| **Python / FastAPI** | Async natif, Pydantic v2, excellent pour RAG (LangChain, LlamaIndex), ecosystem IA | Moins performant que Go/Rust pour le CPU-bound |
| Node.js / Express | M�me runtime que l'extension TS | �cosyst�me IA Python bien plus mature |
| Java Spring Boot | M�me runtime que le parser | Surcharge pour un backend l�ger, d�marrage lent |
| Go | Tr�s performant | Peu de librairies IA natives, effort d'int�gration RAG |

## D�cision

**Python 3.11+ / FastAPI** avec **Pydantic v2** et **uvicorn** (ASGI).
Le parser Java est appel� comme subprocess via `asyncio.create_subprocess_exec`.

## Cons�quences

- `fastapi-developer` est l'agent principal du r�pertoire `backend/`.
- La communication extension ? backend est HTTP REST (WebSocket pour streaming Epic 6).
- Le parser Java produit son JSON sur stdout - le backend le lit via le subprocess.
- D�pendances Python minimales au MVP : fastapi, uvicorn, pydantic, structlog, aiosqlite.
- D�pendances Epic 6 : httpx (appel Ollama), llama-index ou �quivalent.

## Validation

- [ ] `/health` et `/capabilities` r�pondent en < 50ms
- [ ] Pipeline d'indexation Bank-of-Z complet en < 30s