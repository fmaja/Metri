import customtkinter as ctk
from .views.main_screen import MainScreen

APP_NAME = "Metri"


class MetriApp(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("dark-blue")

        super().__init__()

        self.attributes('-fullscreen', True)
        self.overrideredirect(True)
        self.attributes('-topmost', 1)
        self.focus_force()

        # ZMIANA: Użycie bind_all() gwarantuje przechwycenie klawisza
        self.bind_all('<Escape>', self._exit_app)

        self.main = MainScreen(self)

    def _exit_app(self, event=None):
        """Funkcja zamykająca aplikację."""
        # Warto dodać print() na wszelki wypadek, żeby sprawdzić, czy funkcja jest w ogóle wywoływana
        print("Aplikacja została zamknięta klawiszem ESC.")
        self.destroy()


def run():
    app = MetriApp()
    app.mainloop()