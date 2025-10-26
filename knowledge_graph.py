"""
YMERA Knowledge Graph Engine
Entity extraction, relationship mapping, reasoning, and graph-based knowledge management.
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import networkx as nx
import hashlib
from collections import defaultdict

logger = logging.getLogger("ymera.knowledge_graph")


class EntityType(Enum):
    """Types of entities in the knowledge graph"""
    CONCEPT = "concept"
    MODEL = "model"
    DATASET = "dataset"
    ALGORITHM = "algorithm"
    METRIC = "metric"
    TASK = "task"
    PATTERN = "pattern"
    USER = "user"
    ORGANIZATION = "organization"


class RelationType(Enum):
    """Types of relationships between entities"""
    IS_A = "is_a"
    PART_OF = "part_of"
    RELATED_TO = "related_to"
    USES = "uses"
    PRODUCES = "produces"
    TRAINED_ON = "trained_on"
    EVALUATED_BY = "evaluated_by"
    SIMILAR_TO = "similar_to"
    DERIVED_FROM = "derived_from"
    DEPENDS_ON = "depends_on"


@dataclass
class Entity:
    """Represents an entity in the knowledge graph"""
    entity_id: str
    entity_type: EntityType
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class Relationship:
    """Represents a relationship between entities"""
    relationship_id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "relationship_id": self.relationship_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
            "weight": self.weight,
            "properties": self.properties,
            "created_at": self.created_at.isoformat()
        }


class KnowledgeGraphEngine:
    """
    Knowledge Graph Engine for entity extraction, relationship mapping,
    reasoning, and graph-based knowledge management.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Knowledge Graph Engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.graph = nx.DiGraph()
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        
        # Indexes for fast lookup
        self.entity_type_index: Dict[EntityType, Set[str]] = defaultdict(set)
        self.entity_name_index: Dict[str, str] = {}
        
        # Configuration
        self.enable_reasoning = config.get("enable_reasoning", True)
        self.max_path_length = config.get("max_path_length", 5)
        
        logger.info(f"Knowledge Graph Engine initialized with config: {config}")
    
    async def add_entity(self, 
                        entity_type: EntityType,
                        name: str,
                        properties: Optional[Dict[str, Any]] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add an entity to the knowledge graph.
        
        Args:
            entity_type: Type of entity
            name: Entity name
            properties: Entity properties
            metadata: Additional metadata
            
        Returns:
            Entity ID
        """
        entity_id = self._generate_entity_id(entity_type, name)
        
        if entity_id in self.entities:
            # Update existing entity
            entity = self.entities[entity_id]
            if properties:
                entity.properties.update(properties)
            if metadata:
                entity.metadata.update(metadata)
            entity.updated_at = datetime.utcnow()
            logger.info(f"Updated entity {entity_id}")
        else:
            # Create new entity
            entity = Entity(
                entity_id=entity_id,
                entity_type=entity_type,
                name=name,
                properties=properties or {},
                metadata=metadata or {}
            )
            
            self.entities[entity_id] = entity
            self.entity_type_index[entity_type].add(entity_id)
            self.entity_name_index[name.lower()] = entity_id
            
            # Add to graph
            self.graph.add_node(entity_id, **entity.to_dict())
            
            logger.info(f"Added entity {entity_id} ({entity_type.value}): {name}")
        
        return entity_id
    
    async def add_relationship(self,
                              source_id: str,
                              target_id: str,
                              relation_type: RelationType,
                              weight: float = 1.0,
                              properties: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a relationship between two entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relation_type: Type of relationship
            weight: Relationship weight/strength
            properties: Additional properties
            
        Returns:
            Relationship ID
        """
        if source_id not in self.entities or target_id not in self.entities:
            raise ValueError("Source or target entity not found")
        
        relationship_id = self._generate_relationship_id(source_id, target_id, relation_type)
        
        if relationship_id in self.relationships:
            # Update existing relationship
            relationship = self.relationships[relationship_id]
            relationship.weight = weight
            if properties:
                relationship.properties.update(properties)
            logger.info(f"Updated relationship {relationship_id}")
        else:
            # Create new relationship
            relationship = Relationship(
                relationship_id=relationship_id,
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type,
                weight=weight,
                properties=properties or {}
            )
            
            self.relationships[relationship_id] = relationship
            
            # Add edge to graph
            self.graph.add_edge(
                source_id,
                target_id,
                relationship_id=relationship_id,
                relation_type=relation_type.value,
                weight=weight,
                **relationship.to_dict()
            )
            
            logger.info(f"Added relationship {relationship_id}: {source_id} -{relation_type.value}-> {target_id}")
        
        return relationship_id
    
    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID"""
        return self.entities.get(entity_id)
    
    async def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """Get an entity by name"""
        entity_id = self.entity_name_index.get(name.lower())
        return self.entities.get(entity_id) if entity_id else None
    
    async def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Get all entities of a specific type"""
        entity_ids = self.entity_type_index.get(entity_type, set())
        return [self.entities[eid] for eid in entity_ids]
    
    async def get_related_entities(self,
                                  entity_id: str,
                                  relation_type: Optional[RelationType] = None,
                                  direction: str = "outgoing") -> List[Tuple[Entity, Relationship]]:
        """
        Get entities related to a given entity.
        
        Args:
            entity_id: Entity ID
            relation_type: Filter by relationship type
            direction: "outgoing", "incoming", or "both"
            
        Returns:
            List of (Entity, Relationship) tuples
        """
        if entity_id not in self.entities:
            return []
        
        related = []
        
        if direction in ["outgoing", "both"]:
            # Outgoing relationships
            for target_id in self.graph.successors(entity_id):
                edge_data = self.graph[entity_id][target_id]
                rel_id = edge_data.get("relationship_id")
                relationship = self.relationships.get(rel_id)
                
                if relationship and (not relation_type or relationship.relation_type == relation_type):
                    target_entity = self.entities.get(target_id)
                    if target_entity:
                        related.append((target_entity, relationship))
        
        if direction in ["incoming", "both"]:
            # Incoming relationships
            for source_id in self.graph.predecessors(entity_id):
                edge_data = self.graph[source_id][entity_id]
                rel_id = edge_data.get("relationship_id")
                relationship = self.relationships.get(rel_id)
                
                if relationship and (not relation_type or relationship.relation_type == relation_type):
                    source_entity = self.entities.get(source_id)
                    if source_entity:
                        related.append((source_entity, relationship))
        
        return related
    
    async def find_path(self,
                       source_id: str,
                       target_id: str,
                       max_length: Optional[int] = None) -> Optional[List[str]]:
        """
        Find a path between two entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            max_length: Maximum path length
            
        Returns:
            List of entity IDs forming the path, or None if no path exists
        """
        if source_id not in self.graph or target_id not in self.graph:
            return None
        
        try:
            if max_length:
                cutoff = max_length
            else:
                cutoff = self.max_path_length
            
            path = nx.shortest_path(self.graph, source_id, target_id, weight="weight")
            
            if len(path) <= cutoff + 1:  # +1 because path includes source and target
                return path
            return None
        except nx.NetworkXNoPath:
            return None
    
    async def find_all_paths(self,
                            source_id: str,
                            target_id: str,
                            max_length: Optional[int] = None) -> List[List[str]]:
        """
        Find all paths between two entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            max_length: Maximum path length
            
        Returns:
            List of paths (each path is a list of entity IDs)
        """
        if source_id not in self.graph or target_id not in self.graph:
            return []
        
        cutoff = max_length if max_length else self.max_path_length
        
        try:
            paths = nx.all_simple_paths(self.graph, source_id, target_id, cutoff=cutoff)
            return list(paths)
        except nx.NetworkXNoPath:
            return []
    
    async def get_neighbors(self,
                           entity_id: str,
                           depth: int = 1) -> Set[str]:
        """
        Get all neighbors of an entity within a certain depth.
        
        Args:
            entity_id: Entity ID
            depth: Depth of neighborhood (1 = direct neighbors)
            
        Returns:
            Set of entity IDs
        """
        if entity_id not in self.graph:
            return set()
        
        neighbors = set()
        current_level = {entity_id}
        
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                # Get successors and predecessors
                next_level.update(self.graph.successors(node))
                next_level.update(self.graph.predecessors(node))
            
            neighbors.update(next_level)
            current_level = next_level - neighbors - {entity_id}
            
            if not current_level:
                break
        
        return neighbors - {entity_id}
    
    async def compute_centrality(self, 
                                centrality_type: str = "degree") -> Dict[str, float]:
        """
        Compute centrality measures for all entities.
        
        Args:
            centrality_type: "degree", "betweenness", "closeness", or "pagerank"
            
        Returns:
            Dict mapping entity IDs to centrality scores
        """
        if centrality_type == "degree":
            return dict(self.graph.degree())
        elif centrality_type == "betweenness":
            return nx.betweenness_centrality(self.graph, weight="weight")
        elif centrality_type == "closeness":
            return nx.closeness_centrality(self.graph, distance="weight")
        elif centrality_type == "pagerank":
            return nx.pagerank(self.graph, weight="weight")
        else:
            raise ValueError(f"Unknown centrality type: {centrality_type}")
    
    async def detect_communities(self) -> List[Set[str]]:
        """
        Detect communities in the knowledge graph.
        
        Returns:
            List of communities (each community is a set of entity IDs)
        """
        # Convert to undirected for community detection
        undirected = self.graph.to_undirected()
        
        # Use Louvain method for community detection (requires networkx >= 2.5)
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(undirected)
            
            # Group entities by community
            communities = defaultdict(set)
            for entity_id, community_id in partition.items():
                communities[community_id].add(entity_id)
            
            return list(communities.values())
        except ImportError:
            # Fallback to connected components
            return [set(component) for component in nx.connected_components(undirected)]
    
    async def infer_relationships(self, entity_id: str) -> List[Tuple[str, RelationType]]:
        """
        Infer potential relationships using graph reasoning.
        
        This uses simple transitive rules:
        - If A is_a B and B is_a C, then A is_a C
        - If A part_of B and B part_of C, then A part_of C
        
        Args:
            entity_id: Entity ID
            
        Returns:
            List of (target_entity_id, relation_type) tuples
        """
        if not self.enable_reasoning:
            return []
        
        inferred = []
        
        # Get 2-hop neighbors
        neighbors_1hop = self.get_neighbors(entity_id, depth=1)
        neighbors_2hop = await self.get_neighbors(entity_id, depth=2)
        
        # Infer transitive relationships
        for intermediate_id in await neighbors_1hop:
            intermediate_rels = await self.get_related_entities(intermediate_id, direction="outgoing")
            
            for target_entity, rel in intermediate_rels:
                target_id = target_entity.entity_id
                
                # Check if relationship already exists
                existing = await self.get_related_entities(entity_id, relation_type=rel.relation_type)
                existing_ids = {e.entity_id for e, _ in existing}
                
                if target_id not in existing_ids and target_id != entity_id:
                    # Check transitivity rules
                    if rel.relation_type in [RelationType.IS_A, RelationType.PART_OF]:
                        inferred.append((target_id, rel.relation_type))
        
        return inferred
    
    async def extract_entities_from_text(self, text: str) -> List[Entity]:
        """
        Extract entities from text (NER placeholder).
        
        In production, this would use spaCy or transformers for NER.
        
        Args:
            text: Input text
            
        Returns:
            List of extracted entities
        """
        # Placeholder for NER
        # In production, use spaCy or Hugging Face transformers
        
        # Simple keyword matching as placeholder
        keywords = ["model", "algorithm", "dataset", "metric"]
        extracted = []
        
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                entity_id = await self.add_entity(
                    entity_type=EntityType.CONCEPT,
                    name=keyword,
                    properties={"source": "text_extraction"}
                )
                entity = await self.get_entity(entity_id)
                if entity:
                    extracted.append(entity)
        
        return extracted
    
    async def get_subgraph(self, 
                          entity_ids: List[str],
                          include_neighbors: bool = False) -> nx.DiGraph:
        """
        Extract a subgraph containing specified entities.
        
        Args:
            entity_ids: List of entity IDs
            include_neighbors: Whether to include direct neighbors
            
        Returns:
            NetworkX DiGraph
        """
        nodes_to_include = set(entity_ids)
        
        if include_neighbors:
            for entity_id in entity_ids:
                neighbors = await self.get_neighbors(entity_id, depth=1)
                nodes_to_include.update(neighbors)
        
        return self.graph.subgraph(nodes_to_include).copy()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        entities_by_type = {}
        for entity_type in EntityType:
            count = len(self.entity_type_index.get(entity_type, set()))
            if count > 0:
                entities_by_type[entity_type.value] = count
        
        relationships_by_type = defaultdict(int)
        for rel in self.relationships.values():
            relationships_by_type[rel.relation_type.value] += 1
        
        # Graph metrics
        try:
            avg_degree = sum(dict(self.graph.degree()).values()) / len(self.graph.nodes()) if self.graph.nodes() else 0
            density = nx.density(self.graph)
        except Exception:
            avg_degree = 0
            density = 0
        
        return {
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "entities_by_type": entities_by_type,
            "relationships_by_type": dict(relationships_by_type),
            "average_degree": avg_degree,
            "graph_density": density
        }
    
    async def export_to_json(self, filepath: str):
        """Export knowledge graph to JSON file"""
        import json
        
        export_data = {
            "entities": [entity.to_dict() for entity in self.entities.values()],
            "relationships": [rel.to_dict() for rel in self.relationships.values()],
            "exported_at": datetime.utcnow().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported knowledge graph to {filepath}")
    
    def _generate_entity_id(self, entity_type: EntityType, name: str) -> str:
        """Generate a unique entity ID"""
        key = f"{entity_type.value}_{name}".lower()
        return hashlib.md5(key.encode()).hexdigest()[:16]
    
    def _generate_relationship_id(self, 
                                  source_id: str,
                                  target_id: str,
                                  relation_type: RelationType) -> str:
        """Generate a unique relationship ID"""
        key = f"{source_id}_{target_id}_{relation_type.value}"
        return hashlib.md5(key.encode()).hexdigest()[:16]
