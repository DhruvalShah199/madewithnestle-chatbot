# ingest_vector.py

import os
import json
import base64
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    VectorSearch
)
from sentence_transformers import SentenceTransformer

# ── 0) CONFIG ────────────────────────────────────────────────────────────────
ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
KEY      = os.getenv("AZURE_SEARCH_KEY")
INDEX    = "nestle-content"

# ── 1) INDEX SETUP ───────────────────────────────────────────────────────────
idx_client = SearchIndexClient(ENDPOINT, AzureKeyCredential(KEY))

algo = HnswAlgorithmConfiguration(name="hnsw-1", kind="hnsw")
profile = VectorSearchProfile(
    name="vector-profile-hnsw",
    algorithm_configuration_name="hnsw-1"
)
vector_search = VectorSearch(algorithms=[algo], profiles=[profile])

fields = [
    SimpleField(name="id",    type="Edm.String", key=True),
    SimpleField(name="url",   type="Edm.String", searchable=False),
    SearchableField(name="title", type="Edm.String", analyzer_name="en.lucene"),
    SearchableField(name="text",  type="Edm.String", analyzer_name="en.lucene"),

    # 384-dim vector for all-MiniLM-L6-v2
    SearchField(
        name="vector",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True,
        vector_search_dimensions=384,
        vector_search_profile_name="vector-profile-hnsw"
    )
]

# delete & recreate (dev only)
try:
    idx_client.delete_index(INDEX)
except:
    pass

index_def = SearchIndex(
    name=INDEX,
    fields=fields,
    vector_search=vector_search
)
idx_client.create_or_update_index(index_def)
print(f"✅ Search index '{INDEX}' is ready.")

# ── 2) LOAD SCRAPED CONTENT ─────────────────────────────────────────────────
with open("content.json", encoding="utf-8") as f:
    docs = json.load(f)

# ── 3) EMBED LOCALLY & UPLOAD ────────────────────────────────────────────────
model = SentenceTransformer("all-MiniLM-L6-v2")
search_client = SearchClient(ENDPOINT, INDEX, AzureKeyCredential(KEY))

batch = []
for doc in docs:
    # base64-url encode the URL to make a valid key
    raw = doc["url"].encode("utf-8")
    b64  = base64.urlsafe_b64encode(raw).decode("ascii")

    vector = model.encode(doc["text"], show_progress_bar=False).tolist()

    batch.append({
        "id":     b64,
        "url":    doc["url"],
        "title":  doc["title"],
        "text":   doc["text"],
        "vector": vector
    })

result = search_client.upload_documents(documents=batch)
success = sum(1 for r in result if r.succeeded)
print(f"✅ Uploaded {success}/{len(batch)} docs to '{INDEX}'.")