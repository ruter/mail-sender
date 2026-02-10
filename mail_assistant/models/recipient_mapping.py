from dataclasses import dataclass
from typing import List, Optional
from db.database import db
from models.contact import Contact
from models.category import Category


@dataclass
class RecipientMapping:
    id: Optional[int]
    category: Category
    owner_name: str
    recipient: Contact
    cc_contacts: List[Contact]


class RecipientMappingRepository:
    @staticmethod
    def create(category_id: int, owner_name: str, recipient_id: int, cc_contact_ids: List[int]) -> RecipientMapping:
        conn = db.get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO recipient_mappings (category_id, owner_name, recipient_id) VALUES (?, ?, ?)",
                (category_id, owner_name, recipient_id)
            )
            mapping_id = cursor.lastrowid
            
            for cc_id in cc_contact_ids:
                conn.execute(
                    "INSERT INTO recipient_mapping_cc (mapping_id, contact_id) VALUES (?, ?)",
                    (mapping_id, cc_id)
                )
            conn.commit()
            
            return RecipientMappingRepository.get_by_id(mapping_id)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def update(mapping_id: int, category_id: int, owner_name: str, recipient_id: int, cc_contact_ids: List[int]) -> RecipientMapping:
        conn = db.get_connection()
        try:
            conn.execute(
                "UPDATE recipient_mappings SET category_id = ?, owner_name = ?, recipient_id = ? WHERE id = ?",
                (category_id, owner_name, recipient_id, mapping_id)
            )
            conn.execute("DELETE FROM recipient_mapping_cc WHERE mapping_id = ?", (mapping_id,))
            
            for cc_id in cc_contact_ids:
                conn.execute(
                    "INSERT INTO recipient_mapping_cc (mapping_id, contact_id) VALUES (?, ?)",
                    (mapping_id, cc_id)
                )
            conn.commit()
            
            return RecipientMappingRepository.get_by_id(mapping_id)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def delete(mapping_id: int) -> bool:
        conn = db.get_connection()
        try:
            cursor = conn.execute("DELETE FROM recipient_mappings WHERE id = ?", (mapping_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    @staticmethod
    def get_by_id(mapping_id: int) -> Optional[RecipientMapping]:
        conn = db.get_connection()
        try:
            cursor = conn.execute("""
                SELECT m.id, m.owner_name, cat.id as cat_id, cat.name as cat_name, cat.pattern as cat_pattern,
                       c.id as recipient_id, c.name as recipient_name, c.email as recipient_email
                FROM recipient_mappings m
                INNER JOIN categories cat ON m.category_id = cat.id
                INNER JOIN contacts c ON m.recipient_id = c.id
                WHERE m.id = ?
            """, (mapping_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            cc_cursor = conn.execute("""
                SELECT c.id, c.name, c.email
                FROM recipient_mapping_cc mc
                INNER JOIN contacts c ON mc.contact_id = c.id
                WHERE mc.mapping_id = ?
                ORDER BY c.name
            """, (mapping_id,))
            cc_contacts = [Contact(id=r['id'], name=r['name'], email=r['email']) for r in cc_cursor.fetchall()]
            
            return RecipientMapping(
                id=row['id'],
                category=Category(id=row['cat_id'], name=row['cat_name'], pattern=row['cat_pattern']),
                owner_name=row['owner_name'],
                recipient=Contact(id=row['recipient_id'], name=row['recipient_name'], email=row['recipient_email']),
                cc_contacts=cc_contacts
            )
        finally:
            conn.close()
    
    @staticmethod
    def get_by_category_and_owner(category_id: int, owner_name: str) -> Optional[RecipientMapping]:
        """Get mapping by category_id and owner_name for precise matching."""
        conn = db.get_connection()
        try:
            cursor = conn.execute("""
                SELECT m.id, m.owner_name, cat.id as cat_id, cat.name as cat_name, cat.pattern as cat_pattern,
                       c.id as recipient_id, c.name as recipient_name, c.email as recipient_email
                FROM recipient_mappings m
                INNER JOIN categories cat ON m.category_id = cat.id
                INNER JOIN contacts c ON m.recipient_id = c.id
                WHERE m.category_id = ? AND m.owner_name = ?
            """, (category_id, owner_name))
            row = cursor.fetchone()
            if not row:
                return None
            
            cc_cursor = conn.execute("""
                SELECT c.id, c.name, c.email
                FROM recipient_mapping_cc mc
                INNER JOIN contacts c ON mc.contact_id = c.id
                WHERE mc.mapping_id = ?
                ORDER BY c.name
            """, (row['id'],))
            cc_contacts = [Contact(id=r['id'], name=r['name'], email=r['email']) for r in cc_cursor.fetchall()]
            
            return RecipientMapping(
                id=row['id'],
                category=Category(id=row['cat_id'], name=row['cat_name'], pattern=row['cat_pattern']),
                owner_name=row['owner_name'],
                recipient=Contact(id=row['recipient_id'], name=row['recipient_name'], email=row['recipient_email']),
                cc_contacts=cc_contacts
            )
        finally:
            conn.close()
    
    @staticmethod
    def get_all_by_category(category_id: int) -> List[RecipientMapping]:
        """Get all mappings for a category (for listing/config purposes)."""
        conn = db.get_connection()
        try:
            cursor = conn.execute("""
                SELECT m.id, m.owner_name, cat.id as cat_id, cat.name as cat_name, cat.pattern as cat_pattern,
                       c.id as recipient_id, c.name as recipient_name, c.email as recipient_email
                FROM recipient_mappings m
                INNER JOIN categories cat ON m.category_id = cat.id
                INNER JOIN contacts c ON m.recipient_id = c.id
                WHERE m.category_id = ?
                ORDER BY m.owner_name
            """, (category_id,))
            mappings = []
            for row in cursor.fetchall():
                cc_cursor = conn.execute("""
                    SELECT c.id, c.name, c.email
                    FROM recipient_mapping_cc mc
                    INNER JOIN contacts c ON mc.contact_id = c.id
                    WHERE mc.mapping_id = ?
                    ORDER BY c.name
                """, (row['id'],))
                cc_contacts = [Contact(id=r['id'], name=r['name'], email=r['email']) for r in cc_cursor.fetchall()]
                
                mappings.append(RecipientMapping(
                    id=row['id'],
                    category=Category(id=row['cat_id'], name=row['cat_name'], pattern=row['cat_pattern']),
                    owner_name=row['owner_name'],
                    recipient=Contact(id=row['recipient_id'], name=row['recipient_name'], email=row['recipient_email']),
                    cc_contacts=cc_contacts
                ))
            return mappings
        finally:
            conn.close()
    
    @staticmethod
    def get_all() -> List[RecipientMapping]:
        conn = db.get_connection()
        try:
            cursor = conn.execute("""
                SELECT m.id, m.owner_name, cat.id as cat_id, cat.name as cat_name, cat.pattern as cat_pattern,
                       c.id as recipient_id, c.name as recipient_name, c.email as recipient_email
                FROM recipient_mappings m
                INNER JOIN categories cat ON m.category_id = cat.id
                INNER JOIN contacts c ON m.recipient_id = c.id
                ORDER BY cat.name, m.owner_name
            """)
            mappings = []
            for row in cursor.fetchall():
                cc_cursor = conn.execute("""
                    SELECT c.id, c.name, c.email
                    FROM recipient_mapping_cc mc
                    INNER JOIN contacts c ON mc.contact_id = c.id
                    WHERE mc.mapping_id = ?
                    ORDER BY c.name
                """, (row['id'],))
                cc_contacts = [Contact(id=r['id'], name=r['name'], email=r['email']) for r in cc_cursor.fetchall()]
                
                mappings.append(RecipientMapping(
                    id=row['id'],
                    category=Category(id=row['cat_id'], name=row['cat_name'], pattern=row['cat_pattern']),
                    owner_name=row['owner_name'],
                    recipient=Contact(id=row['recipient_id'], name=row['recipient_name'], email=row['recipient_email']),
                    cc_contacts=cc_contacts
                ))
            return mappings
        finally:
            conn.close()
