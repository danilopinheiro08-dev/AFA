import pandas as pd
import hashlib
from pathlib import Path
from loguru import logger
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from app.config import get_settings

settings = get_settings()

_embedding_model = None
_chroma_client = None
_collection = None


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Carregando modelo de embeddings: {settings.embedding_model}")
        _embedding_model = SentenceTransformer(settings.embedding_model)
    return _embedding_model


def get_chroma_collection():
    global _chroma_client, _collection
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    if _collection is None:
        _collection = _chroma_client.get_or_create_collection(
            name="antifraude",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _chunk_dataframe(df: pd.DataFrame, chunk_size: int = 50) -> list[str]:
    """Converte linhas do DataFrame em chunks de texto para embedding."""
    chunks = []
    cols = df.columns.tolist()
    
    for i in range(0, len(df), chunk_size):
        batch = df.iloc[i : i + chunk_size]
        rows_text = []
        for _, row in batch.iterrows():
            row_str = " | ".join(
                f"{col}: {val}" for col, val in zip(cols, row.values) if pd.notna(val)
            )
            rows_text.append(row_str)
        chunk_text = "\n".join(rows_text)
        chunks.append(chunk_text)
    return chunks


def ingest_csv(file_path: str) -> dict:
    """Ingere um arquivo CSV na base vetorial ChromaDB."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    logger.info(f"Iniciando ingestão: {path.name}")
    
    try:
        df = pd.read_csv(file_path, encoding="utf-8", low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="latin-1", low_memory=False)

    logger.info(f"CSV carregado: {len(df)} linhas, {len(df.columns)} colunas")

    chunks = _chunk_dataframe(df, chunk_size=50)
    model = get_embedding_model()
    collection = get_chroma_collection()

    embeddings = model.encode(chunks, show_progress_bar=True, batch_size=32).tolist()

    ids = []
    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.md5(f"{path.name}_{i}_{chunk[:50]}".encode()).hexdigest()
        ids.append(chunk_id)

    # Remove documentos existentes deste arquivo para re-ingestão
    try:
        existing = collection.get(where={"source_file": path.name})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
            logger.info(f"Removidos {len(existing['ids'])} chunks existentes de {path.name}")
    except Exception:
        pass

    metadatas = [
        {
            "source_file": path.name,
            "chunk_index": i,
            "total_rows": len(df),
            "columns": ", ".join(df.columns.tolist()[:20]),
        }
        for i in range(len(chunks))
    ]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )

    logger.info(f"Ingestão concluída: {len(chunks)} chunks indexados de {path.name}")
    return {
        "file": path.name,
        "rows": len(df),
        "chunks": len(chunks),
        "columns": df.columns.tolist(),
    }


def ingest_all_csvs() -> list[dict]:
    """Ingere todos os CSVs da pasta configurada."""
    csv_dir = Path(settings.csv_dir)
    csv_files = list(csv_dir.glob("*.csv"))
    
    if not csv_files:
        logger.warning(f"Nenhum CSV encontrado em {csv_dir}")
        return []

    results = []
    for f in csv_files:
        try:
            result = ingest_csv(str(f))
            results.append(result)
        except Exception as e:
            logger.error(f"Erro ao ingerir {f.name}: {e}")
            results.append({"file": f.name, "error": str(e)})
    
    return results


def get_collection_stats() -> dict:
    """Retorna estatísticas da coleção ChromaDB."""
    collection = get_chroma_collection()
    count = collection.count()
    return {"total_chunks": count, "collection": "antifraude"}
