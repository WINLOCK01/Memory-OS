import streamlit as st
import requests
import json
import time
from datetime import datetime
from streamlit_agraph import agraph, Node, Edge, Config

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="MemoryOS", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Premium Design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono&display=swap');
    
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(14, 18, 25) 0%, rgb(22, 28, 36) 90%);
        color: #e5e7eb;
        font-family: 'Inter', sans-serif;
    }
    header {visibility: hidden;}
    
    /* Neon accents and glassmorphism */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background-color: rgba(255, 255, 255, 0.03);
        padding: 0.5rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        border-radius: 8px;
        background-color: transparent;
        color: #9ca3af;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(59, 130, 246, 0.2)) !important;
        color: white !important;
        border: 1px solid rgba(139, 92, 246, 0.5) !important;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.2);
    }
    
    .metric-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(139, 92, 246, 0.2);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(to right, #a78bfa, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.5rem;
    }
    
    h1 {
        font-weight: 800;
        background: linear-gradient(to right, #c4b5fd, #93c5fd);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .chat-bubble {
        padding: 1.2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
        font-family: 'JetBrains Mono', monospace;
    }
    .chat-user {
        background: rgba(59, 130, 246, 0.1);
        border-left: 4px solid #3b82f6;
    }
    .chat-assistant {
        background: rgba(139, 92, 246, 0.1);
        border-right: 4px solid #8b5cf6;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧬 MemoryOS Pipeline")

tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Ingest Data", "Ask Memory", "Knowledge Graph"])

def fetch_stats():
    try:
        r = requests.get(f"{API_URL}/stats", timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {"total_chunks": 0, "total_sources": 0, "by_type": {}}

def fetch_memory_blocks():
    try:
        r = requests.get(f"{API_URL}/memory_blocks", timeout=5)
        if r.status_code == 200:
            return r.json().get("memory_blocks", ["Default"])
    except:
        pass
    return ["Default"]

st.sidebar.title("⚙️ Configuration")
model_options = ["nvidia/nemotron-3-super-120b-a12b:free", "gemini-2.0-flash", "gemini-3-flash-live", "anthropic/claude-3.5-sonnet", "meta-llama/llama-3.3-70b-instruct", "openai/gpt-4o-mini"]
selected_model = st.sidebar.selectbox("🤖 AI Chatbot", model_options)
available_blocks = fetch_memory_blocks()
if "Default" not in available_blocks:
    available_blocks.insert(0, "Default")
selected_block = st.sidebar.selectbox("🧠 Active Memory Block", ["All"] + available_blocks)

with tab1:
    stats = fetch_stats()
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"""<div class="metric-card"><div class="metric-value">{stats['total_chunks']}</div><div class="metric-label">Memory Chunks</div></div>""", unsafe_allow_html=True)
    c2.markdown(f"""<div class="metric-card"><div class="metric-value">{stats['total_sources']}</div><div class="metric-label">Unique Sources</div></div>""", unsafe_allow_html=True)
    
    types_count = len(stats.get('by_type', {}))
    c3.markdown(f"""<div class="metric-card"><div class="metric-value">{types_count}</div><div class="metric-label">Data Types</div></div>""", unsafe_allow_html=True)

    st.markdown("### Source Breakdown")
    for t, count in stats.get('by_type', {}).items():
        st.write(f"- {t.upper()}: {count} chunks")

with tab2:
    st.markdown("### Ingest Knowledge")
    memory_name = st.text_input("Memory Name (Block)", value="Default", help="Assign a memory block name (e.g. '2nd April')")
    ingest_type = st.radio("Select Source", ["Text Note", "URL / Article", "PDF Document", "Voice Memo"], horizontal=True)
    
    if ingest_type == "Text Note":
        title = st.text_input("Title")
        note = st.text_area("Note Content", height=200)
        if st.button("Save to Memory", use_container_width=True):
            if note and title:
                with st.spinner("Ingesting..."):
                    r = requests.post(f"{API_URL}/ingest/text", json={"title": title, "content": note, "memory_block": memory_name})
                    if r.status_code == 200:
                        st.success(f"Stored {r.json()['chunks_stored']} chunks successfully!")
                    else:
                        err_detail = r.json().get('detail', 'Unknown error') if r.headers.get('content-type','').startswith('application/json') else r.text
                        st.error(f"Failed to ingest note: {err_detail}")
    
    elif ingest_type == "URL / Article":
        url = st.text_input("Web URL")
        if st.button("Scrape & Save", use_container_width=True):
            if url:
                with st.spinner("Scraping..."):
                    r = requests.post(f"{API_URL}/ingest/url", json={"url": url, "memory_block": memory_name})
                    if r.status_code == 200:
                        st.success(f"Stored {r.json()['chunks_stored']} chunks from URL successfully!")
                    else:
                        err_detail = r.json().get('detail', 'Unknown error') if r.headers.get('content-type','').startswith('application/json') else r.text
                        st.error(f"Failed to scrape URL: {err_detail}")

    elif ingest_type == "PDF Document":
        pdf_file = st.file_uploader("Upload PDF", type=['pdf'])
        if st.button("Extract PDF", use_container_width=True) and pdf_file:
            with st.spinner("Extracting..."):
                r = requests.post(f"{API_URL}/ingest/pdf", files={"file": (pdf_file.name, pdf_file.getvalue())}, data={"memory_block": memory_name})
                if r.status_code == 200:
                    st.success(f"Stored {r.json()['chunks_stored']} chunks from PDF!")
                else:
                    err_detail = r.json().get('detail', 'Unknown error') if r.headers.get('content-type','').startswith('application/json') else r.text
                    st.error(f"Failed to process PDF: {err_detail}")
                    
    elif ingest_type == "Voice Memo":
        voice_file = st.file_uploader("Upload Audio", type=['mp3', 'wav', 'm4a'])
        if st.button("Transcribe & Save", use_container_width=True) and voice_file:
            with st.spinner("Whisper transcribing..."):
                r = requests.post(f"{API_URL}/ingest/voice", files={"file": (voice_file.name, voice_file.getvalue())}, data={"memory_block": memory_name})
                if r.status_code == 200:
                    st.success(f"Stored {r.json()['chunks_stored']} chunks from Voice Memo!")
                else:
                    err_detail = r.json().get('detail', 'Unknown error') if r.headers.get('content-type','').startswith('application/json') else r.text
                    st.error(f"Failed to process Audio: {err_detail}")

with tab3:
    st.markdown("### Ask Your Memory")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.chat_input("What do you want to remember?")
    with col2:
        source_filter = st.selectbox("Filter Source", ["All", "pdf", "url", "note", "voice"])

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        role_class = "chat-user" if msg['role'] == 'user' else "chat-assistant"
        st.markdown(f'<div class="chat-bubble {role_class}">**{msg["role"].upper()}**: {msg["content"]}</div>', unsafe_allow_html=True)

    if query:
        st.session_state.chat_history.append({"role": "user", "content": query})
        st.markdown(f'<div class="chat-bubble chat-user">**USER**: {query}</div>', unsafe_allow_html=True)
        
        payload = {"question": query, "model": selected_model}
        if source_filter != "All":
            payload["source_type"] = source_filter
        if selected_block != "All":
            payload["memory_block"] = selected_block
            
        with st.spinner("Synthesizing memory..."):
            try:
                r = requests.post(f"{API_URL}/query", json=payload)
                if r.status_code == 200:
                    data = r.json()
                    ans = data['answer']
                    refs = ", ".join(data['sources'])
                    full_reply = f"{ans}\n\n*Sources referenced: {refs}*"
                    st.session_state.chat_history.append({"role": "assistant", "content": full_reply})
                    st.markdown(f'<div class="chat-bubble chat-assistant">**ASSISTANT**: {full_reply}</div>', unsafe_allow_html=True)
                else:
                    err_detail = r.json().get('detail', 'Query failed') if r.headers.get('content-type','').startswith('application/json') else r.text
                    st.error(f"Query failed: {err_detail}")
            except Exception as e:
                    st.error(f"Backend not reachable or query failed: {e}")

with tab4:
    st.markdown("### Knowledge Graph")
    if st.button("Generate Visualization"):
        with st.spinner("Building Graph..."):
            try:
                r = requests.get(f"{API_URL}/graph")
                if r.status_code == 200:
                    data = r.json()
                    nodes = []
                    edges = []
                    
                    for n in data.get("nodes", []):
                        color = "#3b82f6"
                        if n.get("type") == "pdf": color = "#ef4444"
                        elif n.get("type") == "voice": color = "#8b5cf6"
                        elif n.get("type") == "note": color = "#10b981"
                        
                        nodes.append(
                            Node(id=n["id"], label=n["id"][:20], size=15 + n.get("size", 1)*2, color=color)
                        )
                        
                    for e in data.get("links", []):
                        edges.append(
                            Edge(source=e["source"], target=e["target"], color="#475569")
                        )
                    
                    config = Config(width=1000, height=600, directed=True, 
                                    physics=True, hierarchical=False)
                    agraph(nodes=nodes, edges=edges, config=config)
                else:
                    st.error("Graph unavailable.")
            except:
                st.error("Backend unreachable.")
