"""
Database Layer
Centralized database operations with proper connection management
"""
import sqlite3
import logging
from contextlib import contextmanager
from typing import List, Dict, Optional
import config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations"""

    def __init__(self, db_path: str = None):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file. Defaults to config.DB_PATH
        """
        self.db_path = db_path or config.DB_PATH
        self.initialize_schema()

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections

        Yields:
            sqlite3.Connection: Database connection

        Example:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM matched_markets")
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def initialize_schema(self):
        """Create database schema if it doesn't exist"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS matched_markets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        polymarket_question TEXT NOT NULL,
                        kalshi_title TEXT NOT NULL,
                        polymarket_id TEXT NOT NULL,
                        kalshi_ticker TEXT NOT NULL,
                        similarity_score REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(polymarket_id, kalshi_ticker)
                    )
                """)

                # Create index for faster lookups
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_polymarket_id
                    ON matched_markets(polymarket_id)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_kalshi_ticker
                    ON matched_markets(kalshi_ticker)
                """)

                logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise

    def store_matches(self, matches: List[Dict]) -> int:
        """
        Store market matches in the database

        Args:
            matches: List of match dictionaries containing:
                - polymarket_question
                - kalshi_title
                - polymarket_id
                - kalshi_ticker
                - similarity_score (optional)

        Returns:
            int: Number of matches successfully stored
        """
        stored_count = 0

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                for match in matches:
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO matched_markets
                            (polymarket_question, kalshi_title, polymarket_id,
                             kalshi_ticker, similarity_score)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            match["polymarket_question"],
                            match["kalshi_title"],
                            match["polymarket_id"],
                            match["kalshi_ticker"],
                            match.get("similarity_score")
                        ))

                        if cursor.rowcount > 0:
                            stored_count += 1

                    except Exception as e:
                        logger.warning(f"Failed to store match: {e}")
                        continue

                logger.info(f"Stored {stored_count} new matched markets in database")

        except Exception as e:
            logger.error(f"Failed to store matches: {e}")
            raise

        return stored_count

    def get_all_matches(self) -> List[Dict]:
        """
        Retrieve all matched markets from database

        Returns:
            List[Dict]: List of matched markets with all fields
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, polymarket_question, kalshi_title,
                           polymarket_id, kalshi_ticker, similarity_score, created_at
                    FROM matched_markets
                    ORDER BY created_at DESC
                """)

                rows = cursor.fetchall()
                matches = []

                for row in rows:
                    matches.append({
                        "id": row["id"],
                        "polymarket_question": row["polymarket_question"],
                        "kalshi_title": row["kalshi_title"],
                        "polymarket_id": row["polymarket_id"],
                        "kalshi_ticker": row["kalshi_ticker"],
                        "similarity_score": row["similarity_score"],
                        "created_at": row["created_at"]
                    })

                logger.info(f"Retrieved {len(matches)} matched markets from database")
                return matches

        except Exception as e:
            logger.error(f"Failed to retrieve matches: {e}")
            raise

    def get_match_by_id(self, match_id: int) -> Optional[Dict]:
        """
        Retrieve a specific matched market by ID

        Args:
            match_id: The database ID of the match

        Returns:
            Dict or None: Match data or None if not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, polymarket_question, kalshi_title,
                           polymarket_id, kalshi_ticker, similarity_score, created_at
                    FROM matched_markets
                    WHERE id = ?
                """, (match_id,))

                row = cursor.fetchone()
                if row:
                    return {
                        "id": row["id"],
                        "polymarket_question": row["polymarket_question"],
                        "kalshi_title": row["kalshi_title"],
                        "polymarket_id": row["polymarket_id"],
                        "kalshi_ticker": row["kalshi_ticker"],
                        "similarity_score": row["similarity_score"],
                        "created_at": row["created_at"]
                    }
                return None

        except Exception as e:
            logger.error(f"Failed to retrieve match {match_id}: {e}")
            return None

    def delete_match(self, match_id: int) -> bool:
        """
        Delete a matched market by ID

        Args:
            match_id: The database ID of the match to delete

        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM matched_markets WHERE id = ?", (match_id,))
                deleted = cursor.rowcount > 0

                if deleted:
                    logger.info(f"Deleted match {match_id}")
                else:
                    logger.warning(f"Match {match_id} not found")

                return deleted

        except Exception as e:
            logger.error(f"Failed to delete match {match_id}: {e}")
            return False

    def clear_all_matches(self) -> int:
        """
        Clear all matched markets from database

        Returns:
            int: Number of matches deleted
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM matched_markets")
                count = cursor.rowcount
                logger.info(f"Cleared {count} matches from database")
                return count

        except Exception as e:
            logger.error(f"Failed to clear matches: {e}")
            raise

    def get_match_count(self) -> int:
        """
        Get the total number of matched markets

        Returns:
            int: Count of matched markets
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM matched_markets")
                row = cursor.fetchone()
                return row["count"]

        except Exception as e:
            logger.error(f"Failed to get match count: {e}")
            return 0
