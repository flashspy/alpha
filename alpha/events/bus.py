"""
Alpha - Event Bus

Central event dispatcher for asynchronous event processing.
"""

import asyncio
import logging
from typing import Callable, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event type enumeration."""
    USER_INPUT = "user_input"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TOOL_EXECUTED = "tool_executed"
    SYSTEM_EVENT = "system_event"
    SCHEDULED_EVENT = "scheduled_event"


@dataclass
class Event:
    """Event data structure."""
    type: EventType
    data: Dict[str, Any]
    timestamp: datetime
    id: str = None

    def __post_init__(self):
        if self.id is None:
            self.id = f"{self.type.value}_{self.timestamp.timestamp()}"


class EventBus:
    """
    Central event bus for pub-sub pattern.

    Features:
    - Async event processing
    - Multiple handlers per event type
    - Event queuing
    - Error handling
    """

    def __init__(self):
        self.handlers: Dict[EventType, List[Callable]] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.processor_task = None

    async def initialize(self):
        """Start event processing."""
        self.running = True
        self.processor_task = asyncio.create_task(self._process_events())
        logger.info("Event bus initialized")

    async def _process_events(self):
        """Background task to process events from queue."""
        while self.running:
            try:
                # Wait for event with timeout to allow clean shutdown
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )
                await self._dispatch_event(event)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)

    async def _dispatch_event(self, event: Event):
        """Dispatch event to all registered handlers."""
        handlers = self.handlers.get(event.type, [])

        if not handlers:
            logger.debug(f"No handlers for event type: {event.type}")
            return

        logger.debug(f"Dispatching event {event.id} to {len(handlers)} handlers")

        # Execute all handlers concurrently
        tasks = [handler(event) for handler in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any handler errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Handler {handlers[i].__name__} failed for event {event.id}: {result}"
                )

    def subscribe(self, event_type: EventType, handler: Callable):
        """
        Subscribe a handler to an event type.

        Args:
            event_type: Type of event to listen for
            handler: Async callable that takes Event as parameter
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []

        self.handlers[event_type].append(handler)
        logger.debug(f"Subscribed {handler.__name__} to {event_type.value}")

    def unsubscribe(self, event_type: EventType, handler: Callable):
        """Unsubscribe a handler from an event type."""
        if event_type in self.handlers:
            self.handlers[event_type].remove(handler)
            logger.debug(f"Unsubscribed {handler.__name__} from {event_type.value}")

    async def publish(self, event: Event):
        """
        Publish an event to the bus.

        Args:
            event: Event to publish
        """
        await self.event_queue.put(event)
        logger.debug(f"Published event: {event.id}")

    async def publish_event(self, event_type: EventType, data: Dict[str, Any]):
        """
        Convenience method to create and publish an event.

        Args:
            event_type: Type of event
            data: Event data
        """
        event = Event(
            type=event_type,
            data=data,
            timestamp=datetime.now()
        )
        await self.publish(event)

    async def process_pending(self):
        """Process any pending events (called from main loop)."""
        # Events are processed by background task
        # This method can be used for additional processing if needed
        pass

    async def close(self):
        """Shutdown event bus."""
        logger.info("Closing event bus...")
        self.running = False

        if self.processor_task:
            await self.processor_task

        # Process remaining events
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                await self._dispatch_event(event)
            except asyncio.QueueEmpty:
                break

        logger.info("Event bus closed")
