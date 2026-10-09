import customtkinter as ctk
from tkintermapview import TkinterMapView
from datetime import datetime, timezone
import sqlite3

from infrastructure.repos import EcoPointsRepo

ctk.set_appearance_mode('System')
ctk.set_default_color_theme('green')

class EcoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title('Информационная система мониторинга и категоризации сырья')
        self.geometry('1100x650')

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.repo = EcoPointsRepo()

        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row = 0, column = 0, sticky = 'nsew')
        self.sidebar.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text = "Навигатор пунктов", font = ctk.CTkFont(size=20, weight='bold'))
        self.logo_label.grid(row = 0, column = 0, padx=20, py=(20, 10))

        self.role_label = ctk.CTkLabel(self.sidebar, text='Вы вошли как: ', font=ctk.CTkFont(size=12))
        self.role_label.grid(row=1, column=0, padx=20, py=(10, 0), sticky="w")

        self.role_selector = ctk.CTkOptionMenu(
            self.sidebar, 
            values=['Физ.Лицо', 'Юр.Лицо', 'Владелец', 'Модератор'], 
            command= self.on_role_changed
        )
        self.role_selector.grid(row=2,  column=0, padx=20, py=(5, 10), sticky='ew')
        self.role_selector.set('Физ.Лицо')

        self.mod_panel = ctk.CTkFrame(self.sidebar, fg_color='transparent')

        self.map_widget = TkinterMapView(self, corner_radius=0)
        self.map_widget.grid(row=0, column=1, sticky="nsew")

        self.map_widget.set_position(53.9024, 27.5614)
        self.map_widget.set_zoom(12)

        self.map_markers = []

        self.load_points()

    def clear_all_panels(self):
        if hasattr(self, "bulk_order_btn"):
            self.bulk_order_btn.grid_forget()
        elif hasattr(self, 'owner_panel'):
            self.owner_panel.grid_forget()

    def on_role_changed(self, role):
        self.clear_all_panels()
        if role == 'Юр.Лицо':
            self.show_legal_entity_panel()
        elif role == 'Владелец':
            dialog = ctk.CTkInputDialog(text="Введите пароль Владельца:", title="Вход")
            if dialog.get_input() == "owner123":
                self.show_owner_panel()
            else:
                self.role_selector.set('Физ.Лицо')
        elif role == 'Модератор':
            dialog = ctk.CTkInputDialog(text="Введите пароль Модератора:", title="Вход")
            if dialog.get_input() == "admin123":
                self.show_mod_panel()
            else:
                self.role_selector.set('Физ.Лицо')


    def show_legal_entity_panel(self):
        self.bulk_order_btn = ctk.CTkButton(
            self.sidebar, 
            text='Оформить оптовый вывоз',
            command=self.on_bulk_order_click)
        self.bulk_order_btn.grid(row=3, column=0, padx=20, py=10, sticky='ew')

    def on_bulk_order_click(self):
        dialog = ctk.CTkDialog(text='Введите ID пункта для вывоза сырья:', title='Оптовый заказ')
        point_id = dialog.get_input()
        if point_id and point_id.isdigit():
            current_time = datetime.now(timezone.utc).isoformat()

            conn = sqlite3.connect('ecology.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO reviews (point_id, status, created_at) VALUES (?, 'works', ?)", (int(point_id), current_time))
            conn.commit()
            conn.close()
            self.load_points()

    def show_owner_panel(self):
        self.owner_panel = ctk.CTkFrame(self.sidebar, fg_color='transparent')
        self.owner_panel.grid(row=0, column=0, padx=20, py=10, sticky='ew')

        conn = sqlite3.connect('ecology.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reviews where status = 'broken_or_full'")
        row = cursor.fetchone()
        total_issues = row[0] if row else 0
        conn.close()

        self.analitics_label = ctk.CTkLabel(
            self.owner_panel,
            text=f"АНАЛИТИКА ИС:\n\nВсего сигналов\nо переполнении баков\nв Минске: {total_issues}",
            font=ctk.CTkFont(size=12,weight="bold"), 
            justify="left"
            )
        self.analitics_label.grid(row=3, column=0, padx=20, py=10, sticky='ew')


    def show_mod_panel(self):
        self.mod_panel.grid(row=3, column=0, padx=20, py=10, sticky='ew')
        self.map_widget.add_right_click_map_command(self.on_map_right_click)
        
        self.save_new_point = ctk.CTkButton(self.sidebar, text='Сохранить пункт', font=ctk.CTkFont(size=12))

    def on_map_right_click(self, coordinates = (latitude, longitude)):
        self.clicked_lat = coordinates[0]
        self.clicked_lng = coordinates[1]