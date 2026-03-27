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

SYSTEM_PROMPT = """Você é um Agente Especialista em Antifraude para uma empresa de telecomunicações.

Seu papel é analisar dados de fraude, identificar padrões suspeitos, tipificar fraudes,
quantificar custos e gerar diagnósticos precisos.

## Tipos de Fraude que você conhece:
- **Fraude de Subscrição**: Contratar serviços em nome de outra pessoa
- **Fraude de Alto Uso**: Uso anômalo e repentino de serviços (ex: SMS, dados)
- **Chargeback**: Contestação indevida de cobranças
- **Clonagem de SIM**: Duplicação de chip para interceptar comunicações
- **Fraude de Identificação**: Uso de documentos falsos ou de terceiros
- **Fraude de Cancelamento**: Solicitar cancelamento após uso do serviço

## Diretrizes:
1. SEMPRE baseie suas análises nos dados fornecidos no contexto
2. Cite as fontes de dados (arquivo CSV, colunas) em suas análises
3. Indique o nível de confiança da análise (Alta/Média/Baixa)
4. Se não houver dados suficientes, diga claramente
5. Gere diagnósticos em formato estruturado quando solicitado
6. Identifique padrões de comportamento anômalo nos dados
7. Compare com histórico quando disponível
8. Sugira ações de mitigação concretas

## Formato de Resposta para Análises:
- 🔴 **Risco Alto** | 🟡 **Risco Médio** | 🟢 **Risco Baixo**
- Inclua: O quê, Quando, Onde, Quem, Como, Recomendação

Responda sempre em português brasileiro."""


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
            "Analise os dados fornecidos e identifique padrões suspeitos ou anômalos. "
            "Determine o nível de risco e explique os indicadores de fraude encontrados."
        ),
        "typification": (
            "Classifique o tipo de fraude presente nos dados. "
            "Use as categorias padrão de antifraude e justifique a classificação."
        ),
        "cost_analysis": (
            "Calcule e quantifique o impacto financeiro das fraudes identificadas. "
            "Apresente totais, médias e distribuição por período/segmento quando disponível."
        ),
        "blacklist": (
            "Verifique se os clientes/entidades mencionados estão na blacklist. "
            "Indique o histórico de fraudes e as razões do bloqueio."
        ),
        "report": (
            "Gere um relatório executivo estruturado com: Sumário Executivo, "
            "Principais Achados, Tipificação, Impacto Financeiro e Recomendações."
        ),
        "alert": (
            "Analise os alarmes e indicadores. Identifique falsos positivos, "
            "priorize alertas críticos e sugira ajustes nas regras de monitoramento."
        ),
    }

    instruction = intent_instructions.get(intent, intent_instructions["fraud_analysis"])

    user_message = f"""## Instrução do Agente:
{instruction}

## Pergunta do Analista:
{query}

## Contexto - Dados da Base de Fraudes:
{context}

Por favor, forneça uma análise completa e estruturada."""

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
