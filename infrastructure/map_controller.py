import sqlite3
import tkinter.messagebox as messagebox
from datetime import datetime, timezone
from geopy.geocoders import Nominatim
from ui.mod_panel import ModeratorPanel
from ui.legal_panel import LegalEntityPanel

class MapController:
    def __init__(self, app):
        self.app = app

    def handle_right_click(self, coordinates):
        if self.app.role_selector.get() != "Модератор" or not isinstance(self.app.active_panel, ModeratorPanel):
            messagebox.showwarning("Доступ ограничен", "Добавление новых пунктов сырья доступно только в режиме Модератора!")
            return
            
        self.app.clicked_lat = coordinates[0]
        self.app.clicked_lng = coordinates[1]
        
        try:
            geolocator = Nominatim(user_agent="ecology_navigator_app_v2")
            location = geolocator.reverse((self.app.clicked_lat, self.app.clicked_lng), language="ru")
            
            if location and location.raw and "address" in location.raw:
                address_data = location.raw["address"]
                street = address_data.get("road", address_data.get("suburb", address_data.get("pedestrian", "")))
                house = address_data.get("house_number", "")
                detected_address = f"{street}, {house}".strip(", ") if street else location.address.split(", Минск")[0]
            else:
                detected_address = f"{round(self.app.clicked_lat, 4)}, {round(self.app.clicked_lng, 4)}"
        except Exception:
            detected_address = f"{round(self.app.clicked_lat, 4)}, {round(self.app.clicked_lng, 4)}"
        
        self.app.active_panel.address_entry.delete(0, 'end')
        self.app.active_panel.address_entry.insert(0, detected_address)

    def handle_marker_click(self, marker):
        if self.app.role_selector.get() == 'Юр.Лицо' and isinstance(self.app.active_panel, LegalEntityPanel):
            self.app.active_panel.execute_bulk_order(marker)
            return
            
        if messagebox.askyesno("Информация о пункте сырья", f"{marker.info}\n\nЖелаете отправить экспресс-отзыв?"):
            from customtkinter import CTkInputDialog
            dialog = CTkInputDialog(text="1 - Работает\n2 - Переполнен", title="Отзыв")
            choice = dialog.get_input()
            
            if choice in ["1", "2"]:
                conn = sqlite3.connect('ecology.db')
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO reviews (point_id, status, created_at) VALUES (?, ?, ?)", 
                    (marker.data, "works" if choice == "1" else "broken_or_full", datetime.now(timezone.utc).isoformat())
                )
                conn.commit()
                conn.close()
                self.app.load_points()

    def handle_delete(self, coordinates):
        if self.app.role_selector.get() != "Модератор":
            messagebox.showwarning("Доступ ограничен", "Удаление пунктов доступно только в режиме Модератора!")
            return
            
        target_id, target_name = None, "выбранный пункт"
        for marker in self.app.map_markers:
            if abs(marker.position[0] - coordinates[0]) < 0.005 and abs(marker.position[1] - coordinates[1]) < 0.005:
                target_id = marker.data
                target_name = marker.info.split("\n")[0]
                break

        if target_id is not None and messagebox.askyesno("Подтверждение удаления", f"Вы уверены, что хотите удалить {target_name}?"):
            conn = sqlite3.connect('ecology.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reviews WHERE point_id = ?", (int(target_id),))
            cursor.execute("DELETE FROM eco_points WHERE id = ?", (int(target_id),))
            conn.commit()
            conn.close()
            messagebox.showinfo("Удаление", "Пункт успешно удален.")
            self.app.load_points()
        elif target_id is None:
            messagebox.showwarning("Ошибка", "Кликните точнее по кружку маркера для удаления!")
