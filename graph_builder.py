import networkx as nx
from collections import defaultdict
from typing import List, Dict
from backend.core.vector_store import vector_store
import json


def build_knowledge_graph() -> Dict:
    """
    Build a knowledge graph from stored memory metadata.
    Nodes = unique sources, Edges = shared topics/keywords.
    Returns JSON-serializable dict for D3/frontend.
    """
    all_metadata = vector_store.get_all_metadata()
    if not all_metadata:
        return {"nodes": [], "links": []}

    G = nx.Graph()

    # Group chunks by source
    sources: Dict[str, List[Dict]] = defaultdict(list)
    for meta in all_metadata:
        source = meta.get("source", "unknown")
        sources[source].append(meta)

    # Add nodes
    for source, metas in sources.items():
        source_type = metas[0].get("source_type", "note")
        G.add_node(source, 
                   source_type=source_type,
                   chunk_count=len(metas),
                   ingested_at=metas[0].get("ingested_at", ""))

    # Add edges based on source type clustering
    source_list = list(sources.keys())
    type_groups: Dict[str, List[str]] = defaultdict(list)
    for source, metas in sources.items():
        stype = metas[0].get("source_type", "note")
        type_groups[stype].append(source)

    # Connect nodes of the same type (loose edges)
    for stype, srcs in type_groups.items():
        for i in range(len(srcs)):
            for j in range(i + 1, len(srcs)):
                G.add_edge(srcs[i], srcs[j], relation=f"same_type:{stype}", weight=0.5)

    # Serialize for D3
    nodes = []
    for node, data in G.nodes(data=True):
        nodes.append({
            "id": node,
            "label": node[:40] + "..." if len(node) > 40 else node,
            "type": data.get("source_type", "note"),
            "chunks": data.get("chunk_count", 0),
            "ingested_at": data.get("ingested_at", "")
        })

    links = []
    for u, v, data in G.edges(data=True):
        links.append({
            "source": u,
            "target": v,
            "relation": data.get("relation", "related"),
            "weight": data.get("weight", 1.0)
        })

    return {
        "nodes": nodes,
        "links": links,
        "stats": {
            "total_nodes": len(nodes),
            "total_links": len(links),
            "total_chunks": sum(n["chunks"] for n in nodes)
        }
    }
