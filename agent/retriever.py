import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
import ollama

# Connect to existing ChromaDB
chroma_client = chromadb.PersistentClient(
    path=str(Path.home() / "immigration-agent/data/chroma")
)

# Same embedding function as ingest
embedding_fn = embedding_functions.OllamaEmbeddingFunction(
    url="http://localhost:11434",
    model_name="nomic-embed-text"
)

# Connect to existing collection
collection = chroma_client.get_or_create_collection(
    name="immigration_docs",
    embedding_function=embedding_fn
)

def retrieve(question: str, member: str = None, n_results: int = 3) -> list[dict]:
    """Find most relevant chunks for a question."""

    # Filter by member if specified
    where = {"member": member} if member else None

    results = collection.query(
        query_texts=[question],
        n_results=n_results,
        where=where
    )

    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        chunks.append({
            "text": doc,
            "source": results["metadatas"][0][i]["source"],
            "member": results["metadatas"][0][i]["member"],
            "chunk_index": results["metadatas"][0][i]["chunk_index"]
        })

    return chunks

def ask(question: str, member: str = None) -> dict:
    """Retrieve relevant chunks then ask Qwen3 to answer."""

    print(f"\n🔍 Searching documents...")
    chunks = retrieve(question, member=member)

    if not chunks:
        return {
            "answer": "I could not find any relevant information in your documents.",
            "sources": []
        }

    # Build context from chunks
    context = ""
    sources = []
    for i, chunk in enumerate(chunks):
        context += f"\n[Source {i+1}: {chunk['source']}]\n{chunk['text']}\n"
        if chunk["source"] not in sources:
            sources.append(chunk["source"])

    print(f"📄 Found {len(chunks)} relevant sections from: {', '.join(sources)}")
    print(f"🤔 Thinking...\n")

    # Build prompt
    prompt = f"""You are a helpful immigration document assistant.
Answer the question using ONLY the information provided in the document excerpts below.
If the answer is not in the excerpts, say "I don't see that information in your documents."
Always mention which document your answer comes from.

Document excerpts:
{context}

Question: {question}

Answer:"""

    # Ask Qwen3
    response = ollama.chat(
        model="qwen3:14b",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.1}  # low temp = factual, consistent
    )

    return {
        "answer": response["message"]["content"],
        "sources": sources
    }

if __name__ == "__main__":
    print("🤖 Immigration Document Assistant")
    print("=" * 40)
    print("Type your question. Type 'quit' to exit.\n")

    while True:
        question = input("You: ").strip()

        if not question:
            continue

        if question.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        result = ask(question)

        print(f"\n📋 Answer:\n{result['answer']}")
        print(f"\n📎 Sources: {', '.join(result['sources'])}")
        print("\n" + "=" * 40)
