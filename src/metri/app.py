import customtkinter as ctk
from PIL import Image, ImageSequence
import pygame, os
from .views.main_screen import MainScreen


class SplashGIF(ctk.CTkToplevel):
    def __init__(self, gif_path, sound_path, on_finish):
        super().__init__()
        self.overrideredirect(True)  # splash = bez ramek
        self.configure(fg_color="black")

        # Kwadratowe okno splash
        self.update_idletasks()
        size = 400
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = (sw - size) // 2, (sh - size) // 2
        self.geometry(f"{size}x{size}+{x}+{y}")

        # Wczytanie klatek GIF
        pil_img = Image.open(gif_path)
        frames = [frame.copy() for frame in ImageSequence.Iterator(pil_img)]
        self.frames = [ctk.CTkImage(light_image=img, size=(size, size)) for img in frames]

        self.label = ctk.CTkLabel(self, text="")
        self.label.pack(expand=True, fill="both")

        self.index = 0
        self.on_finish = on_finish
        self.sound_path = sound_path

        # Animacja = 7s
        self.total_duration = 7000
        self.frame_count = len(self.frames)
        self.delay = int(self.total_duration / self.frame_count)

        pygame.mixer.init()

        self.after(0, self.play)

    def play(self):
        if self.index == 0:
            pygame.mixer.Sound(self.sound_path).play()

        if self.index < self.frame_count:
            self.label.configure(image=self.frames[self.index])
            self.index += 1
            self.after(self.delay, self.play)
        else:
            self.destroy()
            self.on_finish()


class MetriApp(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("dark-blue")
        super().__init__()

        # NIE UŻYWAMY override_redirect!
        self.attributes("-fullscreen", False)  # na start
        self.main = MainScreen(self)


def run():
    app = MetriApp()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    gif_path = os.path.join(BASE_DIR, "assets", "splash2.gif")
    sound_path = os.path.join(BASE_DIR, "assets", "splash.mp3")

    def show_app():
        app.deiconify()
        app.attributes("-fullscreen", True)   # pełen ekran bez paska

    splash = SplashGIF(gif_path, sound_path, on_finish=show_app)
    app.withdraw()  # ukrycie głównego okna

    splash.mainloop()
