import { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { UploadCloud, FileSpreadsheet, CheckCircle, XCircle, Loader, FolderOpen } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface FileStatus {
  name: string;
  size: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  result?: { rows: number; chunks: number; columns: string[] };
  error?: string;
  source?: 'upload' | 'path';
}

export default function Upload() {
  const [files, setFiles] = useState<FileStatus[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [localPath, setLocalPath] = useState('');
  const [pathLoading, setPathLoading] = useState(false);
  const [pathError, setPathError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = (newFiles: FileList) => {
    const accepted = Array.from(newFiles).filter((f) => f.name.endsWith('.csv'));
    const startIdx = files.length;
    const entries: FileStatus[] = accepted.map((f) => ({
      name: f.name, size: f.size, status: 'pending', progress: 0, source: 'upload',
    }));
    setFiles((prev) => [...prev, ...entries]);
    accepted.forEach((f, i) => uploadFile(f, startIdx + i));
  };

  const uploadFile = async (file: File, idx: number) => {
    setFiles((prev) => prev.map((f, i) => i === idx ? { ...f, status: 'uploading', progress: 40 } : f));
    const form = new FormData();
    form.append('file', file);
    try {
      const res = await fetch(`${API}/api/upload`, { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Erro no upload');
      setFiles((prev) => prev.map((f, i) => i === idx ? { ...f, status: 'success', progress: 100, result: data } : f));
    } catch (err: any) {
      setFiles((prev) => prev.map((f, i) => i === idx ? { ...f, status: 'error', progress: 0, error: err.message } : f));
    }
  };

  const ingestFromPath = async () => {
    if (!localPath.trim()) return;
    setPathLoading(true);
    setPathError('');
    const fileName = localPath.trim().split(/[/\\]/).pop() || localPath;
    const newEntry: FileStatus = {
      name: fileName, size: 0, status: 'uploading', progress: 50, source: 'path',
    };
    setFiles((prev) => [...prev, newEntry]);
    const idx = files.length;

    try {
      const res = await fetch(`${API}/api/ingest-path`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: localPath.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Erro ao ingerir');
      setFiles((prev) => prev.map((f, i) => i === idx ? { ...f, status: 'success', progress: 100, result: data } : f));
      setLocalPath('');
    } catch (err: any) {
      setPathError(err.message);
      setFiles((prev) => prev.map((f, i) => i === idx ? { ...f, status: 'error', progress: 0, error: err.message } : f));
    } finally {
      setPathLoading(false);
    }
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files) addFiles(e.dataTransfer.files);
  };

  const onInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) addFiles(e.target.files);
  };

  const fmtSize = (b: number) =>
    b > 1024 * 1024 ? `${(b / 1024 / 1024).toFixed(1)} MB` : b > 0 ? `${(b / 1024).toFixed(0)} KB` : '';

  return (
    <div className="upload-page">
      <div style={{ maxWidth: 680 }}>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 20, lineHeight: 1.6 }}>
          Indexe sua base de fraudes. Você pode fazer upload de arquivos ou referenciar um CSV já existente no disco pela pasta de Downloads ou qualquer caminho.
        </p>

        {/* ── Local path input ─────────────────────────────── */}
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-header">
            <span style={{ fontWeight: 600, fontSize: 13 }}><FolderOpen size={14} style={{ display: 'inline', marginRight: 6 }} />Referenciar CSV por caminho local</span>
          </div>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
            Informe o caminho completo do arquivo no seu computador. O servidor lê diretamente do disco e indexa.
          </p>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type="text"
              value={localPath}
              onChange={(e) => setLocalPath(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && ingestFromPath()}
              placeholder="/home/user/Downloads/fraudes.csv  ou  C:\Users\user\Downloads\fraudes.csv"
              style={{
                flex: 1,
                background: 'var(--bg)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                padding: '9px 14px',
                color: 'var(--text-primary)',
                fontFamily: 'monospace',
                fontSize: 12,
                outline: 'none',
              }}
            />
            <button
              className="btn btn-primary"
              onClick={ingestFromPath}
              disabled={pathLoading || !localPath.trim()}
            >
              {pathLoading ? <Loader size={14} style={{ animation: 'spin 1s linear infinite' }} /> : '→ Indexar'}
            </button>
          </div>
          {pathError && (
            <div style={{ fontSize: 12, color: 'var(--danger)', marginTop: 8 }}>❌ {pathError}</div>
          )}

          {/* Common path suggestions */}
          <div style={{ marginTop: 10, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {[
              '/home/danilo/Downloads/',
              '/home/danilo/Desktop/',
              '~/Downloads/',
            ].map((p) => (
              <button
                key={p}
                className="hint-chip"
                onClick={() => setLocalPath(p)}
                style={{ fontFamily: 'monospace', fontSize: 11 }}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* ── Drag-and-drop upload ─────────────────────────── */}
        <div
          className={`drop-zone ${dragOver ? 'drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
        >
          <div className="drop-zone-icon">📂</div>
          <h3>Arraste CSVs aqui ou clique para selecionar</h3>
          <p>Formatos aceitos: .csv (UTF-8 ou Latin-1)</p>
          <input ref={inputRef} type="file" accept=".csv" multiple style={{ display: 'none' }} onChange={onInputChange} />
        </div>

        {files.length > 0 && (
          <div className="file-list">
            {files.map((f, i) => (
              <div key={i} className="file-item">
                <div className="file-icon">
                  <FileSpreadsheet size={24} color="var(--info)" />
                </div>
                <div className="file-info">
                  <div className="file-name">
                    {f.name}
                    {f.source === 'path' && (
                      <span className="badge badge-gray" style={{ marginLeft: 8, fontSize: 10 }}>caminho local</span>
                    )}
                  </div>
                  <div className="file-meta">
                    {fmtSize(f.size)}
                    {f.result && ` · ${f.result.rows.toLocaleString()} linhas · ${f.result.chunks} chunks`}
                    {f.error && ` · ❌ ${f.error}`}
                  </div>
                  {f.result?.columns && (
                    <div className="file-meta" style={{ marginTop: 3 }}>
                      Colunas: {f.result.columns.slice(0, 6).join(', ')}
                      {f.result.columns.length > 6 && ` +${f.result.columns.length - 6}`}
                    </div>
                  )}
                  {f.status === 'uploading' && (
                    <div className="progress-bar"><div className="progress-fill" style={{ width: `${f.progress}%` }} /></div>
                  )}
                </div>
                <div>
                  {f.status === 'uploading' && <Loader size={18} color="var(--info)" style={{ animation: 'spin 1s linear infinite' }} />}
                  {f.status === 'success' && <CheckCircle size={18} color="var(--success)" />}
                  {f.status === 'error' && <XCircle size={18} color="var(--danger)" />}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="card" style={{ marginTop: 24 }}>
          <div className="card-header">
            <span style={{ fontWeight: 600, fontSize: 13 }}>💡 Bases suportadas</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {[
              ['base_fraudes_amostra.csv', 'Gerada automaticamente pelo sistema'],
              ['fraudes_carimbadas.csv', 'Pedidos marcados como fraude'],
              ['base_pedidos.csv', 'Todos os pedidos de venda'],
              ['blacklist.csv', 'Clientes bloqueados'],
              ['alarmes_cockpit.csv', 'Alertas do cockpit antifraude'],
              ['indicadores.csv', 'KPIs e métricas de hit rate'],
            ].map(([name, desc]) => (
              <div key={name} style={{ padding: '10px 12px', background: 'var(--bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                <div style={{ fontWeight: 500, fontSize: 12, color: 'var(--info)' }}>📄 {name}</div>
                <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 3 }}>{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
