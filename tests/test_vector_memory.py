"""
Tests for Vector Memory System

Covers all Phase 2 REQ-2.3 requirements:
- REQ-2.3.1: Semantic Search
- REQ-2.3.2: Knowledge Base Management
- REQ-2.3.3: Context-Aware Responses
- REQ-2.3.4: Long-Term Memory
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import json

from alpha.vector_memory import (
    VectorStore,
    EmbeddingService,
    KnowledgeBase,
    ContextRetriever
)
from alpha.vector_memory.embeddings import ChromaEmbeddingFunction


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def embedding_service():
    """Create embedding service with local provider for testing."""
    try:
        service = EmbeddingService(provider="local")
        return service
    except Exception as e:
        pytest.skip(f"Local embeddings not available: {e}")


@pytest.fixture
def vector_store(temp_dir, embedding_service):
    """Create vector store for testing."""
    embedding_function = ChromaEmbeddingFunction(embedding_service)
    store = VectorStore(
        persist_directory=temp_dir,
        embedding_function=embedding_function
    )
    return store


@pytest.fixture
def knowledge_base(vector_store, embedding_service):
    """Create knowledge base for testing."""
    kb = KnowledgeBase(
        vector_store=vector_store,
        embedding_service=embedding_service
    )
    return kb


@pytest.fixture
def context_retriever(vector_store, embedding_service):
    """Create context retriever for testing."""
    retriever = ContextRetriever(
        vector_store=vector_store,
        embedding_service=embedding_service,
        max_context_tokens=2000
    )
    return retriever


# REQ-2.3.1: Semantic Search Tests
class TestSemanticSearch:
    """Test semantic search capabilities."""

    def test_vector_store_creation(self, vector_store):
        """Test vector store can be created."""
        assert vector_store is not None
        assert vector_store.client is not None

    def test_add_and_query_documents(self, vector_store):
        """Test adding documents and querying them."""
        collection_name = "test_collection"

        # Add documents
        documents = [
            "Python is a programming language",
            "Java is also a programming language",
            "The weather is nice today",
            "Machine learning is a subset of artificial intelligence"
        ]

        vector_store.add(
            collection_name=collection_name,
            documents=documents,
            ids=[f"doc_{i}" for i in range(len(documents))]
        )

        # Query for similar documents
        results = vector_store.query(
            collection_name=collection_name,
            query_texts=["programming languages"],
            n_results=2
        )

        assert len(results['ids'][0]) == 2
        assert "Python" in results['documents'][0][0] or "Java" in results['documents'][0][0]

    def test_metadata_filtering(self, vector_store):
        """Test filtering by metadata."""
        collection_name = "test_metadata"

        documents = [
            "Document about Python",
            "Document about Java",
            "Document about weather"
        ]

        metadatas = [
            {"category": "programming"},
            {"category": "programming"},
            {"category": "weather"}
        ]

        vector_store.add(
            collection_name=collection_name,
            documents=documents,
            metadatas=metadatas,
            ids=[f"doc_{i}" for i in range(len(documents))]
        )

        # Query with metadata filter
        results = vector_store.query(
            collection_name=collection_name,
            query_texts=["programming"],
            n_results=10,
            where={"category": "programming"}
        )

        assert len(results['ids'][0]) == 2
        for metadata in results['metadatas'][0]:
            assert metadata['category'] == 'programming'

    def test_update_documents(self, vector_store):
        """Test updating documents."""
        collection_name = "test_update"

        # Add document
        vector_store.add(
            collection_name=collection_name,
            documents=["Original content"],
            ids=["doc_1"]
        )

        # Update document
        vector_store.update(
            collection_name=collection_name,
            ids=["doc_1"],
            documents=["Updated content"]
        )

        # Verify update
        results = vector_store.get(
            collection_name=collection_name,
            ids=["doc_1"]
        )

        assert results['documents'][0] == "Updated content"

    def test_delete_documents(self, vector_store):
        """Test deleting documents."""
        collection_name = "test_delete"

        # Add documents
        vector_store.add(
            collection_name=collection_name,
            documents=["Doc 1", "Doc 2"],
            ids=["doc_1", "doc_2"]
        )

        # Delete one document
        vector_store.delete(
            collection_name=collection_name,
            ids=["doc_1"]
        )

        # Verify deletion
        results = vector_store.get(
            collection_name=collection_name,
            ids=["doc_1", "doc_2"]
        )

        assert len(results['ids']) == 1
        assert results['ids'][0] == "doc_2"


# REQ-2.3.2: Knowledge Base Management Tests
class TestKnowledgeBaseManagement:
    """Test knowledge base management capabilities."""

    def test_add_knowledge(self, knowledge_base):
        """Test adding knowledge entries."""
        entry_id = knowledge_base.add(
            content="Python is a high-level programming language",
            category="programming",
            tags=["python", "programming"]
        )

        assert entry_id is not None
        assert entry_id.startswith("kb_")

    def test_get_knowledge(self, knowledge_base):
        """Test retrieving knowledge by ID."""
        entry_id = knowledge_base.add(
            content="Test content",
            category="test",
            tags=["test"]
        )

        entry = knowledge_base.get(entry_id)

        assert entry is not None
        assert entry['content'] == "Test content"
        assert entry['category'] == "test"

    def test_update_knowledge(self, knowledge_base):
        """Test updating knowledge entries."""
        entry_id = knowledge_base.add(
            content="Original content",
            category="test"
        )

        knowledge_base.update(
            id=entry_id,
            content="Updated content",
            category="updated"
        )

        entry = knowledge_base.get(entry_id)

        assert entry['content'] == "Updated content"
        assert entry['category'] == "updated"

    def test_delete_knowledge(self, knowledge_base):
        """Test deleting knowledge entries."""
        entry_id = knowledge_base.add(
            content="To be deleted",
            category="test"
        )

        knowledge_base.delete(entry_id)

        entry = knowledge_base.get(entry_id)
        assert entry is None

    def test_search_by_category(self, knowledge_base):
        """Test searching knowledge by category."""
        knowledge_base.add(
            content="Python content",
            category="programming",
            tags=["python"]
        )
        knowledge_base.add(
            content="Java content",
            category="programming",
            tags=["java"]
        )
        knowledge_base.add(
            content="Weather info",
            category="weather",
            tags=["weather"]
        )

        results = knowledge_base.search_by_category("programming")

        assert len(results) == 2
        for entry in results:
            assert entry['category'] == "programming"

    def test_search_by_tags(self, knowledge_base):
        """Test searching knowledge by tags."""
        knowledge_base.add(
            content="Python content",
            category="programming",
            tags=["python", "beginner"]
        )
        knowledge_base.add(
            content="Advanced Python",
            category="programming",
            tags=["python", "advanced"]
        )
        knowledge_base.add(
            content="Java content",
            category="programming",
            tags=["java", "beginner"]
        )

        results = knowledge_base.search_by_tags(["python"])

        assert len(results) == 2
        for entry in results:
            tags = json.loads(entry['tags'])
            assert "python" in tags

    def test_semantic_search(self, knowledge_base):
        """Test semantic search of knowledge."""
        knowledge_base.add(
            content="Python is great for machine learning",
            category="programming",
            tags=["python", "ml"]
        )
        knowledge_base.add(
            content="Java is used for enterprise applications",
            category="programming",
            tags=["java", "enterprise"]
        )

        results = knowledge_base.search_semantic(
            query="artificial intelligence programming",
            n_results=1
        )

        assert len(results) >= 1
        # Should prefer the ML-related content
        assert "machine learning" in results[0]['content'] or "Python" in results[0]['content']

    def test_list_categories(self, knowledge_base):
        """Test listing all categories."""
        knowledge_base.add(content="Content 1", category="cat1")
        knowledge_base.add(content="Content 2", category="cat2")
        knowledge_base.add(content="Content 3", category="cat1")

        categories = knowledge_base.list_categories()

        assert len(categories) == 2
        assert "cat1" in categories
        assert "cat2" in categories

    def test_list_tags(self, knowledge_base):
        """Test listing all tags."""
        knowledge_base.add(content="Content 1", tags=["tag1", "tag2"])
        knowledge_base.add(content="Content 2", tags=["tag2", "tag3"])

        tags = knowledge_base.list_tags()

        assert len(tags) == 3
        assert "tag1" in tags
        assert "tag2" in tags
        assert "tag3" in tags

    def test_export_import_json(self, knowledge_base, temp_dir):
        """Test exporting and importing knowledge base."""
        # Add some knowledge
        knowledge_base.add(
            content="Export test 1",
            category="test",
            tags=["export"]
        )
        knowledge_base.add(
            content="Export test 2",
            category="test",
            tags=["export"]
        )

        # Export
        export_path = Path(temp_dir) / "knowledge_export.json"
        knowledge_base.export_to_json(str(export_path))

        assert export_path.exists()

        # Create new knowledge base
        from alpha.vector_memory import VectorStore, EmbeddingService, KnowledgeBase
        from alpha.vector_memory.embeddings import ChromaEmbeddingFunction

        new_temp_dir = tempfile.mkdtemp()
        try:
            new_embedding_service = EmbeddingService(provider="local")
            new_embedding_function = ChromaEmbeddingFunction(new_embedding_service)
            new_vector_store = VectorStore(
                persist_directory=new_temp_dir,
                embedding_function=new_embedding_function
            )
            new_kb = KnowledgeBase(
                vector_store=new_vector_store,
                embedding_service=new_embedding_service
            )

            # Import
            new_kb.import_from_json(str(export_path))

            # Verify
            results = new_kb.search_by_tags(["export"])
            assert len(results) == 2
        finally:
            shutil.rmtree(new_temp_dir)

    def test_knowledge_stats(self, knowledge_base):
        """Test getting knowledge base statistics."""
        knowledge_base.add(content="Content 1", category="cat1", tags=["tag1"])
        knowledge_base.add(content="Content 2", category="cat2", tags=["tag2"])
        knowledge_base.add(content="Content 3", category="cat1", tags=["tag1", "tag3"])

        stats = knowledge_base.get_stats()

        assert stats['total_entries'] == 3
        assert stats['categories'] == 2
        assert stats['tags'] == 3


# REQ-2.3.3: Context-Aware Responses Tests
class TestContextAwareResponses:
    """Test context-aware response capabilities."""

    def test_add_conversation(self, context_retriever):
        """Test adding conversations."""
        msg_id = context_retriever.add_conversation(
            role="user",
            content="What is Python?",
            metadata={"topic": "programming"}
        )

        assert msg_id is not None
        assert msg_id.startswith("msg_")

    def test_retrieve_relevant_conversations(self, context_retriever):
        """Test retrieving relevant past conversations."""
        # Add conversations
        context_retriever.add_conversation(
            role="user",
            content="How do I learn Python?"
        )
        context_retriever.add_conversation(
            role="assistant",
            content="Start with basic syntax and data structures"
        )
        context_retriever.add_conversation(
            role="user",
            content="What is the weather today?"
        )

        # Retrieve relevant conversations
        results = context_retriever.retrieve_relevant_conversations(
            query="Python programming",
            n_results=2
        )

        assert len(results) >= 1
        # Should prefer Python-related conversations

    def test_retrieve_recent_conversations(self, context_retriever):
        """Test retrieving recent conversations."""
        # Add conversations
        for i in range(5):
            context_retriever.add_conversation(
                role="user",
                content=f"Message {i}"
            )

        results = context_retriever.retrieve_recent_conversations(n_results=3)

        assert len(results) <= 3

    def test_build_context(self, context_retriever, knowledge_base):
        """Test building context for LLM prompt."""
        # Add conversations
        context_retriever.add_conversation(
            role="user",
            content="Tell me about Python"
        )

        # Add knowledge
        knowledge_base.add(
            content="Python is a high-level programming language",
            category="programming"
        )

        # Build context
        context = context_retriever.build_context(
            query="Python programming",
            include_conversations=True,
            include_knowledge=True,
            knowledge_base=knowledge_base
        )

        assert context != ""
        assert "Python" in context or "programming" in context.lower()

    def test_context_token_limit(self, context_retriever):
        """Test context respects token limits."""
        # Add many conversations
        for i in range(100):
            context_retriever.add_conversation(
                role="user",
                content=f"Long message number {i} " * 100
            )

        context = context_retriever.build_context(
            query="test",
            include_conversations=True,
            include_knowledge=False
        )

        # Context should be truncated (max 2000 tokens * 4 chars = 8000 chars)
        assert len(context) <= 8000 + 100  # Allow some overhead


# REQ-2.3.4: Long-Term Memory Tests
class TestLongTermMemory:
    """Test long-term memory capabilities."""

    def test_set_user_preference(self, context_retriever):
        """Test setting user preferences."""
        context_retriever.set_user_preference(
            key="language",
            value="English",
            category="general"
        )

        context_retriever.set_user_preference(
            key="theme",
            value="dark",
            category="ui"
        )

    def test_get_user_preference(self, context_retriever):
        """Test getting user preferences."""
        context_retriever.set_user_preference(
            key="test_pref",
            value="test_value"
        )

        value = context_retriever.get_user_preference("test_pref")

        assert value == "test_value"

    def test_get_all_user_preferences(self, context_retriever):
        """Test getting all user preferences."""
        context_retriever.set_user_preference(key="pref1", value="value1")
        context_retriever.set_user_preference(key="pref2", value="value2")

        preferences = context_retriever.get_user_preferences()

        assert len(preferences) >= 2
        assert preferences['pref1'] == "value1"
        assert preferences['pref2'] == "value2"

    def test_update_user_preference(self, context_retriever):
        """Test updating user preferences."""
        context_retriever.set_user_preference(key="pref", value="old_value")
        context_retriever.set_user_preference(key="pref", value="new_value")

        value = context_retriever.get_user_preference("pref")

        assert value == "new_value"

    def test_delete_user_preference(self, context_retriever):
        """Test deleting user preferences."""
        context_retriever.set_user_preference(key="to_delete", value="value")
        context_retriever.delete_user_preference("to_delete")

        value = context_retriever.get_user_preference("to_delete")

        assert value is None

    def test_filter_preferences_by_category(self, context_retriever):
        """Test filtering preferences by category."""
        context_retriever.set_user_preference(
            key="pref1", value="value1", category="cat1"
        )
        context_retriever.set_user_preference(
            key="pref2", value="value2", category="cat2"
        )

        preferences = context_retriever.get_user_preferences(category="cat1")

        assert "pref1" in preferences
        assert "pref2" not in preferences

    def test_access_count_tracking(self, context_retriever):
        """Test that access counts are tracked."""
        msg_id = context_retriever.add_conversation(
            role="user",
            content="Test message"
        )

        # Retrieve the conversation multiple times
        for _ in range(3):
            context_retriever.retrieve_relevant_conversations(
                query="Test message",
                n_results=1
            )

        # Access count should be tracked (we can't directly verify without
        # accessing internal state, but this tests that the code runs)

    def test_clear_old_conversations(self, context_retriever):
        """Test clearing old conversations."""
        # Add conversation
        context_retriever.add_conversation(
            role="user",
            content="Old message"
        )

        # Clear conversations older than 0 days (should clear all)
        context_retriever.clear_old_conversations(days=0)

        # Note: This tests the method runs without error
        # In a real scenario, we'd need to mock timestamps to properly test

    def test_retriever_stats(self, context_retriever):
        """Test getting retriever statistics."""
        context_retriever.add_conversation(role="user", content="Message 1")
        context_retriever.set_user_preference(key="pref1", value="value1")

        stats = context_retriever.get_stats()

        assert 'conversations' in stats
        assert 'preferences' in stats
        assert stats['conversations'] >= 1
        assert stats['preferences'] >= 1


# Integration Tests
class TestVectorMemoryIntegration:
    """Integration tests for the complete vector memory system."""

    def test_end_to_end_workflow(self, vector_store, embedding_service):
        """Test complete workflow from adding to retrieving."""
        # Create components
        kb = KnowledgeBase(vector_store, embedding_service)
        retriever = ContextRetriever(vector_store, embedding_service)

        # Add knowledge
        kb.add(
            content="Python is excellent for data science",
            category="programming",
            tags=["python", "data-science"]
        )

        # Add conversations
        retriever.add_conversation(
            role="user",
            content="I want to learn data science"
        )
        retriever.add_conversation(
            role="assistant",
            content="Python is a great choice for data science"
        )

        # Set preferences
        retriever.set_user_preference("favorite_language", "Python")

        # Build context
        context = retriever.build_context(
            query="data science programming",
            include_conversations=True,
            include_knowledge=True,
            knowledge_base=kb
        )

        assert context != ""
        assert "data science" in context.lower() or "python" in context.lower()

    def test_vector_store_stats(self, vector_store):
        """Test vector store statistics."""
        vector_store.add(
            collection_name="test_col",
            documents=["Doc 1", "Doc 2"],
            ids=["doc1", "doc2"]
        )

        stats = vector_store.get_stats()

        assert stats['total_documents'] >= 2
        assert len(stats['collections']) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
