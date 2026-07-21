import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", 6333))
COLLECTION_NAME = "researchmind_chunks"

class SemanticMemory:
    def __init__(self):
        # Load local lightweight embedding model (dim=384)
        print("[Embedding Model] Loading sentence-transformer all-MiniLM-L6-v2...")
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        print("[Embedding Model] Loaded successfully.")
        
        # Connect to Qdrant server
        print(f"[Qdrant Client] Connecting to {QDRANT_HOST}:{QDRANT_PORT}...")
        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self.init_collection()

    def init_collection(self):
        """Initializes the Qdrant collection if it does not exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            if COLLECTION_NAME not in collection_names:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )
                print(f"[Qdrant] Created collection '{COLLECTION_NAME}' (dim=384).")
        except Exception as e:
            print(f"[Qdrant Warning] Failed to initialize collection: {e}")

    def add_chunks(self, session_id: int, source: str, chunks: list[str]):
        """Generates embeddings and inserts paper chunks into Qdrant."""
        if not chunks:
            return
            
        embeddings = self.encoder.encode(chunks)
        points = []
        for i, (chunk, vec) in enumerate(zip(chunks, embeddings)):
            point_id = hash(f"{session_id}_{source}_{i}") & 0xFFFFFFFFFFFFFFFF
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vec.tolist(),
                    payload={
                        "session_id": session_id,
                        "source": source,
                        "text": chunk
                    }
                )
            )
            
        try:
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                wait=True,
                points=points
            )
            print(f"[Qdrant] Successfully added {len(chunks)} chunks for Session #{session_id} ({source}).")
        except Exception as e:
            print(f"[Qdrant Error] Upsert failed: {e}")

    def search(self, session_id: int, query: str, top_k: int = 5) -> list[dict]:
        """Search vector database filtered by session_id."""
        query_vector = self.encoder.encode([query])[0].tolist()
        
        try:
            results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="session_id",
                            match=MatchValue(value=session_id)
                        )
                    ]
                ),
                limit=top_k
            )
            return [
                {
                    "text": hit.payload["text"],
                    "source": hit.payload["source"],
                    "score": hit.score
                }
                for hit in results
            ]
        except Exception as e:
            print(f"[Qdrant Error] Search failed: {e}")
            return []

# Singleton Instance
try:
    semantic_memory = SemanticMemory()
except Exception as e:
    print(f"[Semantic Memory] Could not initialize Qdrant. Mock client will be used: {e}")
    semantic_memory = None
