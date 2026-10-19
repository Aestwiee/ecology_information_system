import customtkinter as ctk
import tkinter
from tkintermapview import TkinterMapView
import tkinter.messagebox as messagebox
from infrastructure.owners_repo import OwnersRepo
from infrastructure.database import init_db
from infrastructure.repos import EcoPointsRepo
from infrastructure.map_controller import MapController
from ui.legal_panel import LegalEntityPanel
from ui.owner_panel import OwnerAnalyticsPanel
from ui.mod_panel import ModeratorPanel

ctk.set_appearance_mode('System')
ctk.set_default_color_theme('green')
init_db()

class EcoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('Информационная система мониторинга и категоризации сырья')
        self.geometry('1100x650')

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.repo = EcoPointsRepo()
        self.ctrl = MapController(self)

        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky='nsew')
        self.sidebar.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="Навигатор пунктов", font=ctk.CTkFont(size=20, weight='bold'))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.role_label = ctk.CTkLabel(self.sidebar, text='Вы вошли как: ', font=ctk.CTkFont(size=12))
        self.role_label.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")

        self.role_selector = ctk.CTkOptionMenu(
            self.sidebar, values=['Физ.Лицо', 'Юр.Лицо', 'Владелец', 'Модератор'], command=self.on_role_changed
        )
        self.role_selector.grid(row=2, column=0, padx=20, pady=(5, 10), sticky='ew')
        self.role_selector.set('Физ.Лицо')

        self.map_widget = TkinterMapView(self, corner_radius=0)
        self.map_widget.grid(row=0, column=1, sticky="nsew")
        self.map_widget.set_position(53.9024, 27.5614)
        self.map_widget.set_zoom(12)

        self.map_widget.add_right_click_menu_command(label="Добавить пункт сюда", command=self.ctrl.handle_right_click, pass_coords=True)
        self.map_widget.add_right_click_menu_command(label="Удалить пункт", command=self.ctrl.handle_delete, pass_coords=True)

        self.map_markers = []
        self.active_panel = None
        self.clicked_lat, self.clicked_lng = None, None
        self.load_points()
        self.owners_repo = OwnersRepo()

    def clear_active_panel(self):
        if self.active_panel is not None:
            self.active_panel.grid_forget()
            self.active_panel.destroy()
            self.active_panel = None

    def on_role_changed(self, role):
        self.clear_active_panel()
        if role == 'Юр.Лицо':
            self.active_panel = LegalEntityPanel(self.sidebar, self)
            self.active_panel.grid(row=3, column=0, padx=20, pady=10, sticky='ew')
        elif role == 'Владелец':
            dialog = ctk.CTkInputDialog(text="Введите персональный пароль Владельца:", title="Вход для бизнеса")
            password = dialog.get_input()
            owner_company = self.owners_repo.authenticate(password)
            if owner_company:
                self.active_panel = OwnerAnalyticsPanel(self.sidebar, owner_company)
                self.active_panel.grid(row=3, column=0, padx=20, pady=10, sticky='ew')
            else:
                self.role_selector.set('Физ.Лицо')
                messagebox.showerror("Ошибка", "Неверный пароль владельца инфраструктуры!")
        elif role == 'Модератор':
            dialog = ctk.CTkInputDialog(text="Введите пароль Модератора:", title="Вход")
            if dialog.get_input() == "admin123":
                self.active_panel = ModeratorPanel(self.sidebar, self)
                self.active_panel.grid(row=3, column=0, padx=20, pady=10, sticky='ew')
            else:
                self.role_selector.set('Физ.Лицо')

    def load_points(self):
        for marker in self.map_markers: marker.delete()
        self.map_markers.clear()
        try:
            waste_translator = {
                "PET-01": "Пластиковые бутылки (PET)",
                "HDPE-02": "Плотный пластик (флаконы, канистры)",
                "PAP-20": "Бумага и картон",
                "PAP-21": "Журналы и газеты",
                "GL-70": "Стекло (бутылки, банки)",
                "FE-40": "Металл (жестяные банки)",
                "AL-41": "Алюминий (банки от напитков)"
            }

            for point in self.repo.get_points():
                reliability = point.math_model()
                color = point.get_marker_color()
                
                human_wastes = []
                for code in point.wastes:
                    clean_code = code.strip()
                    human_name = waste_translator.get(clean_code, clean_code)
                    human_wastes.append(human_name)
                
                wastes_list_str = "\n   - " + "\n   - ".join(human_wastes)
                
                info_text = (
                    f"{point.name}\n"
                    f"Адрес: {point.address}\n"
                    f"Надежность пункта: {reliability}%\n"
                    f"Принимаемые категории сырья:{wastes_list_str}"
                )
                
                circle_icon = tkinter.PhotoImage(width=16, height=16)
                for x in range(16):
                    for y in range(16):
                        if (x - 8)**2 + (y - 8)**2 <= 36: circle_icon.put(color, (x, y))
                new_marker = self.map_widget.set_marker(point.latitude, point.longitude, text="", icon=circle_icon, command=self.ctrl.handle_marker_click)
                new_marker.data, new_marker.info = point.id, info_text
                self.map_markers.append(new_marker)
        except Exception as e: print(f"Ошибка: {e}")


if __name__ == "__main__":
    app = EcoApp()
    app.mainloop()
