from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from loguru import logger
from app.config import get_settings
from app.api.router import router

settings = get_settings()


def create_app() -> FastAPI:
    settings.ensure_dirs()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Agente de IA para análise proativa de fraudes em telecomunicações",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(router, prefix="/api")

    @app.on_event("startup")
    async def startup_event():
        logger.info(f"🚀 {settings.app_name} v{settings.app_version} iniciado")
        logger.info(f"🤖 LLM Provider: {settings.llm_provider}")
        
        # Auto-ingest any existing CSVs on startup
        csv_dir = Path(settings.csv_dir)
        csv_files = list(csv_dir.glob("*.csv"))
        if csv_files:
            logger.info(f"📂 Encontrados {len(csv_files)} CSVs para ingestão automática")
            from app.rag.ingestion import ingest_csv
            for f in csv_files:
                try:
                    result = ingest_csv(str(f))
                    logger.info(f"✅ {f.name}: {result['chunks']} chunks indexados")
                except Exception as e:
                    logger.error(f"❌ Erro ao ingerir {f.name}: {e}")
        else:
            logger.info("📂 Nenhum CSV encontrado. Faça upload em /api/upload")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
