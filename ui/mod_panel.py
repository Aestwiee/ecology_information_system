import customtkinter as ctk
import sqlite3
import tkinter.messagebox as messagebox
from infrastructure.owners_repo import OwnersRepo
from ui.owner_add_dialog import AddOwnerDialog

class ModeratorPanel(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master, fg_color='transparent')
        self.app = app_instance
        self.owners_repo = OwnersRepo()

        # 1. Поля ввода метаданных (ТЕ САМЫЕ, КОТОРЫЕ ПОТЕРЯЛИСЬ)
        self.name_entry = ctk.CTkEntry(self, placeholder_text='Название пункта:')
        self.name_entry.grid(row=0, column=0, padx=20, pady=5, sticky='ew')

        self.address_entry = ctk.CTkEntry(self, placeholder_text='Адрес (автозаполнение по ПКМ):')
        self.address_entry.grid(row=1, column=0, padx=20, pady=5, sticky='ew')

        self.wastes_entry = ctk.CTkEntry(self, placeholder_text='Категории сырья (PET-01,PAP-20):')
        self.wastes_entry.grid(row=2, column=0, padx=20, pady=5, sticky='ew')

        # 2. Выбор владельца пункта
        self.owner_label = ctk.CTkLabel(self, text="Владелец инфраструктуры:", font=ctk.CTkFont(size=11))
        self.owner_label.grid(row=3, column=0, padx=20, pady=(5, 0), sticky="w")

        # Строка для селектора и кнопки "+"
        owners_row = ctk.CTkFrame(self, fg_color='transparent')
        owners_row.grid(row=4, column=0, padx=20, pady=5, sticky='ew')
        owners_row.grid_columnconfigure(0, weight=1)

        owners = self.owners_repo.get_all_active()
        
        self.owner_selector = ctk.CTkOptionMenu(owners_row, values=owners or ["—"])
        self.owner_selector.grid(row=0, column=0, sticky='ew')
        if owners:
            self.owner_selector.set(owners[0])

        self.add_owner_btn = ctk.CTkButton(
            owners_row, text="+", width=32,
            command=self._open_add_owner_dialog,
        )
        self.add_owner_btn.grid(row=0, column=1, padx=(5, 0))

        self.del_owner_btn = ctk.CTkButton(owners_row, text="-", width=32, fg_color="#8B0000", hover_color="#5C0000",
                command=self._delete_selected_owner,
        )
        self.del_owner_btn.grid(row=0, column=2, padx=(5, 0))

        # 3. Кнопка сохранения пункта
        self.save_btn = ctk.CTkButton(
            self, 
            text='Сохранить пункт', 
            font=ctk.CTkFont(size=12),
            command=self.save_new_point
        )
        self.save_btn.grid(row=5, column=0, padx=20, pady=10, sticky='ew')

    def _open_add_owner_dialog(self):
        AddOwnerDialog(self, self.owners_repo, on_created=self._refresh_owner_list)

    def _delete_selected_owner(self):
        owner_name = self.owner_selector.get()
        if not owner_name or owner_name == "—":
            messagebox.showwarning("Внимание", "Нет выбранного владельца для удаления.", parent=self)
            return

        # Проверяем, есть ли у него точки
        points_count = self.owners_repo.count_points_by_owner(owner_name)

        if points_count > 0:
            # Если точки есть, задаем сложный вопрос
            msg = (f"У владельца '{owner_name}' есть {points_count} пункт(ов) на карте.\n\n"
                   f"ВНИМАНИЕ: Если вы удалите владельца, все его пункты и отзывы о них БУДУТ УДАЛЕНЫ С КАРТЫ.\n\n"
                   f"Вы уверены, что хотите продолжить?")
            confirm = messagebox.askyesno("Подтверждение удаления", msg, icon="warning", parent=self)
            if not confirm:
                return
            # Вызываем удаление вместе с точками
            self.owners_repo.delete_owner(owner_name, delete_points=True)
        else:
            # Если точек нет, удаляем просто так
            confirm = messagebox.askyesno("Подтверждение", f"Удалить владельца '{owner_name}'?", parent=self)
            if not confirm:
                return
            self.owners_repo.delete_owner(owner_name, delete_points=False)

        # Обновляем список в интерфейсе
        messagebox.showinfo("Успех", f"Владелец '{owner_name}' успешно удален.", parent=self)
        
        owners = self.owners_repo.get_all_active()
        self.owner_selector.configure(values=owners if owners else ["—"])
        self.owner_selector.set(owners[0] if owners else "—")
        
        # Перезагружаем карту, чтобы удаленные точки исчезли
        self.app.load_points()

    def _refresh_owner_list(self, new_name: str):
        owners = self.owners_repo.get_all_active()
        self.owner_selector.configure(values=owners)
        self.owner_selector.set(new_name)

    def save_new_point(self): 
        if self.app.clicked_lat is None or self.app.clicked_lng is None: 
            messagebox.showwarning("Внимание", "Сначала кликните ПРАВОЙ кнопкой мыши по карте Минска и выберите 'Добавить пункт сюда'!")
            return 
            
        name = self.name_entry.get() 
        address = self.address_entry.get() 
        wastes = self.wastes_entry.get().upper()
        owner = self.owner_selector.get()
        
        # Проверка, чтобы не добавить точку с несуществующим/пустым владельцем
        if owner == "—" or not owner:
            messagebox.showwarning("Внимание", "Выберите владельца инфраструктуры!")
            return

        conn = sqlite3.connect('ecology.db') 
        cursor = conn.cursor() 
        cursor.execute(
            "INSERT INTO eco_points (name, address, latitude, longitude, wastes, owner_name) VALUES (?, ?, ?, ?, ?, ?)", 
            (name, address, self.app.clicked_lat, self.app.clicked_lng, wastes, owner)
        ) 
        conn.commit() 
        conn.close() 

        self.name_entry.delete(0, 'end') 
        self.address_entry.delete(0, 'end')
        self.wastes_entry.delete(0, 'end')

        self.app.clicked_lat = None
        self.app.clicked_lng = None

        messagebox.showinfo("Успех", f"Пункт '{name}' успешно добавлен на карту Минска!")
        self.app.load_points()