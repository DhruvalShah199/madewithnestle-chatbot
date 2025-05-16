# test_graph.py

from graph_query import query_graph

if __name__ == "__main__":
    hits = query_graph("Where can I find chocolate recipes?", limit=3)
    for i, h in enumerate(hits, 1):
        print(f"{i}. {h['title']} → {h['url']}\n   {h['snippet']}...\n")