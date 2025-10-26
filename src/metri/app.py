import customtkinter as ctk
from .views.main_screen import MainScreen

APP_NAME = "Metri"

class MetriApp(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("dark-blue")  
        
        super().__init__()

        self.title(APP_NAME)
        self.geometry("900x650")
        self.minsize(800, 600)
        
        self.main = MainScreen(self)

def run():
    app = MetriApp()
    app.mainloop()