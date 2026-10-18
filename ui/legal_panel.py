import customtkinter as ctk
import sqlite3
from datetime import datetime, timezone
import tkinter.messagebox as messagebox

class LegalEntityPanel(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master, fg_color='transparent')
        self.app = app_instance
        
        # Информационный текст для водителя спецтехники
        self.info_label = ctk.CTkLabel(
            self, 
            text="РЕЖИМ СПЕЦТЕХНИКИ:\n\nКликните по маркеру\nпункта на карте,\nчтобы зафиксировать\nоптовый вывоз сырья.",
            font=ctk.CTkFont(size=12, weight="bold"),
            justify="left"
        )
        self.info_label.grid(row=0, column=0, padx=20, pady=10, sticky='ew')

    def execute_bulk_order(self, marker):
        """Метод вызывается главным окном, когда юр. лицо кликает по маркеру"""
        point_id = marker.data
        point_info = marker.info

        confirm = messagebox.askyesno(
            "Подтверждение вывоза сырья", 
            f"{point_info}\n\nНаправить спецтехнику и полностью очистить контейнеры на данном пункте?"
        )
        
        if confirm:
            conn = sqlite3.connect('ecology.db')
            cursor = conn.cursor()
            
            # ИСПРАВЛЕНИЕ ЦВЕТА: Стираем старые жалобы, так как бак теперь пуст
            cursor.execute("DELETE FROM reviews WHERE point_id = ?", (point_id,))
            
            # Фиксируем время уборки сырья
            cursor.execute(
                "INSERT INTO reviews (point_id, status, created_at) VALUES (?, 'works', ?)", 
                (point_id, datetime.now(timezone.utc).isoformat())
            )
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Успех", "Оптовый вывоз завершен. Контейнеры очищены, пункт переведен в зеленый статус!")
            
            # Через ссылку на главное окно обновляем маркеры на карте Минска
            self.app.load_points()
