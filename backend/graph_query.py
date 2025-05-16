# graph_query.py

import os
from neo4j import GraphDatabase

# ── 1) Load Neo4j connection info from environment variables ─────────────────
URI      = os.getenv("NEO4J_URI")       # e.g. "neo4j+s://<your-instance>.databases.neo4j.io:7687"
USER     = os.getenv("NEO4J_USER")      # should be "neo4j"
PASSWORD = os.getenv("NEO4J_PASSWORD")  # your AuraDB password

# ── 2) Initialize the Neo4j driver ───────────────────────────────────────────
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# ── 3) Define the GraphRAG query function ────────────────────────────────────
def query_graph(question: str, limit: int = 5) -> list[dict]:
    """
    Perform a simple GraphRAG lookup: split the question into keywords,
    match pages whose 'text' property contains any keyword, and return up to
    `limit` results with url, title, and a text snippet.
    
    :param question: the user’s question string
    :param limit: maximum number of pages to return
    :return: list of dicts with keys 'url', 'title', 'snippet'
    """
    # 3a) Extract keywords longer than 3 characters
    keywords = [word.lower() for word in question.split() if len(word) > 3]

    # 3b) Cypher query using UNWIND to match any keyword
    cypher = """
    UNWIND $keywords AS kw
    MATCH (p:Page)
    WHERE toLower(p.text) CONTAINS kw
    RETURN DISTINCT
        p.url     AS url,
        p.title   AS title,
        substring(p.text, 0, 200) AS snippet
    LIMIT $limit
    """

    # 3c) Execute the query within a session
    with driver.session() as session:
        results = session.run(cypher, keywords=keywords, limit=limit)
        return [ record.data() for record in results ]