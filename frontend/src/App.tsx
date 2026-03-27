import { useState, useEffect } from 'react';
import './index.css';
import Chat from './pages/Chat';
import Upload from './pages/Upload';
import Alerts from './pages/Alerts';
import Reports from './pages/Reports';
import {
  MessageSquare, Upload as UploadIcon, Bell, FileText,
  ShieldAlert, Database,
} from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

type Page = 'chat' | 'alerts' | 'upload' | 'reports';

const navItems: { id: Page; label: string; icon: React.ReactNode; sub?: string }[] = [
  { id: 'chat', label: 'Chatbot', icon: <MessageSquare size={16} />, sub: 'Análise por IA' },
  { id: 'alerts', label: 'Alarmes', icon: <Bell size={16} />, sub: 'Cockpit Inteligente' },
  { id: 'upload', label: 'Upload CSV', icon: <UploadIcon size={16} />, sub: 'Base de dados' },
  { id: 'reports', label: 'Relatórios', icon: <FileText size={16} />, sub: 'Geração automática' },
];

const pageTitles: Record<Page, { title: string; sub: string; icon: string }> = {
  chat: { title: 'Chatbot Antifraude', sub: 'Análise em linguagem natural com IA', icon: '💬' },
  alerts: { title: 'Cockpit de Alarmes', sub: 'Alertas inteligentes com diagnóstico automático', icon: '🚨' },
  upload: { title: 'Upload de Dados', sub: 'Indexe sua base de fraudes para análise', icon: '📂' },
  reports: { title: 'Relatórios', sub: 'Geração automática de diagnósticos', icon: '📑' },
};

export default function App() {
  const [page, setPage] = useState<Page>('chat');
  const [stats, setStats] = useState<{ total_chunks: number; csv_files: string[] } | null>(null);
  const [provider, setProvider] = useState('groq');

  useEffect(() => {
    fetch(`${API}/api/stats`)
      .then((r) => r.json())
      .then((d) => setStats(d))
      .catch(() => {});
    fetch(`${API}/api/health`)
      .then((r) => r.json())
      .then((d) => setProvider(d.llm_provider))
      .catch(() => {});
  }, []);

  const pt = pageTitles[page];

  return (
    <div className="app-layout">
      {/* SIDEBAR */}
      <nav className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon">🛡️</div>
          <div>
            <div className="logo-text">AFA</div>
            <div className="logo-sub">Anti-Fraud Agent</div>
          </div>
        </div>

        <div className="sidebar-nav">
          <div className="nav-section-label">Menu</div>
          {navItems.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${page === item.id ? 'active' : ''}`}
              onClick={() => setPage(item.id)}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}

          {stats && (
            <>
              <div className="nav-section-label" style={{ marginTop: 16 }}>Base de Dados</div>
              <div style={{ padding: '8px 10px', fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <Database size={12} />
                  <span>{stats.total_chunks.toLocaleString()} chunks indexados</span>
                </div>
                {stats.csv_files.map((f) => (
                  <div key={f} style={{ fontSize: 11, color: 'var(--text-muted)', paddingLeft: 18 }}>📄 {f}</div>
                ))}
                {stats.csv_files.length === 0 && (
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    Nenhum CSV carregado
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        <div className="sidebar-footer">
          <div className="provider-badge">
            <span className="dot" />
            {provider === 'groq' ? '⚡ Groq API' : '🖥️ Ollama Local'}
          </div>
        </div>
      </nav>

      {/* MAIN */}
      <div className="main-content">
        <div className="page-header">
          <div className="page-header-icon">{pt.icon}</div>
          <div>
            <h1>{pt.title}</h1>
            <div className="page-sub">{pt.sub}</div>
          </div>
          {stats && (
            <div style={{ marginLeft: 'auto', display: 'flex', gap: 16 }}>
              <div className="stat-item">
                <span className="stat-num" style={{ fontSize: 20 }}>
                  {stats.csv_files.length}
                </span>
                <span className="stat-label">CSVs</span>
              </div>
              <div className="stat-item">
                <span className="stat-num" style={{ fontSize: 20 }}>
                  {stats.total_chunks.toLocaleString()}
                </span>
                <span className="stat-label">chunks</span>
              </div>
            </div>
          )}
        </div>

        {page === 'chat' && <Chat />}
        {page === 'alerts' && <Alerts />}
        {page === 'upload' && <Upload />}
        {page === 'reports' && <Reports />}
      </div>
    </div>
  );
}
