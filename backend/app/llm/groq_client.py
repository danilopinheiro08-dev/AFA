from groq import AsyncGroq
from app.config import get_settings
from loguru import logger

settings = get_settings()


class GroqLLMClient:
    def __init__(self):
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY não definida no .env")
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.model = settings.groq_model

    async def chat(self, messages: list[dict], temperature: float = 0.1) -> str:
        """Envia mensagens e retorna resposta completa."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=4096,
        )
        return response.choices[0].message.content

    async def stream(self, messages: list[dict], temperature: float = 0.1):
        """Envia mensagens e retorna gerador de streaming."""
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=4096,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
