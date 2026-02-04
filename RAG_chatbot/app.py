"""
FastAPI server for RAG Chatbot.
Provides REST API endpoints for the frontend assistant interface.
"""

import os
from typing import Any, Dict, List

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.rag import RAGRetriever, build_prompt, build_single_context

# Load environment variables
load_dotenv("gemini.env")
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="RAG Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG Retriever (singleton)
retriever: RAGRetriever | None = None
model: Any | None = None

# Configuration
MIN_SCORE_THRESHOLD = 0.3


class ChatRequest(BaseModel):
    question: str


def get_gemini_model():
    """Initialize and return Gemini model instance."""
    global model
    if model is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not found. Please create a 'gemini.env' file "
                "in the project root with: GEMINI_API_KEY=your_real_key"
            )
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
    return model


def get_retriever():
    """Initialize and return RAGRetriever instance (singleton)."""
    global retriever
    if retriever is None:
        retriever = RAGRetriever(use_hybrid=True)
    return retriever


@app.on_event("startup")
async def startup_event():
    """Pre-load retriever and model when the FastAPI app starts."""
    print("Starting RAG Chatbot API server (FastAPI)...")
    print("Loading RAG retriever and Gemini model...")
    try:
        get_retriever()
        get_gemini_model()
        print("✅ RAG retriever and Gemini model loaded successfully!")
    except Exception as e:  # pragma: no cover - startup logging
        print(f"⚠️  Warning: Error loading retriever/model: {e}")
        print("   The API will still start, but /api/chat may fail until fixed.")


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint - API information."""
    return {
        "name": "RAG Chatbot API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "GET /": "API information (this endpoint)",
            "GET /api/health": "Health check",
            "POST /api/chat": "Chat endpoint - requires JSON: {\"question\": \"your question\"}",
        },
    }


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "RAG Chatbot API is running",
    }


@app.post("/api/chat")
async def chat(request: ChatRequest) -> Dict[str, Any]:
    """
    Chat endpoint that processes user questions using RAG.

    Request body:
        {
            "question": "string"  # User's question
        }

    Response:
        {
            "answer": "string",  # AI's answer
            "sources": [  # List of source links
                {
                    "link": "string",
                    "text": "string"  # Snippet of the source
                }
            ],
            "success": true/false,
            "error": "string"  # Error message if success is false
        }
    """
    try:
        question = (request.question or "").strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")

        # Get retriever and model
        rag = get_retriever()
        gemini_model = get_gemini_model()

        # Retrieve relevant documents
        docs: List[Dict[str, Any]] = rag.retrieve(question, top_k=5)

        if not docs:
            return {
                "success": True,
                "answer": "Hiện chưa có dữ liệu để trả lời câu hỏi này.",
                "sources": [],
            }

        # Check top document score
        top_doc = docs[0]
        top_score = top_doc.get("score", 0.0)

        if top_score < MIN_SCORE_THRESHOLD:
            return {
                "success": True,
                "answer": "Hiện chưa có dữ liệu để trả lời câu hỏi này.",
                "sources": [],
            }

        # Find post document (top_doc might be post or comment)
        post_doc = None
        post_id = None

        doc_id = top_doc.get("_id", "")
        if isinstance(doc_id, str) and doc_id.startswith("post::"):
            post_doc = top_doc
            post_id = top_doc.get("source", {}).get("post_id")
        else:
            # If top_doc is comment, get post_id and find post
            post_id = top_doc.get("source", {}).get("post_id")
            if post_id:
                # Try to find post in retrieved docs first
                for d in docs:
                    d_id = d.get("_id", "")
                    if isinstance(d_id, str) and d_id.startswith("post::"):
                        d_post_id = d.get("source", {}).get("post_id")
                        if d_post_id == post_id:
                            post_doc = d
                            break

                # If not found, query from database
                if not post_doc:
                    post_doc = rag.get_post_by_id(post_id)

        # Build context
        if post_doc and post_id:
            context = build_single_context(post_doc, rag)
        else:
            # Fallback: use only the document text
            meta = top_doc.get("source", {})
            link = meta.get("permalink_url") or ""
            context = f"text: {top_doc['text']}\nsource: {link}"

        # Build prompt and generate answer
        prompt = build_prompt(question, context)

        try:
            resp = gemini_model.generate_content(prompt)
            answer = getattr(resp, "text", "").strip() or "[Không nhận được text từ Gemini]"

            # Check if answer indicates no data
            if not answer or answer.lower() in ["không rõ", "không có", "không tìm thấy"]:
                answer = "Hiện chưa có dữ liệu để trả lời câu hỏi này."
        except Exception as exc:
            answer = f"Lỗi khi gọi Gemini: {str(exc)}"

        # Build sources list
        sources: List[Dict[str, str]] = []
        if top_score >= MIN_SCORE_THRESHOLD:
            # Add main source (post used for answer)
            if post_doc:
                top_src = post_doc.get("source", {})
                top_link = top_src.get("permalink_url", "")
                if top_link:
                    txt = post_doc.get("text", "") or ""
                    sources.append(
                        {
                            "link": top_link,
                            "text": txt[:200] + "..." if len(txt) > 200 else txt,
                        }
                    )

            # Add related sources (other docs)
            for d in docs[1:]:  # Skip first one (already added)
                src = d.get("source", {})
                link = src.get("permalink_url", "")
                if link:
                    txt = d.get("text", "") or ""
                    sources.append(
                        {
                            "link": link,
                            "text": txt[:200] + "..." if len(txt) > 200 else txt,
                        }
                    )

        return {
            "success": True,
            "answer": answer,
            "sources": sources,
        }

    except HTTPException:
        raise
    except Exception as e:
        # Unexpected error
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
    )

