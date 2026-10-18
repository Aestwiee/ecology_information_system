import customtkinter as ctk
import tkinter  # Добавь к остальным импортам
from geopy.geocoders import Nominatim
from tkintermapview import TkinterMapView
from PIL import Image as PILImage
from datetime import datetime, timezone
import sqlite3
import tkinter.messagebox as messagebox  # Красивые всплывающие окна предупреждений

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
        self.sidebar.grid_rowconfigure(7, weight=1) # Пружина для прижатия нижних элементов

        self.logo_label = ctk.CTkLabel(self.sidebar, text = "Навигатор пунктов", font = ctk.CTkFont(size=20, weight='bold'))
        self.logo_label.grid(row = 0, column = 0, padx=20, pady=(20, 10))

        self.role_label = ctk.CTkLabel(self.sidebar, text='Вы вошли как: ', font=ctk.CTkFont(size=12))
        self.role_label.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")

        self.role_selector = ctk.CTkOptionMenu(
            self.sidebar, 
            values=['Физ.Лицо', 'Юр.Лицо', 'Владелец', 'Модератор'], 
            command= self.on_role_changed
        )
        self.role_selector.grid(row=2,  column=0, padx=20, pady=(5, 10), sticky='ew')
        self.role_selector.set('Физ.Лицо')

        self.map_widget = TkinterMapView(self, corner_radius=0)
        self.map_widget.grid(row=0, column=1, sticky="nsew")

        self.map_widget.set_position(53.9024, 27.5614)
        self.map_widget.set_zoom(12)

        self.map_widget.add_right_click_menu_command(
            label="Добавить пункт сюда",
            command=self.on_map_right_click,
            pass_coords=True
        )
        self.map_widget.add_right_click_menu_command(
            label="Удалить пункт",
            command=self.delete_point_from_db,
            pass_coords=True
        )

        self.map_markers = []
        self.clicked_lat = None
        self.clicked_lng = None

        self.load_points()

    def clear_all_panels(self):
        if hasattr(self, "bulk_order_btn"):
            self.bulk_order_btn.grid_forget()
        if hasattr(self, 'owner_panel'):
            self.owner_panel.grid_forget()
            
        if hasattr(self, "name_entry"):
            self.name_entry.grid_forget()
        if hasattr(self, "address_entry"):
            self.address_entry.grid_forget()
        if hasattr(self, "wastes_entry"):
            self.wastes_entry.grid_forget()
        if hasattr(self, "save_btn"):
            self.save_btn.grid_forget()

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
        self.bulk_order_btn.grid(row=3, column=0, padx=20, pady=10, sticky='ew')

    def on_bulk_order_click(self):
        dialog = ctk.CTkInputDialog(text='Введите ID пункта для вывоза сырья:', title='Оптовый заказ')
        point_id = dialog.get_input()
        if point_id and point_id.isdigit():
            current_time = datetime.now(timezone.utc).isoformat()

            conn = sqlite3.connect('ecology.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO reviews (point_id, status, created_at) VALUES (?, 'works', ?)", (int(point_id), current_time))
            conn.commit()
            conn.close()
            messagebox.showinfo("Успех", f"Пункт №{point_id} успешно обслужен. Баки очищены!")
            self.load_points()

    def show_owner_panel(self):
        self.owner_panel = ctk.CTkFrame(self.sidebar, fg_color='transparent')
        self.owner_panel.grid(row=3, column=0, padx=20, pady=10, sticky='ew')

        conn = sqlite3.connect('ecology.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reviews where status = 'broken_or_full'")
        row = cursor.fetchone()
        total_issues = row[0] if row else 0
        conn.close()

        self.analitics_label = ctk.CTkLabel(
            self.owner_panel,
            text=f"АНАЛИТИКА ИС:\n\nВсего сигналов\nо переполнении баков\nв Минске: {total_issues}",
            font=ctk.CTkFont(size=12, weight="bold"), 
            justify="left"
            )
        self.analitics_label.grid(row=0, column=0, padx=20, pady=10, sticky='ew')

    def show_mod_panel(self):
        self.clear_all_panels()

        self.name_entry = ctk.CTkEntry(self.sidebar, placeholder_text='Название пункта:')
        self.name_entry.grid(row=3, column=0, padx=20, pady=5, sticky='ew')

        self.address_entry = ctk.CTkEntry(self.sidebar, placeholder_text='Адрес (автозаполнение по ПКМ):')
        self.address_entry.grid(row=4, column=0, padx=20, pady=5, sticky='ew')

        self.wastes_entry = ctk.CTkEntry(self.sidebar, placeholder_text='Категории сырья (PET-01,PAP-20):')
        self.wastes_entry.grid(row=5, column=0, padx=20, pady=5, sticky='ew')

        self.save_btn = ctk.CTkButton(
            self.sidebar, 
            text='Сохранить пункт', 
            font=ctk.CTkFont(size=12),
            command=self.save_new_point
        )
        self.save_btn.grid(row=6, column=0, padx=20, pady=10, sticky='ew')

        self.clicked_lat = None
        self.clicked_lng = None

    def on_map_right_click(self, coordinates):
        if self.role_selector.get() != "Модератор":
            messagebox.showwarning("Доступ ограничен", "Добавление новых пунктов сырья доступно только в режиме Модератора!")
            return
        self.clicked_lat = coordinates[0]
        self.clicked_lng = coordinates[1]
        
        try:
            geolocator = Nominatim(user_agent="ecology_navigator_app_v2")
            location = geolocator.reverse((self.clicked_lat, self.clicked_lng), language="ru")
            
            if location and location.raw and "address" in location.raw:
                address_data = location.raw["address"]
                
                street = address_data.get("road", address_data.get("suburb", address_data.get("pedestrian", "")))
                house = address_data.get("house_number", "")
                
                if street:
                    detected_address = f"{street}, {house}".strip(", ")
                else:
                    detected_address = location.address.split(", Минск")[0]
            else:
                detected_address = f"{round(self.clicked_lat, 4)}, {round(self.clicked_lng, 4)}"
                
        except Exception as e:
            print(f"Ошибка геокодирования geopy: {e}")
            detected_address = f"{round(self.clicked_lat, 4)}, {round(self.clicked_lng, 4)}"
        
        if hasattr(self, "address_entry"):
            self.address_entry.delete(0, 'end')
            self.address_entry.insert(0, detected_address)



    def save_new_point(self): 
        if self.clicked_lat is None or self.clicked_lng is None: 
            messagebox.showwarning("Внимание", "Сначала кликните ПРАВОЙ кнопкой мыши по карте Минска и выберите 'Добавить пункт сюда'!")
            return 
            
        name = self.name_entry.get() 
        address = self.address_entry.get() 
        wastes = self.wastes_entry.get() 
        
        conn = sqlite3.connect('ecology.db') 
        cursor = conn.cursor() 
        cursor.execute("INSERT INTO eco_points (name, address, latitude, longitude, wastes) VALUES (?, ?, ?, ? ,?)", 
                    (name, address, self.clicked_lat, self.clicked_lng, wastes)) 
        conn.commit() 
        conn.close() 

        self.name_entry.delete(0, 'end') 
        self.address_entry.delete(0, 'end')
        self.wastes_entry.delete(0, 'end')

        self.clicked_lat = None
        self.clicked_lng = None

        messagebox.showinfo("Успех", f"Пункт '{name}' успешно добавлен на карту Минска!")
        self.load_points()

    def delete_point_from_db(self, coordinates):
        if self.role_selector.get() != "Модератор":
            messagebox.showwarning("Доступ ограничен", "Удаление пунктов инфраструктуры доступно только в режиме Модератора!")
            return

        target_lat, target_lng = coordinates[0], coordinates[1]
        target_id = None
        target_name = "выбранный пункт"
        for marker in self.map_markers:
            if abs(marker.position[0] - target_lat) < 0.005 and abs(marker.position[1] - target_lng) < 0.005:
                target_id = marker.data
                target_name = marker.info.split("\n")[0]
                break

        if target_id is not None:
            confirm = messagebox.askyesno(
                "Подтверждение удаления", 
                f"Вы уверены, что хотите полностью демонтировать и удалить из ИС {target_name}?"
            )
            
            if confirm:
                conn = sqlite3.connect('ecology.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM reviews WHERE point_id = ?", (int(target_id),))
                cursor.execute("DELETE FROM eco_points WHERE id = ?", (int(target_id),))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Удаление", "Пункт успешно и бесследно удален из базы данных.")
                self.load_points()
        else:
            messagebox.showwarning("Ошибка", "Не удалось точно определить пункт для удаления. Кликните прямо по кружку маркера!")

    def load_points(self):
        for marker in self.map_markers:
            marker.delete()
        self.map_markers.clear()

        try:
            points = self.repo.get_points()

            for point in points:
                reliability = point.math_model()
                color = point.get_marker_color()
                categories = ", ".join(point.wastes)
            
                info_text = f"ID: {point.id} | {point.name}\nАдрес: {point.address}\nНадежность: {reliability}%\nПринимает: {categories}"

                circle_icon = tkinter.PhotoImage(width=16, height=16)
                
                for x in range(16):
                    for y in range(16):
                        if (x - 8)**2 + (y - 8)**2 <= 36:
                            circle_icon.put(color, (x, y))

                new_marker = self.map_widget.set_marker(
                    point.latitude,
                    point.longitude,
                    text="",
                    icon=circle_icon,
                    command=self.on_marker_click  
                )
                
                new_marker.data = point.id
                new_marker.info = info_text  
                self.map_markers.append(new_marker)

        except Exception as e:
            print(f"Ошибка загрузки точек на карту Минска: {e}")



    def on_marker_click(self, marker):
        point_id = marker.data
        point_info = marker.info  
        
        user_wants_to_review = messagebox.askyesno(
            "Информация о пункте сырья", 
            f"{point_info}\n\nЖелаете отправить экспресс-отзыв о состоянии этого пункта?"
        )
        
        if user_wants_to_review:
            dialog = ctk.CTkInputDialog(
                text="Введите состояние пункта сырья:\n1 - Работает штатно\n2 - Переполнен / Закрыт", 
                title="Отзыв жителя"
            )
            choice = dialog.get_input()
            
            if choice in ["1", "2"]:
                status_str = "works" if choice == "1" else "broken_or_full"
                current_time = datetime.now(timezone.utc).isoformat()
                
                conn = sqlite3.connect('ecology.db')
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO reviews (point_id, status, created_at) VALUES (?, ?, ?)",
                    (point_id, status_str, current_time)
                )
                conn.commit()
                conn.close()
                
                self.load_points()


if __name__ == "__main__":
    app = EcoApp()
    app.mainloop()