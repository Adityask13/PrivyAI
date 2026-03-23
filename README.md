# PrivyAI

> Your personal AI agent. Local. Private. Fully yours.

PrivyAI is a privacy-first AI agent for managing sensitive personal documents and cases — starting with immigration. Everything runs on your own machine. No cloud. No subscriptions. No data ever leaves your device.

Built in public, one hour a day.

---

## Why PrivyAI

Every AI tool today asks you to upload your most sensitive documents to someone else's server. For immigration cases — I-797 notices, I-20s, passports, employment records — that's not acceptable.

PrivyAI flips the model. The AI comes to your data. Not the other way around.

- **Local LLM** — Qwen3 runs entirely on your device via Ollama
- **Local vector search** — ChromaDB stores your document embeddings on disk
- **Local memory** — SQLite keeps your conversation history and structured records
- **No API keys** — no OpenAI, no Anthropic, no external services required
- **No Docker** — runs as a simple Python app, one command to start

---

## What it does today

### Document ingestion — any format
Drop a document into the `docs/` folder. PrivyAI handles the rest.

```
docs/
├── primary/      ← your documents
├── spouse/       ← spouse documents (coming soon)
└── shared/       ← joint documents
```

Supported formats:
- PDF with text layer — direct extraction via PyMuPDF
- Scanned PDF — automatic OCR via EasyOCR
- JPG, PNG, TIFF — phone photos of documents, fully supported
- Auto-detects which method to use per page

### Semantic search
Ask questions in plain English. PrivyAI finds the relevant sections across all your documents using vector embeddings — not keyword search. It understands meaning, not just words.

### Local AI reasoning
Powered by Qwen3 14B (or 8B for speed) via Ollama. Fully GPU-accelerated on Apple Silicon. No internet required for inference.

**Measured performance on M1 Pro 36GB:**
```
ChromaDB search:     0.71s
Model warm response: 0.47s
Cold start:          2.92s
```

Keeping the model warm (via `--keepalive`) gives near-instant responses on consumer hardware.

---

## What is being built next

PrivyAI is being built incrementally, one day at a time. Here is the current roadmap:

| Day | Feature | Status |
|-----|---------|--------|
| Day 1 | Ollama + Qwen3 14B running, project scaffold | ✅ Done |
| Day 2 | Document ingestion — PDF + OCR + image support | ✅ Done |
| Day 3 | Chainlit UI — browser chat interface | 🔲 Next |
| Day 4 | Structured data extractor — LLM pulls facts into SQLite | 🔲 Planned |
| Day 5 | Question router — lookup / deep / strategy / calculation modes | 🔲 Planned |
| Day 6 | PII filter — two-layer privacy protection for web queries | 🔲 Planned |
| Day 7 | Web search — hypothetical questions against trusted sources | 🔲 Planned |
| Day 8 | Mobile access — Tailscale + PWA for iPhone | 🔲 Planned |
| Day 9 | Accuracy test suite — regression testing framework | 🔲 Planned |
| Day 10 | Family profiles — multi-member case management | 🔲 Planned |

Follow the build: updates posted daily on LinkedIn and Medium.

---

## Tech stack

| Layer | Tool | Why |
|-------|------|-----|
| LLM runtime | Ollama | Native Apple Silicon GPU, no Docker needed |
| Reasoning model | Qwen3 14B | Best quality for 36GB unified RAM |
| Fast model | Qwen3 8B | Sub-second responses for simple queries |
| Embedding model | nomic-embed-text | Fast, accurate, 274MB |
| Vector store | ChromaDB | Embedded, file-based, no server needed |
| Structured data | SQLite | Single file, zero config |
| Document parsing | PyMuPDF | Text PDF extraction |
| OCR | EasyOCR | Scanned docs and phone photos |
| UI | Chainlit | Python-native, browser-based (coming Day 3) |
| API | FastAPI | Mobile and future agent access |

**Intentionally NOT in the stack:**
- No LangChain — LlamaIndex handles RAG natively at this scale
- No Mem0 — raw SQLite is simpler and sufficient for personal use
- No Docker for Ollama — kills GPU acceleration on Mac
- No cloud of any kind

---

## Getting started

### Requirements
- macOS with Apple Silicon (M1 or later) — Windows/Linux support coming
- Python 3.10+
- ~15GB free disk space (model + dependencies)
- [Ollama](https://ollama.com) installed

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/PrivyAI.git
cd PrivyAI

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Pull the models
ollama pull qwen3:14b
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

### Ingest your first document

```bash
# Drop a PDF into docs/primary/
cp your-document.pdf docs/primary/

# Run ingestion
python3 agent/ingest.py
```

### Ask a question

```bash
python3 agent/retriever.py
```

```
You: When was this document filed?
```

---

## Project structure

```
PrivyAI/
│
├── agent/
│   ├── ingest.py        # document ingestion — PDF, OCR, images
│   └── retriever.py     # question answering against documents
│
├── docs/
│   ├── primary/         # your documents (gitignored)
│   ├── spouse/          # spouse documents (gitignored)
│   └── shared/          # joint documents (gitignored)
│
├── data/                # ChromaDB + SQLite (gitignored)
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Privacy model

PrivyAI is designed around a simple rule: **your data never leaves your machine.**

- Documents are stored locally in `docs/`
- Vector embeddings are stored locally in `data/chroma/`
- Conversation memory is stored locally in `data/memory.db`
- LLM inference runs locally via Ollama
- Web search (coming Day 7) strips all PII before any query leaves the device

---

## Hardware tested on

| Device | RAM | Model | Warm response |
|--------|-----|-------|--------------|
| MacBook Pro M1 Pro | 36GB | Qwen3 8B | ~0.47s |
| MacBook Pro M1 Pro | 36GB | Qwen3 14B | ~1.0s |

Target devices for future testing:
- Mac Mini M4 Pro (dedicated always-on server)
- Orange Pi 5 Plus (portable edge device)
- Windows 11 with RTX GPU

---

## Contributing

PrivyAI is being built in public. Contributions welcome at any stage.

**Most needed right now:**
- Windows 11 setup guide and testing
- Linux ARM setup guide (Orange Pi, Raspberry Pi alternatives)
- Additional document type support
- Bug reports from real-world document ingestion

Open an issue or submit a PR. All experience levels welcome.

---

## License

Apache 2.0 — use it, modify it, build on it. Attribution appreciated.

---

## Follow the build

This project is being built one hour a day and documented publicly.

- LinkedIn: daily build updates
- Medium: deep technical articles on each component

*Built with curiosity. Shared with the community.*
