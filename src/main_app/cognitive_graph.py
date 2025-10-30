# -*- coding: utf-8 -*-
"""
Cognitive Graph (A2 Specification Implementation)
=================================================
VERSION: V4.0

Implements the A2 specification:
- Provides a 'CognitiveGraph' class.
- Provides 'add_node' and 'add_edge' (in-memory).
- This is a lightweight, non-persistent implementation for V4.0.
"""
from loguru import logger
from typing import Dict, Any, List
import uuid

class CognitiveGraph:
    """
    (A2) Implements the Cognitive Graph (In-Memory).
    """
    
    def __init__(self):
        logger.info("Initializing CognitiveGraph (A2)...")
        # (A2, 6.1) In-Memory Representation
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []

    def add_node(self, node_dict: Dict[str, Any]) -> str:
        """
        (A2, 7) Adds a node to the graph and returns its ID.
        """
        node_id = f"{node_dict.get('type', 'node')}_{uuid.uuid4().hex[:8]}"
        
        if "id" not in node_dict:
            node_dict["id"] = node_id
            
        self.nodes[node_id] = node_dict
        logger.debug(f"CognitiveGraph: Added Node {node_id} (Label: {node_dict.get('label')})")
        
        return node_id

    def add_edge(self, src_id: str, dst_id: str, relation: str, meta: Dict[str, Any] = None):
        """
        (A2, 7) Adds an edge (relationship) between two nodes.
        """
        if src_id not in self.nodes:
            logger.warning(f"CognitiveGraph: Source node '{src_id}' not found for edge.")
            return
        if dst_id not in self.nodes:
            logger.warning(f"CognitiveGraph: Destination node '{dst_id}' not found for edge.")
            return

        edge = {
            "id": f"edge_{uuid.uuid4().hex[:8]}",
            "source": src_id,
            "target": dst_id,
            "relation": relation,
            "meta": meta or {}
        }
        self.edges.append(edge)
        logger.debug(f"CognitiveGraph: Added Edge ({src_id} -[{relation}]-> {dst_id})")

    def get_graph_snapshot(self) -> Dict[str, Any]:
        """
        (A2, 7) Exports the current graph state.
        """
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges
        }