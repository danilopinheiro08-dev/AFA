import { useEffect, useState } from 'react';
import { AlertTriangle, RefreshCw, Bot } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const DEMO_ALERTS = [
  {
    id: 'a1',
    title: 'Alto uso de SMS — Padrão Anômalo',
    description: 'Cliente com histórico de 3 SMS/mês passou a consumir 500 SMS em 48h. Indicador de fraude de subscrição ou uso fraudulento de plano.',
    risk_level: 'high',
    source_file: 'base_pedidos.csv',
    detected_at: '2026-03-26 22:00',
    recommended_action: 'Verificar identidade do titular. Checar na blacklist.',
  },
  {
    id: 'a2',
    title: 'Fraude de Subscrição — Residencial',
    description: 'Múltiplos contratos residenciais novos com mesmo CPF em regiões distintas. Possível uso de documento de terceiro.',
    risk_level: 'high',
    source_file: 'fraudes_carimbadas.csv',
    detected_at: '2026-03-26 21:30',
    recommended_action: 'Cancelar contratos pendentes. Iniciar análise de KYC.',
  },
  {
    id: 'a3',
    title: 'Aumento Atípico de Cancelamentos — Claro Móvel',
    description: 'Segmento Claro Móvel apresenta +18% de cancelamentos vs. mediana histórica. Possível campanha de fraude coordenada.',
    risk_level: 'medium',
    source_file: 'alarmes_cockpit.csv',
    detected_at: '2026-03-26 20:15',
    recommended_action: 'Revisar regras de cancelamento automático. Alertar equipe.',
  },
  {
    id: 'a4',
    title: 'Falso Positivo Detectado — Regra CTR-12',
    description: 'Regra CTR-12 com taxa de falso positivo de 34% no último período. Revisar threshold.',
    risk_level: 'medium',
    source_file: 'indicadores.csv',
    detected_at: '2026-03-26 19:00',
    recommended_action: 'Ajustar threshold da regra. Analisar casos marcados.',
  },
  {
    id: 'a5',
    title: 'Cliente na Blacklist — Novo Pedido',
    description: 'Pedido #PD-991234 iniciado por CPF presente na blacklist de fraude confirmada.',
    risk_level: 'high',
    source_file: 'blacklist.csv',
    detected_at: '2026-03-26 18:45',
    recommended_action: 'Bloquear pedido imediatamente. Registrar ocorrência.',
  },
  {
    id: 'a6',
    title: 'Chargeback Recorrente — Mesmo Endereço',
    description: 'Mesmo endereço de entrega com 7 chargebacks nos últimos 30 dias por CPFs distintos.',
    risk_level: 'medium',
    source_file: 'base_pedidos.csv',
    detected_at: '2026-03-26 17:30',
    recommended_action: 'Bloquear CEP/endereço. Investigar rede de fraude.',
  },
];

const riskLabel: Record<string, string> = {
  high: '🔴 Risco Alto',
  medium: '🟡 Risco Médio',
  low: '🟢 Risco Baixo',
};

const riskClass: Record<string, string> = {
  high: 'badge-red',
  medium: 'badge-yellow',
  low: 'badge-green',
};

export default function Alerts() {
  const [alerts, setAlerts] = useState(DEMO_ALERTS);
  const [filter, setFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');
  const [analyzing, setAnalyzing] = useState<string | null>(null);
  const [diagnoses, setDiagnoses] = useState<Record<string, string>>({});

  const filtered = filter === 'all' ? alerts : alerts.filter((a) => a.risk_level === filter);

  const analyzeAlert = async (alert: typeof DEMO_ALERTS[0]) => {
    setAnalyzing(alert.id);
    try {
      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: `Analise este alarme: "${alert.title}". Descrição: ${alert.description}. Gere um diagnóstico rápido com causa raiz, impacto estimado e próximos passos.`,
          stream: false,
        }),
      });
      const data = await res.json();
      setDiagnoses((prev) => ({ ...prev, [alert.id]: data.response }));
    } catch {
      setDiagnoses((prev) => ({ ...prev, [alert.id]: '❌ Erro ao analisar com IA.' }));
    } finally {
      setAnalyzing(null);
    }
  };

  const counts = {
    high: alerts.filter((a) => a.risk_level === 'high').length,
    medium: alerts.filter((a) => a.risk_level === 'medium').length,
    low: alerts.filter((a) => a.risk_level === 'low').length,
  };

  return (
    <div className="alerts-page">
      {/* Stats */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        {[
          { label: 'Críticos', count: counts.high, cls: 'badge-red', filter: 'high' as const },
          { label: 'Médios', count: counts.medium, cls: 'badge-yellow', filter: 'medium' as const },
          { label: 'Baixos', count: counts.low, cls: 'badge-green', filter: 'low' as const },
        ].map((s) => (
          <button
            key={s.filter}
            onClick={() => setFilter((f) => (f === s.filter ? 'all' : s.filter))}
            className={`badge ${s.cls}`}
            style={{
              cursor: 'pointer', padding: '8px 16px', fontSize: 13,
              opacity: filter !== 'all' && filter !== s.filter ? 0.4 : 1,
            }}
          >
            {s.label}: {s.count}
          </button>
        ))}
        <button
          onClick={() => setFilter('all')}
          className="btn btn-ghost"
          style={{ marginLeft: 'auto', fontSize: 12, padding: '6px 12px' }}
        >
          <RefreshCw size={13} />
          Todos ({alerts.length})
        </button>
      </div>

      <div className="alerts-grid">
        {filtered.map((alert) => (
          <div key={alert.id} className={`alert-card ${alert.risk_level}`}>
            <div className="alert-card-header">
              <div>
                <div className="alert-card-title">
                  <AlertTriangle size={14} style={{ display: 'inline', marginRight: 6 }} />
                  {alert.title}
                </div>
                <div style={{ marginTop: 6 }}>
                  <span className={`badge ${riskClass[alert.risk_level]}`}>
                    {riskLabel[alert.risk_level]}
                  </span>
                </div>
              </div>
            </div>

            <div className="alert-card-desc">{alert.description}</div>

            {diagnoses[alert.id] && (
              <div style={{
                marginTop: 12, background: 'var(--bg)', borderRadius: 'var(--radius-sm)',
                padding: '10px 12px', fontSize: 12, color: 'var(--text-secondary)',
                borderLeft: '3px solid var(--primary)', lineHeight: 1.6,
              }}>
                <strong style={{ color: 'var(--primary)', fontSize: 11 }}>🤖 Diagnóstico IA:</strong><br />
                {diagnoses[alert.id]}
              </div>
            )}

            <div className="alert-card-footer">
              <span>📁 {alert.source_file}</span>
              <span>🕐 {alert.detected_at}</span>
            </div>

            <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
              <button
                className="btn btn-primary"
                style={{ fontSize: 11.5, padding: '6px 12px' }}
                onClick={() => analyzeAlert(alert)}
                disabled={analyzing === alert.id}
              >
                {analyzing === alert.id ? (
                  <><RefreshCw size={12} style={{ animation: 'spin 1s linear infinite' }} /> Analisando...</>
                ) : (
                  <><Bot size={12} /> Analisar com IA</>
                )}
              </button>
              <div style={{ flex: 1, fontSize: 11.5, color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}>
                💡 {alert.recommended_action}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
