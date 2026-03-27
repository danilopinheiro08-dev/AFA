"""
Report Agent — Gera relatórios em HTML e PDF.
"""

import uuid
from datetime import datetime
from pathlib import Path
from jinja2 import Template
from loguru import logger
from app.config import get_settings
from app.rag.retriever import retrieve, format_context
from app.agents.orchestrator import get_llm_client, SYSTEM_PROMPT

settings = get_settings()

REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Relatório de Antifraude — {{ report_date }}</title>
<style>
  body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 40px; background: #f8f9fa; color: #212529; }
  h1 { color: #c0392b; border-bottom: 3px solid #c0392b; padding-bottom: 10px; }
  h2 { color: #2c3e50; border-left: 4px solid #e74c3c; padding-left: 12px; margin-top: 30px; }
  h3 { color: #34495e; }
  .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 0.85em; }
  .badge-red { background: #e74c3c; color: white; }
  .badge-yellow { background: #f39c12; color: white; }
  .badge-green { background: #27ae60; color: white; }
  .metadata { background: #ecf0f1; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
  .metadata p { margin: 4px 0; font-size: 0.9em; }
  .section { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); }
  .source-tag { background: #3498db; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-right: 5px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
  th { background: #2c3e50; color: white; }
  tr:hover { background: #f5f5f5; }
  .footer { text-align: center; color: #7f8c8d; font-size: 0.85em; margin-top: 40px; border-top: 1px solid #ddd; padding-top: 20px; }
</style>
</head>
<body>
<h1>🔍 Relatório de Análise — Antifraude</h1>

<div class="metadata">
  <p><strong>Data/Hora:</strong> {{ report_date }}</p>
  <p><strong>ID do Relatório:</strong> {{ report_id }}</p>
  <p><strong>Query original:</strong> {{ query }}</p>
  <p><strong>Fontes utilizadas:</strong>
    {% for src in sources %}<span class="source-tag">{{ src }}</span>{% endfor %}
  </p>
  <p><strong>Chunks analisados:</strong> {{ chunks_used }}</p>
</div>

<div class="section">
  <h2>📊 Análise</h2>
  <div>{{ analysis | safe }}</div>
</div>

<div class="footer">
  <p>Gerado automaticamente pelo <strong>Anti-Fraud Agent (AFA)</strong></p>
  <p>Este relatório é baseado exclusivamente nos dados da base local. Verifique com o analista responsável antes de tomar ações.</p>
</div>
</body>
</html>"""


async def generate_report(query: str) -> dict:
    """
    Gera um relatório completo de análise de fraude.
    Retorna: { report_id, file_path, html_content, ... }
    """
    report_id = str(uuid.uuid4())[:8].upper()
    report_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # RAG retrieval
    retrieved = retrieve(query, top_k=settings.top_k_results)
    context = format_context(retrieved)
    sources = list({item["source_file"] for item in retrieved})

    # Prompt para relatório
    report_prompt = f"""Gere um relatório executivo de antifraude baseado EXCLUSIVAMENTE nos dados abaixo.
Sem introduções, sem explicações teóricas. Apenas fatos dos dados.

## Nível de Risco Geral: [🔴 Alto / 🟡 Médio / 🟢 Baixo] — decida com base nos dados

## Achados Principais
- [bullet com números concretos dos dados]

## Distribuição por Tipo de Fraude
- [tipo]: [contagem] casos

## Top Casos (maior score/risco)
- [identificador anonimizado] | score: X | tipo: Y | histórico: Z fraudes

## Regiões com Maior Incidência
- [região]: [contagem]

## Ações Recomendadas
1. [ação específica baseada nos dados]
2. [ação específica baseada nos dados]
3. [ação específica baseada nos dados]

---
Pergunta original: {query}

Dados:
{context}"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": report_prompt},
    ]

    llm = await get_llm_client()
    analysis_text = await llm.chat(messages, temperature=0.15)

    # Converte markdown básico para HTML
    analysis_html = analysis_text.replace("\n## ", "</p><h3>").replace("\n### ", "</p><h4>")
    analysis_html = f"<p>{analysis_html}</p>"

    # Renderiza template
    template = Template(REPORT_TEMPLATE)
    html_content = template.render(
        report_id=report_id,
        report_date=report_date,
        query=query,
        analysis=analysis_text.replace("\n", "<br>"),
        sources=sources,
        chunks_used=len(retrieved),
    )

    # Salva arquivo
    reports_dir = Path(settings.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    file_name = f"relatorio_antifraude_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    file_path = reports_dir / file_name

    file_path.write_text(html_content, encoding="utf-8")
    logger.info(f"Relatório gerado: {file_path}")

    return {
        "report_id": report_id,
        "file_name": file_name,
        "file_path": str(file_path),
        "analysis": analysis_text,
        "sources": sources,
        "chunks_used": len(retrieved),
        "generated_at": report_date,
    }
