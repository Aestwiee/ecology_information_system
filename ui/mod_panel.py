import customtkinter as ctk
import sqlite3
import tkinter.messagebox as messagebox

class ModeratorPanel(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master, fg_color='transparent')
        self.app = app_instance

        # 1. Поля ввода метаданных
        self.name_entry = ctk.CTkEntry(self, placeholder_text='Название пункта:')
        self.name_entry.grid(row=0, column=0, padx=20, pady=5, sticky='ew')

        self.address_entry = ctk.CTkEntry(self, placeholder_text='Адрес (автозаполнение по ПКМ):')
        self.address_entry.grid(row=1, column=0, padx=20, pady=5, sticky='ew')

        self.wastes_entry = ctk.CTkEntry(self, placeholder_text='Категории сырья (PET-01,PAP-20):')
        self.wastes_entry.grid(row=2, column=0, padx=20, pady=5, sticky='ew')

        # 2. НОВЫЙ ВЫБОР ВЛАДЕЛЬЦА ПУНКТА [3.2]
        self.owner_label = ctk.CTkLabel(self, text="Владелец инфраструктуры:", font=ctk.CTkFont(size=11))
        self.owner_label.grid(row=3, column=0, padx=20, pady=(5, 0), sticky="w")

        self.owner_selector = ctk.CTkOptionMenu(
            self, 
            values=['БЕЛВТОРРЕСУРСЫ', 'ЭКОЛАЙН']
        )
        self.owner_selector.grid(row=4, column=0, padx=20, pady=5, sticky='ew') # py оставляем для внутренней геометрии виджета
        self.owner_selector.set('БЕЛВТОРРЕСУРСЫ')

        # 3. Кнопка сохранения
        self.save_btn = ctk.CTkButton(
            self, 
            text='Сохранить пункт', 
            font=ctk.CTkFont(size=12),
            command=self.save_new_point
        )
        self.save_btn.grid(row=5, column=0, padx=20, pady=10, sticky='ew')

    def save_new_point(self): 
        if self.app.clicked_lat is None or self.app.clicked_lng is None: 
            messagebox.showwarning("Внимание", "Сначала кликните ПРАВОЙ кнопкой мыши по карте Минска и выберите 'Добавить пункт сюда'!")
            return 
            
        name = self.name_entry.get() 
        address = self.address_entry.get() 
        wastes = self.wastes_entry.get() 
        owner = self.owner_selector.get() # Считываем выбранного из меню владельца! [3.2]
        
        conn = sqlite3.connect('ecology.db') 
        cursor = conn.cursor() 
        
        # Записываем в БД реального владельца, выбранного модератором [3.2]
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
