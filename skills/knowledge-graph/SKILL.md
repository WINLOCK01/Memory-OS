---
name: knowledge-graph
description: >
  USE THIS SKILL whenever the user mentions knowledge graph, graph builder, NetworkX, node,
  edge, connections between memories, topic clusters, community detection, centrality, D3
  visualization, or relationships. Also trigger when the user wants to "see how memories
  connect" or "find related topics." If they want to visualize or analyze the structure of
  their stored knowledge, THIS is the skill.
---

# Knowledge Graph Skill — Extending the MemoryOS Graph Builder

## Overview

The knowledge graph builder lives in `backend/agents/graph_builder.py`. It uses NetworkX
to create a graph where **nodes** are memory chunks and **edges** represent relationships
(co-occurrence, semantic similarity, shared source). The graph can be exported as D3-compatible
JSON for frontend visualization.

---

## Core Graph Builder

```python
# backend/agents/graph_builder.py

import networkx as nx
from datetime import datetime
from backend.core.vector_store import vector_store

class KnowledgeGraphBuilder:
    def __init__(self):
        self.graph = nx.Graph()
    
    def build_from_memories(self, memories: list[dict]):
        """Build graph from a list of memory chunks."""
        # Add nodes
        for mem in memories:
            self.graph.add_node(
                mem["id"],
                text=mem["text"][:200],  # truncate for display
                source=mem["metadata"]["source"],
                source_type=mem["metadata"]["source_type"],
                ingested_at=mem["metadata"]["ingested_at"],
            )
        
        # Add edges based on shared source
        self._add_source_edges(memories)
        
        # Add edges based on semantic similarity
        self._add_similarity_edges(memories)
        
        return self.graph
    
    def _add_source_edges(self, memories):
        """Connect chunks from the same source document."""
        by_source = {}
        for mem in memories:
            source = mem["metadata"]["source"]
            by_source.setdefault(source, []).append(mem["id"])
        
        for source, ids in by_source.items():
            for i in range(len(ids) - 1):
                self.graph.add_edge(
                    ids[i], ids[i + 1],
                    relationship="same_source",
                    weight=1.0,
                )
    
    def _add_similarity_edges(self, memories, threshold: float = 0.7):
        """Connect chunks with high semantic similarity."""
        from sentence_transformers import SentenceTransformer
        import numpy as np
        
        model = SentenceTransformer("all-MiniLM-L6-v2")
        texts = [m["text"] for m in memories]
        embeddings = model.encode(texts, normalize_embeddings=True)
        
        # Cosine similarity matrix
        sim_matrix = np.dot(embeddings, embeddings.T)
        
        for i in range(len(memories)):
            for j in range(i + 1, len(memories)):
                if sim_matrix[i][j] >= threshold:
                    self.graph.add_edge(
                        memories[i]["id"],
                        memories[j]["id"],
                        relationship="semantic_similarity",
                        weight=float(sim_matrix[i][j]),
                    )
    
    def export_d3_json(self) -> dict:
        """Export graph as D3-compatible JSON."""
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "label": data.get("text", "")[:50],
                "source": data.get("source", ""),
                "source_type": data.get("source_type", ""),
                "group": data.get("source_type", "unknown"),
            })
        
        links = []
        for u, v, data in self.graph.edges(data=True):
            links.append({
                "source": u,
                "target": v,
                "relationship": data.get("relationship", ""),
                "weight": data.get("weight", 1.0),
            })
        
        return {"nodes": nodes, "links": links}
    
    def get_communities(self) -> list[set]:
        """Detect topic communities using Louvain method."""
        from networkx.algorithms.community import louvain_communities
        return louvain_communities(self.graph, weight="weight")
    
    def get_central_nodes(self, top_n: int = 10) -> list[tuple]:
        """Find the most central/important memory nodes."""
        centrality = nx.betweenness_centrality(self.graph, weight="weight")
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_n]
    
    def get_node_neighbors(self, node_id: str) -> list[dict]:
        """Get all neighbors of a node with edge data."""
        neighbors = []
        for neighbor in self.graph.neighbors(node_id):
            edge_data = self.graph.edges[node_id, neighbor]
            node_data = self.graph.nodes[neighbor]
            neighbors.append({
                "id": neighbor,
                "text": node_data.get("text", ""),
                "relationship": edge_data.get("relationship", ""),
                "weight": edge_data.get("weight", 0),
            })
        return neighbors
```

---

## Adding Smarter Edge Logic

### Semantic Similarity Edges (Cosine Distance)

```python
def _add_similarity_edges(self, memories, threshold=0.7):
    """Add edges between memories that are semantically similar."""
    # Use the vector store's embedding function for consistency
    embeddings = vector_store.embedding_fn(
        [m["text"] for m in memories]
    )
    
    for i in range(len(memories)):
        for j in range(i + 1, len(memories)):
            # Cosine similarity
            sim = np.dot(embeddings[i], embeddings[j])
            if sim >= threshold:
                self.graph.add_edge(
                    memories[i]["id"],
                    memories[j]["id"],
                    relationship="semantic_similarity",
                    weight=float(sim),
                )
```

### Temporal Edges

```python
def _add_temporal_edges(self, memories, max_hours_apart=24):
    """Connect memories ingested close together in time."""
    from datetime import datetime, timedelta
    
    for i in range(len(memories)):
        for j in range(i + 1, len(memories)):
            t1 = datetime.fromisoformat(memories[i]["metadata"]["ingested_at"])
            t2 = datetime.fromisoformat(memories[j]["metadata"]["ingested_at"])
            hours_apart = abs((t1 - t2).total_seconds()) / 3600
            
            if hours_apart <= max_hours_apart:
                self.graph.add_edge(
                    memories[i]["id"],
                    memories[j]["id"],
                    relationship="temporal_proximity",
                    weight=1.0 - (hours_apart / max_hours_apart),
                )
```

---

## FastAPI Endpoint for Graph Data

```python
# backend/api/main.py

from backend.agents.graph_builder import KnowledgeGraphBuilder

@app.get("/graph")
async def get_knowledge_graph(limit: int = 100):
    """Get the knowledge graph as D3-compatible JSON."""
    memories = vector_store.list_memories(limit=limit)
    
    builder = KnowledgeGraphBuilder()
    formatted = [
        {"id": memories["ids"][i], "text": memories["documents"][i], "metadata": memories["metadatas"][i]}
        for i in range(len(memories["ids"]))
    ]
    builder.build_from_memories(formatted)
    
    return builder.export_d3_json()

@app.get("/graph/communities")
async def get_communities():
    """Detect topic communities in the knowledge graph."""
    # Build graph first
    memories = vector_store.list_memories(limit=200)
    builder = KnowledgeGraphBuilder()
    formatted = [
        {"id": memories["ids"][i], "text": memories["documents"][i], "metadata": memories["metadatas"][i]}
        for i in range(len(memories["ids"]))
    ]
    builder.build_from_memories(formatted)
    
    communities = builder.get_communities()
    return {
        "communities": [list(c) for c in communities],
        "num_communities": len(communities),
    }
```

---

## NetworkX Algorithms Reference

| Algorithm | Use Case | Method |
|-----------|----------|--------|
| Louvain Communities | Topic/cluster detection | `louvain_communities(G)` |
| Betweenness Centrality | Find key connecting memories | `betweenness_centrality(G)` |
| PageRank | Find most important memories | `nx.pagerank(G)` |
| Shortest Path | Find connection between two memories | `nx.shortest_path(G, s, t)` |
| Connected Components | Find isolated memory groups | `nx.connected_components(G)` |

---

## Error Handling

- **Empty graph**: Check that memories exist before building
- **Too many edges**: Increase similarity threshold (0.7 → 0.85)
- **Slow performance**: Limit memories to 200–500 for graph building
- **Disconnected nodes**: Lower threshold or add temporal edges
