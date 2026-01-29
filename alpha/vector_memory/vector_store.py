"""
Alpha - Vector Store

ChromaDB integration for vector storage and retrieval.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Manages vector storage using ChromaDB.

    Features:
    - Store and retrieve embeddings
    - Semantic similarity search
    - Collection management
    - Metadata filtering
    """

    def __init__(self, persist_directory: str, embedding_function=None):
        """
        Initialize vector store.

        Args:
            persist_directory: Directory for persistent storage
            embedding_function: Custom embedding function (optional)
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        self.embedding_function = embedding_function
        self.collections: Dict[str, chromadb.Collection] = {}

        logger.info(f"Vector store initialized: {self.persist_directory}")

    def get_or_create_collection(
        self,
        name: str,
        metadata: Optional[Dict] = None
    ) -> chromadb.Collection:
        """
        Get or create a collection.

        Args:
            name: Collection name
            metadata: Collection metadata

        Returns:
            ChromaDB collection
        """
        if name in self.collections:
            return self.collections[name]

        try:
            collection = self.client.get_or_create_collection(
                name=name,
                metadata=metadata or {},
                embedding_function=self.embedding_function
            )
            self.collections[name] = collection
            logger.info(f"Collection ready: {name}")
            return collection
        except Exception as e:
            logger.error(f"Failed to get/create collection {name}: {e}")
            raise

    def add(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None
    ):
        """
        Add documents to collection.

        Args:
            collection_name: Target collection
            documents: Document texts
            metadatas: Document metadata
            ids: Document IDs (auto-generated if not provided)
            embeddings: Pre-computed embeddings (optional)
        """
        collection = self.get_or_create_collection(collection_name)

        # Generate IDs if not provided
        if ids is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ids = [f"{timestamp}_{i}" for i in range(len(documents))]

        # Add timestamps to metadata
        if metadatas is None:
            metadatas = [{} for _ in documents]

        for metadata in metadatas:
            if 'timestamp' not in metadata:
                metadata['timestamp'] = datetime.now().isoformat()

        try:
            if embeddings:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            else:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )

            logger.info(f"Added {len(documents)} documents to {collection_name}")
        except Exception as e:
            logger.error(f"Failed to add documents to {collection_name}: {e}")
            raise

    def query(
        self,
        collection_name: str,
        query_texts: Optional[List[str]] = None,
        query_embeddings: Optional[List[List[float]]] = None,
        n_results: int = 10,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None,
        include: List[str] = None
    ) -> Dict:
        """
        Query collection for similar documents.

        Args:
            collection_name: Target collection
            query_texts: Query texts
            query_embeddings: Query embeddings
            n_results: Number of results to return
            where: Metadata filter
            where_document: Document content filter
            include: Fields to include in results

        Returns:
            Query results
        """
        collection = self.get_or_create_collection(collection_name)

        if include is None:
            include = ["documents", "metadatas", "distances"]

        try:
            results = collection.query(
                query_texts=query_texts,
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=include
            )

            logger.info(
                f"Query returned {len(results.get('ids', [[]])[0])} results "
                f"from {collection_name}"
            )
            return results
        except Exception as e:
            logger.error(f"Query failed on {collection_name}: {e}")
            raise

    def update(
        self,
        collection_name: str,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict]] = None,
        embeddings: Optional[List[List[float]]] = None
    ):
        """
        Update documents in collection.

        Args:
            collection_name: Target collection
            ids: Document IDs to update
            documents: New document texts
            metadatas: New metadata
            embeddings: New embeddings
        """
        collection = self.get_or_create_collection(collection_name)

        # Add update timestamp to metadata
        if metadatas:
            for metadata in metadatas:
                metadata['updated_at'] = datetime.now().isoformat()

        try:
            collection.update(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
            logger.info(f"Updated {len(ids)} documents in {collection_name}")
        except Exception as e:
            logger.error(f"Failed to update documents in {collection_name}: {e}")
            raise

    def delete(
        self,
        collection_name: str,
        ids: Optional[List[str]] = None,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ):
        """
        Delete documents from collection.

        Args:
            collection_name: Target collection
            ids: Document IDs to delete
            where: Metadata filter
            where_document: Document content filter
        """
        collection = self.get_or_create_collection(collection_name)

        try:
            collection.delete(
                ids=ids,
                where=where,
                where_document=where_document
            )
            logger.info(f"Deleted documents from {collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete documents from {collection_name}: {e}")
            raise

    def get(
        self,
        collection_name: str,
        ids: Optional[List[str]] = None,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include: List[str] = None
    ) -> Dict:
        """
        Get documents from collection.

        Args:
            collection_name: Target collection
            ids: Document IDs to retrieve
            where: Metadata filter
            where_document: Document content filter
            limit: Maximum number of results
            offset: Offset for pagination
            include: Fields to include

        Returns:
            Retrieved documents
        """
        collection = self.get_or_create_collection(collection_name)

        if include is None:
            include = ["documents", "metadatas"]

        try:
            results = collection.get(
                ids=ids,
                where=where,
                where_document=where_document,
                limit=limit,
                offset=offset,
                include=include
            )
            logger.info(f"Retrieved {len(results.get('ids', []))} documents from {collection_name}")
            return results
        except Exception as e:
            logger.error(f"Failed to get documents from {collection_name}: {e}")
            raise

    def count(self, collection_name: str) -> int:
        """
        Get document count in collection.

        Args:
            collection_name: Target collection

        Returns:
            Number of documents
        """
        collection = self.get_or_create_collection(collection_name)
        return collection.count()

    def list_collections(self) -> List[str]:
        """
        List all collections.

        Returns:
            List of collection names
        """
        collections = self.client.list_collections()
        return [col.name for col in collections]

    def delete_collection(self, collection_name: str):
        """
        Delete a collection.

        Args:
            collection_name: Collection to delete
        """
        try:
            self.client.delete_collection(name=collection_name)
            if collection_name in self.collections:
                del self.collections[collection_name]
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            raise

    def reset(self):
        """Reset all collections (WARNING: deletes all data)."""
        try:
            self.client.reset()
            self.collections.clear()
            logger.warning("Vector store reset - all data deleted")
        except Exception as e:
            logger.error(f"Failed to reset vector store: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get vector store statistics.

        Returns:
            Statistics dictionary
        """
        stats = {
            'collections': [],
            'total_documents': 0
        }

        for collection_name in self.list_collections():
            count = self.count(collection_name)
            stats['collections'].append({
                'name': collection_name,
                'count': count
            })
            stats['total_documents'] += count

        return stats
