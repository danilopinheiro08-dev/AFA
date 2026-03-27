"""
Orchestrator de agentes antifraude.
Recebe a query do usuário, identifica o tipo de análise,
executa os agentes especializados e consolida a resposta.
"""

from loguru import logger
from app.rag.retriever import retrieve, format_context
from app.guardrails.guards import run_input_guardrails, validate_output, GuardrailViolation
from app.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = """Você é um analista sênior de antifraude de uma operadora de telecomunicações.

## Regras absolutas:
1. Responda APENAS com base nos dados do contexto fornecido. Sem dados = diga que não há dados suficientes.
2. NUNCA escreva introduções, metodologias, conclusões genéricas ou textos educativos.
3. NUNCA explique o que é fraude de subscrição, chargeback etc. O analista já sabe.
4. Vá direto ao ponto: cite registros, valores, contagens e padrões encontrados nos dados.
5. Use marcadores curtos. Evite parágrafos longos.
6. Se os dados forem insuficientes para responder, diga em uma linha e pare.

## Formato obrigatório:
- Comece com o resultado principal (ex: "3 clientes com score > 0.9 e tipo Subscrição:")
- Liste os casos com dados concretos
- Termine com 1-2 ações recomendadas baseadas nos dados, não em teoria

## Classificação de risco:
🔴 Score > 0.8 ou histórico ≥ 2 fraudes | 🟡 Score 0.5–0.8 | 🟢 Score < 0.5

Responda em português brasileiro. Seja direto como um analista em uma sala de guerra."""


INTENT_KEYWORDS = {
    "fraud_analysis": [
        "fraude", "suspeito", "anomalia", "estranho", "irregular", "detectar",
        "identificar fraude", "analise", "analisar", "risco",
    ],
    "typification": [
        "tipo", "tipificar", "tipificação", "classificar", "categoria", "qual fraude",
    ],
    "cost_analysis": [
        "custo", "prejuízo", "valor", "quantificar", "quanto", "impacto financeiro",
    ],
    "blacklist": [
        "blacklist", "lista negra", "cliente na lista", "bloqueado", "banido",
    ],
    "report": [
        "relatório", "gerar relatório", "report", "sintetizar", "resumo executivo",
    ],
    "alert": [
        "alarme", "alerta", "cockpit", "monitoramento", "regra",
    ],
}


def detect_intent(query: str) -> str:
    """Detecta a intenção principal da query."""
    query_lower = query.lower()
    scores = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        scores[intent] = score

    best_intent = max(scores, key=scores.get)
    if scores[best_intent] == 0:
        return "fraud_analysis"  # default
    return best_intent


def build_agent_prompt(intent: str, query: str, context: str) -> list[dict]:
    """Constrói o prompt de acordo com a intenção detectada."""

    intent_instructions = {
        "fraud_analysis": (
            "Liste diretamente os casos suspeitos encontrados nos dados com: identificador do cliente, "
            "score, tipo de fraude, histórico. Ordene por risco. Não explique conceitos."
        ),
        "typification": (
            "Conte quantos casos existem por tipo de fraude nos dados. Mostre a distribuição. "
            "Não explique o que cada tipo significa."
        ),
        "cost_analysis": (
            "Extraia valores financeiros dos dados (custo, prejuízo, valor_fraude). "
            "Mostre total, média e os maiores casos. Se não houver coluna de valor, diga isso."
        ),
        "blacklist": (
            "Verifique diretamente nos dados quem está na blacklist. "
            "Mostre: identificador, motivo do bloqueio, histórico de fraudes."
        ),
        "report": (
            "Gere um resumo executivo direto: totais por tipo de fraude, top casos por score, "
            "regiões com maior incidência, 3 ações recomendadas. Sem introdução."
        ),
        "alert": (
            "Liste os alarmes críticos encontrados nos dados com score e tipo. "
            "Indique quais parecem falso positivo (score baixo + sem histórico)."
        ),
    }

    instruction = intent_instructions.get(intent, intent_instructions["fraud_analysis"])

    user_message = f"""## Instrução:
{instruction}

## Pergunta:
{query}

## Dados disponíveis:
{context}

Responda diretamente com base nos dados acima. Sem introdução, sem explicações teóricas."""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


async def get_llm_client():
    """Retorna o cliente LLM configurado."""
    if settings.llm_provider.lower() == "groq":
        from app.llm.groq_client import GroqLLMClient
        return GroqLLMClient()
    else:
        from app.llm.ollama_client import OllamaLLMClient
        return OllamaLLMClient()


async def run_agent(query: str) -> dict:
    """
    Executa o pipeline completo do agente:
    1. Guardrails de entrada
    2. RAG retrieval
    3. Detecção de intent
    4. LLM generation
    5. Validação de output
    """
    # 1. Guardrails de entrada
    try:
        safe_query = run_input_guardrails(query)
    except GuardrailViolation as e:
        return {
            "response": f"⛔ {e.reason}",
            "intent": "blocked",
            "sources": [],
            "guardrail_code": e.code,
        }

    # 2. RAG retrieval
    retrieved = retrieve(safe_query, top_k=settings.top_k_results)
    context = format_context(retrieved)

    # 3. Detecta intent
    intent = detect_intent(safe_query)
    logger.info(f"Intent detectado: {intent} | Query: '{safe_query[:60]}'")

    # 4. Monta prompt e chama LLM
    messages = build_agent_prompt(intent, safe_query, context)
    
    llm = await get_llm_client()
    response = await llm.chat(messages, temperature=0.1)

    # 5. Valida output
    validated_response = validate_output(response, retrieved)

    sources = list({item["source_file"] for item in retrieved})

    return {
        "response": validated_response,
        "intent": intent,
        "sources": sources,
        "chunks_used": len(retrieved),
        "guardrail_code": None,
    }


async def stream_agent(query: str):
    """
    Versão streaming do agente.
    Yields tokens à medida que são gerados.
    """
    # Guardrails
    try:
        safe_query = run_input_guardrails(query)
    except GuardrailViolation as e:
        yield f"⛔ {e.reason}"
        return

    # RAG
    retrieved = retrieve(safe_query, top_k=settings.top_k_results)
    context = format_context(retrieved)
    intent = detect_intent(safe_query)

    logger.info(f"[STREAM] Intent: {intent} | Query: '{safe_query[:60]}'")

    messages = build_agent_prompt(intent, safe_query, context)
    llm = await get_llm_client()

    full_response = ""
    async for token in llm.stream(messages, temperature=0.1):
        full_response += token
        yield token

    # Validate e adiciona disclaimer se necessário
    validated = validate_output(full_response, retrieved)
    if validated != full_response:
        extra = validated[len(full_response):]
        yield extra
