import customtkinter as ctk
from .views.main_screen import MainScreen
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)  # lub 2
except:
    pass
APP_NAME = "Metri"


class MetriApp(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("dark-blue")

        super().__init__()

        self.overrideredirect(False)
        self.attributes('-fullscreen', False)
        self.attributes('-topmost', False)
        self._set_window_geometry()
        self.focus_force()

        # ZMIANA: Użycie bind_all() gwarantuje przechwycenie klawisza
        self.bind_all('<Escape>', self._exit_app)

        self.main = MainScreen(self)

    def _set_window_geometry(self):
        """Place the borderless window in centered windowed mode."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        window_width = int(screen_width * 0.85)
        window_height = int(screen_height * 0.85)

        offset_x = (screen_width - window_width) // 2
        offset_y = (screen_height - window_height) // 2

        self.geometry(f"{window_width}x{window_height}+{offset_x}+{offset_y}")

    def _exit_app(self, event=None):
        """Funkcja zamykająca aplikację."""
        # Warto dodać print() na wszelki wypadek, żeby sprawdzić, czy funkcja jest w ogóle wywoływana
        print("Aplikacja została zamknięta klawiszem ESC.")
        self.destroy()


def run():
    app = MetriApp()
    app.mainloop()