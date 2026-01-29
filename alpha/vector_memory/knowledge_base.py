"""
Alpha - Knowledge Base Management

Provides structured knowledge storage and retrieval with semantic search.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .vector_store import VectorStore
from .embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class KnowledgeEntry:
    """Represents a knowledge entry."""

    def __init__(
        self,
        id: str,
        content: str,
        category: str = "general",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Initialize knowledge entry.

        Args:
            id: Unique identifier
            content: Knowledge content
            category: Category name
            tags: List of tags
            metadata: Additional metadata
        """
        self.id = id
        self.content = content
        self.category = category
        self.tags = tags or []
        self.metadata = metadata or {}
        self.created_at = self.metadata.get('created_at', datetime.now().isoformat())
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'content': self.content,
            'category': self.category,
            'tags': self.tags,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'KnowledgeEntry':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            content=data['content'],
            category=data.get('category', 'general'),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )


class KnowledgeBase:
    """
    Manages structured knowledge with semantic search.

    Features:
    - Add/update/delete knowledge entries
    - Tag and categorize knowledge
    - Semantic and keyword search
    - Export/import functionality
    """

    COLLECTION_NAME = "knowledge_base"

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService
    ):
        """
        Initialize knowledge base.

        Args:
            vector_store: Vector store instance
            embedding_service: Embedding service instance
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service

        # Ensure collection exists
        self.vector_store.get_or_create_collection(
            self.COLLECTION_NAME,
            metadata={'description': 'Alpha knowledge base'}
        )

        logger.info("Knowledge base initialized")

    def add(
        self,
        content: str,
        category: str = "general",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        id: Optional[str] = None
    ) -> str:
        """
        Add knowledge entry.

        Args:
            content: Knowledge content
            category: Category name
            tags: List of tags
            metadata: Additional metadata
            id: Optional custom ID

        Returns:
            Entry ID
        """
        # Generate ID if not provided
        if id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            id = f"kb_{timestamp}"

        # Create entry
        entry = KnowledgeEntry(
            id=id,
            content=content,
            category=category,
            tags=tags,
            metadata=metadata
        )

        # Prepare metadata for vector store
        vector_metadata = {
            'category': category,
            'tags': json.dumps(tags or []),
            'created_at': entry.created_at,
            'updated_at': entry.updated_at,
            'type': 'knowledge'
        }

        if metadata:
            vector_metadata.update({
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for k, v in metadata.items()
            })

        # Generate embedding and store
        try:
            self.vector_store.add(
                collection_name=self.COLLECTION_NAME,
                documents=[content],
                metadatas=[vector_metadata],
                ids=[id]
            )

            logger.info(f"Added knowledge entry: {id}")
            return id
        except Exception as e:
            logger.error(f"Failed to add knowledge entry: {e}")
            raise

    def update(
        self,
        id: str,
        content: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Update knowledge entry.

        Args:
            id: Entry ID
            content: New content
            category: New category
            tags: New tags
            metadata: New metadata
        """
        # Get existing entry
        existing = self.get(id)
        if not existing:
            raise ValueError(f"Knowledge entry not found: {id}")

        # Update fields
        new_content = content if content is not None else existing['content']
        new_category = category if category is not None else existing['category']
        new_tags = tags if tags is not None else json.loads(existing.get('tags', '[]'))

        # Merge metadata
        new_metadata = existing.copy()
        if metadata:
            new_metadata.update(metadata)

        new_metadata['updated_at'] = datetime.now().isoformat()
        new_metadata['category'] = new_category
        new_metadata['tags'] = json.dumps(new_tags)

        # Update in vector store
        try:
            self.vector_store.update(
                collection_name=self.COLLECTION_NAME,
                ids=[id],
                documents=[new_content] if content else None,
                metadatas=[new_metadata]
            )

            logger.info(f"Updated knowledge entry: {id}")
        except Exception as e:
            logger.error(f"Failed to update knowledge entry: {e}")
            raise

    def delete(self, id: str):
        """
        Delete knowledge entry.

        Args:
            id: Entry ID
        """
        try:
            self.vector_store.delete(
                collection_name=self.COLLECTION_NAME,
                ids=[id]
            )
            logger.info(f"Deleted knowledge entry: {id}")
        except Exception as e:
            logger.error(f"Failed to delete knowledge entry: {e}")
            raise

    def get(self, id: str) -> Optional[Dict]:
        """
        Get knowledge entry by ID.

        Args:
            id: Entry ID

        Returns:
            Entry data or None
        """
        try:
            result = self.vector_store.get(
                collection_name=self.COLLECTION_NAME,
                ids=[id],
                include=["documents", "metadatas"]
            )

            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'content': result['documents'][0],
                    **result['metadatas'][0]
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get knowledge entry: {e}")
            return None

    def search_semantic(
        self,
        query: str,
        n_results: int = 10,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Search knowledge using semantic similarity.

        Args:
            query: Search query
            n_results: Number of results
            category: Filter by category
            tags: Filter by tags

        Returns:
            List of matching entries
        """
        # Build metadata filter
        where = {'type': 'knowledge'}
        if category:
            where['category'] = category

        try:
            results = self.vector_store.query(
                collection_name=self.COLLECTION_NAME,
                query_texts=[query],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )

            # Format results
            entries = []
            if results['ids'] and results['ids'][0]:
                for i, entry_id in enumerate(results['ids'][0]):
                    entry = {
                        'id': entry_id,
                        'content': results['documents'][0][i],
                        'distance': results['distances'][0][i],
                        **results['metadatas'][0][i]
                    }

                    # Filter by tags if specified
                    if tags:
                        entry_tags = json.loads(entry.get('tags', '[]'))
                        if not any(tag in entry_tags for tag in tags):
                            continue

                    entries.append(entry)

            logger.info(f"Semantic search returned {len(entries)} results")
            return entries
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def search_by_category(
        self,
        category: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search knowledge by category.

        Args:
            category: Category name
            limit: Maximum results

        Returns:
            List of matching entries
        """
        try:
            results = self.vector_store.get(
                collection_name=self.COLLECTION_NAME,
                where={'category': category, 'type': 'knowledge'},
                limit=limit,
                include=["documents", "metadatas"]
            )

            entries = []
            if results['ids']:
                for i, entry_id in enumerate(results['ids']):
                    entries.append({
                        'id': entry_id,
                        'content': results['documents'][i],
                        **results['metadatas'][i]
                    })

            logger.info(f"Category search returned {len(entries)} results")
            return entries
        except Exception as e:
            logger.error(f"Category search failed: {e}")
            return []

    def search_by_tags(
        self,
        tags: List[str],
        match_all: bool = False,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search knowledge by tags.

        Args:
            tags: List of tags to search
            match_all: If True, match all tags; if False, match any tag
            limit: Maximum results

        Returns:
            List of matching entries
        """
        try:
            # Get all knowledge entries
            results = self.vector_store.get(
                collection_name=self.COLLECTION_NAME,
                where={'type': 'knowledge'},
                limit=limit,
                include=["documents", "metadatas"]
            )

            entries = []
            if results['ids']:
                for i, entry_id in enumerate(results['ids']):
                    entry_tags = json.loads(
                        results['metadatas'][i].get('tags', '[]')
                    )

                    # Check tag match
                    if match_all:
                        if all(tag in entry_tags for tag in tags):
                            entries.append({
                                'id': entry_id,
                                'content': results['documents'][i],
                                **results['metadatas'][i]
                            })
                    else:
                        if any(tag in entry_tags for tag in tags):
                            entries.append({
                                'id': entry_id,
                                'content': results['documents'][i],
                                **results['metadatas'][i]
                            })

            logger.info(f"Tag search returned {len(entries)} results")
            return entries
        except Exception as e:
            logger.error(f"Tag search failed: {e}")
            return []

    def list_categories(self) -> List[str]:
        """
        List all categories.

        Returns:
            List of category names
        """
        try:
            results = self.vector_store.get(
                collection_name=self.COLLECTION_NAME,
                where={'type': 'knowledge'},
                include=["metadatas"]
            )

            categories = set()
            if results['metadatas']:
                for metadata in results['metadatas']:
                    if 'category' in metadata:
                        categories.add(metadata['category'])

            return sorted(list(categories))
        except Exception as e:
            logger.error(f"Failed to list categories: {e}")
            return []

    def list_tags(self) -> List[str]:
        """
        List all tags.

        Returns:
            List of tag names
        """
        try:
            results = self.vector_store.get(
                collection_name=self.COLLECTION_NAME,
                where={'type': 'knowledge'},
                include=["metadatas"]
            )

            all_tags = set()
            if results['metadatas']:
                for metadata in results['metadatas']:
                    tags = json.loads(metadata.get('tags', '[]'))
                    all_tags.update(tags)

            return sorted(list(all_tags))
        except Exception as e:
            logger.error(f"Failed to list tags: {e}")
            return []

    def export_to_json(self, file_path: str):
        """
        Export knowledge base to JSON file.

        Args:
            file_path: Output file path
        """
        try:
            # Get all entries
            results = self.vector_store.get(
                collection_name=self.COLLECTION_NAME,
                where={'type': 'knowledge'},
                include=["documents", "metadatas"]
            )

            entries = []
            if results['ids']:
                for i, entry_id in enumerate(results['ids']):
                    entries.append({
                        'id': entry_id,
                        'content': results['documents'][i],
                        **results['metadatas'][i]
                    })

            # Write to file
            output_path = Path(file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported {len(entries)} entries to {file_path}")
        except Exception as e:
            logger.error(f"Failed to export knowledge base: {e}")
            raise

    def import_from_json(self, file_path: str):
        """
        Import knowledge base from JSON file.

        Args:
            file_path: Input file path
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                entries = json.load(f)

            count = 0
            for entry_data in entries:
                try:
                    self.add(
                        id=entry_data.get('id'),
                        content=entry_data['content'],
                        category=entry_data.get('category', 'general'),
                        tags=json.loads(entry_data.get('tags', '[]'))
                        if isinstance(entry_data.get('tags'), str)
                        else entry_data.get('tags'),
                        metadata={
                            k: v for k, v in entry_data.items()
                            if k not in ['id', 'content', 'category', 'tags']
                        }
                    )
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to import entry: {e}")

            logger.info(f"Imported {count} entries from {file_path}")
        except Exception as e:
            logger.error(f"Failed to import knowledge base: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get knowledge base statistics.

        Returns:
            Statistics dictionary
        """
        try:
            total = self.vector_store.count(self.COLLECTION_NAME)
            categories = self.list_categories()
            tags = self.list_tags()

            return {
                'total_entries': total,
                'categories': len(categories),
                'tags': len(tags),
                'category_list': categories,
                'tag_list': tags
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
