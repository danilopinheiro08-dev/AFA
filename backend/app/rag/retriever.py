from loguru import logger
from app.rag.ingestion import get_embedding_model, get_chroma_collection
from app.config import get_settings

settings = get_settings()


def retrieve(query: str, top_k: int = None, filters: dict = None) -> list[dict]:
    """
    Busca os chunks mais relevantes para uma query no ChromaDB.
    
    Returns:
        Lista de dicts com 'content', 'source_file', 'score'
    """
    if top_k is None:
        top_k = settings.top_k_results

    model = get_embedding_model()
    collection = get_chroma_collection()

    query_embedding = model.encode([query]).tolist()

    where_clause = filters if filters else None

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k, max(collection.count(), 1)),
        where=where_clause,
        include=["documents", "metadatas", "distances"],
    )

    if not results["documents"] or not results["documents"][0]:
        logger.warning(f"Nenhum resultado encontrado para: {query[:80]}")
        return []

    retrieved = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        score = 1 - dist  # cosine similarity
        retrieved.append(
            {
                "content": doc,
                "source_file": meta.get("source_file", "unknown"),
                "columns": meta.get("columns", ""),
                "score": round(score, 4),
            }
        )

    logger.debug(f"RAG: {len(retrieved)} chunks recuperados para '{query[:60]}...'")
    return retrieved


def format_context(retrieved: list[dict]) -> str:
    """Formata os chunks recuperados como contexto para o LLM."""
    if not retrieved:
        return "Nenhum dado relevante encontrado na base."

    lines = ["=== DADOS RELEVANTES DA BASE DE FRAUDES ===\n"]
    for i, item in enumerate(retrieved, 1):
        lines.append(f"[Fonte {i}: {item['source_file']} | Relevância: {item['score']:.2%}]")
        lines.append(item["content"])
        lines.append("")

    return "\n".join(lines)
