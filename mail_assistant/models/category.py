import re
from dataclasses import dataclass
from typing import List, Optional
from db.database import db


@dataclass
class Category:
    id: Optional[int]
    name: str
    pattern: str
    subject_template: str = '{month}月绩效数据结果'
    body_template: str = '@{owner} 这是{month}月的绩效数据结果，请查收。'


class CategoryRepository:
    @staticmethod
    def create(name: str, pattern: str, subject_template: str = '', body_template: str = '') -> Category:
        try:
            re.compile(pattern)
        except re.error as e:
            raise ValueError(f"无效的正则表达式: {e}")
        
        # Use defaults if empty
        if not subject_template:
            subject_template = '{month}月绩效数据结果'
        if not body_template:
            body_template = '@{owner} 这是{month}月的绩效数据结果，请查收。'
        
        conn = db.get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO categories (name, pattern, subject_template, body_template) VALUES (?, ?, ?, ?)",
                (name, pattern, subject_template, body_template)
            )
            conn.commit()
            return Category(id=cursor.lastrowid, name=name, pattern=pattern,
                          subject_template=subject_template, body_template=body_template)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def update(category_id: int, name: str, pattern: str, subject_template: str = '', body_template: str = '') -> Category:
        try:
            re.compile(pattern)
        except re.error as e:
            raise ValueError(f"无效的正则表达式: {e}")
        
        # Use defaults if empty
        if not subject_template:
            subject_template = '{month}月绩效数据结果'
        if not body_template:
            body_template = '@{owner} 这是{month}月的绩效数据结果，请查收。'
        
        conn = db.get_connection()
        try:
            conn.execute(
                "UPDATE categories SET name = ?, pattern = ?, subject_template = ?, body_template = ? WHERE id = ?",
                (name, pattern, subject_template, body_template, category_id)
            )
            conn.commit()
            return Category(id=category_id, name=name, pattern=pattern,
                          subject_template=subject_template, body_template=body_template)
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
            cursor = conn.execute("SELECT id, name, pattern, subject_template, body_template FROM categories ORDER BY name")
            return [Category(
                id=row['id'], 
                name=row['name'], 
                pattern=row['pattern'],
                subject_template=row['subject_template'] if 'subject_template' in row.keys() else '{month}月绩效数据结果',
                body_template=row['body_template'] if 'body_template' in row.keys() else '@{owner} 这是{month}月的绩效数据结果，请查收。'
            ) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    @staticmethod
    def get_by_id(category_id: int) -> Optional[Category]:
        conn = db.get_connection()
        try:
            cursor = conn.execute(
                "SELECT id, name, pattern, subject_template, body_template FROM categories WHERE id = ?",
                (category_id,)
            )
            row = cursor.fetchone()
            if row:
                return Category(
                    id=row['id'], 
                    name=row['name'], 
                    pattern=row['pattern'],
                    subject_template=row['subject_template'] if 'subject_template' in row.keys() else '{month}月绩效数据结果',
                    body_template=row['body_template'] if 'body_template' in row.keys() else '@{owner} 这是{month}月的绩效数据结果，请查收。'
                )
            return None
        finally:
            conn.close()
    
    @staticmethod
    def get_by_name(name: str) -> Optional[Category]:
        conn = db.get_connection()
        try:
            cursor = conn.execute(
                "SELECT id, name, pattern, subject_template, body_template FROM categories WHERE name = ?",
                (name,)
            )
            row = cursor.fetchone()
            if row:
                return Category(
                    id=row['id'], 
                    name=row['name'], 
                    pattern=row['pattern'],
                    subject_template=row['subject_template'] if 'subject_template' in row.keys() else '{month}月绩效数据结果',
                    body_template=row['body_template'] if 'body_template' in row.keys() else '@{owner} 这是{month}月的绩效数据结果，请查收。'
                )
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
