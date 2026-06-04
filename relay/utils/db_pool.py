# -*- coding: utf-8 -*-
"""
Database Connection Pooling Module

Provides efficient connection pooling for MySQL using DBUtils.
Implements the singleton pattern for centralized pool management.

Requires: pip install DBUtils
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DatabasePool:
    """
    Singleton database connection pool for MySQL.
    
    Manages a pool of reusable database connections to avoid
    connection creation overhead.
    
    Usage:
        pool = DatabasePool()
        conn = pool.get_connection()
        cursor = conn.cursor()
        try:
            # Use cursor
            pass
        finally:
            conn.close()  # Returns to pool
    """
    
    _instance: Optional['DatabasePool'] = None
    _pool = None
    _initialized = False
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize pool (called once due to singleton pattern)."""
        if self._initialized:
            return
        
        self._init_pool()
        self._initialized = True
    
    @classmethod
    def _init_pool(cls):
        """Initialize connection pool from configuration."""
        try:
            from DBUtils.PooledDB import PooledDB
            import MySQLdb
        except ImportError:
            logger.error(
                'DBUtils not installed. Install with: pip install DBUtils'
            )
            raise
        
        from relay.core.config import ConfigManager
        
        config = ConfigManager().config.database
        
        try:
            cls._pool = PooledDB(
                MySQLdb,
                maxconnections=20,      # Maximum pool size
                mincached=2,            # Minimum cached connections
                maxcached=5,            # Maximum cached connections
                maxshared=3,            # Maximum shared connections
                blocking=True,          # Block if pool exhausted
                host=config.host,
                user=config.user,
                passwd=config.password,
                db=config.database,
                port=config.port,
                charset='utf8',
                use_unicode=True
            )
            logger.info('Database connection pool initialized')
        except Exception as e:
            logger.error(f'Failed to initialize database pool: {e}')
            raise
    
    def get_connection(self):
        """
        Get a connection from the pool.
        
        Returns:
            Database connection
        
        Raises:
            RuntimeError: If pool not initialized
        """
        if self._pool is None:
            raise RuntimeError('Database pool not initialized')
        
        try:
            conn = self._pool.connection()
            logger.debug('Got connection from pool')
            return conn
        except Exception as e:
            logger.error(f'Failed to get pool connection: {e}')
            raise
    
    @classmethod
    def reset(cls):
        """Reset pool (useful for testing)."""
        cls._pool = None
        cls._initialized = False


# =============================================================================
# DATABASE QUERY UTILITIES (Issue #13: Prepared Statements)
# =============================================================================

class PreparedQueryExecutor:
    """Helper for executing parameterized SQL queries safely."""
    
    @staticmethod
    def select_count(conn, table_name: str, **conditions) -> int:
        """
        Execute parameterized COUNT query.
        
        Args:
            conn: Database connection
            table_name: Table name
            **conditions: WHERE clause as keyword arguments
        
        Returns:
            Row count
        
        Example:
            >>> count = PreparedQueryExecutor.select_count(
            ...     conn,
            ...     'users',
            ...     status='active',
            ...     role='admin'
            ... )
        """
        if not conditions:
            where_clause = ''
            params = []
        else:
            conditions_list = [f'{k}=%s' for k in conditions.keys()]
            where_clause = ' WHERE ' + ' AND '.join(conditions_list)
            params = list(conditions.values())
        
        query = f'SELECT COUNT(*) FROM {table_name}{where_clause}'
        
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            cursor.close()
    
    @staticmethod
    def select_one(conn, table_name: str, columns: str = '*', **conditions):
        """
        Execute parameterized SELECT query for single row.
        
        Args:
            conn: Database connection
            table_name: Table name
            columns: Columns to select (default: '*')
            **conditions: WHERE clause
        
        Returns:
            Row as tuple or None
        """
        if not conditions:
            where_clause = ''
            params = []
        else:
            conditions_list = [f'{k}=%s' for k in conditions.keys()]
            where_clause = ' WHERE ' + ' AND '.join(conditions_list)
            params = list(conditions.values())
        
        query = f'SELECT {columns} FROM {table_name}{where_clause} LIMIT 1'
        
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchone()
        finally:
            cursor.close()
    
    @staticmethod
    def insert(conn, table_name: str, **values) -> bool:
        """
        Execute parameterized INSERT query.
        
        Args:
            conn: Database connection
            table_name: Table name
            **values: Column-value pairs
        
        Returns:
            True if successful
        
        Example:
            >>> PreparedQueryExecutor.insert(
            ...     conn,
            ...     'users',
            ...     name='John',
            ...     email='john@example.com',
            ...     status='active'
            ... )
        """
        columns = ', '.join(values.keys())
        placeholders = ', '.join(['%s'] * len(values))
        query = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})'
        
        cursor = conn.cursor()
        try:
            cursor.execute(query, list(values.values()))
            conn.commit()
            logger.debug(f'Inserted row into {table_name}')
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f'Insert failed: {e}')
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def update(conn, table_name: str, values: dict, **conditions) -> bool:
        """
        Execute parameterized UPDATE query.
        
        Args:
            conn: Database connection
            table_name: Table name
            values: Column-value pairs to update
            **conditions: WHERE clause
        
        Returns:
            True if successful
        
        Example:
            >>> PreparedQueryExecutor.update(
            ...     conn,
            ...     'users',
            ...     {'status': 'inactive', 'updated_at': '2024-01-01'},
            ...     user_id=123
            ... )
        """
        if not values:
            logger.warning('No values provided for update')
            return False
        
        set_clause = ', '.join([f'{k}=%s' for k in values.keys()])
        params = list(values.values())
        
        if conditions:
            conditions_list = [f'{k}=%s' for k in conditions.keys()]
            where_clause = ' WHERE ' + ' AND '.join(conditions_list)
            params.extend(conditions.values())
        else:
            where_clause = ''
        
        query = f'UPDATE {table_name} SET {set_clause}{where_clause}'
        
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            logger.debug(f'Updated {cursor.rowcount} rows in {table_name}')
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f'Update failed: {e}')
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def upsert(conn, table_name: str, row_data: dict, 
               unique_keys: list) -> bool:
        """
        Insert or update row (INSERT ... ON DUPLICATE KEY UPDATE).
        
        This is more efficient than separate SELECT + INSERT/UPDATE.
        
        Args:
            conn: Database connection
            table_name: Table name
            row_data: All column-value pairs
            unique_keys: List of columns that form unique constraint
        
        Returns:
            True if successful
        
        Example:
            >>> PreparedQueryExecutor.upsert(
            ...     conn,
            ...     'device_stats',
            ...     {
            ...         'date': '2024-01-01',
            ...         'serial': 'ABC123',
            ...         'adb_lost': 1,
            ...         'adb_recovery': 1,
            ...         'total_run': 1,
            ...     },
            ...     unique_keys=['date', 'serial']
            ... )
        """
        columns = ', '.join(row_data.keys())
        placeholders = ', '.join(['%s'] * len(row_data))
        
        # UPDATE clause: set all non-key columns
        update_pairs = [
            f'{k}=VALUES({k})' for k in row_data.keys()
            if k not in unique_keys
        ]
        update_clause = ', '.join(update_pairs)
        
        query = f"""
        INSERT INTO {table_name} ({columns})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_clause}
        """
        
        cursor = conn.cursor()
        try:
            cursor.execute(query, list(row_data.values()))
            conn.commit()
            logger.debug(f'Upserted row in {table_name}')
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f'Upsert failed: {e}')
            return False
        finally:
            cursor.close()


__all__ = [
    'DatabasePool',
    'PreparedQueryExecutor',
]
