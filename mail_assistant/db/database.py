import sqlite3
import sys
import os
from pathlib import Path


def get_base_path():
    """获取基础路径，支持打包后的环境"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def get_resource_path(relative_path):
    """获取资源文件路径"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后，资源在 _MEIPASS 或可执行文件同级的 db 目录
        base = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(sys.executable).parent
        return base / relative_path
    return Path(__file__).parent / relative_path


class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.db_path = get_base_path() / "data" / "mail_assistant.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._run_migrations()
    
    def _init_db(self):
        migrations_path = get_resource_path("migrations.sql")
        with open(migrations_path, 'r', encoding='utf-8') as f:
            migrations = f.read()
        
        conn = self.get_connection()
        conn.executescript(migrations)
        conn.commit()
        conn.close()
    
    def _run_migrations(self):
        """Run incremental migrations for schema changes."""
        conn = self.get_connection()
        try:
            # Migration 1: Add owner_name column to recipient_mappings if not exists
            cursor = conn.execute("PRAGMA table_info(recipient_mappings)")
            columns = [row['name'] for row in cursor.fetchall()]
            
            if 'owner_name' not in columns:
                # Need to recreate the table with the new schema
                # Step 1: Create new table
                conn.execute("""
                    CREATE TABLE recipient_mappings_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category_id INTEGER NOT NULL,
                        owner_name TEXT NOT NULL DEFAULT '',
                        recipient_id INTEGER NOT NULL,
                        UNIQUE(category_id, owner_name),
                        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
                        FOREIGN KEY (recipient_id) REFERENCES contacts(id) ON DELETE CASCADE
                    )
                """)
                
                # Step 2: Copy data (set owner_name to empty string for old records)
                conn.execute("""
                    INSERT INTO recipient_mappings_new (id, category_id, owner_name, recipient_id)
                    SELECT id, category_id, '', recipient_id FROM recipient_mappings
                """)
                
                # Step 3: Drop old table
                conn.execute("DROP TABLE recipient_mappings")
                
                # Step 4: Rename new table
                conn.execute("ALTER TABLE recipient_mappings_new RENAME TO recipient_mappings")
                
                conn.commit()
        finally:
            conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


db = Database()
