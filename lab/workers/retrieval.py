"""
workers/retrieval.py — Retrieval Worker
Implement retrieval từ ChromaDB, trả về chunks + sources.

Input (từ AgentState):
    - task: câu hỏi cần retrieve
    - retrieval_top_k (optional): số lượng chunk cần lấy (default: 3)

Output (vào AgentState):
    - retrieved_chunks: list of {"text", "source", "score", "metadata"}
    - retrieved_sources: list of source filenames
    - worker_io_log: log input/output của worker này

Gọi độc lập để test:
    python workers/retrieval.py
"""

import os
from typing import List, Dict, Any, Callable
from dotenv import load_dotenv

# Load các biến môi trường từ file .env
load_dotenv()

# ─────────────────────────────────────────────
# Cấu hình & Hằng số
# ─────────────────────────────────────────────
WORKER_NAME = "retrieval_worker"
DEFAULT_TOP_K = 3

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "day09_docs")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")

# Global Cache (tránh việc load lại model/DB mỗi lần query)
_EMBED_FN: Callable[[str], List[float]] | None = None
_COLLECTION = None

# ─────────────────────────────────────────────
# Core Logic
# ─────────────────────────────────────────────

def _get_embedding_fn() -> Callable[[str], List[float]]:
    """
    Khởi tạo và cache embedding function.
    Ưu tiên: Sentence Transformers (Local) → OpenAI → Random (test).
    """
    global _EMBED_FN
    if _EMBED_FN is not None:
        return _EMBED_FN

    # 1. ƯU TIÊN 1: Sentence Transformers (Offline Local)
    try:
        from sentence_transformers import SentenceTransformer
        print(f"🔄 Loading SentenceTransformer model: {EMBED_MODEL_NAME}...")
        model = SentenceTransformer(EMBED_MODEL_NAME)
        
        def embed_st(text: str) -> List[float]:
            return model.encode([text])[0].tolist()
            
        _EMBED_FN = embed_st
        return _EMBED_FN
    except ImportError:
        pass

    # 2. ƯU TIÊN 2: OpenAI (Nếu có API Key)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            print("🔄 Using OpenAI for embeddings...")
            
            def embed_oai(text: str) -> List[float]:
                resp = client.embeddings.create(input=text, model="text-embedding-3-small")
                return resp.data[0].embedding
                
            _EMBED_FN = embed_oai
            return _EMBED_FN
        except ImportError:
            print("⚠️ Có OPENAI_API_KEY nhưng chưa cài thư viện `openai`. Chuyển qua Option 2...")
            pass
    else:print("ℹ️ Không tìm thấy OPENAI_API_KEY trong .env. Chuyển qua Option 2...")

    # 3. FALLBACK: Random (Chỉ dùng cho testing khi thiếu thư viện)
    import random
    print("⚠️ WARNING: Using random embeddings (test only). Please install openai or sentence-transformers.")
    
    def embed_random(text: str) -> List[float]:
        return [random.random() for _ in range(384)]  # Trùng dimension với MiniLM hoặc có thể sửa tùy ý
        
    _EMBED_FN = embed_random
    return _EMBED_FN


def _get_collection() -> Any:
    """
    Khởi tạo và cache kết nối đến ChromaDB Collection.
    """
    global _COLLECTION
    if _COLLECTION is not None:
        return _COLLECTION

    import chromadb
    print(f"🔄 Connecting to ChromaDB at {CHROMA_DB_PATH}...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    try:
        _COLLECTION = client.get_collection(CHROMA_COLLECTION)
    except Exception:
        # Auto-create nếu chưa có
        _COLLECTION = client.get_or_create_collection(
            CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"⚠️ Collection '{CHROMA_COLLECTION}' created but is empty. Please run index script.")
        
    return _COLLECTION


def retrieve_dense(query: str, top_k: int = DEFAULT_TOP_K) -> List[Dict[str, Any]]:
    """
    Dense retrieval: embed query → query ChromaDB → trả về top_k chunks.
    """
    if not query or not query.strip():
        return []

    embed = _get_embedding_fn()
    query_embedding = embed(query)

    try:
        collection = _get_collection()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "distances", "metadatas"]
        )

        # Kiểm tra kết quả trả về có hợp lệ không
        if not results or not results.get("documents") or not results["documents"][0]:
            return []

        chunks = []
        # ChromaDB trả về mảng 2 chiều vì có thể query nhiều câu cùng lúc
        for doc, dist, meta in zip(
            results["documents"][0],
            results["distances"][0],
            results["metadatas"][0]
        ):
            # Xử lý an toàn trường hợp metadata bị thiếu (None) trong database
            safe_meta = meta or {}
            
            # Clamp score trong [0, 1]
            score = max(0.0, min(1.0, round(1 - dist, 4)))

            chunks.append({
                "text": doc,
                "source": safe_meta.get("source", "unknown"),
                "score": score,
                "metadata": safe_meta,
            })
        return chunks

    except Exception as e:
        print(f"⚠️ ChromaDB query failed: {e}")
        return []


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """Worker entry point — gọi từ graph.py.
    """
    task = state.get("task", "")
    top_k = state.get("retrieval_top_k", DEFAULT_TOP_K)

    # Initialize state fields nếu chưa có
    state.setdefault("workers_called", [])
    state.setdefault("history", [])
    state.setdefault("worker_io_logs", [])

    state["workers_called"].append(WORKER_NAME)

    worker_io = {
        "worker": WORKER_NAME,
        "input": {"task": task, "top_k": top_k},
        "output": None,
        "error": None,
    }

    try:
        chunks = retrieve_dense(task, top_k=top_k)
        sources = list({c["source"] for c in chunks})

        state["retrieved_chunks"] = chunks
        state["retrieved_sources"] = sources

        worker_io["output"] = {
            "chunks_count": len(chunks),
            "sources": sources,
        }
        state["history"].append(
            f"[{WORKER_NAME}] retrieved {len(chunks)} chunks from {len(sources)} sources."
        )

    except Exception as e:
        worker_io["error"] = {"code": "RETRIEVAL_FAILED", "reason": str(e)}
        state["retrieved_chunks"] = []
        state["retrieved_sources"] = []
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    state["worker_io_logs"].append(worker_io)

    return state


# ─────────────────────────────────────────────
# Test độc lập
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Retrieval Worker — Standalone Test")
    print("=" * 50)

    test_queries = [
        "SLA ticket P1 là bao lâu?",
        "Điều kiện được hoàn tiền là gì?",
        "Ai phê duyệt cấp quyền Level 3?",
    ]

    for query in test_queries:
        print(f"\n▶ Query: {query}")
        result = run({"task": query, "retrieval_top_k": 2})
        
        chunks = result.get("retrieved_chunks", [])
        print(f"  Retrieved: {len(chunks)} chunks")
        
        for i, c in enumerate(chunks):
            text_preview = c['text'][:80].replace('\n', ' ')
            print(f"    {i+1}. [{c['score']:.3f}] {c['source']}: {text_preview}...")
            
        print(f"  Sources: {result.get('retrieved_sources', [])}")

    print("\n✅ retrieval_worker test done.")