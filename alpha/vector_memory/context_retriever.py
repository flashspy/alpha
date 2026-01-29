"""
Alpha - Context Retriever

Retrieves relevant context from conversations and knowledge for LLM prompts.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .vector_store import VectorStore
from .embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class ContextRetriever:
    """
    Retrieves relevant context for LLM prompts.

    Features:
    - Retrieve relevant past conversations
    - Get related knowledge entries
    - Prioritize recent and frequently accessed information
    - Manage context size to avoid token overflow
    - Store user preferences for long-term memory
    """

    CONVERSATION_COLLECTION = "conversations"
    PREFERENCES_COLLECTION = "user_preferences"

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        max_context_tokens: int = 4000
    ):
        """
        Initialize context retriever.

        Args:
            vector_store: Vector store instance
            embedding_service: Embedding service instance
            max_context_tokens: Maximum tokens for context
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.max_context_tokens = max_context_tokens

        # Ensure collections exist
        self.vector_store.get_or_create_collection(
            self.CONVERSATION_COLLECTION,
            metadata={'description': 'Conversation history'}
        )
        self.vector_store.get_or_create_collection(
            self.PREFERENCES_COLLECTION,
            metadata={'description': 'User preferences'}
        )

        logger.info("Context retriever initialized")

    def add_conversation(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Add conversation message to vector store.

        Args:
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Additional metadata

        Returns:
            Message ID
        """
        timestamp = datetime.now()
        message_id = f"msg_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"

        vector_metadata = {
            'role': role,
            'timestamp': timestamp.isoformat(),
            'type': 'conversation',
            'access_count': '0'
        }

        if metadata:
            vector_metadata.update({
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for k, v in metadata.items()
            })

        try:
            self.vector_store.add(
                collection_name=self.CONVERSATION_COLLECTION,
                documents=[content],
                metadatas=[vector_metadata],
                ids=[message_id]
            )

            logger.info(f"Added conversation message: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to add conversation: {e}")
            raise

    def retrieve_relevant_conversations(
        self,
        query: str,
        n_results: int = 5,
        time_window_days: Optional[int] = None,
        role_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve relevant past conversations.

        Args:
            query: Search query
            n_results: Number of results
            time_window_days: Limit to recent N days
            role_filter: Filter by role (user/assistant)

        Returns:
            List of relevant conversations
        """
        # Build metadata filter
        where = {'type': 'conversation'}
        if role_filter:
            where['role'] = role_filter

        try:
            results = self.vector_store.query(
                collection_name=self.CONVERSATION_COLLECTION,
                query_texts=[query],
                n_results=n_results * 2,  # Get more for filtering
                where=where,
                include=["documents", "metadatas", "distances"]
            )

            # Filter by time window if specified
            conversations = []
            if results['ids'] and results['ids'][0]:
                cutoff_time = None
                if time_window_days:
                    cutoff_time = (
                        datetime.now() - timedelta(days=time_window_days)
                    ).isoformat()

                for i, msg_id in enumerate(results['ids'][0]):
                    metadata = results['metadatas'][0][i]
                    timestamp = metadata.get('timestamp', '')

                    # Apply time filter
                    if cutoff_time and timestamp < cutoff_time:
                        continue

                    conversation = {
                        'id': msg_id,
                        'content': results['documents'][0][i],
                        'distance': results['distances'][0][i],
                        **metadata
                    }

                    conversations.append(conversation)

                    # Update access count
                    self._increment_access_count(msg_id, metadata)

                    if len(conversations) >= n_results:
                        break

            # Sort by timestamp (most recent first)
            conversations.sort(
                key=lambda x: x.get('timestamp', ''),
                reverse=True
            )

            logger.info(
                f"Retrieved {len(conversations)} relevant conversations"
            )
            return conversations
        except Exception as e:
            logger.error(f"Failed to retrieve conversations: {e}")
            return []

    def retrieve_recent_conversations(
        self,
        n_results: int = 10,
        role_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve recent conversations without semantic search.

        Args:
            n_results: Number of results
            role_filter: Filter by role

        Returns:
            List of recent conversations
        """
        where = {'type': 'conversation'}
        if role_filter:
            where['role'] = role_filter

        try:
            results = self.vector_store.get(
                collection_name=self.CONVERSATION_COLLECTION,
                where=where,
                limit=n_results * 2,
                include=["documents", "metadatas"]
            )

            conversations = []
            if results['ids']:
                for i, msg_id in enumerate(results['ids']):
                    conversations.append({
                        'id': msg_id,
                        'content': results['documents'][i],
                        **results['metadatas'][i]
                    })

            # Sort by timestamp
            conversations.sort(
                key=lambda x: x.get('timestamp', ''),
                reverse=True
            )

            return conversations[:n_results]
        except Exception as e:
            logger.error(f"Failed to retrieve recent conversations: {e}")
            return []

    def _increment_access_count(self, message_id: str, metadata: Dict):
        """
        Increment access count for a message.

        Args:
            message_id: Message ID
            metadata: Current metadata
        """
        try:
            access_count = int(metadata.get('access_count', 0)) + 1
            metadata['access_count'] = str(access_count)
            metadata['last_accessed'] = datetime.now().isoformat()

            self.vector_store.update(
                collection_name=self.CONVERSATION_COLLECTION,
                ids=[message_id],
                metadatas=[metadata]
            )
        except Exception as e:
            logger.warning(f"Failed to update access count: {e}")

    def build_context(
        self,
        query: str,
        include_conversations: bool = True,
        include_knowledge: bool = True,
        conversation_limit: int = 5,
        knowledge_limit: int = 3,
        knowledge_base=None
    ) -> str:
        """
        Build context string for LLM prompt.

        Args:
            query: Current query
            include_conversations: Include relevant conversations
            include_knowledge: Include relevant knowledge
            conversation_limit: Max conversations to include
            knowledge_limit: Max knowledge entries to include
            knowledge_base: KnowledgeBase instance (if available)

        Returns:
            Formatted context string
        """
        context_parts = []

        # Add relevant conversations
        if include_conversations:
            conversations = self.retrieve_relevant_conversations(
                query=query,
                n_results=conversation_limit,
                time_window_days=30  # Last 30 days
            )

            if conversations:
                context_parts.append("=== Relevant Past Conversations ===")
                for conv in conversations:
                    role = conv.get('role', 'unknown')
                    timestamp = conv.get('timestamp', '')[:10]  # Date only
                    content = conv.get('content', '')
                    context_parts.append(
                        f"[{timestamp}] {role}: {content}"
                    )
                context_parts.append("")

        # Add relevant knowledge
        if include_knowledge and knowledge_base:
            try:
                knowledge_entries = knowledge_base.search_semantic(
                    query=query,
                    n_results=knowledge_limit
                )

                if knowledge_entries:
                    context_parts.append("=== Relevant Knowledge ===")
                    for entry in knowledge_entries:
                        category = entry.get('category', 'general')
                        content = entry.get('content', '')
                        context_parts.append(f"[{category}] {content}")
                    context_parts.append("")
            except Exception as e:
                logger.warning(f"Failed to retrieve knowledge: {e}")

        # Add user preferences
        preferences = self.get_user_preferences()
        if preferences:
            context_parts.append("=== User Preferences ===")
            for key, value in preferences.items():
                context_parts.append(f"{key}: {value}")
            context_parts.append("")

        context = "\n".join(context_parts)

        # Truncate if too long (rough estimate: 4 chars per token)
        max_chars = self.max_context_tokens * 4
        if len(context) > max_chars:
            context = context[:max_chars] + "\n... (context truncated)"
            logger.warning("Context truncated to fit token limit")

        return context

    def set_user_preference(
        self,
        key: str,
        value: Any,
        category: str = "general"
    ):
        """
        Store user preference.

        Args:
            key: Preference key
            value: Preference value
            category: Category name
        """
        pref_id = f"pref_{key}"

        metadata = {
            'key': key,
            'value': json.dumps(value),
            'category': category,
            'type': 'preference',
            'updated_at': datetime.now().isoformat()
        }

        # Create searchable content
        content = f"{key}: {value}"

        try:
            # Check if preference exists
            existing = self.vector_store.get(
                collection_name=self.PREFERENCES_COLLECTION,
                ids=[pref_id]
            )

            if existing['ids']:
                # Update existing
                self.vector_store.update(
                    collection_name=self.PREFERENCES_COLLECTION,
                    ids=[pref_id],
                    documents=[content],
                    metadatas=[metadata]
                )
            else:
                # Add new
                self.vector_store.add(
                    collection_name=self.PREFERENCES_COLLECTION,
                    documents=[content],
                    metadatas=[metadata],
                    ids=[pref_id]
                )

            logger.info(f"Set user preference: {key} = {value}")
        except Exception as e:
            logger.error(f"Failed to set user preference: {e}")
            raise

    def get_user_preference(self, key: str) -> Optional[Any]:
        """
        Get user preference.

        Args:
            key: Preference key

        Returns:
            Preference value or None
        """
        pref_id = f"pref_{key}"

        try:
            result = self.vector_store.get(
                collection_name=self.PREFERENCES_COLLECTION,
                ids=[pref_id],
                include=["metadatas"]
            )

            if result['ids']:
                value_str = result['metadatas'][0].get('value')
                if value_str:
                    return json.loads(value_str)
            return None
        except Exception as e:
            logger.error(f"Failed to get user preference: {e}")
            return None

    def get_user_preferences(
        self,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all user preferences.

        Args:
            category: Filter by category

        Returns:
            Dictionary of preferences
        """
        where = {'type': 'preference'}
        if category:
            where['category'] = category

        try:
            results = self.vector_store.get(
                collection_name=self.PREFERENCES_COLLECTION,
                where=where,
                include=["metadatas"]
            )

            preferences = {}
            if results['metadatas']:
                for metadata in results['metadatas']:
                    key = metadata.get('key')
                    value_str = metadata.get('value')
                    if key and value_str:
                        try:
                            preferences[key] = json.loads(value_str)
                        except json.JSONDecodeError:
                            preferences[key] = value_str

            return preferences
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return {}

    def delete_user_preference(self, key: str):
        """
        Delete user preference.

        Args:
            key: Preference key
        """
        pref_id = f"pref_{key}"

        try:
            self.vector_store.delete(
                collection_name=self.PREFERENCES_COLLECTION,
                ids=[pref_id]
            )
            logger.info(f"Deleted user preference: {key}")
        except Exception as e:
            logger.error(f"Failed to delete user preference: {e}")
            raise

    def clear_old_conversations(self, days: int = 90):
        """
        Clear conversations older than specified days.

        Args:
            days: Number of days to keep
        """
        cutoff_time = (
            datetime.now() - timedelta(days=days)
        ).isoformat()

        try:
            # Get all conversations
            results = self.vector_store.get(
                collection_name=self.CONVERSATION_COLLECTION,
                where={'type': 'conversation'},
                include=["metadatas"]
            )

            ids_to_delete = []
            if results['ids']:
                for i, msg_id in enumerate(results['ids']):
                    timestamp = results['metadatas'][i].get('timestamp', '')
                    if timestamp < cutoff_time:
                        ids_to_delete.append(msg_id)

            if ids_to_delete:
                self.vector_store.delete(
                    collection_name=self.CONVERSATION_COLLECTION,
                    ids=ids_to_delete
                )
                logger.info(f"Cleared {len(ids_to_delete)} old conversations")
        except Exception as e:
            logger.error(f"Failed to clear old conversations: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get context retriever statistics.

        Returns:
            Statistics dictionary
        """
        try:
            conv_count = self.vector_store.count(self.CONVERSATION_COLLECTION)
            pref_count = self.vector_store.count(self.PREFERENCES_COLLECTION)

            return {
                'conversations': conv_count,
                'preferences': pref_count
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
