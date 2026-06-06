import faiss
import numpy as np
import re
import math
from collections import Counter
from sentence_transformers import SentenceTransformer
from rag.embed import chunk_text_semantic, load_documents_semantic, get_embedding, _embedder

_index = None
_documents = []  # List of dict: {"text": str, "metadata": dict}
_bm25 = None

class SimpleBM25:
    """Self-contained, dependency-free BM25 implementation."""
    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        tokenized_corpus = [self._tokenize(doc) for doc in corpus]
        self.avg_doc_len = sum(len(doc) for doc in tokenized_corpus) / self.corpus_size if self.corpus_size > 0 else 0
        self.doc_freqs = []
        self.idf = {}
        self.doc_lens = [len(doc) for doc in tokenized_corpus]
        
        nd = {}
        for doc in tokenized_corpus:
            self.doc_freqs.append(Counter(doc))
            for word in set(doc):
                nd[word] = nd.get(word, 0) + 1
                
        for word, freq in nd.items():
            self.idf[word] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)
            
    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r'\w+', text.lower())
        
    def get_scores(self, query: str) -> list[float]:
        query_tokens = self._tokenize(query)
        scores = [0.0] * self.corpus_size
        for i in range(self.corpus_size):
            doc_freq = self.doc_freqs[i]
            doc_len = self.doc_lens[i]
            score = 0.0
            for word in query_tokens:
                if word in doc_freq:
                    freq = doc_freq[word]
                    numerator = self.idf.get(word, 0.0) * freq * (self.k1 + 1)
                    denominator = freq + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
                    score += numerator / denominator
            scores[i] = score
        return scores

def init_retriever(docs_dir: str = "rag/documents", task_id: int = 0):
    """Initialize FAISS index and BM25 index from local text documents."""
    global _index, _documents, _bm25
    
    # Load chunks with metadata
    _documents = load_documents_semantic(docs_dir, task_id)
    if not _documents:
        print("[RAG Retrieve] No documents found in rag/documents.")
        return
        
    # Generate embeddings
    texts = [doc["text"] for doc in _documents]
    embeddings = _embedder.encode(texts)
    embedding_dim = embeddings.shape[1]
    
    # Init FAISS with Cosine Similarity (Flat Inner Product index after L2 normalization)
    embeddings_np = np.array(embeddings).astype("float32")
    faiss.normalize_L2(embeddings_np)
    _index = faiss.IndexFlatIP(embedding_dim)
    _index.add(embeddings_np)
    
    # Init BM25
    _bm25 = SimpleBM25(texts)
    print(f"[RAG Retrieve] Initialized RAG with {len(_documents)} semantic chunks.")

def add_documents_to_index(text_content: str, source_name: str, task_id: int = 0):
    """Dynamically add new document text to RAG indexes."""
    global _index, _documents, _bm25
    
    chunks = chunk_text_semantic(text_content, source=source_name, task_id=task_id)
    if not chunks:
        return
        
    texts = [c["text"] for c in chunks]
    embeddings = _embedder.encode(texts)
    embeddings_np = np.array(embeddings).astype("float32")
    faiss.normalize_L2(embeddings_np)
    
    if _index is None:
        embedding_dim = embeddings_np.shape[1]
        _index = faiss.IndexFlatIP(embedding_dim)
        _index.add(embeddings_np)
        _documents = chunks
    else:
        _index.add(embeddings_np)
        _documents.extend(chunks)
        
    # Rebuild BM25 search space
    all_texts = [d["text"] for d in _documents]
    _bm25 = SimpleBM25(all_texts)
    print(f"[RAG Retrieve] Dynamically added {len(chunks)} chunks from {source_name} to search index.")

def retrieve(query: str, top_k: int = 3) -> list[str]:
    """Retrieve top_k text snippets (backwards compatible wrapper)."""
    items = retrieve_hybrid(query, task_id=0, top_k=top_k, rerank=True)
    return [item["text"] for item in items]

def retrieve_hybrid(query: str, task_id: int = 0, top_k: int = 3, rerank: bool = True) -> list[dict]:
    """
    Performs Hybrid Search (Dense FAISS Inner Product + BM25 Lexical Score)
    with Reciprocal Rank Fusion (RRF) and metadata task filtering.
    """
    if not _index or not _documents:
        return []
        
    # 1. Filter documents by task_id if relevant
    valid_indices = []
    for i, doc in enumerate(_documents):
        doc_task_id = doc["metadata"].get("task_id", 0)
        # Match matches specific task ID, or global tasks (task_id 0)
        if task_id == 0 or doc_task_id == task_id or doc_task_id == 0:
            valid_indices.append(i)
            
    if not valid_indices:
        return []
        
    # 2. Get dense search ranking
    query_emb = get_embedding(query)
    query_emb_2d = np.array([query_emb]).astype("float32")
    faiss.normalize_L2(query_emb_2d)
    
    # Retrieve top match candidates
    k_search = min(len(_documents), 30)
    sims, indices = _index.search(query_emb_2d, k_search)
    
    dense_ranks = {}
    rank = 1
    for sim, idx in zip(sims[0], indices[0]):
        if idx in valid_indices and idx != -1:
            dense_ranks[idx] = rank
            rank += 1
            
    # 3. Get lexical ranking via SimpleBM25
    bm25_scores = _bm25.get_scores(query)
    bm25_valid = [(idx, bm25_scores[idx]) for idx in valid_indices if bm25_scores[idx] > 0]
    bm25_valid.sort(key=lambda x: x[1], reverse=True)
    
    lexical_ranks = {}
    rank = 1
    for idx, score in bm25_valid:
        lexical_ranks[idx] = rank
        rank += 1
        
    # 4. Reciprocal Rank Fusion (RRF)
    # Score = 1 / (60 + dense_rank) + 1 / (60 + lexical_rank)
    rrf_scores = []
    for idx in valid_indices:
        dense_r = dense_ranks.get(idx, 999)
        lexical_r = lexical_ranks.get(idx, 999)
        rrf_val = (1.0 / (60.0 + dense_r)) + (1.0 / (60.0 + lexical_r))
        rrf_scores.append((idx, rrf_val))
        
    rrf_scores.sort(key=lambda x: x[1], reverse=True)
    top_rrf = rrf_scores[:top_k * 2]  # Fetch candidate set for rerank
    
    # 5. Rerank candidates using bi-encoder Cosine Similarity
    retrieved_items = []
    for idx, rrf in top_rrf:
        doc = _documents[idx]
        doc_emb = _embedder.encode([doc["text"]])[0]
        # Cosine similarity = dot(a, b) / (norm(a)*norm(b))
        cos_sim = float(np.dot(query_emb, doc_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(doc_emb)))
        retrieved_items.append({
            "text": doc["text"],
            "metadata": doc["metadata"],
            "score": cos_sim
        })
        
    if rerank:
        retrieved_items.sort(key=lambda x: x["score"], reverse=True)
        
    return retrieved_items[:top_k]
