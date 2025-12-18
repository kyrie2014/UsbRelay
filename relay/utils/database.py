# -*- coding: utf-8 -*-
"""
Database Management Module

Provides MySQL database operations for storing relay recovery statistics.
"""

try:
    import MySQLdb
except ImportError:
    try:
        import pymysql as MySQLdb
        MySQLdb.install_as_MySQLdb()
    except ImportError:
        raise ImportError(
            "No MySQL library found. Please install either "
            "'mysqlclient' or 'PyMySQL':\n"
            "  pip install mysqlclient\n"
            "or\n"
            "  pip install PyMySQL"
        )


class DatabaseManager:
    """
    MySQL database manager for relay recovery data.
    
    This class provides methods for creating tables, inserting data,
    updating records, and querying the relay recovery database.
    """
    
    def __init__(self, host, user, password, database, port=3306):
        """
        Initialize database connection.
        
        Args:
            host (str): Database server host
            user (str): Database username
            password (str): Database password
            database (str): Database name
            port (int): Database server port (default: 3306)
        """
        self.conn = MySQLdb.connect(
            host=host,
            user=user,
            passwd=password,
            db=database,
            port=port,
            charset='utf8'
        )
        self.cursor = self.conn.cursor()
    
    def get_row_count(self, table_name, condition='1=1'):
        """
        Get number of rows in table matching condition.
        
        Args:
            table_name (str): Table name
            condition (str): WHERE clause condition (default: '1=1' for all rows)
        
        Returns:
            int: Number of matching rows
        """
        query = f'SELECT COUNT(*) FROM {table_name} WHERE {condition};'
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def has_row(self, table_name, condition):
        """
        Check if table contains rows matching condition.
        
        Args:
            table_name (str): Table name
            condition (str): WHERE clause condition
        
        Returns:
            bool: True if matching rows exist
        """
        return self.get_row_count(table_name, condition) > 0
    
    def get_table_fields(self, table_name):
        """
        Get all column names of a table.
        
        Args:
            table_name (str): Table name
        
        Returns:
            list: List of column names
        """
        self.cursor.execute(f'SELECT * FROM {table_name} LIMIT 0;')
        return [column[0] for column in self.cursor.description]
    
    def table_exists(self, table_name):
        """
        Check if table exists in database.
        
        Args:
            table_name (str): Table name
        
        Returns:
            bool: True if table exists
        """
        query = f'SHOW TABLES LIKE "{table_name}"'
        self.cursor.execute(query)
        return bool(self.cursor.fetchall())
    
    def insert_row(self, table_name, values):
        """
        Insert a row into table.
        
        Args:
            table_name (str): Table name
            values (list): List of values to insert
        
        Returns:
            bool: True if successful
        """
        formatted_values = []
        for item in values:
            if isinstance(item, str):
                item = '"' + item.encode('utf8').decode('utf8') + '"'
            formatted_values.append(str(item))
        
        query = f'INSERT INTO {table_name} VALUES({",".join(formatted_values)});'
        
        try:
            self.cursor.execute(query)
            self.conn.commit()
            return True
        except Exception as err:
            print(f'Insert error: {err}')
            self.conn.rollback()
            return False
    
    def update_row(self, table_name, update_items, condition):
        """
        Update rows in table matching condition.
        
        Args:
            table_name (str): Table name
            update_items (str): SET clause (e.g., 'column1=value1, column2=value2')
            condition (str): WHERE clause condition
        
        Returns:
            bool: True if successful
        """
        query = f'UPDATE {table_name} SET {update_items} WHERE {condition};'
        
        try:
            self.cursor.execute(query)
            self.conn.commit()
            return True
        except Exception as err:
            print(f'Update error: {err}')
            self.conn.rollback()
            return False
    
    def delete_rows(self, table_name, condition=None):
        """
        Delete rows from table.
        
        Args:
            table_name (str): Table name
            condition (str): WHERE clause condition (None to delete all rows)
        
        Returns:
            bool: True if successful
        """
        query = f'DELETE FROM {table_name}'
        if condition:
            query += f' WHERE {condition}'
        query += ';'
        
        try:
            self.cursor.execute(query)
            self.conn.commit()
            return True
        except Exception as err:
            print(f'Delete error: {err}')
            self.conn.rollback()
            return False
    
    def query_table(self, table_name, columns='*', condition=None, order_by=None):
        """
        Query data from table.
        
        Args:
            table_name (str): Table name
            columns (str): Columns to select (default: '*')
            condition (str): WHERE clause condition
            order_by (str): ORDER BY clause
        
        Returns:
            list: List of result tuples
        """
        query = f'SELECT {columns} FROM {table_name}'
        
        if condition:
            query += f' WHERE {condition}'
        
        if order_by:
            query += f' ORDER BY {order_by}'
        
        self.cursor.execute(query)
        return list(self.cursor.fetchall())
    
    def create_table(self, table_name, columns):
        """
        Create a new table.
        
        Args:
            table_name (str): Table name
            columns (list): List of column definitions
        
        Returns:
            bool: True if successful
        """
        if not columns:
            print('Error: Column list is empty')
            return False
        
        query = f'CREATE TABLE IF NOT EXISTS {table_name} ({",".join(columns)})'
        
        try:
            self.cursor.execute(query)
            self.conn.commit()
            return True
        except Exception as err:
            print(f'Create table error: {err}')
            self.conn.rollback()
            return False
    
    def drop_table(self, table_name):
        """
        Drop a table from database.
        
        Args:
            table_name (str): Table name
        
        Returns:
            bool: True if successful
        """
        try:
            query = f'DROP TABLE {table_name}'
            self.cursor.execute(query)
            self.conn.commit()
            return True
        except Exception as err:
            print(f'Drop table error: {err}')
            self.conn.rollback()
            return False
    
    def close(self):
        """Close database connection."""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def __del__(self):
        """Cleanup on object destruction."""
        self.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

