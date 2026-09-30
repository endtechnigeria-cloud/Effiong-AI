"""
EFFIONG AI - Knowledge Graph Service
====================================
Lightweight entity/relationship graph (no external graph DB needed) used to visualise how heritage records,
research sources and predictions connect. Built from named entities (capitalised phrases + known heritage/African
place & people patterns) found in the text - a good approximation without needing spaCy/NLTK downloads.

Designed to upgrade cleanly: swap `build_graph` for a Neo4j / GraphRAG-backed version later without changing the
public API (`build_heritage_graph`, `build_research_graph`, `graph_statistics`, `export_graph`).
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List

_STOPWORD_ENTITIES = {"The", "This", "That", "These", "Those", "It", "In", "On", "At", "By", "For", "With",
                      "A", "An", "And", "Or", "But", "However", "Therefore", "Also", "According"}
# multi-word capitalised phrases (e.g. "Kingdom of Benin", "Oba Ewuare II")
_PHRASE_RE = re.compile(r"\b([A-Z][a-zA-Z'’]+(?:\s+(?:of|the|de|bin|ibn|al)\s+[A-Z][a-zA-Z'’]+|\s+[A-Z][a-zA-Z'’]+)*)\b")


class KnowledgeGraphService:
    def __init__(self) -> None:
        self.graph: Dict[str, List[Dict[str, Any]]] = {"nodes": [], "edges": []}

    # ------------------------------------------------------------------ entities
    def extract_entities(self, text: str, limit: int = 40) -> List[str]:
        text = text or ""
        found = [m.group(1).strip() for m in _PHRASE_RE.finditer(text)]
        counts = Counter(f for f in found if f not in _STOPWORD_ENTITIES and len(f) > 2)
        # prefer longer, more specific phrases and drop ones that are a strict substring of a more frequent one
        ranked = sorted(counts.items(), key=lambda kv: (-kv[1], -len(kv[0])))
        kept: List[str] = []
        for name, _ in ranked:
            if not any(name != other and name in other for other in kept):
                kept.append(name)
            if len(kept) >= limit:
                break
        return kept

    # ------------------------------------------------------------------ build
    def build_graph(self, documents: List[str], doc_labels: List[str] = None) -> Dict[str, Any]:
        node_weight: Counter = Counter()
        edge_weight: Counter = Counter()
        doc_labels = doc_labels or [f"doc_{i}" for i in range(len(documents))]
        for label, document in zip(doc_labels, documents):
            entities = self.extract_entities(document)
            for e in entities:
                node_weight[e] += 1
            for i in range(len(entities)):
                for j in range(i + 1, len(entities)):
                    key = tuple(sorted((entities[i], entities[j])))
                    edge_weight[key] += 1
        self.graph = {
            "nodes": [{"id": n, "label": n, "weight": w} for n, w in node_weight.most_common(150)],
            "edges": [{"source": a, "target": b, "weight": w} for (a, b), w in edge_weight.most_common(300)
                      if a in node_weight and b in node_weight],
        }
        return self.graph

    def build_heritage_graph(self, heritage_nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        docs = [f"{n.get('title', '')}. {n.get('description', '')}" for n in heritage_nodes]
        labels = [n.get("id", f"node_{i}") for i, n in enumerate(heritage_nodes)]
        graph = self.build_graph(docs, labels)
        for node, src in zip(heritage_nodes, docs):
            pass  # entity extraction already reflects the record content
        return graph

    def build_research_graph(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        docs = [f"{s.get('title', '')}. {s.get('summary', '')}" for s in sources]
        return self.build_graph(docs)

    def build_prediction_graph(self, forecasts: List[Dict[str, Any]]) -> Dict[str, Any]:
        docs = [f"{f.get('topic', '')}. {f.get('disclaimer', '')}" for f in forecasts]
        return self.build_graph(docs)

    # ------------------------------------------------------------------ read
    def graph_statistics(self) -> Dict[str, int]:
        return {"nodes": len(self.graph["nodes"]), "edges": len(self.graph["edges"])}

    def export_graph(self) -> Dict[str, Any]:
        return self.graph

    def top_entities(self, n: int = 10) -> List[str]:
        return [node["id"] for node in sorted(self.graph["nodes"], key=lambda x: -x["weight"])[:n]]

    def neighbors(self, entity: str) -> List[str]:
        out = []
        for e in self.graph["edges"]:
            if e["source"] == entity:
                out.append(e["target"])
            elif e["target"] == entity:
                out.append(e["source"])
        return out


knowledge_graph_service = KnowledgeGraphService()
