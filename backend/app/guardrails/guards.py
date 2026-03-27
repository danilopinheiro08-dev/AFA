"""
Guardrails para o Anti-Fraud Agent.
Valida inputs e outputs para evitar:
- Perguntas fora do escopo de antifraude
- Vazamento de PII
- Alucinações sem embasamento em dados
- Prompt injection
"""

import re
from loguru import logger

# Termos relacionados ao domínio de antifraude (PT-BR)
FRAUD_DOMAIN_KEYWORDS = {
    "fraude", "fraud", "antifraude", "suspeito", "suspeita", "anomalia",
    "blacklist", "lista negra", "pedido", "venda", "cliente", "cpf", "cnpj",
    "subscrição", "assinatura", "contrato", "cancelamento", "chargeback",
    "alerta", "alarme", "cockpit", "indicador", "hit", "falso positivo",
    "tipificação", "custo", "prejuízo", "risco", "score", "ranking",
    "sms", "serviço", "produto", "claro", "telecom", "celular", "residencial",
    "análise", "analisar", "verificar", "checar", "monitorar", "detectar",
    "relatório", "dashboard", "base de dados", "dados", "csv",
    "reclamação", "ocorrência", "incidente", "caso",
    "quantificação", "quantificar", "medir", "count", "total",
    "período", "mês", "dia", "semana", "data", "quando",
    "quem", "onde", "qual", "quais", "como", "por que",
    "listar", "mostrar", "exibir", "apresentar", "comparar",
}

# Palavras que indicam claramente fora do escopo
OUT_OF_SCOPE_PATTERNS = [
    r"\breceita\b.*\b(bolo|comida|culinária)\b",
    r"\b(futebol|esporte|time|jogo|partida)\b",
    r"\b(política|eleição|presidente|governo)\b",
    r"\b(novela|série|filme|entretenimento)\b",
    r"\b(piada|humor|engraçado)\b",
    r"\b(religião|deus|oração)\b",
]

# Padrões de PII para detectar/bloquear no prompt
PII_PATTERNS = {
    "cpf": r"\b\d{3}[\.\-]?\d{3}[\.\-]?\d{3}[\.\-]?\d{2}\b",
    "telefone": r"\b(\+55\s?)?(\(?\d{2}\)?\s?)(\d{4,5}[\-\s]?\d{4})\b",
    "email": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
}


class GuardrailViolation(Exception):
    def __init__(self, reason: str, code: str):
        self.reason = reason
        self.code = code
        super().__init__(reason)


def check_scope(query: str) -> bool:
    """
    Verifica se a query está dentro do domínio de antifraude.
    Retorna True se OK, levanta GuardrailViolation se fora do escopo.
    """
    query_lower = query.lower()

    # Verifica se contém alguma keyword do domínio
    has_domain_keyword = any(kw in query_lower for kw in FRAUD_DOMAIN_KEYWORDS)

    # Verifica padrões explicitamente fora do escopo
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, query_lower):
            raise GuardrailViolation(
                reason="Pergunta fora do escopo do sistema de antifraude.",
                code="OUT_OF_SCOPE",
            )

    # Queries genéricas curtas (< 10 chars) passam (ex: "oi", "olá")
    if len(query.strip()) < 10:
        return True

    if not has_domain_keyword:
        # Permite queries ambíguas mas avisa
        logger.warning(f"Query sem keywords de antifraude: '{query[:80]}'")

    return True


def detect_pii(text: str) -> dict:
    """
    Detecta PII no texto.
    Retorna dict com tipos detectados e posições.
    """
    found = {}
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            found[pii_type] = matches
    return found


def redact_pii(text: str) -> str:
    """Substitui PII por placeholders."""
    result = text
    for pii_type, pattern in PII_PATTERNS.items():
        placeholder = f"[{pii_type.upper()}_REDACTED]"
        result = re.sub(pattern, placeholder, result)
    return result


def check_prompt_injection(query: str) -> bool:
    """
    Detecta tentativas de prompt injection.
    """
    injection_patterns = [
        r"ignore (all )?(previous|above|prior) (instructions?|prompts?|context)",
        r"you are now",
        r"pretend (you are|to be)",
        r"jailbreak",
        r"DAN mode",
        r"act as (a |an )?(different|new|another)",
        r"forget (everything|all)",
        r"system prompt",
        r"override (your )?(instructions?|rules?|guidelines?)",
    ]
    query_lower = query.lower()
    for pattern in injection_patterns:
        if re.search(pattern, query_lower, re.IGNORECASE):
            raise GuardrailViolation(
                reason="Tentativa de manipulação do sistema detectada.",
                code="PROMPT_INJECTION",
            )
    return True


def validate_output(response: str, context_chunks: list[dict]) -> str:
    """
    Valida o output do LLM.
    - Redige PII do output antes de exibir.
    - Se não há dados de contexto, alerta sobre possível alucinação.
    - Adiciona disclaimer se necessário.
    """
    # Redige PII do output do LLM
    response = redact_pii(response)

    if not context_chunks:
        disclaimer = (
            "\n\n⚠️ **Aviso:** Esta resposta foi gerada sem dados da base local. "
            "Faça upload de CSVs para análises baseadas em dados reais."
        )
        return response + disclaimer

    # Verifica se resposta é muito curta (possível erro)
    if len(response.strip()) < 20:
        return "Não foi possível gerar uma análise adequada. Reformule a pergunta ou verifique os dados disponíveis."

    return response


def run_input_guardrails(query: str) -> str:
    """
    Executa todos os guardrails de entrada.
    Retorna a query (possivelmente com PII redacted).
    Levanta GuardrailViolation em caso de violação.
    """
    # 1. Checa prompt injection
    check_prompt_injection(query)

    # 2. Checa escopo
    check_scope(query)

    # 3. Detecta e redige PII
    pii_found = detect_pii(query)
    if pii_found:
        logger.warning(f"PII detectado no prompt: {list(pii_found.keys())}")
        query = redact_pii(query)

    return query
