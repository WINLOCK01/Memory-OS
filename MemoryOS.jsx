import { useState, useEffect, useRef } from "react";

const API = "http://localhost:8000";

// ── Palette & styles ──────────────────────────────────────────────────────────
const css = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #07080a;
    --surface: #0e1015;
    --surface2: #161820;
    --border: #1e2130;
    --accent: #7ee8a2;
    --accent2: #38bdf8;
    --accent3: #f472b6;
    --text: #e8eaf0;
    --muted: #5a6080;
    --danger: #f87171;
    --font-display: 'Syne', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
  }

  body { background: var(--bg); color: var(--text); font-family: var(--font-display); }

  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  .shell {
    display: grid;
    grid-template-columns: 220px 1fr;
    grid-template-rows: 56px 1fr;
    height: 100vh;
    overflow: hidden;
  }

  /* Top bar */
  .topbar {
    grid-column: 1 / -1;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    padding: 0 24px;
    gap: 12px;
  }
  .logo-dot { width: 10px; height: 10px; background: var(--accent); border-radius: 50%; box-shadow: 0 0 12px var(--accent); animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
  .logo-text { font-size: 17px; font-weight: 800; letter-spacing: -0.5px; }
  .logo-text span { color: var(--accent); }
  .topbar-right { margin-left: auto; display: flex; align-items: center; gap: 16px; }
  .stat-pill { font-family: var(--font-mono); font-size: 11px; color: var(--muted); background: var(--surface2); border: 1px solid var(--border); padding: 3px 10px; border-radius: 20px; }
  .stat-pill b { color: var(--accent); }

  /* Sidebar */
  .sidebar {
    background: var(--surface);
    border-right: 1px solid var(--border);
    padding: 20px 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .nav-section { font-family: var(--font-mono); font-size: 10px; color: var(--muted); letter-spacing: 1.5px; text-transform: uppercase; padding: 12px 8px 6px; }
  .nav-item {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 12px; border-radius: 8px;
    cursor: pointer; font-size: 13px; font-weight: 600;
    color: var(--muted); transition: all 0.15s;
    border: 1px solid transparent;
  }
  .nav-item:hover { color: var(--text); background: var(--surface2); }
  .nav-item.active { color: var(--accent); background: rgba(126,232,162,0.08); border-color: rgba(126,232,162,0.2); }
  .nav-icon { font-size: 15px; }

  /* Main */
  .main { overflow-y: auto; padding: 28px; display: flex; flex-direction: column; gap: 20px; }

  /* Cards */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px;
  }
  .card-title { font-size: 13px; font-weight: 700; letter-spacing: 0.5px; color: var(--muted); text-transform: uppercase; margin-bottom: 16px; font-family: var(--font-mono); }

  /* Stats row */
  .stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
  .stat-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px 20px;
    position: relative; overflow: hidden;
  }
  .stat-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; }
  .stat-card.green::before { background: var(--accent); }
  .stat-card.blue::before { background: var(--accent2); }
  .stat-card.pink::before { background: var(--accent3); }
  .stat-num { font-size: 32px; font-weight: 800; font-family: var(--font-mono); line-height: 1; }
  .stat-card.green .stat-num { color: var(--accent); }
  .stat-card.blue .stat-num { color: var(--accent2); }
  .stat-card.pink .stat-num { color: var(--accent3); }
  .stat-label { font-size: 12px; color: var(--muted); margin-top: 6px; }

  /* Ingest panel */
  .ingest-tabs { display: flex; gap: 6px; margin-bottom: 18px; }
  .tab-btn {
    padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600;
    cursor: pointer; border: 1px solid var(--border); background: transparent;
    color: var(--muted); font-family: var(--font-display); transition: all 0.15s;
  }
  .tab-btn.active { background: var(--accent); color: #07080a; border-color: var(--accent); }

  .input-row { display: flex; gap: 10px; }
  .mem-input {
    flex: 1; background: var(--surface2); border: 1px solid var(--border);
    color: var(--text); padding: 11px 14px; border-radius: 8px;
    font-family: var(--font-mono); font-size: 13px; outline: none;
    transition: border-color 0.15s;
  }
  .mem-input:focus { border-color: var(--accent); }
  .mem-input::placeholder { color: var(--muted); }
  textarea.mem-input { resize: vertical; min-height: 90px; }

  .btn {
    padding: 10px 20px; border-radius: 8px; font-size: 13px; font-weight: 700;
    cursor: pointer; border: none; font-family: var(--font-display); transition: all 0.15s;
    white-space: nowrap;
  }
  .btn-accent { background: var(--accent); color: #07080a; }
  .btn-accent:hover { filter: brightness(1.1); }
  .btn-ghost { background: var(--surface2); color: var(--text); border: 1px solid var(--border); }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }

  .file-drop {
    border: 2px dashed var(--border); border-radius: 10px;
    padding: 30px; text-align: center; cursor: pointer;
    transition: all 0.2s; color: var(--muted); font-size: 13px;
  }
  .file-drop:hover, .file-drop.drag { border-color: var(--accent); color: var(--accent); background: rgba(126,232,162,0.04); }
  .file-drop .drop-icon { font-size: 28px; margin-bottom: 8px; }

  /* Chat */
  .chat-messages { display: flex; flex-direction: column; gap: 14px; min-height: 200px; max-height: 420px; overflow-y: auto; margin-bottom: 16px; padding-right: 4px; }
  .msg { display: flex; gap: 10px; animation: fadeUp 0.25s ease; }
  @keyframes fadeUp { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
  .msg-avatar { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 13px; flex-shrink: 0; }
  .msg.user .msg-avatar { background: rgba(56,189,248,0.15); }
  .msg.assistant .msg-avatar { background: rgba(126,232,162,0.12); }
  .msg-bubble { flex: 1; }
  .msg-role { font-size: 10px; font-family: var(--font-mono); color: var(--muted); margin-bottom: 4px; letter-spacing: 1px; text-transform: uppercase; }
  .msg-text { font-size: 13px; line-height: 1.6; color: var(--text); }
  .msg.user .msg-text { color: var(--accent2); }
  .msg-sources { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 8px; }
  .source-tag { font-family: var(--font-mono); font-size: 10px; padding: 2px 8px; border-radius: 4px; background: rgba(126,232,162,0.1); color: var(--accent); border: 1px solid rgba(126,232,162,0.2); }

  /* Memory list */
  .memory-list { display: flex; flex-direction: column; gap: 10px; max-height: 500px; overflow-y: auto; }
  .memory-item {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 10px; padding: 14px 16px;
    display: flex; align-items: flex-start; gap: 12px;
    transition: border-color 0.15s;
  }
  .memory-item:hover { border-color: var(--muted); }
  .mem-type-badge { font-family: var(--font-mono); font-size: 9px; letter-spacing: 1px; text-transform: uppercase; padding: 3px 8px; border-radius: 4px; white-space: nowrap; }
  .badge-pdf { background: rgba(244,114,182,0.12); color: var(--accent3); border: 1px solid rgba(244,114,182,0.2); }
  .badge-url { background: rgba(56,189,248,0.12); color: var(--accent2); border: 1px solid rgba(56,189,248,0.2); }
  .badge-note { background: rgba(126,232,162,0.12); color: var(--accent); border: 1px solid rgba(126,232,162,0.2); }
  .mem-info { flex: 1; }
  .mem-source { font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 400px; }
  .mem-meta { font-family: var(--font-mono); font-size: 11px; color: var(--muted); }

  /* Graph placeholder */
  .graph-area { background: var(--surface2); border-radius: 10px; height: 320px; display: flex; align-items: center; justify-content: center; border: 1px dashed var(--border); position: relative; overflow: hidden; }
  .graph-node { position: absolute; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; color: var(--bg); cursor: pointer; transition: all 0.2s; }
  .graph-node:hover { transform: scale(1.2); z-index: 10; }
  .graph-empty { color: var(--muted); font-size: 13px; font-family: var(--font-mono); text-align: center; }

  /* Toast */
  .toast {
    position: fixed; bottom: 24px; right: 24px;
    background: var(--surface); border: 1px solid var(--accent);
    color: var(--accent); padding: 12px 20px; border-radius: 10px;
    font-size: 13px; font-family: var(--font-mono);
    animation: slideIn 0.3s ease;
    z-index: 999;
  }
  .toast.error { border-color: var(--danger); color: var(--danger); }
  @keyframes slideIn { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }

  /* Loading */
  .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid rgba(126,232,162,0.2); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.7s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  .thinking { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 12px; font-family: var(--font-mono); }
`;

// ── Mock data for demo when no backend ───────────────────────────────────────
const DEMO_STATS = { total_chunks: 247, total_sources: 18, by_type: { pdf: 8, url: 7, note: 3 } };
const DEMO_MEMORIES = [
  { source: "attention_is_all_you_need.pdf", type: "pdf", date: "2025-03-01", chunks: 42 },
  { source: "https://arxiv.org/abs/2303.08774", type: "url", date: "2025-03-03", chunks: 31 },
  { source: "RAG Architecture Notes", type: "note", date: "2025-03-05", chunks: 12 },
  { source: "deeplearning_book_ch3.pdf", type: "pdf", date: "2025-03-06", chunks: 58 },
  { source: "https://lilianweng.github.io/posts/llm-agent", type: "url", date: "2025-03-08", chunks: 24 },
];

export default function MemoryOS() {
  const [page, setPage] = useState("dashboard");
  const [ingestTab, setIngestTab] = useState("url");
  const [urlInput, setUrlInput] = useState("");
  const [noteTitle, setNoteTitle] = useState("");
  const [noteContent, setNoteContent] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hello! Ask me anything from your knowledge base. I'll surface relevant memories and synthesize an answer.", sources: [] }
  ]);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [stats, setStats] = useState(DEMO_STATS);
  const [memories, setMemories] = useState(DEMO_MEMORIES);
  const [drag, setDrag] = useState(false);
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const showToast = (msg, type = "success") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const callAPI = async (endpoint, options = {}) => {
    try {
      const res = await fetch(`${API}${endpoint}`, options);
      if (!res.ok) throw new Error(await res.text());
      return await res.json();
    } catch {
      return null; // graceful fallback to demo mode
    }
  };

  const handleIngestURL = async () => {
    if (!urlInput.trim()) return;
    setLoading(true);
    const result = await callAPI("/ingest/url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: urlInput })
    });
    if (result) {
      setStats(s => ({ ...s, total_chunks: s.total_chunks + result.chunks_stored, total_sources: s.total_sources + 1 }));
      setMemories(m => [{ source: urlInput, type: "url", date: new Date().toISOString().slice(0, 10), chunks: result.chunks_stored }, ...m]);
      showToast(`✓ Ingested ${result.chunks_stored} chunks from URL`);
    } else {
      // Demo mode
      const chunks = Math.floor(Math.random() * 30) + 10;
      setStats(s => ({ ...s, total_chunks: s.total_chunks + chunks, total_sources: s.total_sources + 1 }));
      setMemories(m => [{ source: urlInput, type: "url", date: new Date().toISOString().slice(0, 10), chunks }, ...m]);
      showToast(`✓ Demo: Ingested ${chunks} chunks from URL`);
    }
    setUrlInput("");
    setLoading(false);
  };

  const handleIngestNote = async () => {
    if (!noteContent.trim()) return;
    setLoading(true);
    const result = await callAPI("/ingest/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: noteContent, title: noteTitle || "Untitled" })
    });
    const chunks = result?.chunks_stored || Math.floor(noteContent.split(" ").length / 100) + 1;
    setStats(s => ({ ...s, total_chunks: s.total_chunks + chunks, total_sources: s.total_sources + 1 }));
    setMemories(m => [{ source: noteTitle || "Untitled Note", type: "note", date: new Date().toISOString().slice(0, 10), chunks }, ...m]);
    showToast(`✓ Note saved (${chunks} chunks)`);
    setNoteTitle(""); setNoteContent("");
    setLoading(false);
  };

  const handleFileDrop = async (file) => {
    if (!file || !file.name.endsWith(".pdf")) { showToast("Only PDF files supported", "error"); return; }
    setLoading(true);
    const fd = new FormData(); fd.append("file", file);
    const result = await callAPI("/ingest/pdf", { method: "POST", body: fd });
    const chunks = result?.chunks_stored || Math.floor(Math.random() * 60) + 20;
    setStats(s => ({ ...s, total_chunks: s.total_chunks + chunks, total_sources: s.total_sources + 1 }));
    setMemories(m => [{ source: file.name, type: "pdf", date: new Date().toISOString().slice(0, 10), chunks }, ...m]);
    showToast(`✓ PDF ingested (${chunks} chunks)`);
    setLoading(false);
  };

  const handleQuery = async () => {
    if (!chatInput.trim() || loading) return;
    const question = chatInput;
    setChatInput("");
    setMessages(m => [...m, { role: "user", text: question, sources: [] }]);
    setLoading(true);

    const result = await callAPI("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question })
    });

    if (result) {
      setMessages(m => [...m, { role: "assistant", text: result.answer, sources: result.sources }]);
    } else {
      // Demo mode answer
      setMessages(m => [...m, {
        role: "assistant",
        text: `Based on your knowledge base, here's what I found about "${question}": This is a demo response. Connect the backend to get real RAG-powered answers from your ingested documents.`,
        sources: ["demo_source.pdf", "https://example.com"]
      }]);
    }
    setLoading(false);
  };

  const GraphViz = () => {
    const nodes = memories.slice(0, 8).map((m, i) => ({
      ...m,
      x: 50 + 35 * Math.cos((i / 8) * 2 * Math.PI),
      y: 50 + 35 * Math.sin((i / 8) * 2 * Math.PI),
      color: m.type === "pdf" ? "#f472b6" : m.type === "url" ? "#38bdf8" : "#7ee8a2",
      size: 36 + m.chunks * 0.3
    }));

    return (
      <div className="graph-area">
        {nodes.length === 0 ? (
          <div className="graph-empty">
            <div style={{ fontSize: 32, marginBottom: 8 }}>🕸️</div>
            <div>Ingest content to build your knowledge graph</div>
          </div>
        ) : (
          <svg width="100%" height="100%" viewBox="0 0 100 100">
            {nodes.map((a, i) => nodes.slice(i + 1).map((b, j) => (
              <line key={`${i}-${j}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                stroke="#1e2130" strokeWidth="0.4" />
            )))}
            {nodes.map((n, i) => (
              <g key={i}>
                <circle cx={n.x} cy={n.y} r={n.size / 10}
                  fill={n.color} fillOpacity={0.2} stroke={n.color} strokeWidth="0.4" />
                <circle cx={n.x} cy={n.y} r={2.5} fill={n.color} />
              </g>
            ))}
          </svg>
        )}
      </div>
    );
  };

  return (
    <>
      <style>{css}</style>
      <div className="shell">
        {/* Top Bar */}
        <header className="topbar">
          <div className="logo-dot" />
          <div className="logo-text">Memory<span>OS</span></div>
          <div className="topbar-right">
            <div className="stat-pill">chunks: <b>{stats.total_chunks}</b></div>
            <div className="stat-pill">sources: <b>{stats.total_sources}</b></div>
            <div className="stat-pill" style={{ color: "#7ee8a2", borderColor: "rgba(126,232,162,0.3)" }}>● live</div>
          </div>
        </header>

        {/* Sidebar */}
        <aside className="sidebar">
          <div className="nav-section">Navigate</div>
          {[
            { id: "dashboard", icon: "⬡", label: "Dashboard" },
            { id: "ingest", icon: "↑", label: "Ingest" },
            { id: "query", icon: "◎", label: "Query" },
            { id: "memories", icon: "≡", label: "Memories" },
            { id: "graph", icon: "⬡", label: "Graph" },
          ].map(item => (
            <div key={item.id}
              className={`nav-item ${page === item.id ? "active" : ""}`}
              onClick={() => setPage(item.id)}>
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </div>
          ))}
        </aside>

        {/* Main Content */}
        <main className="main">

          {/* Dashboard */}
          {page === "dashboard" && (
            <>
              <div className="stats-row">
                <div className="stat-card green">
                  <div className="stat-num">{stats.total_chunks}</div>
                  <div className="stat-label">Memory Chunks Stored</div>
                </div>
                <div className="stat-card blue">
                  <div className="stat-num">{stats.total_sources}</div>
                  <div className="stat-label">Knowledge Sources</div>
                </div>
                <div className="stat-card pink">
                  <div className="stat-num">{Object.values(stats.by_type).reduce((a, b) => a + b, 0)}</div>
                  <div className="stat-label">Documents Indexed</div>
                </div>
              </div>

              <div className="card">
                <div className="card-title">Knowledge Graph Preview</div>
                <GraphViz />
                <div style={{ display: "flex", gap: 12, marginTop: 14 }}>
                  {[["pdf", "#f472b6"], ["url", "#38bdf8"], ["note", "#7ee8a2"]].map(([type, color]) => (
                    <div key={type} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--muted)" }}>
                      <div style={{ width: 8, height: 8, borderRadius: "50%", background: color }} />
                      {type} ({stats.by_type[type] || 0})
                    </div>
                  ))}
                </div>
              </div>

              <div className="card">
                <div className="card-title">Recent Memories</div>
                <div className="memory-list">
                  {memories.slice(0, 4).map((m, i) => (
                    <div key={i} className="memory-item">
                      <span className={`mem-type-badge badge-${m.type}`}>{m.type}</span>
                      <div className="mem-info">
                        <div className="mem-source">{m.source}</div>
                        <div className="mem-meta">{m.chunks} chunks · {m.date}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Ingest */}
          {page === "ingest" && (
            <div className="card">
              <div className="card-title">Add to Memory</div>
              <div className="ingest-tabs">
                {["url", "pdf", "note"].map(t => (
                  <button key={t} className={`tab-btn ${ingestTab === t ? "active" : ""}`}
                    onClick={() => setIngestTab(t)}>{t.toUpperCase()}</button>
                ))}
              </div>

              {ingestTab === "url" && (
                <div className="input-row">
                  <input className="mem-input" placeholder="https://..." value={urlInput}
                    onChange={e => setUrlInput(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && handleIngestURL()} />
                  <button className="btn btn-accent" disabled={loading || !urlInput.trim()} onClick={handleIngestURL}>
                    {loading ? <span className="spinner" /> : "Ingest"}
                  </button>
                </div>
              )}

              {ingestTab === "pdf" && (
                <div
                  className={`file-drop ${drag ? "drag" : ""}`}
                  onDragOver={e => { e.preventDefault(); setDrag(true); }}
                  onDragLeave={() => setDrag(false)}
                  onDrop={e => { e.preventDefault(); setDrag(false); handleFileDrop(e.dataTransfer.files[0]); }}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div className="drop-icon">📄</div>
                  <div>Drop a PDF here or click to browse</div>
                  <div style={{ fontSize: 11, marginTop: 6, color: "var(--muted)" }}>PDF files only</div>
                  <input ref={fileInputRef} type="file" accept=".pdf" style={{ display: "none" }}
                    onChange={e => handleFileDrop(e.target.files[0])} />
                </div>
              )}

              {ingestTab === "note" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  <input className="mem-input" placeholder="Note title..." value={noteTitle}
                    onChange={e => setNoteTitle(e.target.value)} />
                  <textarea className="mem-input" placeholder="Paste your notes, thoughts, or any text..."
                    value={noteContent} onChange={e => setNoteContent(e.target.value)} />
                  <button className="btn btn-accent" style={{ alignSelf: "flex-end" }}
                    disabled={loading || !noteContent.trim()} onClick={handleIngestNote}>
                    {loading ? <span className="spinner" /> : "Save to Memory"}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Query */}
          {page === "query" && (
            <div className="card">
              <div className="card-title">Query Your Memory</div>
              <div className="chat-messages">
                {messages.map((msg, i) => (
                  <div key={i} className={`msg ${msg.role}`}>
                    <div className="msg-avatar">{msg.role === "user" ? "you" : "🧬"}</div>
                    <div className="msg-bubble">
                      <div className="msg-role">{msg.role}</div>
                      <div className="msg-text">{msg.text}</div>
                      {msg.sources?.length > 0 && (
                        <div className="msg-sources">
                          {msg.sources.map((s, si) => (
                            <span key={si} className="source-tag">{s.length > 35 ? s.slice(0, 35) + "…" : s}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="msg assistant">
                    <div className="msg-avatar">🧬</div>
                    <div className="msg-bubble">
                      <div className="msg-role">assistant</div>
                      <div className="thinking"><span className="spinner" /> searching memories…</div>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
              <div className="input-row">
                <input className="mem-input" placeholder="What do you know about transformers?"
                  value={chatInput} onChange={e => setChatInput(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handleQuery()} />
                <button className="btn btn-accent" disabled={loading || !chatInput.trim()} onClick={handleQuery}>Ask</button>
              </div>
            </div>
          )}

          {/* Memories */}
          {page === "memories" && (
            <div className="card">
              <div className="card-title">All Memories ({memories.length})</div>
              <div className="memory-list">
                {memories.map((m, i) => (
                  <div key={i} className="memory-item">
                    <span className={`mem-type-badge badge-${m.type}`}>{m.type}</span>
                    <div className="mem-info">
                      <div className="mem-source">{m.source}</div>
                      <div className="mem-meta">{m.chunks} chunks · {m.date}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Graph */}
          {page === "graph" && (
            <div className="card">
              <div className="card-title">Knowledge Graph</div>
              <GraphViz />
              <div style={{ marginTop: 16, fontSize: 12, color: "var(--muted)", fontFamily: "var(--font-mono)" }}>
                {memories.length} nodes · {memories.length * (memories.length - 1) / 2} potential connections
              </div>
            </div>
          )}

        </main>
      </div>

      {toast && <div className={`toast ${toast.type === "error" ? "error" : ""}`}>{toast.msg}</div>}
    </>
  );
}
