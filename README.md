# 🛡️ Anti-Fraud Agent (AFA)

Sistema de IA para análise proativa de fraudes em telecomunicações.

## O que faz

- 💬 **Chatbot** — Pergunte sobre fraudes em linguagem natural
- 🚨 **Cockpit de Alarmes** — Alertas inteligentes com diagnóstico automático por IA
- 📂 **Upload de CSVs** — Ingere sua base de fraudes localmente (ChromaDB)
- 📑 **Relatórios** — Geração automática de diagnósticos em HTML

## Stack

| Componente | Tecnologia |
|---|---|
| Backend | FastAPI + Python 3.11 |
| LLM (padrão) | Groq API (llama-3.3-70b-versatile) |
| LLM (local) | Ollama (qwen2.5:7b) |
| RAG | ChromaDB + sentence-transformers (PT-BR) |
| Frontend | React + Vite + TypeScript |
| Guardrails | Escopo, PII, Prompt Injection |

## Instalação Rápida

### Windows — Instalador automático (recomendado)

**Opção A: `.exe` gerado previamente**
```
1. Duplo clique em AFA-Setup.exe
2. Aguarde ~5 minutos (instala Python, Node, dependências)
3. Cole sua GROQ_API_KEY quando solicitado
4. Sistema inicia automaticamente
```

**Opção B: PowerShell (sem precisar gerar .exe)**
```powershell
# Com a chave já em mãos:
powershell -ExecutionPolicy Bypass -File setup.ps1 -GroqKey "gsk_suachave"

# Ou interativo (pergunta a chave durante o setup):
powershell -ExecutionPolicy Bypass -File setup.ps1
```

O script instala Git, Python 3.11 e Node.js automaticamente via `winget` se não estiverem presentes, e cria um atalho na Área de Trabalho.

**Gerar o AFA-Setup.exe** (rodar uma vez na máquina do desenvolvedor):
```powershell
powershell -ExecutionPolicy Bypass -File build-exe.ps1
```

---

### Linux / Mac

```bash
git clone https://github.com/danilopinheiro08-dev/AFA.git && cd AFA && chmod +x install.sh start.sh && ./install.sh
```

```bash
# Edite backend/.env com sua GROQ_API_KEY e inicie:
./start.sh
```

Acesse: http://localhost:5173

## Configuração do LLM

### Opção 1: Groq API (recomendado — mais rápido)
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_sua_chave_aqui
GROQ_MODEL=llama-3.3-70b-versatile
```
Obtenha sua chave grátis em: https://console.groq.com

### Opção 2: Ollama local (100% privado, sem egresso)
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
```
```bash
ollama pull qwen2.5:7b
```

## Uso

1. **Suba seus CSVs** pela aba Upload (base de fraudes, pedidos, blacklist)
2. **Pergunte no chat**: "Quais clientes com maior risco de fraude de subscrição?"
3. **Analise alarmes** no Cockpit — clique em "Analisar com IA"
4. **Gere relatórios** com diagnóstico automático

## Sobre Privacidade / Egresso de Dados

- Com **Groq**: apenas o trecho relevante dos dados (extraído pelo RAG) vai para a API. Os CSVs brutos ficam 100% locais.
- Com **Ollama**: zero egresso. Tudo roda na sua máquina.

## Requisitos

- Python 3.11+
- Node.js 18+
- 4GB RAM (mínimo) | 8GB+ (recomendado para Ollama)
