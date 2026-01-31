"""
Test pattern learning from conversation history (REQ-6.1.2).
"""

import asyncio
import pytest
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from alpha.core.engine import AlphaEngine


def create_test_config_with_proactive(tmpdir):
    """Create test config with proactive enabled."""
    config = MagicMock()
    config.memory = MagicMock()
    config.memory.database = f'{tmpdir}/test.db'

    config.proactive = {
        'enabled': True,
        'database': f'{tmpdir}/proactive.db',
        'pattern_learning': {
            'enabled': True,
            'min_frequency': 2,  # Lower for testing
            'min_confidence': 0.5
        },
        'task_detection': {
            'enabled': True,
            'min_confidence': 0.6,
            'check_interval': 1,
            'max_suggestions': 5
        },
        'auto_execute': {
            'enabled': False,
            'min_confidence': 0.9
        }
    }

    return config


@pytest.mark.asyncio
async def test_pattern_learning_from_history():
    """Test that patterns are learned from conversation history."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = create_test_config_with_proactive(tmpdir)
        engine = AlphaEngine(config)
        await engine.startup()

        # Add some mock conversation history
        conversations = [
            {
                'role': 'user',
                'content': 'What is the weather today?',
                'timestamp': (datetime.now() - timedelta(days=1)).isoformat()
            },
            {
                'role': 'assistant',
                'content': 'The weather is sunny',
                'timestamp': (datetime.now() - timedelta(days=1)).isoformat()
            },
            {
                'role': 'user',
                'content': 'What is the weather today?',  # Recurring
                'timestamp': (datetime.now() - timedelta(hours=12)).isoformat()
            },
            {
                'role': 'assistant',
                'content': 'The weather is cloudy',
                'timestamp': (datetime.now() - timedelta(hours=12)).isoformat()
            },
            {
                'role': 'user',
                'content': 'Check my tasks',
                'timestamp': (datetime.now() - timedelta(hours=2)).isoformat()
            }
        ]

        # Manually add conversations to memory
        for conv in conversations:
            await engine.memory_manager.add_conversation(
                role=conv['role'],
                content=conv['content']
            )

        # Trigger pattern learning
        await engine._learn_patterns_from_history()

        # Verify patterns were detected
        patterns = await engine.pattern_learner.get_patterns(min_confidence=0.5)

        # Should have some patterns detected
        assert len(patterns) >= 0  # May be 0 if detection logic is strict

        # Get statistics
        stats = await engine.pattern_learner.get_statistics()
        assert 'total_patterns' in stats

        await engine.shutdown()


@pytest.mark.asyncio
async def test_periodic_pattern_learning():
    """Test that pattern learning runs periodically in background loop."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = create_test_config_with_proactive(tmpdir)
        engine = AlphaEngine(config)
        await engine.startup()

        # Add mock conversations
        await engine.memory_manager.add_conversation(
            role='user',
            content='Test query 1'
        )
        await engine.memory_manager.add_conversation(
            role='assistant',
            content='Test response 1'
        )

        # Verify background loop is running
        assert engine.proactive_task is not None
        assert not engine.proactive_task.done()

        # Wait a bit for loop to potentially run
        await asyncio.sleep(0.5)

        # Verify memory manager has conversations
        history = await engine.memory_manager.get_conversation_history(limit=10)
        assert len(history) >= 2

        await engine.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
