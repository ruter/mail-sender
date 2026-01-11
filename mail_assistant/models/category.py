import re
from dataclasses import dataclass
from typing import List, Optional
from db.database import db


@dataclass
class Category:
    id: Optional[int]
    name: str
    pattern: str


class CategoryRepository:
    @staticmethod
    def create(name: str, pattern: str) -> Category:
        try:
            re.compile(pattern)
        except re.error as e:
            raise ValueError(f"无效的正则表达式: {e}")
        
        conn = db.get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO categories (name, pattern) VALUES (?, ?)",
                (name, pattern)
            )
            conn.commit()
            return Category(id=cursor.lastrowid, name=name, pattern=pattern)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def update(category_id: int, name: str, pattern: str) -> Category:
        try:
            re.compile(pattern)
        except re.error as e:
            raise ValueError(f"无效的正则表达式: {e}")
        
        conn = db.get_connection()
        try:
            conn.execute(
                "UPDATE categories SET name = ?, pattern = ? WHERE id = ?",
                (name, pattern, category_id)
            )
            conn.commit()
            return Category(id=category_id, name=name, pattern=pattern)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def delete(category_id: int) -> bool:
        conn = db.get_connection()
        try:
            cursor = conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    @staticmethod
    def get_all() -> List[Category]:
        conn = db.get_connection()
        try:
            cursor = conn.execute("SELECT id, name, pattern FROM categories ORDER BY name")
            return [Category(id=row['id'], name=row['name'], pattern=row['pattern']) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    @staticmethod
    def get_by_id(category_id: int) -> Optional[Category]:
        conn = db.get_connection()
        try:
            cursor = conn.execute(
                "SELECT id, name, pattern FROM categories WHERE id = ?",
                (category_id,)
            )
            row = cursor.fetchone()
            if row:
                return Category(id=row['id'], name=row['name'], pattern=row['pattern'])
            return None
        finally:
            conn.close()
    
    @staticmethod
    def get_by_name(name: str) -> Optional[Category]:
        conn = db.get_connection()
        try:
            cursor = conn.execute(
                "SELECT id, name, pattern FROM categories WHERE name = ?",
                (name,)
            )
            row = cursor.fetchone()
            if row:
                return Category(id=row['id'], name=row['name'], pattern=row['pattern'])
            return None
        finally:
            conn.close()
    
    @staticmethod
    def match_filename(filename: str) -> Optional[Category]:
        categories = CategoryRepository.get_all()
        for category in categories:
            try:
                if re.match(category.pattern, filename):
                    return category
            except re.error:
                continue
        return None
