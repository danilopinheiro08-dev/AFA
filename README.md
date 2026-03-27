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
| LLM (padrão) | Groq API (llama-3.1-70b) |
| LLM (local) | Ollama (qwen2.5:7b) |
| RAG | ChromaDB + sentence-transformers (PT-BR) |
| Frontend | React + Vite + TypeScript |
| Guardrails | Escopo, PII, Prompt Injection |

## Instalação Rápida

### Windows
```
1. Duplo clique em install.bat
2. Configure GROQ_API_KEY em backend/.env
3. Duplo clique em start.bat
4. Acesse http://localhost:5173
```

### Linux / Mac
```bash
chmod +x install.sh start.sh
./install.sh
# Configure backend/.env com sua GROQ_API_KEY
./start.sh
```

## Configuração do LLM

### Opção 1: Groq API (recomendado — mais rápido)
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_sua_chave_aqui
GROQ_MODEL=llama-3.1-70b-versatile
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
