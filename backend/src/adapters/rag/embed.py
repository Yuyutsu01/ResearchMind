import os
import glob
import re
from sentence_transformers import SentenceTransformer

# Load embedding model (Bi-Encoder)
_embedder = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_text_semantic(text: str, source: str = "unknown", task_id: int = 0) -> list[dict]:
    """
    Splits text semantically based on paragraphs and sentence boundaries.
    Each chunk is returned as a dictionary containing text and metadata.
    """
    # Normalize newlines
    text = text.replace("\r\n", "\n")
    paragraphs = text.split("\n\n")
    chunks = []
    
    current_chunk = []
    current_length = 0
    max_chunk_char_len = 800  # Target size for chunks
    overlap_sentences = 2
    
    # Regex split on sentence endings (. ? !) preserving spacing
    sentence_end = re.compile(r'(?<=[.!?])\s+')
    
    for para in paragraphs:
        if not para.strip():
            continue
        sentences = sentence_end.split(para.strip())
        for sent in sentences:
            if not sent.strip():
                continue
            sent_len = len(sent)
            
            # If a single sentence is extremely long, split it by characters
            if sent_len > max_chunk_char_len:
                if current_chunk:
                    chunk_text_str = " ".join(current_chunk)
                    chunks.append({
                        "text": chunk_text_str,
                        "metadata": {"source": source, "task_id": task_id}
                    })
                    current_chunk = []
                    current_length = 0
                
                # Split large sentence by character limits
                for idx in range(0, sent_len, max_chunk_char_len):
                    chunks.append({
                        "text": sent[idx:idx + max_chunk_char_len],
                        "metadata": {"source": source, "task_id": task_id}
                    })
                continue

            if current_length + sent_len > max_chunk_char_len:
                if current_chunk:
                    chunk_text_str = " ".join(current_chunk)
                    chunks.append({
                        "text": chunk_text_str,
                        "metadata": {"source": source, "task_id": task_id}
                    })
                # Retain overlap sentences
                current_chunk = current_chunk[-overlap_sentences:] if len(current_chunk) >= overlap_sentences else current_chunk
                current_length = sum(len(s) for s in current_chunk) + len(current_chunk)
            
            current_chunk.append(sent)
            current_length += sent_len + 1  # Add 1 for the joining space
            
    if current_chunk:
        chunk_text_str = " ".join(current_chunk)
        chunks.append({
            "text": chunk_text_str,
            "metadata": {"source": source, "task_id": task_id}
        })
        
    return chunks

def load_documents_semantic(docs_dir: str = "rag/documents", task_id: int = 0) -> list[dict]:
    """Load and chunk all .txt files from the specified folder."""
    all_chunks = []
    for filepath in glob.glob(os.path.join(docs_dir, "*.txt")):
        try:
            filename = os.path.basename(filepath)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                all_chunks.extend(chunk_text_semantic(content, source=filename, task_id=task_id))
        except Exception as e:
            print(f"[RAG Embed] Failed to read {filepath}: {e}")
    return all_chunks

def get_embedding(text: str):
    """Return embedding vector for a given text."""
    return _embedder.encode([text])[0]
