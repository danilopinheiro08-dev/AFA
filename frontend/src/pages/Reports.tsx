import { useState, useEffect } from 'react';
import { FileText, Download, Loader, RefreshCw } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Report {
  name: string;
  size_kb: number;
  created_at: number;
  download_url: string;
}

export default function Reports() {
  const [query, setQuery] = useState('');
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [error, setError] = useState('');

  const fetchReports = async () => {
    setLoadingList(true);
    try {
      const res = await fetch(`${API}/api/reports`);
      const data = await res.json();
      setReports(data.reports || []);
    } catch {
      setReports([]);
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => { fetchReports(); }, []);

  const generateReport = async () => {
    if (!query.trim()) return;
    setGenerating(true);
    setError('');
    setResult(null);
    try {
      const res = await fetch(`${API}/api/reports`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Erro ao gerar relatório');
      setResult(data);
      fetchReports();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  };

  const fmtDate = (ts: number) =>
    new Date(ts * 1000).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });

  const PRESET_QUERIES = [
    'Gere um relatório executivo completo de fraudes do período atual',
    'Relatório de tipificação de fraudes por segmento (Móvel / Residencial)',
    'Análise de impacto financeiro de fraudes de subscrição',
    'Relatório de clientes na blacklist com histórico de fraude',
    'Diagnóstico de alarmes de alto risco no cockpit',
  ];

  return (
    <div className="reports-page">
      <div style={{ maxWidth: 720 }}>
        <div className="report-form">
          <label className="inp-label">Descreva o relatório que deseja gerar</label>
          <textarea
            className="inp"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ex: Gere um relatório executivo com os principais tipos de fraude, custo estimado e recomendações de ação..."
            rows={4}
          />

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7, margin: '12px 0' }}>
            {PRESET_QUERIES.map((q) => (
              <button
                key={q}
                className="hint-chip"
                onClick={() => setQuery(q)}
              >
                {q}
              </button>
            ))}
          </div>

          <button
            className="btn btn-primary"
            onClick={generateReport}
            disabled={generating || !query.trim()}
          >
            {generating
              ? <><Loader size={14} style={{ animation: 'spin 1s linear infinite' }} /> Gerando relatório...</>
              : <><FileText size={14} /> Gerar Relatório</>
            }
          </button>
        </div>

        {error && (
          <div style={{ background: 'rgba(231,76,60,0.1)', border: '1px solid rgba(231,76,60,0.3)', borderRadius: 'var(--radius-sm)', padding: '12px 16px', color: '#e74c3c', marginBottom: 20 }}>
            ❌ {error}
          </div>
        )}

        {result && (
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-header">
              <span style={{ fontWeight: 600 }}>✅ Relatório Gerado — ID: {result.report_id}</span>
              <a
                href={`${API}${result.download_url}`}
                target="_blank"
                rel="noreferrer"
                className="btn btn-ghost"
                style={{ fontSize: 12, padding: '6px 12px' }}
              >
                <Download size={13} /> Abrir Relatório
              </a>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
              Fontes: {result.sources?.join(', ') || 'N/A'} · {result.chunks_used} chunks analisados · {result.generated_at}
            </div>
            <div style={{
              background: 'var(--bg)',
              borderRadius: 'var(--radius-sm)',
              padding: '14px 16px',
              fontSize: 12.5,
              color: 'var(--text-secondary)',
              lineHeight: 1.7,
              maxHeight: 300,
              overflow: 'auto',
              whiteSpace: 'pre-wrap',
            }}>
              {result.analysis}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600 }}>📁 Relatórios Anteriores</h3>
          <button className="btn btn-ghost" onClick={fetchReports} style={{ fontSize: 12, padding: '5px 10px' }}>
            <RefreshCw size={12} /> Atualizar
          </button>
        </div>

        {loadingList ? (
          <div style={{ textAlign: 'center', padding: 32, color: 'var(--text-muted)' }}>
            <Loader size={20} style={{ animation: 'spin 1s linear infinite' }} />
          </div>
        ) : reports.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📄</div>
            <h3>Nenhum relatório ainda</h3>
            <p>Gere seu primeiro relatório usando o formulário acima</p>
          </div>
        ) : (
          <div className="reports-list">
            {reports.map((r, i) => (
              <div key={i} className="report-item">
                <div className="report-icon">📑</div>
                <div className="report-info">
                  <div className="report-name">{r.name}</div>
                  <div className="report-meta">{r.size_kb} KB · {fmtDate(r.created_at)}</div>
                </div>
                <a
                  href={`${API}${r.download_url}`}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-ghost"
                  style={{ fontSize: 12, padding: '6px 10px' }}
                >
                  <Download size={13} />
                </a>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
