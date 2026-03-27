"""
Vision LLM client — Analisa imagens com Groq (llama-3.2-11b-vision-preview)
ou Ollama (llava:7b).
"""

import base64
from pathlib import Path
from loguru import logger
from app.config import get_settings

settings = get_settings()

GROQ_VISION_MODEL = "llama-3.2-11b-vision-preview"
OLLAMA_VISION_MODEL = "llava:7b"

VISION_SYSTEM_PROMPT = """Você é um especialista em análise de fraudes com capacidade de interpretar gráficos e dashboards.

Ao analisar uma imagem:
1. Identifique o tipo de gráfico/dashboard (linha, barra, cockpit, tabela, etc.)
2. Extraia os dados e métricas visíveis
3. Identifique anomalias, picos suspeitos ou padrões de fraude
4. Correlacione com tipos de fraude conhecidos em telecomunicações
5. Gere um diagnóstico estruturado com nível de risco

Responda sempre em português brasileiro com foco em antifraude."""


def encode_image_to_base64(image_bytes: bytes) -> str:
    """Converte bytes de imagem para base64."""
    return base64.b64encode(image_bytes).decode("utf-8")


def detect_image_media_type(filename: str) -> str:
    """Detecta o media type pela extensão do arquivo."""
    ext = Path(filename).suffix.lower()
    types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    return types.get(ext, "image/jpeg")


async def analyze_image_groq(
    image_bytes: bytes,
    filename: str,
    question: str = "Analise esta imagem e identifique padrões de fraude ou anomalias.",
) -> str:
    """Analisa imagem com Groq Vision (llama-3.2-11b-vision-preview)."""
    from groq import AsyncGroq

    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY não configurada")

    client = AsyncGroq(api_key=settings.groq_api_key)
    b64 = encode_image_to_base64(image_bytes)
    media_type = detect_image_media_type(filename)

    logger.info(f"[Vision/Groq] Analisando imagem: {filename} ({len(image_bytes)//1024}KB)")

    response = await client.chat.completions.create(
        model=GROQ_VISION_MODEL,
        messages=[
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{b64}",
                        },
                    },
                    {
                        "type": "text",
                        "text": question,
                    },
                ],
            },
        ],
        temperature=0.1,
        max_tokens=2048,
    )
    return response.choices[0].message.content


async def analyze_image_ollama(
    image_bytes: bytes,
    filename: str,
    question: str = "Analise esta imagem e identifique padrões de fraude ou anomalias.",
) -> str:
    """Analisa imagem com Ollama Vision (llava:7b)."""
    import httpx

    b64 = encode_image_to_base64(image_bytes)

    logger.info(f"[Vision/Ollama] Analisando: {filename} ({len(image_bytes)//1024}KB)")

    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": OLLAMA_VISION_MODEL,
                "messages": [
                    {"role": "system", "content": VISION_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": question,
                        "images": [b64],
                    },
                ],
                "stream": False,
                "options": {"temperature": 0.1},
            },
        )
        response.raise_for_status()
        return response.json()["message"]["content"]


async def analyze_image(
    image_bytes: bytes,
    filename: str,
    question: str = "Analise esta imagem e identifique padrões de fraude ou anomalias.",
) -> dict:
    """
    Analisa imagem usando o provider LLM configurado.
    Retorna: { analysis, model_used, provider }
    """
    provider = settings.llm_provider.lower()

    try:
        if provider == "groq":
            analysis = await analyze_image_groq(image_bytes, filename, question)
            model = GROQ_VISION_MODEL
        else:
            analysis = await analyze_image_ollama(image_bytes, filename, question)
            model = OLLAMA_VISION_MODEL

        return {
            "analysis": analysis,
            "model": model,
            "provider": provider,
        }
    except Exception as e:
        logger.error(f"Erro na análise de imagem ({provider}): {e}")
        raise
