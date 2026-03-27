import { useState, useRef, useEffect, KeyboardEvent, DragEvent, ClipboardEvent } from 'react';
import { Send, Bot, User, ShieldAlert, Image as ImageIcon, X, Loader, Eye } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  sources?: string[];
  intent?: string;
  isStreaming?: boolean;
  imagePreview?: string;  // base64 data URL for display
  visionModel?: string;
}

const QUICK_HINTS = [
  'Quais clientes com maior risco de fraude de subscrição?',
  'Quais os tipos de fraude mais recorrentes?',
  'Quantifique o custo de fraude do último período',
  'Detecte anomalias de alto uso de SMS',
  'Gere diagnóstico dos alarmes críticos',
];

function formatMessage(text: string) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.*?)__/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>');
}

const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/bmp'];

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      role: 'ai',
      content:
        '🔍 **Olá! Sou o Agente Antifraude.**\n\nEstou pronto para analisar sua base de fraudes, detectar padrões suspeitos e gerar diagnósticos.\n\n📂 Faça upload de CSVs pela aba **Upload** e depois pergunte qualquer coisa.\n\n🖼️ **Novo:** Cole ou arraste um gráfico/dashboard diretamente no chat para análise visual por IA!',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingImage, setPendingImage] = useState<{ file: File; preview: string } | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ── Image handling ────────────────────────────────────────────────────
  const handleImageFile = (file: File) => {
    if (!IMAGE_TYPES.includes(file.type)) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      setPendingImage({ file, preview: e.target?.result as string });
    };
    reader.readAsDataURL(file);
  };

  const onPaste = (e: ClipboardEvent<HTMLTextAreaElement>) => {
    const items = e.clipboardData.items;
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        const file = item.getAsFile();
        if (file) {
          e.preventDefault();
          handleImageFile(file);
        }
      }
    }
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files).filter(f => IMAGE_TYPES.includes(f.type));
    if (files.length > 0) handleImageFile(files[0]);
  };

  // ── Send message (text or image) ──────────────────────────────────────
  const sendMessage = async (text?: string) => {
    const msg = (text || input).trim();
    if ((!msg && !pendingImage) || loading) return;

    const displayMsg = msg || (pendingImage ? '🖼️ [Imagem para análise]' : '');
    const capturedImage = pendingImage;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: displayMsg,
      imagePreview: capturedImage?.preview,
    };
    const aiMsgId = (Date.now() + 1).toString();
    const aiMsg: Message = {
      id: aiMsgId,
      role: 'ai',
      content: '',
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, aiMsg]);
    setInput('');
    setPendingImage(null);
    setLoading(true);

    try {
      // If there's an image, use vision endpoint
      if (capturedImage) {
        const form = new FormData();
        form.append('file', capturedImage.file);
        form.append('question', msg || 'Analise esta imagem e identifique padrões de fraude, anomalias ou informações relevantes para antifraude.');

        const res = await fetch(`${API}/api/vision`, { method: 'POST', body: form });
        const data = await res.json();

        if (!res.ok) throw new Error(data.detail || 'Erro na análise visual');

        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMsgId
              ? { ...m, content: data.analysis, isStreaming: false, visionModel: data.model }
              : m
          )
        );
      } else {
        // Text: use streaming SSE
        const url = `${API}/api/chat/stream?message=${encodeURIComponent(msg)}`;
        const eventSource = new EventSource(url);
        let buffer = '';

        eventSource.onmessage = (e) => {
          if (e.data === '[DONE]') {
            eventSource.close();
            setMessages((prev) =>
              prev.map((m) => m.id === aiMsgId ? { ...m, isStreaming: false } : m)
            );
            setLoading(false);
            return;
          }
          try {
            const parsed = JSON.parse(e.data);
            if (parsed.token) {
              buffer += parsed.token;
              setMessages((prev) =>
                prev.map((m) => m.id === aiMsgId ? { ...m, content: buffer } : m)
              );
            }
          } catch {}
        };

        eventSource.onerror = () => {
          eventSource.close();
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMsgId
                ? { ...m, content: '❌ Erro de conexão com o servidor.', isStreaming: false }
                : m
            )
          );
          setLoading(false);
        };
        return; // don't set loading=false here, SSE handles it
      }
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMsgId
            ? { ...m, content: `❌ Erro: ${err.message}`, isStreaming: false }
            : m
        )
      );
    } finally {
      if (capturedImage) setLoading(false);
    }
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-page">
      <div
        className="chat-messages"
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
      >
        {messages.map((msg) => (
          <div key={msg.id} className={`chat-msg ${msg.role === 'user' ? 'user' : ''}`}>
            <div className={`msg-avatar ${msg.role === 'ai' ? 'ai' : 'user-av'}`}>
              {msg.role === 'ai' ? <ShieldAlert size={16} /> : <User size={15} />}
            </div>
            <div className="msg-bubble">
              {/* Image preview in user message */}
              {msg.imagePreview && (
                <div style={{ marginBottom: 10 }}>
                  <img
                    src={msg.imagePreview}
                    alt="Imagem enviada"
                    style={{ maxWidth: '100%', maxHeight: 280, borderRadius: 8, border: '1px solid var(--border)' }}
                  />
                </div>
              )}

              {msg.isStreaming && !msg.content ? (
                <div className="typing-dots"><span /><span /><span /></div>
              ) : (
                <div dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }} />
              )}
              {msg.isStreaming && msg.content && (
                <span style={{ display: 'inline-block', width: '2px', height: '14px', background: 'var(--primary)', marginLeft: '2px', animation: 'pulse 0.8s infinite' }} />
              )}
              {/* Vision model badge */}
              {msg.visionModel && (
                <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span className="badge badge-blue"><Eye size={10} /> {msg.visionModel}</span>
                </div>
              )}
              {msg.sources && msg.sources.length > 0 && (
                <div className="msg-sources">
                  <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Fontes:</span>
                  {msg.sources.map((s) => <span key={s} className="source-tag">{s}</span>)}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-area">
        {/* Pending image preview */}
        {pendingImage && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10,
            background: 'var(--bg-card)', borderRadius: 'var(--radius-sm)',
            padding: '8px 12px', border: '1px solid var(--border)',
          }}>
            <img src={pendingImage.preview} alt="" style={{ width: 48, height: 48, objectFit: 'cover', borderRadius: 6 }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, fontWeight: 500 }}>{pendingImage.file.name}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                🤖 Será analisado com llama-3.2-11b-vision — adicione uma pergunta opcional abaixo
              </div>
            </div>
            <button
              onClick={() => setPendingImage(null)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
            >
              <X size={16} />
            </button>
          </div>
        )}

        <div className="chat-input-hints">
          {QUICK_HINTS.map((hint) => (
            <button key={hint} className="hint-chip" onClick={() => sendMessage(hint)}>{hint}</button>
          ))}
          <button
            className="hint-chip"
            onClick={() => fileInputRef.current?.click()}
            style={{ borderColor: 'var(--info)', color: 'var(--info)' }}
          >
            🖼️ Anexar imagem
          </button>
        </div>

        <div className="chat-input-row">
          <textarea
            ref={textareaRef}
            className="chat-input"
            placeholder={pendingImage ? 'Pergunta sobre a imagem (opcional)...' : 'Pergunte sobre fraudes ou cole/arraste um gráfico aqui...'}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            onPaste={onPaste}
            rows={1}
          />
          {pendingImage ? (
            <button
              className="btn btn-primary"
              onClick={() => sendMessage()}
              disabled={loading}
              style={{ height: 46, paddingInline: 14 }}
              title="Analisar imagem com IA"
            >
              {loading ? <Loader size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <ImageIcon size={16} />}
            </button>
          ) : (
            <button
              className="btn btn-primary"
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              style={{ height: 46, paddingInline: 16 }}
            >
              {loading ? <Loader size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <Send size={16} />}
            </button>
          )}
        </div>

        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, textAlign: 'center' }}>
          💡 Cole um gráfico do Power BI (Ctrl+V) ou arraste uma imagem para análise visual com IA
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={(e) => { if (e.target.files?.[0]) handleImageFile(e.target.files[0]); }}
      />
    </div>
  );
}
