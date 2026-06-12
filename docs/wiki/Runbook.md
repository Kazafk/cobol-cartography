# Runbook - Installation et exploitation

> Voir aussi : [[Architecture-technique]] | [[Contrats-API]] | [[Strategie-documentation]]

## Pr�requis

| Outil | Version minimale | R�le |
|-------|-----------------|------|
| VS Code | 1.85+ | IDE h�te de l'extension |
| Node.js | 20 LTS | Build extension |
| Python | 3.11+ | Backend FastAPI |
| Java JDK | 17+ | Parser COBOL |
| Gradle | 8+ (wrapper inclus) | Build parser |
| Docker + Compose | 24+ | D�ploiement stack compl�te |
| Ollama | derni�re | Mod�le IA local (Epic 6) |
| Git | 2.40+ | Cloner les sources |

---

## Mode d�veloppeur local (sans Docker)

### 1. Cloner le d�p�t

```bash
git clone https://github.com/votre-org/cobol-cartography
cd cobol-cartography
```

### 2. Builder le parser

```bash
cd parser
./gradlew build
# Produit : parser/build/libs/parser.jar
cd ..
```

### 3. D�marrer le backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
cp .env.example .env            # puis éditer .env
python -m uvicorn src.main:app --reload --port 8000
# Note : utiliser "python -m uvicorn" et non "uvicorn" directement (PATH Windows)
```

Variables `.env` requises :
```dotenv
PARSER_JAR_PATH=../parser/build/libs/parser.jar
AI_MODE=local_strict
LOG_LEVEL=INFO
# Epic 6 uniquement :
OLLAMA_BASE_URL=http://localhost:11434
```

### 4. Installer l'extension VS Code

```bash
cd extension
npm install
npm run compile          # compilation TypeScript → out/
```

Ouvrir le dossier `extension/` dans VS Code, puis appuyer sur **F5** pour lancer une fenêtre "Extension Development Host".
La configuration `extension/.vscode/launch.json` (type `extensionHost`, preLaunchTask `npm: compile`) est déjà incluse dans le dépôt.

Alternative packaging :
```bash
vsce package && code --install-extension cobol-cartography-*.vsix
```

### 5. Vérifier le health check

```bash
curl http://localhost:8000/api/health
# {"status": "ok", "version": "0.1.0"}
```

---

## Mode stack compl�te (Docker Compose)

```bash
cp deployment/.env.example deployment/.env
# �diter deployment/.env (chemin workspace COBOL, ai_mode)
docker compose -f deployment/docker-compose.yml up -d
```

Services d�marr�s :
| Service | Port | Description |
|---------|------|-------------|
| `backend` | 8000 | API FastAPI |
| `ollama` | 11434 | Mod�le IA local (Epic 6) |

Arr�t :
```bash
docker compose -f deployment/docker-compose.yml down
```

---

## Indexer Bank-of-Z

```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{
    "root": "C:/Repos/Bank-of-Z/src/base/cics",
    "copybook_paths": [
      "C:/Repos/Bank-of-Z/src/base/cics/copy",
      "C:/Repos/Bank-of-Z/src/base/ims/copy"
    ],
    "include_patterns": ["*.cbl"]
  }'

# R�ponse : {"job_id": "...", "status": "queued"}

# Suivre le statut :
curl http://localhost:8000/index/<job_id>/status
```

---

## Lancer les tests

```bash
# Parser (Java)
cd parser && ./gradlew test

# Backend (Python)
cd backend && pytest -v

# Extension (TypeScript)
cd extension && npm test
```

---

## V�rifier la configuration s�curit�

```bash
curl http://localhost:8000/capabilities
# V�rifier : "ai_mode": "local_strict"
# V�rifier : "features.ai_explanation": false (jusqu'� Epic 6)
```

---

## Troubleshooting

### Parser JAR introuvable
```
ERROR: PARSER_JAR_PATH not found
```
? V�rifier que `./gradlew build` a �t� ex�cut� et que le chemin dans `.env` est correct.

### Copybook non r�solu
```
"unresolved_copies": ["MYBOOK"]
```
? Ajouter le dossier contenant `MYBOOK.cpy` � `copybook_paths` dans la requ�te POST /index.

### Directive PROCESS non reconnue
```
parse_errors: ["Unexpected token PROCESS at line 1"]
```
? Le pr�processeur doit �tre actif. V�rifier la version du parser JAR (doit �tre ? 0.2.0).

### Ollama ne r�pond pas (Epic 6)
```
ConnectionRefusedError: [Errno 111] localhost:11434
```
? D�marrer Ollama : `ollama serve` ou `docker compose up ollama`.
? V�rifier que le mod�le est t�l�charg� : `ollama list`.