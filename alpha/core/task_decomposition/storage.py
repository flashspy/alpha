"""
ProgressStorage - SQLite persistence for task decomposition progress (REQ-8.1.2)

Stores task execution sessions and progress snapshots in SQLite database.
Enables progress restoration after restarts and historical tracking.
"""

import json
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from alpha.core.task_decomposition.models import (
    ProgressSummary,
    TaskTree,
)

logger = logging.getLogger(__name__)


class ProgressStorage:
    """
    SQLite-based storage for task execution progress.

    Schema:
    - task_execution_sessions: Top-level session metadata
    - task_progress_snapshots: Point-in-time progress snapshots

    Responsibilities:
    - Create and manage task execution sessions
    - Save progress snapshots during execution
    - Load historical progress data
    - Support progress restoration
    """

    def __init__(self, db_path: str = "data/task_decomposition.db"):
        """
        Initialize storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_schema()

        logger.info(f"ProgressStorage initialized: {db_path}")

    def _init_schema(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Task execution sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_execution_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_request TEXT NOT NULL,
                    task_tree JSON NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    metadata JSON
                )
            """)

            # Task progress snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_progress_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    task_tree JSON NOT NULL,
                    progress_summary JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES task_execution_sessions(session_id)
                )
            """)

            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_status
                ON task_execution_sessions(status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_session
                ON task_progress_snapshots(session_id)
            """)

            conn.commit()

        logger.debug("Database schema initialized")

    def create_session(
        self,
        session_id: str,
        user_request: str,
        task_tree: TaskTree,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new task execution session.

        Args:
            session_id: Unique session identifier
            user_request: Original user request
            task_tree: Initial task tree
            metadata: Additional session metadata

        Returns:
            Session ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO task_execution_sessions
                (session_id, user_request, task_tree, status, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                user_request,
                json.dumps(task_tree.to_dict()),
                "pending",
                json.dumps(metadata or {})
            ))

            conn.commit()

        logger.info(f"Created session {session_id}")
        return session_id

    def start_session(self, session_id: str):
        """Mark session as started."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE task_execution_sessions
                SET status = ?, started_at = ?
                WHERE session_id = ?
            """, ("running", datetime.now().isoformat(), session_id))

            conn.commit()

        logger.info(f"Started session {session_id}")

    def complete_session(self, session_id: str, success: bool):
        """
        Mark session as completed.

        Args:
            session_id: Session identifier
            success: Whether execution succeeded
        """
        status = "completed" if success else "failed"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE task_execution_sessions
                SET status = ?, completed_at = ?
                WHERE session_id = ?
            """, (status, datetime.now().isoformat(), session_id))

            conn.commit()

        logger.info(f"Completed session {session_id}, success={success}")

    def save_snapshot(
        self,
        session_id: str,
        task_tree: TaskTree,
        summary: ProgressSummary
    ) -> str:
        """
        Save a progress snapshot.

        Args:
            session_id: Session identifier
            task_tree: Current task tree state
            summary: Progress summary

        Returns:
            Snapshot ID
        """
        snapshot_id = f"{session_id}_{uuid.uuid4().hex[:8]}"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO task_progress_snapshots
                (snapshot_id, session_id, task_tree, progress_summary)
                VALUES (?, ?, ?, ?)
            """, (
                snapshot_id,
                session_id,
                json.dumps(task_tree.to_dict()),
                json.dumps(summary.to_dict())
            ))

            conn.commit()

        logger.debug(f"Saved snapshot {snapshot_id} for session {session_id}")
        return snapshot_id

    def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a progress snapshot.

        Args:
            snapshot_id: Snapshot identifier

        Returns:
            Dict with task_tree, progress_summary, metadata
            None if snapshot not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT task_tree, progress_summary, created_at
                FROM task_progress_snapshots
                WHERE snapshot_id = ?
            """, (snapshot_id,))

            row = cursor.fetchone()
            if not row:
                logger.warning(f"Snapshot {snapshot_id} not found")
                return None

            task_tree_data = json.loads(row[0])
            summary_data = json.loads(row[1])
            created_at = row[2]

            return {
                "task_tree": TaskTree.from_dict(task_tree_data),
                "progress_summary": summary_data,
                "metadata": {
                    "created_at": created_at,
                    "snapshot_id": snapshot_id
                }
            }

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session data.

        Args:
            session_id: Session identifier

        Returns:
            Dict with session metadata, initial task_tree, and latest snapshot
            None if session not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get session data
            cursor.execute("""
                SELECT user_request, task_tree, status,
                       created_at, started_at, completed_at, metadata
                FROM task_execution_sessions
                WHERE session_id = ?
            """, (session_id,))

            row = cursor.fetchone()
            if not row:
                logger.warning(f"Session {session_id} not found")
                return None

            session_data = {
                "session_id": session_id,
                "user_request": row[0],
                "initial_task_tree": TaskTree.from_dict(json.loads(row[1])),
                "status": row[2],
                "created_at": row[3],
                "started_at": row[4],
                "completed_at": row[5],
                "metadata": json.loads(row[6]) if row[6] else {}
            }

            # Get latest snapshot
            cursor.execute("""
                SELECT snapshot_id, task_tree, progress_summary, created_at
                FROM task_progress_snapshots
                WHERE session_id = ?
                ORDER BY ROWID DESC
                LIMIT 1
            """, (session_id,))

            snapshot_row = cursor.fetchone()
            if snapshot_row:
                session_data["latest_snapshot"] = {
                    "snapshot_id": snapshot_row[0],
                    "task_tree": TaskTree.from_dict(json.loads(snapshot_row[1])),
                    "progress_summary": json.loads(snapshot_row[2]),
                    "created_at": snapshot_row[3]
                }

            return session_data

    def list_sessions(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List task execution sessions.

        Args:
            status: Filter by status (pending, running, completed, failed)
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of session metadata dicts
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = """
                SELECT session_id, user_request, status,
                       created_at, started_at, completed_at
                FROM task_execution_sessions
            """

            params = []
            if status:
                query += " WHERE status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)

            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "session_id": row[0],
                    "user_request": row[1],
                    "status": row[2],
                    "created_at": row[3],
                    "started_at": row[4],
                    "completed_at": row[5]
                })

            return sessions

    def list_snapshots(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List snapshots for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshot metadata dicts
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT snapshot_id, progress_summary, created_at
                FROM task_progress_snapshots
                WHERE session_id = ?
                ORDER BY ROWID DESC
                LIMIT ?
            """, (session_id, limit))

            snapshots = []
            for row in cursor.fetchall():
                summary = json.loads(row[1])
                snapshots.append({
                    "snapshot_id": row[0],
                    "overall_progress": summary.get("overall_progress", 0.0),
                    "completed_count": summary.get("completed_count", 0),
                    "created_at": row[2]
                })

            return snapshots

    def delete_session(self, session_id: str):
        """
        Delete a session and all its snapshots.

        Args:
            session_id: Session identifier
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Delete snapshots first (foreign key constraint)
            cursor.execute("""
                DELETE FROM task_progress_snapshots
                WHERE session_id = ?
            """, (session_id,))

            # Delete session
            cursor.execute("""
                DELETE FROM task_execution_sessions
                WHERE session_id = ?
            """, (session_id,))

            conn.commit()

        logger.info(f"Deleted session {session_id} and its snapshots")

    def cleanup_old_sessions(self, days: int = 30):
        """
        Delete sessions older than specified days.

        Args:
            days: Keep sessions created within this many days
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get old session IDs
            cursor.execute("""
                SELECT session_id FROM task_execution_sessions
                WHERE created_at < datetime(?, 'unixepoch')
            """, (cutoff_date,))

            old_sessions = [row[0] for row in cursor.fetchall()]

            # Delete snapshots
            for session_id in old_sessions:
                cursor.execute("""
                    DELETE FROM task_progress_snapshots
                    WHERE session_id = ?
                """, (session_id,))

            # Delete sessions
            cursor.execute("""
                DELETE FROM task_execution_sessions
                WHERE created_at < datetime(?, 'unixepoch')
            """, (cutoff_date,))

            conn.commit()

        logger.info(f"Cleaned up {len(old_sessions)} old sessions (>{days} days)")
