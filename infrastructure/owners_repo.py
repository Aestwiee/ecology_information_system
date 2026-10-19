import sqlite3
import hashlib
import os
import customtkinter as ctk

def _hash(password: str, salt: bytes = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 200_000)
    return salt.hex() + "$" + digest.hex()

def _verify(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$")
        salt = bytes.fromhex(salt_hex)
        expected = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 200_000).hex()
        return expected == digest_hex
    except Exception:
        return False

class OwnersRepo:
    def get_all_active(self):
        conn = sqlite3.connect('ecology.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT name FROM owners WHERE is_active = 1 ORDER BY name")
        rows = cur.fetchall()
        conn.close()
        return [r['name'] for r in rows]

    def exists(self, name: str) -> bool:
        conn = sqlite3.connect('ecology.db')
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM owners WHERE name = ?", (name,))
        found = cur.fetchone() is not None
        conn.close()
        return found

    def add(self, name: str, password: str):
        conn = sqlite3.connect('ecology.db')
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO owners (name, password) VALUES (?, ?)",
            (name, password),
        )
        conn.commit()
        conn.close()

    def authenticate(self, password: str):
        """Возвращает имя владельца или None."""
        conn = sqlite3.connect('ecology.db')
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM owners WHERE password = ? AND is_active = 1",
            (password,),
        )
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None

    def count_points_by_owner(self, owner_name: str) -> int:
        """Считает, сколько пунктов привязано к владельцу."""
        conn = sqlite3.connect('ecology.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM eco_points WHERE owner_name = ?", (owner_name,))
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def delete_owner(self, owner_name: str, delete_points: bool = False):
        """Удаляет владельца. Если delete_points=True, удаляет и его точки."""
        conn = sqlite3.connect('ecology.db')
        cursor = conn.cursor()
        
        if delete_points:
            cursor.execute("""
                DELETE FROM reviews 
                WHERE point_id IN (SELECT id FROM eco_points WHERE owner_name = ?)
            """, (owner_name,))
            cursor.execute("DELETE FROM eco_points WHERE owner_name = ?", (owner_name,))

        cursor.execute("DELETE FROM owners WHERE name = ?", (owner_name,))
        
        conn.commit()
        conn.close()