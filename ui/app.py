import chainlit as cl
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.utils import embedding_functions
import ollama
import time

# ── Setup ──────────────────────────────────────────────────────
CHROMA_PATH = str(Path.home() / "PrivyAI/data/chroma")
MODEL_FAST = "qwen3:8b"
MODEL_DEEP = "qwen3:14b"

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
embedding_fn = embedding_functions.OllamaEmbeddingFunction(
    url="http://localhost:11434",
    model_name="nomic-embed-text"
)

# ── Helpers ────────────────────────────────────────────────────
STRATEGY_SIGNALS = [
    "what should i", "what do i", "next step", "what to do",
    "recommend", "strategy", "plan", "risk", "deadline",
    "expire", "priority", "urgent", "should i", "worried"
]
CALC_SIGNALS = [
    "how many", "average", "total", "how much", "salary",
    "hours", "income", "sum", "count", "how long", "calculate"
]

def classify(question: str) -> str:
    q = question.lower()
    if any(s in q for s in CALC_SIGNALS):
        return "calculation"
    if any(s in q for s in STRATEGY_SIGNALS):
        return "strategy"
    return "lookup"

def get_collection():
    try:
        return chroma_client.get_collection(
            name="immigration_docs",
            embedding_function=embedding_fn
        )
    except Exception:
        return None

def retrieve(question: str, n: int = 3):
    collection = get_collection()
    if not collection or collection.count() == 0:
        return [], []
    results = collection.query(
        query_texts=[question],
        n_results=min(n, collection.count())
    )
    chunks = results["documents"][0]
    sources = list(set(
        m["source"] for m in results["metadatas"][0]
    ))
    return chunks, sources

def build_prompt(mode: str, question: str, context: str) -> tuple[str, str]:
    if mode == "strategy":
        model = MODEL_DEEP
        prompt = f"""You are an immigration document assistant.
Analyze the documents and provide:
SITUATION — current status from documents
PRIORITY ACTIONS — numbered, most urgent first
WHAT TO WATCH — deadlines, risks, gaps
QUESTIONS FOR ATTORNEY — items needing legal clarification

Always end with: ⚠️ Not legal advice. Verify with your attorney.

Documents:
{context}

Question: {question}
Analysis:"""
    elif mode == "calculation":
        model = MODEL_FAST
        prompt = f"""/no_think
You are an immigration document assistant.
Answer calculation questions from the documents only.
If data is missing say exactly: DATA_NOT_FOUND
Be concise and show your working.

Documents:
{context}

Question: {question}
Answer:"""
    else:
        model = MODEL_FAST
        prompt = f"""/no_think
You are an immigration document assistant.
Answer from documents only. Be concise.
Cite which document your answer comes from.
If not found say: "I don't see that in your documents."

Documents:
{context}

Question: {question}
Answer:"""
    return prompt, model

# ── Chainlit handlers ──────────────────────────────────────────
@cl.on_chat_start
async def start():
    collection = get_collection()
    doc_count = collection.count() if collection else 0

    await cl.Message(
        content=f"""## PrivyAI — Your Private Document Agent

**Status:** {'✅ ' + str(doc_count) + ' document chunks loaded' if doc_count > 0 else '⚠️ No documents loaded yet'}
**Models:** Qwen3 8B (fast) · Qwen3 14B (strategy)
**Privacy:** Everything runs locally · No data leaves your Mac

---
Ask me anything about your documents.
For strategy questions I'll do a deeper analysis.
Type `status` to check document count.
""",
        author="PrivyAI"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    question = message.content.strip()

    # ── Special commands ──
    if question.lower() == "status":
        collection = get_collection()
        count = collection.count() if collection else 0
        await cl.Message(
            content=f"📊 **Status**\n- Document chunks: {count}\n- Models ready: Qwen3 8B + 14B\n- ChromaDB: {'✅ Connected' if collection else '❌ Not found'}",
            author="PrivyAI"
        ).send()
        return

    # ── Classify question ──
    mode = classify(question)
    mode_labels = {
        "lookup": "🔍 Lookup",
        "calculation": "🧮 Calculation",
        "strategy": "🧠 Strategy"
    }

    # ── Retrieve chunks ──
    n_chunks = 4 if mode == "strategy" else 3 if mode == "calculation" else 2
    chunks, sources = retrieve(question, n=n_chunks)

    if not chunks:
        await cl.Message(
            content="❌ No documents found. Please ingest some documents first using `python3 agent/ingest.py`",
            author="PrivyAI"
        ).send()
        return

    context = "\n\n".join(
        f"[Source: {s}]\n{c}"
        for s, c in zip(
            [m for m in sources for _ in range(len(chunks) // max(len(sources), 1))],
            chunks
        )
    )

    # ── Build prompt ──
    prompt, model = build_prompt(mode, question, context)

    # ── Stream response ──
    thinking_msg = f"{mode_labels[mode]} · using {model.split(':')[1].upper()} model"
    if mode == "strategy":
        thinking_msg += " · deep analysis — 30-60 sec"

    msg = cl.Message(content="", author="PrivyAI")
    await msg.send()

    full_response = ""
    think_mode = (mode == "strategy")

    stream = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": "You are PrivyAI, a private local document assistant."},
            {"role": "user", "content": prompt}
        ],
        options={
            "temperature": 0.1 if mode != "strategy" else 0.2,
            "num_predict": 2048 if mode == "strategy" else 512
        },
        think=False,
        stream=True
    )

    t_start = time.time()
    for chunk in stream:
        word = chunk["message"]["content"]
        full_response += word
        await msg.stream_token(word)

    elapsed = time.time() - t_start

    # ── Append metadata ──
    footer = f"\n\n---\n📎 **Sources:** {', '.join(sources)}\n🔧 **Mode:** {mode_labels[mode]} · ⏱️ {elapsed:.1f}s"
    await msg.stream_token(footer)
    await msg.update()

    # ── Handle data not found ──
    if "DATA_NOT_FOUND" in full_response:
        await cl.Message(
            content="💡 **Data not found in your documents.**\n\nYou can:\n1. Upload the relevant document and run ingestion again\n2. Type the information manually — just tell me what to remember",
            author="PrivyAI"
        ).send()

