#!/usr/bin/env python3
"""
Gerador de CSV de amostra para o Anti-Fraud Agent.
Gera ~5000 registros com todos os tipos de fraude em telecomunicações.
Execute: python generate_sample_data.py
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)
np.random.seed(42)

# ── Configurações ──────────────────────────────────────────────────────────
N_ROWS = 5000
OUTPUT_DIR = Path(__file__).parent / "data" / "csv"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "base_fraudes_amostra.csv"

# ── Dados de referência ────────────────────────────────────────────────────
SEGMENTOS = ["Claro Móvel", "Claro Residencial", "Claro TV", "NET", "Claro Empresas"]
PRODUTOS = [
    "Controle", "Pós-Pago", "Pré-Pago", "Plano Família",
    "Fibra 200MB", "Fibra 500MB", "Fibra 1GB",
    "TV HD", "TV Plus", "Combo Família",
    "CNPJ Básico", "CNPJ Avançado",
]
REGIOES = ["SP-Capital", "SP-Interior", "RJ", "MG", "RS", "PR", "BA", "PE", "CE", "DF"]
CANAIS = ["E-COMMERCE", "TELEVENDAS B2C", "LOJA FÍSICA", "RETENÇÃO", "APP"]
CAMPANHAS = ["REC-100 - FPD", "REC-200 - Automático", "PROMO-500 - Móvel", "CAMP-VIP"]
STATUS_PEDIDO = ["APROVADO", "CANCELADO", "PENDENTE", "BLOQUEADO"]

TIPOS_FRAUDE = [
    "Fraude de Subscrição",
    "Fraude de Alto Uso (SMS)",
    "Fraude de Alto Uso (Dados)",
    "Chargeback",
    "Clonagem de SIM",
    "Fraude de Identidade",
    "Fraude de Cancelamento",
    "Conta Mula",
    "Fraude Corporativa",
    "Falso Positivo",
]

def random_cpf():
    digits = [random.randint(0, 9) for _ in range(11)]
    return f"{digits[0]}{digits[1]}{digits[2]}.{digits[3]}{digits[4]}{digits[5]}.{digits[6]}{digits[7]}{digits[8]}-{digits[9]}{digits[10]}"

def random_phone():
    ddd = random.choice(["11","21","31","41","51","61","71","81","85","62"])
    num = random.randint(90000000, 99999999)
    return f"({ddd}) 9{num}"

def random_date(start_days_ago=365):
    base = datetime.now() - timedelta(days=start_days_ago)
    return base + timedelta(days=random.randint(0, start_days_ago))

# ── Pool de CPFs ────────────────────────────────────────────────────────────
print("Gerando pool de clientes...")
N_CLIENTES = 1200
clientes = []
for i in range(N_CLIENTES):
    is_blacklist = random.random() < 0.08
    clientes.append({
        "cpf": random_cpf(),
        "telefone": random_phone(),
        "regiao": random.choice(REGIOES),
        "blacklist": is_blacklist,
        "historico_fraude": random.randint(0, 5) if is_blacklist else 0,
        "score_credito": random.randint(200, 400) if is_blacklist else random.randint(500, 900),
    })

# ── Gerar registros ──────────────────────────────────────────────────────────
print(f"Gerando {N_ROWS} registros de pedidos/fraudes...")
rows = []

for i in range(N_ROWS):
    cliente = random.choice(clientes)
    data_pedido = random_date(365)
    segmento = random.choice(SEGMENTOS)
    produto = random.choice(PRODUTOS)
    canal = random.choice(CANAIS)
    regiao = cliente["regiao"]
    
    # Define se é fraude (30% dos registros)
    is_fraude = random.random() < 0.30 or cliente["blacklist"]
    
    # Define tipo de fraude
    tipo_fraude = None
    flag_fraude = 0
    score_fraude = 0.0
    
    if is_fraude:
        tipo_fraude = random.choice(TIPOS_FRAUDE)
        flag_fraude = 1 if tipo_fraude != "Falso Positivo" else 0
        score_fraude = round(random.uniform(0.65, 0.99), 3)
    else:
        score_fraude = round(random.uniform(0.01, 0.35), 3)

    # Métricas de uso
    uso_normal_sms = random.randint(0, 20)
    if tipo_fraude == "Fraude de Alto Uso (SMS)":
        sms_mes = random.randint(400, 500)  # anomalia!
        dados_gb = round(random.uniform(0.1, 2.0), 2)
    elif tipo_fraude == "Fraude de Alto Uso (Dados)":
        sms_mes = random.randint(0, 10)
        dados_gb = round(random.uniform(50.0, 200.0), 2)  # anomalia!
    else:
        sms_mes = uso_normal_sms
        dados_gb = round(random.uniform(1.0, 20.0), 2)
    
    sms_historico_media = round(random.uniform(1, 15), 1)
    
    # Valores financeiros
    valor_plano = random.choice([29.9, 49.9, 79.9, 99.9, 149.9, 199.9, 299.9, 499.9])
    valor_fraude = round(valor_plano * random.uniform(1, 12), 2) if is_fraude else 0.0
    
    # Chargeback
    qtd_chargeback = 0
    if tipo_fraude == "Chargeback":
        qtd_chargeback = random.randint(1, 7)
    
    # Status do pedido
    if is_fraude and flag_fraude:
        status = random.choices(
            STATUS_PEDIDO, weights=[0.3, 0.4, 0.1, 0.2]
        )[0]
    else:
        status = random.choices(
            STATUS_PEDIDO, weights=[0.75, 0.10, 0.10, 0.05]
        )[0]

    row = {
        "id_pedido": f"PD-{1000000 + i}",
        "data_pedido": data_pedido.strftime("%Y-%m-%d"),
        "hora_pedido": data_pedido.strftime("%H:%M:%S"),
        "cpf_cliente": cliente["cpf"],
        "telefone": cliente["telefone"],
        "segmento": segmento,
        "produto": produto,
        "canal_venda": canal,
        "regiao": regiao,
        "campanha": random.choice(CAMPANHAS) if random.random() < 0.4 else "",
        "status_pedido": status,
        "valor_plano": valor_plano,
        "valor_fraude_estimado": valor_fraude,
        "qtd_sms_mes": sms_mes,
        "media_historica_sms": sms_historico_media,
        "variacao_sms_pct": round((sms_mes - sms_historico_media) / max(sms_historico_media, 1) * 100, 1),
        "uso_dados_gb": dados_gb,
        "qtd_chargeback": qtd_chargeback,
        "score_credito": cliente["score_credito"],
        "score_fraude": score_fraude,
        "flag_fraude": flag_fraude,
        "tipo_fraude": tipo_fraude if flag_fraude else "",
        "em_blacklist": int(cliente["blacklist"]),
        "historico_fraudes_anteriores": cliente["historico_fraude"],
        "regra_disparada": f"CTR-{random.choice([12, 28, 30, 42, 53, 61, 74])}" if is_fraude else "",
        "analista_responsavel": random.choice(["Carlos M.", "Ana L.", "Pedro R.", "Juliana S.", ""]),
        "status_tratativa": random.choice(["Aberta", "Em andamento", "Fechada", ""]) if is_fraude else "",
        "data_fechamento": (data_pedido + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d") if is_fraude and random.random() < 0.5 else "",
        "custo_operacional": round(random.uniform(10, 200), 2) if is_fraude else 0.0,
        "mes_referencia": data_pedido.strftime("%Y-%m"),
        "flag_novo_cliente": int(random.random() < 0.25),
        "dias_desde_ativacao": random.randint(1, 1825),
        "qtd_linhas_ativas": random.randint(1, 8),
    }
    rows.append(row)

df = pd.DataFrame(rows)

# ── Validar ──────────────────────────────────────────────────────────────────
print(f"\nEstatísticas do dataset:")
print(f"  Total de registros: {len(df):,}")
print(f"  Fraudes confirmadas: {df['flag_fraude'].sum():,} ({df['flag_fraude'].mean()*100:.1f}%)")
print(f"  Clientes em blacklist: {df['em_blacklist'].sum():,}")
print(f"  Valor total fraude: R$ {df['valor_fraude_estimado'].sum():,.2f}")
print(f"\n  Distribuição por tipo de fraude:")
fraude_df = df[df['tipo_fraude'] != '']
print(fraude_df['tipo_fraude'].value_counts().to_string())
print(f"\n  Distribuição por segmento:")
print(df['segmento'].value_counts().to_string())

# ── Salvar ──────────────────────────────────────────────────────────────────
df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
print(f"\n✅ CSV gerado: {OUTPUT_FILE}")
print(f"   Tamanho: {OUTPUT_FILE.stat().st_size / 1024:.0f} KB")
print(f"   Colunas ({len(df.columns)}): {', '.join(df.columns.tolist())}")

# Gera também uma blacklist separada
blacklist_df = df[df['em_blacklist'] == 1][
    ["cpf_cliente", "telefone", "regiao", "historico_fraudes_anteriores", "tipo_fraude", "score_fraude"]
].drop_duplicates(subset=["cpf_cliente"])

blacklist_file = OUTPUT_DIR / "blacklist.csv"
blacklist_df.to_csv(blacklist_file, index=False, encoding="utf-8-sig")
print(f"✅ Blacklist gerada: {blacklist_file} ({len(blacklist_df)} clientes)")
