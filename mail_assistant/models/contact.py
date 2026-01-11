import re
from dataclasses import dataclass
from typing import Optional, List
from db.database import db


@dataclass
class Contact:
    id: Optional[int]
    name: str
    email: str


class ContactRepository:
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    @staticmethod
    def validate_email(email: str) -> bool:
        return bool(ContactRepository.EMAIL_REGEX.match(email))
    
    @staticmethod
    def create(name: str, email: str) -> Contact:
        if not ContactRepository.validate_email(email):
            raise ValueError(f"无效的邮箱格式: {email}")
        
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO contacts (name, email) VALUES (?, ?)",
                (name, email)
            )
            conn.commit()
            return Contact(id=cursor.lastrowid, name=name, email=email)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def update(contact_id: int, name: str, email: str) -> Contact:
        if not ContactRepository.validate_email(email):
            raise ValueError(f"无效的邮箱格式: {email}")
        
        conn = db.get_connection()
        try:
            conn.execute(
                "UPDATE contacts SET name = ?, email = ? WHERE id = ?",
                (name, email, contact_id)
            )
            conn.commit()
            return Contact(id=contact_id, name=name, email=email)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def delete(contact_id: int) -> bool:
        conn = db.get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM contacts WHERE id = ?",
                (contact_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    @staticmethod
    def get_all() -> List[Contact]:
        conn = db.get_connection()
        try:
            cursor = conn.execute("SELECT id, name, email FROM contacts ORDER BY name")
            return [Contact(id=row['id'], name=row['name'], email=row['email']) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    @staticmethod
    def get_by_name(name: str) -> Optional[Contact]:
        conn = db.get_connection()
        try:
            cursor = conn.execute(
                "SELECT id, name, email FROM contacts WHERE name = ?",
                (name,)
            )
            row = cursor.fetchone()
            if row:
                return Contact(id=row['id'], name=row['name'], email=row['email'])
            return None
        finally:
            conn.close()
    
    @staticmethod
    def get_by_id(contact_id: int) -> Optional[Contact]:
        conn = db.get_connection()
        try:
            cursor = conn.execute(
                "SELECT id, name, email FROM contacts WHERE id = ?",
                (contact_id,)
            )
            row = cursor.fetchone()
            if row:
                return Contact(id=row['id'], name=row['name'], email=row['email'])
            return None
        finally:
            conn.close()
