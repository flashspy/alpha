"""
Alpha - Learning Store

Persistent storage for learning data using SQLite.
Stores patterns, improvements, metrics, and correlations.
"""

import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict


logger = logging.getLogger(__name__)


class LearningStore:
    """
    Unified database for learning system data.

    Tables:
    - patterns_detected: Patterns found in logs
    - improvements_applied: Applied improvements and their outcomes
    - success_metrics: Task success rates and performance metrics
    - correlations: Correlations between patterns and outcomes
    """

    def __init__(self, db_path: str = "data/learning.db"):
        """
        Initialize learning store.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Learning store initialized: {self.db_path}")

    def initialize(self):
        """Initialize database connection and create tables."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info(f"Learning database ready: {self.db_path}")

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns_detected (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT UNIQUE NOT NULL,
                pattern_type TEXT NOT NULL,
                description TEXT NOT NULL,
                occurrences INTEGER NOT NULL,
                impact_score REAL NOT NULL,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                examples TEXT,
                metadata TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)

        # Improvements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS improvements_applied (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                improvement_id TEXT UNIQUE NOT NULL,
                recommendation_title TEXT NOT NULL,
                action_type TEXT NOT NULL,
                changes TEXT NOT NULL,
                status TEXT NOT NULL,
                applied_at TIMESTAMP,
                rolled_back_at TIMESTAMP,
                error TEXT,
                metadata TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)

        # Success metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS success_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_type TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP NOT NULL
            )
        """)

        # Correlations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS correlations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                correlation_type TEXT NOT NULL,
                entity_a TEXT NOT NULL,
                entity_b TEXT NOT NULL,
                correlation_score REAL NOT NULL,
                sample_size INTEGER NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_type
            ON patterns_detected(pattern_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_impact
            ON patterns_detected(impact_score DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_improvements_status
            ON improvements_applied(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_improvements_applied_at
            ON improvements_applied(applied_at)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_type_name
            ON success_metrics(metric_type, metric_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_correlations_type
            ON correlations(correlation_type)
        """)

        self.conn.commit()

    async def store_pattern(self, pattern: Any) -> str:
        """
        Store a detected pattern.

        Args:
            pattern: LogPattern instance

        Returns:
            Pattern ID
        """
        cursor = self.conn.cursor()

        pattern_id = f"pat_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(pattern)}"
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO patterns_detected (
                pattern_id, pattern_type, description, occurrences,
                impact_score, first_seen, last_seen, examples, metadata,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern_id,
            pattern.pattern_type.value,
            pattern.description,
            pattern.occurrences,
            pattern.impact_score,
            pattern.first_seen.isoformat() if pattern.first_seen else None,
            pattern.last_seen.isoformat() if pattern.last_seen else None,
            json.dumps(pattern.examples),
            json.dumps(pattern.metadata),
            now,
            now
        ))

        self.conn.commit()
        logger.debug(f"Stored pattern: {pattern_id}")
        return pattern_id

    async def store_improvement(self, improvement: Any) -> str:
        """
        Store an applied improvement.

        Args:
            improvement: AppliedImprovement instance

        Returns:
            Improvement ID
        """
        cursor = self.conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO improvements_applied (
                improvement_id, recommendation_title, action_type,
                changes, status, applied_at, error, metadata,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            improvement.id,
            improvement.recommendation_title,
            improvement.action_type,
            json.dumps(improvement.changes),
            improvement.status.value,
            improvement.applied_at.isoformat() if improvement.applied_at else None,
            improvement.error,
            json.dumps(improvement.metadata),
            now,
            now
        ))

        self.conn.commit()
        logger.debug(f"Stored improvement: {improvement.id}")
        return improvement.id

    async def update_improvement_status(
        self,
        improvement_id: str,
        status: Any
    ):
        """
        Update improvement status.

        Args:
            improvement_id: Improvement ID
            status: New status
        """
        cursor = self.conn.cursor()

        updates = {
            "status": status.value,
            "updated_at": datetime.now().isoformat()
        }

        if status.value == "rolled_back":
            updates["rolled_back_at"] = datetime.now().isoformat()

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [improvement_id]

        cursor.execute(f"""
            UPDATE improvements_applied
            SET {set_clause}
            WHERE improvement_id = ?
        """, values)

        self.conn.commit()

    async def store_metric(
        self,
        metric_type: str,
        metric_name: str,
        value: float,
        period_start: datetime,
        period_end: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Store a success metric.

        Args:
            metric_type: Type of metric (e.g., "success_rate", "avg_duration")
            metric_name: Specific metric name
            value: Metric value
            period_start: Start of measurement period
            period_end: End of measurement period
            metadata: Optional additional data

        Returns:
            Metric ID
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO success_metrics (
                metric_type, metric_name, value,
                period_start, period_end, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            metric_type,
            metric_name,
            value,
            period_start.isoformat(),
            period_end.isoformat(),
            json.dumps(metadata or {}),
            datetime.now().isoformat()
        ))

        self.conn.commit()
        return cursor.lastrowid

    async def store_correlation(
        self,
        correlation_type: str,
        entity_a: str,
        entity_b: str,
        correlation_score: float,
        sample_size: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Store a correlation between entities.

        Args:
            correlation_type: Type of correlation
            entity_a: First entity
            entity_b: Second entity
            correlation_score: Correlation score (-1 to 1)
            sample_size: Number of samples
            metadata: Optional additional data

        Returns:
            Correlation ID
        """
        cursor = self.conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO correlations (
                correlation_type, entity_a, entity_b,
                correlation_score, sample_size, metadata,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            correlation_type,
            entity_a,
            entity_b,
            correlation_score,
            sample_size,
            json.dumps(metadata or {}),
            now,
            now
        ))

        self.conn.commit()
        return cursor.lastrowid

    def get_patterns(
        self,
        pattern_type: Optional[str] = None,
        min_impact: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query patterns from database.

        Args:
            pattern_type: Filter by pattern type
            min_impact: Minimum impact score
            limit: Maximum results

        Returns:
            List of pattern dictionaries
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM patterns_detected WHERE 1=1"
        params = []

        if pattern_type:
            query += " AND pattern_type = ?"
            params.append(pattern_type)

        if min_impact is not None:
            query += " AND impact_score >= ?"
            params.append(min_impact)

        query += " ORDER BY impact_score DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_improvements(
        self,
        status: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query improvements from database.

        Args:
            status: Filter by status
            action_type: Filter by action type
            limit: Maximum results

        Returns:
            List of improvement dictionaries
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM improvements_applied WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if action_type:
            query += " AND action_type = ?"
            params.append(action_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_metrics(
        self,
        metric_type: Optional[str] = None,
        metric_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query metrics from database.

        Args:
            metric_type: Filter by metric type
            metric_name: Filter by metric name
            start_date: Filter by period start
            end_date: Filter by period end
            limit: Maximum results

        Returns:
            List of metric dictionaries
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM success_metrics WHERE 1=1"
        params = []

        if metric_type:
            query += " AND metric_type = ?"
            params.append(metric_type)

        if metric_name:
            query += " AND metric_name = ?"
            params.append(metric_name)

        if start_date:
            query += " AND period_start >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND period_end <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_correlations(
        self,
        correlation_type: Optional[str] = None,
        min_score: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query correlations from database.

        Args:
            correlation_type: Filter by correlation type
            min_score: Minimum correlation score
            limit: Maximum results

        Returns:
            List of correlation dictionaries
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM correlations WHERE 1=1"
        params = []

        if correlation_type:
            query += " AND correlation_type = ?"
            params.append(correlation_type)

        if min_score is not None:
            query += " AND ABS(correlation_score) >= ?"
            params.append(abs(min_score))

        query += " ORDER BY ABS(correlation_score) DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get learning store statistics.

        Returns:
            Statistics dictionary
        """
        cursor = self.conn.cursor()

        # Pattern stats
        cursor.execute("SELECT COUNT(*) as count FROM patterns_detected")
        pattern_count = cursor.fetchone()["count"]

        cursor.execute("""
            SELECT pattern_type, COUNT(*) as count
            FROM patterns_detected
            GROUP BY pattern_type
        """)
        patterns_by_type = {row["pattern_type"]: row["count"] for row in cursor.fetchall()}

        # Improvement stats
        cursor.execute("SELECT COUNT(*) as count FROM improvements_applied")
        improvement_count = cursor.fetchone()["count"]

        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM improvements_applied
            GROUP BY status
        """)
        improvements_by_status = {row["status"]: row["count"] for row in cursor.fetchall()}

        # Metric stats
        cursor.execute("SELECT COUNT(*) as count FROM success_metrics")
        metric_count = cursor.fetchone()["count"]

        # Correlation stats
        cursor.execute("SELECT COUNT(*) as count FROM correlations")
        correlation_count = cursor.fetchone()["count"]

        return {
            "patterns": {
                "total": pattern_count,
                "by_type": patterns_by_type
            },
            "improvements": {
                "total": improvement_count,
                "by_status": improvements_by_status
            },
            "metrics": {
                "total": metric_count
            },
            "correlations": {
                "total": correlation_count
            }
        }

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert SQLite row to dictionary with JSON parsing."""
        data = dict(row)

        # Parse JSON fields
        for field in ["examples", "metadata", "changes"]:
            if field in data and data[field]:
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    data[field] = {}

        return data

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Learning store closed")

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
