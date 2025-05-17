# backend/main.py

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

from sentence_transformers import SentenceTransformer
from graph_query import query_graph

# If/when you re-enable the real OpenAI chat, uncomment:
# from openai import OpenAI

# ── 0) LOAD ENVIRONMENT ──────────────────────────────────────────────────────
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY      = os.getenv("AZURE_SEARCH_KEY")
SEARCH_INDEX_NAME     = "nestle-content"

if not (AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY):
    raise RuntimeError(
        "Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_KEY env var"
    )

# ── 1) INITIALIZE CLIENTS & MODELS ───────────────────────────────────────────
# 1a) Azure Cognitive Search client (vector retrieval)
search_client = SearchClient(
    endpoint=AZURE_SEARCH_ENDPOINT,
    index_name=SEARCH_INDEX_NAME,
    credential=AzureKeyCredential(AZURE_SEARCH_KEY)
)

# 1b) SBERT model for local embeddings
sbert = SentenceTransformer("all-MiniLM-L6-v2")

# When ready to use OpenAI embeddings & chat, uncomment and configure:
# openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── 2) FASTAPI SETUP ──────────────────────────────────────────────────────────
app = FastAPI(title="MadeWithNestlé Chatbot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    references: list[str]

# ── 3) /chat ENDPOINT ─────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(req: QueryRequest):
    try:
        # ----- VECTOR EMBEDDING -----
        # Real OpenAI embedding (commented out until you re-enable):
        # emb = openai_client.embeddings.create(
        #     model="text-embedding-ada-002",
        #     input=req.question
        # )["data"][0]["embedding"]
        # q_vec = emb

        # Free-mode SBERT embedding (currently unused in fallback):
        q_vec = sbert.encode(req.question, show_progress_bar=False).tolist()

        # ----- VECTOR RETRIEVAL -----
        # REMOVED: vector_search call (not available in this SDK version)
        # vs = search_client.vector_search(
        #     vector=q_vec,
        #     top=3,
        #     fields="url,title,text"
        # ).results
        # vector_docs = [r.document for r in vs]

        # ADDED: fallback full-text search until vector_search() exists
        results = search_client.search(
            search_text=req.question,
            top=3,
            select=["url", "title", "text"]
        )
        vector_docs = [
            {"url": r["url"], "title": r["title"], "text": r["text"]}
            for r in results
        ]

        # ----- GRAPH RETRIEVAL -----
        graph_hits = query_graph(req.question, limit=3)

        # ----- CHAT COMPLETION -----
        # Real OpenAI chat (commented out until re-enabled):
        # prompt = (
        #     f"User: {req.question}\n\n"
        #     "Vector context:\n" + 
        #     "\n".join(f"- {d['url']}: {d['text'][:200]}…" for d in vector_docs) +
        #     "\n\nGraph context:\n" +
        #     "\n".join(f"- {h['url']}: {h['snippet']}…" for h in graph_hits)
        # )
        # chat_resp = openai_client.chat.completions.create(
        #     model="gpt-4o-mini",
        #     messages=[{"role":"user","content":prompt}]
        # )
        # answer = chat_resp.choices[0].message.content.strip()

        # Stubbed answer for free mode:
        vect_list = "\n".join(f"- {d['url']}" for d in vector_docs)
        graph_list = "\n".join(f"- {h['url']}" for h in graph_hits)
        answer = (
            "**Vector search results** (top 3):\n"
            f"{vect_list}\n\n"
            "**Graph search results** (top 3):\n"
            f"{graph_list}"
        )

        # ----- REFERENCES -----
        refs = list({
            *[d["url"] for d in vector_docs],
            *[h["url"] for h in graph_hits],
        })

        return ChatResponse(answer=answer, references=refs)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 4) HEALTHCHECK ───────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}