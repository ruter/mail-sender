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
    
    def _init_db(self):
        migrations_path = get_resource_path("migrations.sql")
        with open(migrations_path, 'r', encoding='utf-8') as f:
            migrations = f.read()
        
        conn = self.get_connection()
        conn.executescript(migrations)
        conn.commit()
        conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


db = Database()
