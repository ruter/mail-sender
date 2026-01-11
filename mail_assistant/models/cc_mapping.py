from dataclasses import dataclass
from typing import List, Optional
from db.database import db
from models.contact import Contact


@dataclass
class CCMapping:
    id: Optional[int]
    owner_name: str
    contact_id: int


class CCMappingRepository:
    @staticmethod
    def set_cc_contacts(owner_name: str, contact_ids: List[int]) -> None:
        conn = db.get_connection()
        try:
            conn.execute("DELETE FROM cc_mappings WHERE owner_name = ?", (owner_name,))
            for contact_id in contact_ids:
                conn.execute(
                    "INSERT INTO cc_mappings (owner_name, contact_id) VALUES (?, ?)",
                    (owner_name, contact_id)
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_cc_contacts(owner_name: str) -> List[Contact]:
        conn = db.get_connection()
        try:
            cursor = conn.execute("""
                SELECT c.id, c.name, c.email 
                FROM contacts c
                INNER JOIN cc_mappings m ON c.id = m.contact_id
                WHERE m.owner_name = ?
                ORDER BY c.name
            """, (owner_name,))
            return [Contact(id=row['id'], name=row['name'], email=row['email']) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    @staticmethod
    def get_cc_contact_ids(owner_name: str) -> List[int]:
        conn = db.get_connection()
        try:
            cursor = conn.execute(
                "SELECT contact_id FROM cc_mappings WHERE owner_name = ?",
                (owner_name,)
            )
            return [row['contact_id'] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    @staticmethod
    def get_all_owners() -> List[str]:
        conn = db.get_connection()
        try:
            cursor = conn.execute(
                "SELECT DISTINCT owner_name FROM cc_mappings ORDER BY owner_name"
            )
            return [row['owner_name'] for row in cursor.fetchall()]
        finally:
            conn.close()
