# backend/main.py

import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph_query import query_graph

# ── 0) LOAD SCRAPED CONTENT ─────────────────────────────────────────────────
HERE = os.path.dirname(__file__)
with open(os.path.join(HERE, "content.json"), encoding="utf-8") as f:
    ALL_DOCS = json.load(f)  # list of {"url", "title", "text"}

# ── 1) FASTAPI SETUP ─────────────────────────────────────────────────────────
app = FastAPI(title="MadeWithNestlé Chatbot (Stubbed)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    references: list[str]

# ── 2) /chat ENDPOINT ─────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(req: QueryRequest):
    try:
        # 2a) Fake vector hits = first 3 scraped pages
        vector_hits = ALL_DOCS[:3]
        
        # 2b) Real graph hits from Neo4j
        graph_hits = query_graph(req.question, limit=3)

        # 2c) Build a stubbed answer
        vect_list = "\n".join(f"- {d['url']}" for d in vector_hits)
        graph_list = "\n".join(f"- {h['url']}" for h in graph_hits)

        answer = (
            "📄 **Vector search results** (top 3):\n"
            f"{vect_list}\n\n"
            "🔗 **Graph search results** (top 3):\n"
            f"{graph_list}"
        )

        # 2d) Collect unique references
        refs = list({
            * (d["url"] for d in vector_hits),
            * (h["url"] for h in graph_hits),
        })

        return ChatResponse(answer=answer, references=refs)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── 3) HEALTHCHECK ───────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}
