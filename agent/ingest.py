import os
import fitz  # PyMuPDF
import chromadb
from chromadb.utils import embedding_functions
import hashlib
from pathlib import Path
import easyocr
import numpy as np
from PIL import Image
import io

# Setup ChromaDB
chroma_client = chromadb.PersistentClient(
    path=str(Path.home() / "immigration-agent/data/chroma")
)

# Use Ollama embeddings
embedding_fn = embedding_functions.OllamaEmbeddingFunction(
    url="http://localhost:11434",
    model_name="nomic-embed-text"
)

# Get or create collection
collection = chroma_client.get_or_create_collection(
    name="immigration_docs",
    embedding_function=embedding_fn
)

# Initialize OCR reader once (loads model into memory)
print("🔍 Loading OCR engine...")
reader = easyocr.Reader(['en'], gpu=False)
print("✅ OCR engine ready")

def extract_text_with_ocr(pdf_path: str) -> str:
    """Extract text from scanned PDF using EasyOCR."""
    doc = fitz.open(pdf_path)
    full_text = ""

    for page_num, page in enumerate(doc):
        print(f"   🔍 OCR scanning page {page_num + 1}/{len(doc)}...")

        # Render page as image at 300 DPI for good OCR quality
        mat = fitz.Matrix(300/72, 300/72)
        pix = page.get_pixmap(matrix=mat)

        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        img_array = np.array(img)

        # Run OCR
        results = reader.readtext(img_array)

        # Extract just the text
        page_text = " ".join([result[1] for result in results])
        full_text += f"\n[Page {page_num + 1}]\n{page_text}"

    doc.close()
    return full_text

def extract_text_from_pdf(pdf_path: str) -> str:
    """Try direct extraction first, fall back to OCR."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()

    if text.strip():
        print("   📝 Direct text extraction successful")
        return text
    else:
        print("   🔍 Scanned document detected — using OCR...")
        return extract_text_with_ocr(pdf_path)

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return [c for c in chunks if len(c.strip()) > 50]

def ingest_document(file_path: str, member: str = "primary"):
    """Ingest a single document into ChromaDB."""
    path = Path(file_path)
    print(f"\n📄 Reading: {path.name}")

    # Extract text (with OCR fallback)
    text = extract_text_from_pdf(file_path)

    if not text.strip():
        print(f"⚠️  Could not extract text from {path.name}")
        return

    # Chunk it
    chunks = chunk_text(text)
    print(f"   ✂️  Split into {len(chunks)} chunks")

    # Store each chunk
    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.md5(f"{path.name}_{i}".encode()).hexdigest()
        collection.upsert(
            documents=[chunk],
            metadatas=[{
                "source": path.name,
                "member": member,
                "chunk_index": i,
                "file_path": str(path)
            }],
            ids=[chunk_id]
        )

    print(f"   ✅ Stored {len(chunks)} chunks from {path.name}")

def ingest_folder(folder_path: str, member: str):
    """Ingest all PDFs in a folder."""
    folder = Path(folder_path)
    pdfs = list(folder.glob("*.pdf"))

    if not pdfs:
        print(f"📭 No PDFs found in {folder.name}/")
        return

    print(f"\n📁 Found {len(pdfs)} PDF(s) in {folder.name}/")
    for pdf in pdfs:
        ingest_document(str(pdf), member=member)

if __name__ == "__main__":
    base = Path.home() / "immigration-agent/docs"

    print("🚀 Starting document ingestion...\n")
    ingest_folder(str(base / "primary"), member="primary")
    ingest_folder(str(base / "spouse"), member="spouse")
    ingest_folder(str(base / "shared"), member="shared")

    total = collection.count()
    print(f"\n✅ Done. Total chunks in database: {total}")

def ingest_image(file_path: str, member: str = "primary"):
    """Ingest a standalone image file (JPG, PNG, TIFF)."""
    path = Path(file_path)
    print(f"\n🖼️  Reading image: {path.name}")

    img = Image.open(file_path)
    img_array = np.array(img)

    print("   🔍 Running OCR on image...")
    results = reader.readtext(img_array)
    text = " ".join([result[1] for result in results])

    if not text.strip():
        print(f"   ⚠️  No text found in {path.name}")
        return

    chunks = chunk_text(text)
    print(f"   ✂️  Split into {len(chunks)} chunks")

    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.md5(f"{path.name}_{i}".encode()).hexdigest()
        collection.upsert(
            documents=[chunk],
            metadatas=[{
                "source": path.name,
                "member": member,
                "chunk_index": i,
                "file_path": str(path)
            }],
            ids=[chunk_id]
        )

    print(f"   ✅ Stored {len(chunks)} chunks from {path.name}")

def ingest_folder(folder_path: str, member: str):
    """Ingest all PDFs and images in a folder."""
    folder = Path(folder_path)

    # Collect all supported files
    pdfs = list(folder.glob("*.pdf"))
    images = (
        list(folder.glob("*.jpg")) +
        list(folder.glob("*.jpeg")) +
        list(folder.glob("*.png")) +
        list(folder.glob("*.tiff")) +
        list(folder.glob("*.tif"))
    )

    all_files = pdfs + images

    if not all_files:
        print(f"📭 No documents found in {folder.name}/")
        return

    print(f"\n📁 Found {len(pdfs)} PDF(s) and {len(images)} image(s) in {folder.name}/")

    for pdf in pdfs:
        ingest_document(str(pdf), member=member)

    for img in images:
        ingest_image(str(img), member=member)
