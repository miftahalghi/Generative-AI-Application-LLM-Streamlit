"""
app.py
------
UI Streamlit — hanya bertanggung jawab atas tampilan dan interaksi pengguna.
Tidak ada logika bisnis, koneksi DB, atau konfigurasi agent di sini.
"""

import streamlit as st
from bot.agent import build_agent
from bot.database import fetch_all_orders

# ── Inisialisasi session state ────────────────────────────────────────────────

def _init_state() -> None:
    """Inisialisasi semua session state yang diperlukan di awal."""
    defaults = {
        "agent": None,
        "messages": [],          # pesan sesi aktif: [{"role": ..., "content": ...}]
        "chat_sessions": [],     # daftar sesi yang sudah disimpan
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Bangun agent sekali saja
    if st.session_state.agent is None:
        with st.spinner("Memuat agent..."):
            st.session_state.agent = build_agent()


_init_state()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🧭 Navigasi")
    selected_page = st.radio(
        "Pilih Halaman:",
        ["💬 Chatbot", "📦 Riwayat Order", "🕐 Riwayat Chat", "ℹ️ Tentang"],
        index=0,
        label_visibility="collapsed",
        key="page_nav",
    )

    st.markdown("---")
    st.markdown("### 🛠️ Aksi Cepat")

    if st.button("🔄 Reset Chat", use_container_width=True):
        # Simpan sesi aktif ke riwayat sebelum reset
        if st.session_state.messages:
            st.session_state.chat_sessions.append(
                st.session_state.messages.copy()
            )
        st.session_state.messages = []
        st.session_state.agent = build_agent()
        st.success("Chat berhasil direset.")

    if st.button("🗑️ Hapus Semua Riwayat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_sessions = []
        st.success("Semua riwayat telah dihapus.")

    st.markdown("---")
    st.markdown("### 📜 Riwayat Sesi")

    if st.session_state.chat_sessions:
        for i, session in enumerate(st.session_state.chat_sessions):
            # Ambil preview dari pesan terakhir di sesi
            last_msg = session[-1]["content"] if session else ""
            label = f"🗂️ Sesi {i + 1}: {last_msg[:25]}..."
            if st.button(label, key=f"session_btn_{i}", use_container_width=True):
                st.session_state.messages = session.copy()
    else:
        st.info("Belum ada sesi tersimpan.")

    st.markdown("---")
    st.caption("👤 Dibuat oleh Miftah Al Ghifari")

# ── Halaman: Chatbot ──────────────────────────────────────────────────────────

def render_chatbot() -> None:
    st.title("💬 Chatbot e-Commerce")
    st.markdown("> Tanyakan apa saja — kendaraan, produk, cuaca, dan lebih banyak lagi.")
    st.divider()

    # Tampilkan riwayat percakapan sesi aktif
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]

        if role == "tool":
            # Tampilan tool call dengan styling ringan
            with st.chat_message("assistant", avatar="🛠️"):
                st.markdown(
                    f"<small style='color:#888'>🛠️ Tool dipanggil: {content}</small>",
                    unsafe_allow_html=True,
                )
        else:
            with st.chat_message(role):
                st.markdown(content)

    # Input pengguna
    human_message = st.chat_input("Ketik pesan...")
    if human_message:
        _handle_chat(human_message)


def _handle_chat(human_message: str) -> None:
    """Memproses pesan pengguna dan mendapatkan respons dari agent."""
    # Simpan & tampilkan pesan user
    st.session_state.messages.append({"role": "human", "content": human_message})
    with st.chat_message("human"):
        st.markdown(human_message)

    with st.spinner("Sedang berpikir..."):
        try:
            config = {"configurable": {"thread_id": "1"}}
            
            # Hitung jumlah state messages SEBELUM pemanggilan
            current_state = st.session_state.agent.get_state(config)
            old_msg_count = len(current_state.values.get("messages", [])) if current_state.values else 0
            
            # Invoke dengan input pesan baru
            result = st.session_state.agent.invoke(
                {"messages": [("user", human_message)]}, 
                config
            )
            
            # Ambil pesan-pesan baru yang dihasilkan agen
            new_msgs = result["messages"][old_msg_count + 1:]  # +1 skip user msg
            
            ai_output = result["messages"][-1].content
            
            # Cari dan tampilkan tool calls
            for msg in new_msgs:
                if msg.type == "tool":
                    tool_info = f"{msg.name}()"
                    st.session_state.messages.append({"role": "tool", "content": tool_info})
                    with st.chat_message("assistant", avatar="🛠️"):
                        st.markdown(
                            f"<small style='color:#888'>🛠️ {tool_info}</small>",
                            unsafe_allow_html=True,
                        )
                        
        except Exception as e:
            ai_output = f"⚠️ Terjadi error: {e}"

    # Simpan & tampilkan respons assistant
    st.session_state.messages.append({"role": "assistant", "content": ai_output})
    with st.chat_message("assistant"):
        st.markdown(ai_output)

# ── Halaman: Riwayat Order ────────────────────────────────────────────────────

def render_orders() -> None:
    """
    Mengambil data order langsung dari DB — bukan lewat agent.
    Lebih efisien, deterministic, dan tidak membuang token LLM.
    """
    st.title("📦 Riwayat Order")
    st.divider()

    orders = fetch_all_orders()

    if not orders:
        st.info("Belum ada order yang tersimpan.")
        return

    st.markdown(f"**Total: {len(orders)} order**")
    st.divider()

    for o in orders:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"#### 🧾 Order #{o['id']} — {o['customer_name']}")
                st.markdown(
                    f"🚗 **Tipe:** {o['vehicle_type']}  |  "
                    f"📦 **Brand:** {o['brand_code']}  |  "
                    f"🔢 **Model:** {o['model_code']}  |  "
                    f"📅 **Tahun:** {o['year_code']}"
                )
            with col2:
                st.markdown(f"🚚 **Estimasi Kirim:**")
                st.markdown(f"`{o['delivery_date'][:10]}`")
            st.divider()

# ── Halaman: Riwayat Chat ─────────────────────────────────────────────────────

def render_chat_history() -> None:
    st.title("🕐 Riwayat Chat")
    st.divider()

    if not st.session_state.chat_sessions:
        st.info("Belum ada sesi chat yang tersimpan. Reset chat untuk menyimpan sesi.")
        return

    for i, session in enumerate(st.session_state.chat_sessions):
        with st.expander(f"🗂️ Sesi {i + 1} ({len(session)} pesan)"):
            for msg in session:
                role_label = "🧑 Anda" if msg["role"] == "human" else "🤖 Bot"
                st.markdown(f"**{role_label}:** {msg['content']}")

# ── Halaman: Tentang ──────────────────────────────────────────────────────────

def render_about() -> None:
    st.title("ℹ️ Tentang Project")
    st.divider()
    st.markdown("""
**Proyek ini** adalah chatbot berbasis [LangChain](https://www.langchain.com/) dan
[Groq](https://groq.com/) yang membantu pengguna dalam:

- 🚗 Memesan kendaraan (mobil, motor, truk) via FIPE API
- 🔍 Melakukan perbandingan produk real-time
- 🌤️ Mendapatkan informasi cuaca terkini
- 💡 Dan banyak lagi!

**Stack Teknologi:**
- LangChain ReAct Agent
- Groq Cloud (model: Llama 3.1 8B Instant)
- Streamlit untuk UI
- SQLite untuk persistensi data order
- Streamlit Cloud untuk deployment

---
Dibuat oleh **Miftah Al Ghifari** 🚀
""")

# ── Router Halaman ─────────────────────────────────────────────────────────────

if "Chatbot" in selected_page:
    render_chatbot()
elif "Order" in selected_page:
    render_orders()
elif "Riwayat Chat" in selected_page:
    render_chat_history()
elif "Tentang" in selected_page:
    render_about()
