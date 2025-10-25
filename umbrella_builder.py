#!/usr/bin/env python3
"""
Umbrella Builder - Clusters related topics into semantic umbrellas

This module builds topic similarity graphs and uses community detection
to group related topics into meaningful umbrellas (meta-topics).

Clustering Strategies:
1. Leiden/Louvain (preferred) - Graph-based community detection
2. HDBSCAN (fallback) - Density-based clustering

Usage:
    python umbrella_builder.py build --account kwrt_
    python umbrella_builder.py build-all
    python umbrella_builder.py visualize --account kwrt_
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Try importing graph clustering libraries
LEIDEN_AVAILABLE = False
LOUVAIN_AVAILABLE = False
HDBSCAN_AVAILABLE = False

try:
    import igraph as ig
    import leidenalg
    LEIDEN_AVAILABLE = True
    logger.info("✓ Leiden algorithm available")
except ImportError:
    logger.warning("⚠ leidenalg not available, trying louvain...")

try:
    import community.community_louvain as community_louvain
    import networkx as nx
    LOUVAIN_AVAILABLE = True
    logger.info("✓ Louvain algorithm available")
except ImportError:
    logger.warning("⚠ Louvain not available, falling back to HDBSCAN...")

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
    logger.info("✓ HDBSCAN available")
except ImportError:
    logger.warning("⚠ HDBSCAN not available")

if not (LEIDEN_AVAILABLE or LOUVAIN_AVAILABLE or HDBSCAN_AVAILABLE):
    logger.error("❌ No clustering library available! Install one of:")
    logger.error("   pip install leidenalg python-igraph")
    logger.error("   pip install python-louvain networkx")
    logger.error("   pip install hdbscan")


@dataclass
class TopicNode:
    """Represents a single topic in the graph"""
    topic: str
    canonical: str
    frequency: int
    avg_score: float
    video_ids: List[str]
    embedding: np.ndarray = None


@dataclass
class UmbrellaCluster:
    """Represents a semantic umbrella containing related topics"""
    umbrella_id: str
    label: str
    members: List[str]  # canonical topic names
    member_count: int
    total_frequency: int
    avg_coherence: float
    representative_topics: List[str]  # top 3-5 topics
    video_ids: Set[str]
    stats: Dict


class UmbrellaBuilder:
    """Builds topic umbrellas using graph clustering"""
    
    def __init__(self, 
                 similarity_threshold: float = 0.7,
                 min_cluster_size: int = 2,
                 resolution: float = 1.0):
        """
        Args:
            similarity_threshold: Minimum cosine similarity to create edge
            min_cluster_size: Minimum topics per umbrella
            resolution: Clustering resolution (higher = more clusters)
        """
        self.similarity_threshold = similarity_threshold
        self.min_cluster_size = min_cluster_size
        self.resolution = resolution
        
        # Load sentence transformer for embeddings
        logger.info("Loading sentence transformer model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Model loaded successfully")
        
    def build_account_umbrellas(self, username: str, max_umbrellas: int = 5) -> Dict:
        """
        Build umbrellas for a single account
        
        Args:
            username: TikTok username
            max_umbrellas: Maximum number of umbrellas to return (default: 5)
            
        Returns:
            Dictionary with umbrella data
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Building umbrellas for @{username}")
        logger.info(f"{'='*60}")
        
        # Load account tags
        account_path = Path(f"accounts/{username}/topics/account_tags.json")
        if not account_path.exists():
            logger.error(f"Account tags not found: {account_path}")
            return None
            
        with open(account_path) as f:
            account_data = json.load(f)
            
        tags = account_data.get('tags', [])
        if len(tags) < self.min_cluster_size:
            logger.warning(f"Too few tags ({len(tags)}) to build umbrellas")
            return None
            
        logger.info(f"Loaded {len(tags)} tags")
        
        # Extract canonical topics with metadata
        # Load canonical mapping if exists
        canonical_config_path = Path("config/canonical_topics.json")
        canonical_rules = {}
        if canonical_config_path.exists():
            with open(canonical_config_path) as f:
                config = json.load(f)
                canonical_rules = config.get('merge_rules', {})
        
        topic_nodes = []
        canonical_map = {}  # canonical -> list of original tags
        
        for tag_data in tags:
            tag = tag_data['tag']
            
            # Get canonical form (from V2 data or apply rules)
            if 'canonical' in tag_data:
                canonical = tag_data['canonical']
            else:
                # Apply canonical rules for V1 data
                canonical = canonical_rules.get(tag.lower(), tag)
            
            if canonical not in canonical_map:
                canonical_map[canonical] = []
            canonical_map[canonical].append(tag)
            
            node = TopicNode(
                topic=tag,
                canonical=canonical,
                frequency=tag_data.get('frequency', 1),
                avg_score=tag_data.get('avg_score', 0.5),
                video_ids=tag_data.get('video_ids', [])
            )
            topic_nodes.append(node)
            
        logger.info(f"Found {len(canonical_map)} unique canonical topics")
        
        # Compute embeddings for canonical topics
        canonical_topics = list(canonical_map.keys())
        logger.info("Computing embeddings...")
        embeddings = self.model.encode(canonical_topics, show_progress_bar=False)
        
        # Store embeddings in nodes
        embedding_map = {topic: emb for topic, emb in zip(canonical_topics, embeddings)}
        for node in topic_nodes:
            node.embedding = embedding_map[node.canonical]
            
        # Build similarity graph
        logger.info("Building similarity graph...")
        adj_matrix, edge_count = self._build_similarity_graph(
            canonical_topics, 
            embeddings
        )
        logger.info(f"Created graph with {edge_count} edges (threshold={self.similarity_threshold})")
        
        # Apply clustering algorithm
        logger.info("Running community detection...")
        clusters = self._cluster_topics(canonical_topics, adj_matrix)
        
        if not clusters:
            logger.warning("No clusters found")
            return None
            
        # Build umbrella objects
        logger.info(f"Found {len(clusters)} clusters")
        umbrellas = self._build_umbrellas(
            clusters, 
            topic_nodes, 
            canonical_map,
            embeddings,
            canonical_topics
        )
        
        # Sort umbrellas by size (member_count) descending and limit
        umbrellas.sort(key=lambda u: u.member_count, reverse=True)
        top_umbrellas = umbrellas[:max_umbrellas]
        
        logger.info(f"Limiting to top {len(top_umbrellas)} umbrellas (out of {len(umbrellas)} total)")
        
        # Create output structure
        output = {
            'username': username,
            'total_topics': len(tags),
            'canonical_topics': len(canonical_map),
            'umbrella_count': len(top_umbrellas),
            'total_clusters': len(umbrellas),  # Keep track of total clusters found
            'clustering_method': self._get_clustering_method(),
            'similarity_threshold': self.similarity_threshold,
            'umbrellas': [asdict(u) for u in top_umbrellas]
        }
        
        # Convert sets to lists for JSON serialization
        for umbrella in output['umbrellas']:
            umbrella['video_ids'] = sorted(list(umbrella['video_ids']))
            
        # Save to file
        output_path = Path(f"accounts/{username}/topics/topic_umbrellas.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
            
        logger.info(f"✓ Saved umbrellas to {output_path}")
        
        # Print summary
        self._print_umbrella_summary(top_umbrellas)
        
        return output
        
    def _build_similarity_graph(self, 
                                 topics: List[str], 
                                 embeddings: np.ndarray) -> Tuple[np.ndarray, int]:
        """
        Build adjacency matrix from topic embeddings
        
        Args:
            topics: List of topic strings
            embeddings: Topic embeddings matrix
            
        Returns:
            (adjacency_matrix, edge_count)
        """
        # Compute pairwise cosine similarities
        sim_matrix = cosine_similarity(embeddings)
        
        # Threshold and remove self-loops
        adj_matrix = (sim_matrix >= self.similarity_threshold).astype(int)
        np.fill_diagonal(adj_matrix, 0)
        
        edge_count = np.sum(adj_matrix) // 2  # Divide by 2 for undirected
        
        return adj_matrix, edge_count
        
    def _cluster_topics(self, 
                        topics: List[str], 
                        adj_matrix: np.ndarray) -> List[List[int]]:
        """
        Apply community detection algorithm
        
        Args:
            topics: List of topic strings
            adj_matrix: Adjacency matrix
            
        Returns:
            List of clusters (each cluster is list of topic indices)
        """
        if LEIDEN_AVAILABLE:
            return self._cluster_leiden(adj_matrix)
        elif LOUVAIN_AVAILABLE:
            return self._cluster_louvain(adj_matrix)
        elif HDBSCAN_AVAILABLE:
            return self._cluster_hdbscan(topics, adj_matrix)
        else:
            # Fallback: connected components
            logger.warning("Using basic connected components (no optimization)")
            return self._cluster_connected_components(adj_matrix)
            
    def _cluster_leiden(self, adj_matrix: np.ndarray) -> List[List[int]]:
        """Leiden algorithm clustering"""
        # Convert to igraph
        sources, targets = np.where(np.triu(adj_matrix, k=1))
        edges = list(zip(sources.tolist(), targets.tolist()))
        
        g = ig.Graph()
        g.add_vertices(adj_matrix.shape[0])
        g.add_edges(edges)
        
        # Run Leiden
        partition = leidenalg.find_partition(
            g, 
            leidenalg.ModularityVertexPartition,
            resolution_parameter=self.resolution
        )
        
        # Group by community
        clusters = defaultdict(list)
        for node_id, community_id in enumerate(partition.membership):
            clusters[community_id].append(node_id)
            
        # Filter by min size
        clusters = [c for c in clusters.values() if len(c) >= self.min_cluster_size]
        
        logger.info(f"Leiden found {len(clusters)} clusters")
        return clusters
        
    def _cluster_louvain(self, adj_matrix: np.ndarray) -> List[List[int]]:
        """Louvain algorithm clustering"""
        # Convert to networkx
        G = nx.from_numpy_array(adj_matrix)
        
        # Run Louvain
        partition = community_louvain.best_partition(
            G, 
            resolution=self.resolution,
            random_state=42
        )
        
        # Group by community
        clusters = defaultdict(list)
        for node_id, community_id in partition.items():
            clusters[community_id].append(node_id)
            
        # Filter by min size
        clusters = [c for c in clusters.values() if len(c) >= self.min_cluster_size]
        
        logger.info(f"Louvain found {len(clusters)} clusters")
        return clusters
        
    def _cluster_hdbscan(self, topics: List[str], adj_matrix: np.ndarray) -> List[List[int]]:
        """HDBSCAN clustering (fallback)"""
        # Convert adjacency to distance
        distance_matrix = 1 - (adj_matrix.astype(float) / adj_matrix.max())
        
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            metric='precomputed',
            cluster_selection_epsilon=0.3
        )
        
        labels = clusterer.fit_predict(distance_matrix)
        
        # Group by label (ignore noise points with label=-1)
        clusters = defaultdict(list)
        for idx, label in enumerate(labels):
            if label >= 0:
                clusters[label].append(idx)
                
        clusters = list(clusters.values())
        
        logger.info(f"HDBSCAN found {len(clusters)} clusters")
        return clusters
        
    def _cluster_connected_components(self, adj_matrix: np.ndarray) -> List[List[int]]:
        """Basic connected components (no optimization)"""
        sparse_matrix = csr_matrix(adj_matrix)
        n_components, labels = connected_components(sparse_matrix, directed=False)
        
        # Group by component
        clusters = defaultdict(list)
        for idx, label in enumerate(labels):
            clusters[label].append(idx)
            
        # Filter by min size
        clusters = [c for c in clusters.values() if len(c) >= self.min_cluster_size]
        
        logger.info(f"Connected components found {len(clusters)} clusters")
        return clusters
    
    def _generate_umbrella_label(self, cluster_topics: List[str], cluster_embeddings: np.ndarray) -> str:
        """
        Generate a broad, concise label for an umbrella cluster
        
        Strategy:
        1. Extract meaningful noun/adjective words
        2. Prioritize words that appear across multiple topics (high coverage)
        3. Use 1-2 words that capture the semantic theme
        
        Args:
            cluster_topics: List of canonical topics in cluster
            cluster_embeddings: Embeddings for these topics
            
        Returns:
            1-2 word label (capitalized)
        """
        # Extract individual words from all topics
        word_counts = defaultdict(int)
        word_topics = defaultdict(set)  # Track which topics contain each word
        
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'from', 'by', 'is', 'are', 'was', 'were', 'be', 'been',
                     'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                     'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
                     'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
                     'my', 'your', 'his', 'her', 'its', 'our', 'their', 'me', 'him',
                     'just', 'like', 'really', 'very', 'too', 'so', 'such', 'make',
                     'get', 'got', 'going', 'go', 'thing', 'things', 'people', 'person',
                     'video', 'videos', 'watching', 'watch', 'thank', 'thanks'}
        
        for topic in cluster_topics:
            words = topic.lower().split()
            for word in words:
                # Clean word
                word = word.strip('.,!?;:()[]{}"\'-#')
                if len(word) > 3 and word not in stopwords and word.isalpha():
                    word_counts[word] += 1
                    word_topics[word].add(topic)
        
        if not word_counts:
            # Fallback: use first topic cleaned up
            first_topic = cluster_topics[0].lower()
            words = [w.strip('.,!?;:()[]{}"\'-#') for w in first_topic.split()]
            for w in words:
                if len(w) > 3 and w not in stopwords:
                    return w.capitalize()
            return first_topic.split()[0].capitalize()
        
        # Score words by coverage (prioritize words that appear in many topics)
        word_scores = {}
        for word, count in word_counts.items():
            coverage = len(word_topics[word]) / len(cluster_topics)  # 0-1
            # Heavily weight coverage to get broader terms
            word_scores[word] = (coverage * 3) + (count * 0.5)
        
        # Get top words
        sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Strategy: Use top word if it has good coverage (>30%)
        top_word = sorted_words[0][0]
        top_coverage = len(word_topics[top_word]) / len(cluster_topics)
        
        # If single word has decent coverage, use it
        if top_coverage >= 0.3 or len(sorted_words) == 1:
            return top_word.capitalize()
        
        # Otherwise, try to find a complementary second word
        if len(sorted_words) >= 2:
            for second_word, score in sorted_words[1:4]:  # Check next 3 words
                # Check if they're complementary (not in same topics too often)
                overlap = len(word_topics[top_word] & word_topics[second_word])
                overlap_ratio = overlap / min(len(word_topics[top_word]), len(word_topics[second_word]))
                
                # If they're complementary (<50% overlap), combine them
                if overlap_ratio < 0.5:
                    return f"{top_word.capitalize()} {second_word.capitalize()}"
        
        return top_word.capitalize()
        
    def _build_umbrellas(self,
                         clusters: List[List[int]],
                         topic_nodes: List[TopicNode],
                         canonical_map: Dict,
                         embeddings: np.ndarray,
                         canonical_topics: List[str]) -> List[UmbrellaCluster]:
        """
        Convert clusters to umbrella objects
        
        Args:
            clusters: List of topic index lists
            topic_nodes: All topic nodes
            canonical_map: Canonical -> original tags
            embeddings: Topic embeddings
            canonical_topics: List of canonical topics
            
        Returns:
            List of UmbrellaCluster objects
        """
        umbrellas = []
        
        for i, cluster_indices in enumerate(clusters):
            # Get canonical topics in this cluster
            cluster_topics = [canonical_topics[idx] for idx in cluster_indices]
            
            # Find all nodes with these canonicals
            cluster_nodes = [
                node for node in topic_nodes 
                if node.canonical in cluster_topics
            ]
            
            if not cluster_nodes:
                continue
                
            # Aggregate stats
            total_frequency = sum(node.frequency for node in cluster_nodes)
            video_ids = set()
            for node in cluster_nodes:
                video_ids.update(node.video_ids)
                
            # Compute cluster coherence (average pairwise similarity)
            cluster_embeddings = embeddings[cluster_indices]
            if len(cluster_embeddings) > 1:
                sim_matrix = cosine_similarity(cluster_embeddings)
                # Average of upper triangle (excluding diagonal)
                mask = np.triu(np.ones_like(sim_matrix), k=1).astype(bool)
                avg_coherence = sim_matrix[mask].mean()
            else:
                avg_coherence = 1.0
                
            # Generate broad umbrella label
            label = self._generate_umbrella_label(cluster_topics, cluster_embeddings)
            
            # Get top representative topics (by frequency)
            sorted_nodes = sorted(cluster_nodes, key=lambda n: n.frequency, reverse=True)
            representative_topics = [n.canonical for n in sorted_nodes[:5]]
            
            umbrella = UmbrellaCluster(
                umbrella_id=f"umbrella_{i+1}",
                label=label,
                members=cluster_topics,
                member_count=len(cluster_topics),
                total_frequency=total_frequency,
                avg_coherence=float(avg_coherence),
                representative_topics=representative_topics,
                video_ids=video_ids,
                stats={
                    'min_frequency': min(n.frequency for n in cluster_nodes),
                    'max_frequency': max(n.frequency for n in cluster_nodes),
                    'avg_score': np.mean([n.avg_score for n in cluster_nodes])
                }
            )
            
            umbrellas.append(umbrella)
            
        # Sort by total frequency
        umbrellas.sort(key=lambda u: u.total_frequency, reverse=True)
        
        return umbrellas
        
    def _get_clustering_method(self) -> str:
        """Return name of clustering method used"""
        if LEIDEN_AVAILABLE:
            return "leiden"
        elif LOUVAIN_AVAILABLE:
            return "louvain"
        elif HDBSCAN_AVAILABLE:
            return "hdbscan"
        else:
            return "connected_components"
            
    def _print_umbrella_summary(self, umbrellas: List[UmbrellaCluster]):
        """Print human-readable summary of umbrellas"""
        logger.info(f"\n{'='*60}")
        logger.info(f"UMBRELLA SUMMARY")
        logger.info(f"{'='*60}\n")
        
        for umbrella in umbrellas:
            logger.info(f"🌂 {umbrella.label.upper()}")
            logger.info(f"   ID: {umbrella.umbrella_id}")
            logger.info(f"   Members: {umbrella.member_count} topics")
            logger.info(f"   Frequency: {umbrella.total_frequency} occurrences")
            logger.info(f"   Coherence: {umbrella.avg_coherence:.3f}")
            logger.info(f"   Videos: {len(umbrella.video_ids)}")
            logger.info(f"   Top Topics: {', '.join(umbrella.representative_topics[:3])}")
            logger.info("")
            
    def build_all_accounts(self):
        """Build umbrellas for all accounts"""
        accounts_dir = Path("accounts")
        
        if not accounts_dir.exists():
            logger.error("accounts/ directory not found")
            return
            
        # Find all accounts with topics
        accounts = []
        for account_dir in accounts_dir.iterdir():
            if account_dir.is_dir():
                tags_file = account_dir / "topics" / "account_tags.json"
                if tags_file.exists():
                    accounts.append(account_dir.name)
                    
        logger.info(f"Found {len(accounts)} accounts with topics")
        
        for username in accounts:
            try:
                self.build_account_umbrellas(username)
            except Exception as e:
                logger.error(f"Failed to build umbrellas for @{username}: {e}")
                continue


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build topic umbrellas")
    parser.add_argument('command', choices=['build', 'build-all', 'visualize'])
    parser.add_argument('--account', help='TikTok username')
    parser.add_argument('--threshold', type=float, default=0.7,
                       help='Similarity threshold (default: 0.7)')
    parser.add_argument('--min-size', type=int, default=2,
                       help='Minimum cluster size (default: 2)')
    parser.add_argument('--resolution', type=float, default=1.0,
                       help='Clustering resolution (default: 1.0)')
    
    args = parser.parse_args()
    
    builder = UmbrellaBuilder(
        similarity_threshold=args.threshold,
        min_cluster_size=args.min_size,
        resolution=args.resolution
    )
    
    if args.command == 'build':
        if not args.account:
            parser.error("--account required for build command")
        builder.build_account_umbrellas(args.account)
        
    elif args.command == 'build-all':
        builder.build_all_accounts()
        
    elif args.command == 'visualize':
        if not args.account:
            parser.error("--account required for visualize command")
        # TODO: Add visualization
        logger.info("Visualization not yet implemented")


if __name__ == '__main__':
    main()
