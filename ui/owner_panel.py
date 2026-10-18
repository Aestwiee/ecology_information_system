import customtkinter as ctk
import sqlite3

class OwnerAnalyticsPanel(ctk.CTkFrame):
    def __init__(self, master, owner_name):
        super().__init__(master, fg_color='transparent')
        
        conn = sqlite3.connect('ecology.db')
        cursor = conn.cursor()
        
    
        cursor.execute("SELECT COUNT(*) FROM eco_points WHERE owner_name = ?", (owner_name,))
        total_my_points = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(DISTINCT p.id) 
            FROM eco_points p
            JOIN reviews r ON p.id = r.point_id
            WHERE p.owner_name = ? AND r.id = (
                SELECT id FROM reviews 
                WHERE point_id = p.id 
                ORDER BY created_at DESC LIMIT 1
            ) AND r.status = 'broken_or_full'
        """, (owner_name,))
        
        active_issues = cursor.fetchone()[0]
        conn.close()

        self.title_label = ctk.CTkLabel(
            self,
            text=f"КОМПАНИЯ:\n{owner_name}\n",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1f538d",
            justify="left"
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(5, 0), sticky='ew')

        self.analitics_label = ctk.CTkLabel(
            self,
            text=f"Всего ваших объектов: {total_my_points}\n\nТребуют очистки: {active_issues}",
            font=ctk.CTkFont(size=12, weight="bold"), 
            justify="left"
        )
        self.analitics_label.grid(row=1, column=0, padx=20, pady=10, sticky='ew')
