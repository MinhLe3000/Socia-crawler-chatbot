"""
Streamlit UI: Pipeline Runner + Semantic Search (RAG).
Chạy: streamlit run streamlit_app.py (từ thư mục RAG_chatbot)
"""

import os
import subprocess
import sys
from pathlib import Path

import streamlit as st

# Đảm bảo chạy từ thư mục RAG_chatbot
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

# Load env sớm
from dotenv import load_dotenv
load_dotenv("gemini.env")
load_dotenv()

MIN_SCORE_THRESHOLD = 0.3

st.set_page_config(
    page_title="RAG Control",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar
st.sidebar.title("RAG Control")
page = st.sidebar.radio(
    "Chọn chức năng",
    ["Pipeline Runner", "Semantic Search"],
    label_visibility="collapsed",
)
st.sidebar.markdown("---")
st.sidebar.caption("Dữ liệu: Mongo → Qdrant. RAG: BGE-M3 + Gemini.")

# ---------- Pipeline Runner ----------
if page == "Pipeline Runner":
    st.header("Pipeline Runner")
    st.markdown("Chọn bước để chạy pipeline dữ liệu (index Mongo → Qdrant, tạo embedding).")

    step = st.selectbox(
        "Chạy ở bước",
        [
            "1. Index Mongo → Qdrant",
            "2. Generate Embeddings (BGE-M3)",
            "Chạy toàn bộ (1 rồi 2)",
        ],
    )

    allow_only_if_data = st.checkbox(
        "Cho phép chạy chỉ khi đã có dữ liệu (bỏ chọn = chạy bất kể)",
        value=False,
    )

    if st.button("Chạy", type="primary"):
        scripts_dir = ROOT / "scripts"
        env = os.environ.copy()

        def run_script(name: str, script: str) -> bool:
            st.markdown(f"**Đang chạy: {name}**")
            out = st.empty()
            env_run = {**env, "PYTHONPATH": str(ROOT)}
            try:
                p = subprocess.run(
                    [sys.executable, script],
                    cwd=str(ROOT),
                    capture_output=True,
                    text=True,
                    timeout=3600,
                    env=env_run,
                )
                out.code(p.stdout or "(no output)\n" + (p.stderr or ""), language="text")
                if p.returncode != 0:
                    st.error(f"Lỗi (exit {p.returncode})")
                    return False
                st.success(f"Xong: {name}")
                return True
            except subprocess.TimeoutExpired:
                st.error("Timeout. Chạy lại hoặc tăng thời gian.")
                return False
            except Exception as e:
                st.exception(e)
                return False

        if "1." in step or "toàn bộ" in step:
            ok1 = run_script("Index Mongo → Qdrant", str(scripts_dir / "index_mongo.py"))
            if not ok1 and "toàn bộ" not in step:
                st.stop()
        if "2." in step or "toàn bộ" in step:
            run_script("Generate Embeddings", str(scripts_dir / "embed_bge_m3.py"))

# ---------- Semantic Search ----------
else:
    st.header("Semantic Search")
    st.markdown(
        "Tìm kiếm theo nghĩa (semantic): nhập câu hỏi tự nhiên, hệ thống tìm các đoạn tài liệu "
        "tương đồng dựa trên embedding (BGE-M3). Score Cosine 0–1: càng gần 1 càng liên quan."
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_area(
            "Query (nhập câu hỏi hoặc ngữ cảnh)",
            placeholder="Ví dụ: review thầy Minh môn CTDL?",
            height=80,
        )
    with col2:
        top_k = st.slider("Top K", min_value=1, max_value=20, value=5)
        use_threshold = st.checkbox("Chỉ trả lời nếu score ≥ 0.3", value=True)

    if st.button("Search", type="primary"):
        if not query or not query.strip():
            st.warning("Nhập query và bấm Search.")
        else:
            with st.spinner("Đang tải RAG và Gemini..."):
                try:
                    import google.generativeai as genai
                    from src.rag import RAGRetriever, build_prompt, build_single_context

                    api_key = os.environ.get("GEMINI_API_KEY")
                    if not api_key:
                        st.error("Thiếu GEMINI_API_KEY trong .env / gemini.env")
                        st.stop()

                    @st.cache_resource
                    def load_rag():
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel("gemini-2.5-flash")
                        retriever = RAGRetriever(use_hybrid=True)
                        return retriever, model

                    retriever, model = load_rag()
                except Exception as e:
                    st.exception(e)
                    st.stop()

            docs = retriever.retrieve(query.strip(), top_k=top_k)
            if not docs:
                st.info("Không tìm thấy tài liệu phù hợp.")
                st.stop()

            top_doc = docs[0]
            top_score = top_doc.get("score", 0.0)

            if use_threshold and top_score < MIN_SCORE_THRESHOLD:
                st.warning("Điểm tương đồng thấp. Chưa đủ dữ liệu để trả lời.")
                st.markdown("**Các kết quả gần nhất:**")
                for i, d in enumerate(docs[:5], 1):
                    st.caption(f"[{i}] score={d.get('score', 0):.3f} — {d.get('text', '')[:150]}...")
                st.stop()

            # Resolve post for context
            post_doc = None
            post_id = top_doc.get("source", {}).get("post_id")
            doc_id = top_doc.get("_id", "")
            if isinstance(doc_id, str) and doc_id.startswith("post::"):
                post_doc = top_doc
            elif post_id:
                for d in docs:
                    if (d.get("_id") or "").startswith("post::") and d.get("source", {}).get("post_id") == post_id:
                        post_doc = d
                        break
                if not post_doc:
                    post_doc = retriever.get_post_by_id(post_id)

            if post_doc and post_id:
                context = build_single_context(post_doc, retriever)
            else:
                context = f"text: {top_doc.get('text', '')}\nsource: {top_doc.get('source', {}).get('permalink_url', '')}"

            prompt = build_prompt(query.strip(), context)
            try:
                resp = model.generate_content(prompt)
                answer = (getattr(resp, "text", "") or "").strip() or "[Không nhận được text]"
            except Exception as e:
                answer = f"Lỗi Gemini: {e}"

            st.subheader("Trả lời")
            st.markdown(answer)

            # Nguồn (dedup theo link)
            seen_links = set()
            sources = []
            if post_doc:
                link = (post_doc.get("source") or {}).get("permalink_url", "")
                if link and link not in seen_links:
                    seen_links.add(link)
                    sources.append(("Bài viết đã dùng", link, (post_doc.get("text") or "")[:200]))
            for d in docs[1:]:
                link = (d.get("source") or {}).get("permalink_url", "")
                if link and link not in seen_links:
                    seen_links.add(link)
                    sources.append(("Liên quan", link, (d.get("text") or "")[:200]))

            if sources:
                st.subheader("Nguồn")
                for label, link, txt in sources:
                    st.markdown(f"**{label}:** [{link}]({link})")
                    if txt:
                        st.caption(txt + ("..." if len(txt) >= 200 else ""))
