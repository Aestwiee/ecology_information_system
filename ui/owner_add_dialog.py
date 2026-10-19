import customtkinter as ctk
import tkinter.messagebox as messagebox


class AddOwnerDialog(ctk.CTkToplevel):
    def __init__(self, master, owners_repo, on_created):
        super().__init__(master)
        self.title("Новый владелец инфраструктуры")
        self.geometry("360x220")

        self.lift()
        self.attributes("-topmost", True) 

        self.owners_repo = owners_repo
        self.on_created = on_created

        ctk.CTkLabel(self, text="Название компании:").pack(padx=20, pady=(15, 0), anchor="w")
        self.name_entry = ctk.CTkEntry(self, placeholder_text="например, ЭКОЛАЙН-2")
        self.name_entry.pack(padx=20, pady=5, fill="x")

        ctk.CTkLabel(self, text="Пароль для входа:").pack(padx=20, pady=(10, 0), anchor="w")
        self.pass_entry = ctk.CTkEntry(self, placeholder_text="минимум 6 символов", show="*")
        self.pass_entry.pack(padx=20, pady=5, fill="x")

        self.save_btn = ctk.CTkButton(self, text="Создать", command=self._save)
        self.save_btn.pack(padx=20, pady=15, fill="x")

    def _save(self):
        name = self.name_entry.get().strip().upper()
        password = self.pass_entry.get().strip()

        if not name:
            messagebox.showwarning("Ошибка", "Название не может быть пустым.", parent=self)
            return
        if len(password) < 6:
            messagebox.showwarning("Ошибка", "Пароль должен быть не короче 6 символов.", parent=self)
            return
        if self.owners_repo.exists(name):
            messagebox.showwarning("Ошибка", f"Владелец '{name}' уже существует.", parent=self)
            return

        self.owners_repo.add(name, password)
        messagebox.showinfo("Успех", f"Владелец '{name}' создан.", parent=self)
        self.on_created(name)
        self.destroy()