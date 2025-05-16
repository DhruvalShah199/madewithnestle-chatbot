# ingest_graph.py

import os, json
from neo4j import GraphDatabase

# ── 1) CONFIG ────────────────────────────────────────────────────────────────
URI      = os.getenv("NEO4J_URI")
USER     = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

# ── 2) DRIVER SETUP ──────────────────────────────────────────────────────────
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# ── 3) INGEST FUNCTION ───────────────────────────────────────────────────────
def ingest_page(tx, url, title, text):
    tx.run(
        """
        MERGE (p:Page {url: $url})
        SET p.title = $title,
            p.text  = $text
        """,
        url=url, title=title, text=text
    )

# ── 4) MAIN ─────────────────────────────────────────────────────────────────
def main():
    # load your content.json created on Day 2
    with open("content.json", encoding="utf-8") as f:
        docs = json.load(f)

    with driver.session() as sess:
        for doc in docs:
            sess.write_transaction(
                ingest_page,
                doc["url"],
                doc["title"],
                doc["text"]
            )
    print(f"✅ Ingested {len(docs)} pages into Neo4j")

if __name__ == "__main__":
    main()