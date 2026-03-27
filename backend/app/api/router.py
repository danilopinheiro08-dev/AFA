import json
import asyncio
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import StreamingResponse, FileResponse
from pathlib import Path
from pydantic import BaseModel
from loguru import logger
from app.models.schemas import (
    ChatRequest, ChatResponse, UploadResponse,
    ReportRequest, ReportResponse, CollectionStats,
)
from app.agents.orchestrator import run_agent, stream_agent
from app.agents.report_agent import generate_report
from app.rag.ingestion import ingest_csv, get_collection_stats
from app.config import get_settings
import shutil

settings = get_settings()
router = APIRouter()


class LocalPathRequest(BaseModel):
    path: str  # Ex: /home/user/Downloads/fraudes.csv


# ─────────────────────────────────────────────
# CHAT ENDPOINT
# ─────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat_endpoint(req: ChatRequest):
    """Processa uma mensagem e retorna análise do agente (sem streaming)."""
    result = await run_agent(req.message)
    return ChatResponse(**result)


@router.get("/chat/stream", tags=["chat"])
async def chat_stream_endpoint(message: str):
    """Processa uma mensagem com streaming SSE."""

    async def event_generator():
        try:
            async for token in stream_agent(message):
                data = json.dumps({"token": token})
                yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Erro no streaming: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ─────────────────────────────────────────────
# UPLOAD ENDPOINT
# ─────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse, tags=["data"])
async def upload_csv(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Faz upload de um CSV e o ingere na base vetorial."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Apenas arquivos .csv são aceitos.")

    csv_dir = Path(settings.csv_dir)
    csv_dir.mkdir(parents=True, exist_ok=True)
    dest = csv_dir / file.filename

    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    logger.info(f"Arquivo salvo: {dest}")

    try:
        result = ingest_csv(str(dest))
        return UploadResponse(
            **result,
            message=f"✅ {result['rows']} linhas indexadas em {result['chunks']} chunks."
        )
    except Exception as e:
        logger.error(f"Erro na ingestão: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar CSV: {str(e)}")


# ─────────────────────────────────────────────
# REPORTS ENDPOINT
# ─────────────────────────────────────────────

@router.post("/reports", response_model=ReportResponse, tags=["reports"])
async def create_report(req: ReportRequest):
    """Gera um relatório completo de análise de fraude."""
    try:
        result = await generate_report(req.query)
        return ReportResponse(
            **result,
            download_url=f"/api/reports/{result['file_name']}",
        )
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{file_name}", tags=["reports"])
async def download_report(file_name: str):
    """Download de um relatório gerado."""
    file_path = Path(settings.reports_dir) / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Relatório não encontrado.")
    return FileResponse(
        str(file_path),
        media_type="text/html",
        filename=file_name,
    )


@router.get("/reports", tags=["reports"])
async def list_reports():
    """Lista todos os relatórios gerados."""
    reports_dir = Path(settings.reports_dir)
    if not reports_dir.exists():
        return {"reports": []}
    files = sorted(reports_dir.glob("*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
    return {
        "reports": [
            {
                "name": f.name,
                "size_kb": round(f.stat().st_size / 1024, 1),
                "created_at": f.stat().st_mtime,
                "download_url": f"/api/reports/{f.name}",
            }
            for f in files
        ]
    }


# ─────────────────────────────────────────────
# DATA / STATS ENDPOINT
# ─────────────────────────────────────────────

@router.get("/stats", response_model=CollectionStats, tags=["data"])
async def get_stats():
    """Retorna estatísticas da base vetorial."""
    try:
        stats = get_collection_stats()
        csv_dir = Path(settings.csv_dir)
        csv_files = [f.name for f in csv_dir.glob("*.csv")] if csv_dir.exists() else []
        return CollectionStats(**stats, csv_files=csv_files)
    except Exception as e:
        return CollectionStats(total_chunks=0, collection="antifraude", csv_files=[])


@router.get("/health", tags=["system"])
async def health():
    """Health check."""
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "model": settings.groq_model if settings.llm_provider == "groq" else settings.ollama_model,
        "version": settings.app_version,
        "vision_support": True,
        "vision_model": "llama-3.2-11b-vision-preview" if settings.llm_provider == "groq" else "llava:7b",
    }


# ─────────────────────────────────────────────
# LOCAL PATH INGESTION ENDPOINT
# ─────────────────────────────────────────────

@router.post("/ingest-path", response_model=UploadResponse, tags=["data"])
async def ingest_from_path(req: LocalPathRequest):
    """
    Ingere um CSV a partir de um caminho local do sistema de arquivos.
    Ex: { "path": "/home/user/Downloads/fraudes.csv" }
    """
    path = Path(req.path.strip())

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Arquivo não encontrado: {path}. Verifique o caminho completo."
        )

    if path.suffix.lower() != ".csv":
        raise HTTPException(status_code=400, detail="Apenas arquivos .csv são aceitos.")

    # Copia para a pasta de dados do sistema (opcional — mantém o original e cria link)
    csv_dir = Path(settings.csv_dir)
    csv_dir.mkdir(parents=True, exist_ok=True)
    dest = csv_dir / path.name

    if not dest.exists() or path.resolve() != dest.resolve():
        shutil.copy2(str(path), str(dest))
        logger.info(f"CSV copiado de {path} → {dest}")

    try:
        result = ingest_csv(str(dest))
        return UploadResponse(
            **result,
            message=f"✅ {result['rows']:,} linhas indexadas de '{path.name}' em {result['chunks']} chunks."
        )
    except Exception as e:
        logger.error(f"Erro ao ingerir {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar CSV: {str(e)}")


# ─────────────────────────────────────────────
# VISION / IMAGE ANALYSIS ENDPOINT
# ─────────────────────────────────────────────

@router.post("/vision", tags=["chat"])
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    question: str = Form(
        default="Analise esta imagem e identifique padrões de fraude, anomalias ou informações relevantes para antifraude."
    ),
):
    """
    Analisa uma imagem (gráfico, dashboard, screenshot) com LLM vision.
    Suporta: PNG, JPG, WEBP (máx 20MB para Groq).
    """
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"}
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo não suportado: {file.content_type}. Use PNG, JPG ou WEBP."
        )

    MAX_SIZE_MB = 18
    image_bytes = await file.read()
    size_mb = len(image_bytes) / (1024 * 1024)

    if size_mb > MAX_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"Imagem muito grande ({size_mb:.1f}MB). Máximo: {MAX_SIZE_MB}MB."
        )

    logger.info(f"[Vision] Recebida: {file.filename} ({size_mb:.2f}MB)")

    try:
        from app.llm.vision_client import analyze_image
        result = await analyze_image(image_bytes, file.filename or "image", question)
        return {
            "analysis": result["analysis"],
            "model": result["model"],
            "provider": result["provider"],
            "file": file.filename,
            "size_mb": round(size_mb, 2),
        }
    except Exception as e:
        logger.error(f"Erro na análise de imagem: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na análise visual: {str(e)}")
