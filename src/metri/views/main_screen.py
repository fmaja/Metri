import customtkinter as ctk
from .calendar import CalendarView
from .day import DayView
from .theory import TheoryView
from .quiz import QuizView
from .metronome import MetronomeView
from .chord_finder import ChordFinderView
import os
from PIL import Image
from datetime import datetime
from typing import Optional, Type, Tuple


class MainScreen:
    # --- Stałe (Kolory i Konfiguracja) ---
    HEADER_BG = "#FFFFFF"
    BG_MAIN = "#f2f2f2"
    CARD_BG = "#FFFFFF"

    # Kolory akcentujące
    ACCENT_CYAN = "#25b4b6"
    ACCENT_GOLD = "#cca839"
    COLOR_RED = "#E74C3C"
    COLOR_GREEN = "#2ECC71"
    COLOR_BLUE = "#3498DB"

    # Mapowanie modułów na przyciski w menu i ich ikony
    MODULES = {
        "Sesja Dziennna": {"View": DayView, "Icon": "practice", "Color": ACCENT_GOLD},
        "Kalendarz": {"View": CalendarView, "Icon": "calendar", "Color": COLOR_BLUE},
        "Quizy": {"View": QuizView, "Icon": "quiz", "Color": COLOR_RED},
        "Teoria": {"View": TheoryView, "Icon": "theory", "Color": ACCENT_CYAN},
        "Metronom": {"View": MetronomeView, "Icon": "metronome", "Color": COLOR_BLUE},
        "Tetekror": {"View": ChordFinderView, "Icon": "search", "Color": COLOR_GREEN},
    }

    BUTTON_ORDER = [
        "Sesja Dziennna",
        "Quizy",
        "Teoria",
        "Metronom",
        "Tetekror"
    ]

    def __init__(self, master: ctk.CTk):
        self.master = master
        master.title("Metri - Menu Główne")
        master.geometry("1000x800")

        ctk.set_appearance_mode("Light")
        self.current_theme = ctk.get_appearance_mode()

        self.container = ctk.CTkFrame(master, fg_color=self.BG_MAIN)
        self.container.pack(fill="both", expand=True)

        # Zmienne referencji
        self.current_view_frame: Optional[ctk.CTkFrame] = None
        self.current_view_object = None
        self.stats = {}

        # Inicjalizacja UI
        self._get_day_view_stats()
        self._create_menu_frame()  # Ta metoda teraz zawiera tworzenie paska

    # --- Narzędzia ---

    def _get_icon(self, name: str, size: int = 40) -> Optional[ctk.CTkImage]:
        """Ładuje ikonę na podstawie nazwy."""
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                     "assets", "icons", f"{name}.png")
            return ctk.CTkImage(light_image=Image.open(icon_path), size=(size, size))
        except:
            return None

    def _get_day_view_stats(self):
        """Pobiera statystyki dzienne/tygodniowe."""
        temp_frame = ctk.CTkFrame(self.master)
        try:
            temp_day_view = DayView(temp_frame, selected_date=datetime.now())
            percentage, week_total = temp_day_view._get_current_week_progress()
            daily_minutes = temp_day_view._get_practice_minutes(datetime.now())
            daily_goal = temp_day_view.PRACTICE_GOAL

            self.stats = {
                "week_progress": percentage, "week_total_min": week_total, "week_goal_min": temp_day_view.WEEKLY_GOAL,
                "daily_min": daily_minutes, "daily_goal": daily_goal,
            }
            temp_day_view.destroy()
        except Exception:
            self.stats = {
                "week_progress": 0, "week_total_min": 0, "week_goal_min": 180,
                "daily_min": 0, "daily_goal": 30
            }
        finally:
            temp_frame.destroy()

    def _get_darker_color(self, hex_color: str) -> str:
        """Zwraca nieco ciemniejszy odcień koloru (do efektu hover)."""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        new_rgb = (int(r * 0.85) for r in rgb)
        return '#%02x%02x%02x' % tuple(new_rgb)

    # --- Elementy UI Menu Głównego ---

    def _create_header_bar(self, master_frame: ctk.CTkFrame):
        """Tworzy pasek nagłówka jako część ramki menu."""

        header_bar = ctk.CTkFrame(master_frame, fg_color=self.HEADER_BG, height=60, corner_radius=0)
        header_bar.pack(fill="x", side="top", padx=0, pady=0)
        header_bar.grid_columnconfigure(1, weight=1)

        # 1. Logo/Ikona
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.png")
        if os.path.exists(logo_path):
            app_icon = self._get_icon("icon", size=40)
            ctk.CTkLabel(header_bar, image=app_icon, text="").grid(row=0, column=0, padx=(20, 10), pady=10, sticky="w")

        # 2. Tytuł (Metri)
        ctk.CTkLabel(
            header_bar,
            text="Metri",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.ACCENT_CYAN
        ).grid(row=0, column=1, padx=0, pady=10, sticky="w")

        # 3. Zmiana Motywu
        self.theme_button = ctk.CTkButton(
            header_bar,
            text="☀️ Tryb Jasny" if self.current_theme == "Light" else "🌙 Tryb Ciemny",
            command=self._toggle_theme,
            width=120,
            height=35,
            font=ctk.CTkFont(size=14),
            fg_color="#E0E0E0",
            text_color="#333333",
            hover_color="#CCCCCC"
        )
        self.theme_button.grid(row=0, column=2, padx=(10, 10), sticky="e")

        # 4. Przycisk Wyjdź
        ctk.CTkButton(
            header_bar,
            text="✕ Wyjdź",
            command=self.master.quit,
            width=100,
            height=35,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#C0392B",
            hover_color="#A93226"
        ).grid(row=0, column=3, padx=(0, 20), sticky="e")

    def _create_menu_frame(self):
        """Tworzy główną ramkę menu, która zawiera pasek nagłówka, podsumowanie i przyciski."""

        self.menu_frame = ctk.CTkFrame(self.container, fg_color=self.BG_MAIN)
        self.menu_frame.pack(fill="both", expand=True)  # Pakujemy ramkę menu, która będzie ukrywana

        # 1. Pasek Nagłówka (teraz jest częścią menu_frame)
        self._create_header_bar(self.menu_frame)

        # Ramka na zawartość pod paskiem nagłówka
        content_frame = ctk.CTkFrame(self.menu_frame, fg_color=self.BG_MAIN)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Podział ekranu: 40% na podsumowanie (r0), 60% na przyciski (r1)
        content_frame.grid_rowconfigure(0, weight=40, uniform="a")
        content_frame.grid_rowconfigure(1, weight=60, uniform="a")
        content_frame.grid_columnconfigure(0, weight=1)

        # --- Sekcja 1: Podsumowanie Kalendarza (Góra) ---
        self._create_summary_panel(content_frame)

        # --- Sekcja 2: Przyciski Modułów (Dół) ---
        self.buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        self.buttons_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(15, 0))
        self._create_module_buttons()

    def _create_summary_panel(self, master_frame: ctk.CTkFrame):
        """Tworzy klikalny panel podsumowania z postępem tygodniowym i dziennym."""

        initial_border_color = self.BG_MAIN

        self.summary_card = ctk.CTkFrame(
            master_frame,
            fg_color=self.CARD_BG,
            corner_radius=15,
            cursor="hand2",
            border_width=2,
            border_color=initial_border_color
        )
        self.summary_card.grid(row=0, column=0, sticky="nsew", padx=10, pady=(0, 15))
        self.summary_card.grid_columnconfigure(0, weight=1)
        self.summary_card.grid_columnconfigure(1, weight=1)

        self.summary_card.bind("<Button-1>", lambda e: self._show_module("Kalendarz"))
        self.summary_card.bind("<Enter>", lambda e: self.summary_card.configure(border_color=self.ACCENT_CYAN))
        self.summary_card.bind("<Leave>", lambda e: self.summary_card.configure(border_color=self.BG_MAIN))

        # --- Lewa strona: Postęp Tygodniowy ---
        progress_panel = ctk.CTkFrame(self.summary_card, fg_color="transparent")
        progress_panel.grid(row=0, column=0, sticky="nsew", padx=40, pady=30)
        progress_panel.columnconfigure(0, weight=1)

        ctk.CTkLabel(progress_panel, text="🎯 CEL TYGODNIOWY", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#555555").grid(row=0, column=0, sticky="w", pady=(0, 10))

        percentage = self.stats.get('week_progress', 0)
        progress_color = self.ACCENT_CYAN if percentage < 100 else self.COLOR_GREEN

        self.progress_bar_main = ctk.CTkProgressBar(progress_panel, height=30, progress_color=progress_color,
                                                    corner_radius=15)
        self.progress_bar_main.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        self.progress_bar_main.set(percentage / 100)

        progress_text = f"{self.stats.get('week_total_min', 0)} / {self.stats.get('week_goal_min', 180)} min osiągnięte ({percentage}%)"
        ctk.CTkLabel(progress_panel, text=progress_text, font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#333333").grid(row=2, column=0, sticky="nw", pady=(0, 10))

        ctk.CTkLabel(progress_panel, text="KLIKNIJ, ABY OTWORZYĆ KALENDARZ", font=ctk.CTkFont(size=12),
                     text_color=self.ACCENT_GOLD).grid(row=3, column=0, sticky="sw", pady=(10, 0))

        # --- Prawa strona: Wynik Dzienny ---
        daily_panel = ctk.CTkFrame(self.summary_card, fg_color="transparent")
        daily_panel.grid(row=0, column=1, sticky="nsew", padx=40, pady=30)
        daily_panel.columnconfigure(0, weight=1)

        ctk.CTkLabel(daily_panel, text="📅 DZISIEJSZY WYNIK", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#555555").grid(row=0, column=0, sticky="w", pady=(0, 10))

        daily_min = self.stats.get('daily_min', 0)
        daily_goal = self.stats.get('daily_goal', 30)
        color_daily = self.COLOR_GREEN if daily_min >= daily_goal else self.COLOR_RED

        ctk.CTkLabel(daily_panel, text=f"{daily_min}", font=ctk.CTkFont(size=60, weight="bold"),
                     text_color=color_daily).grid(row=1, column=0, sticky="w")
        ctk.CTkLabel(daily_panel, text=f"Minut ćwiczeń / Cel: {daily_goal} min", font=ctk.CTkFont(size=18),
                     text_color="#333333").grid(row=2, column=0, sticky="nw")
        daily_panel.grid_rowconfigure(3, weight=1)

    def _create_module_buttons(self):
        """Tworzy pięć kwadratowych przycisków dla głównych modułów."""

        self.buttons_frame.columnconfigure((0, 1, 2), weight=1, uniform="b")
        self.buttons_frame.rowconfigure((0, 1), weight=1, uniform="c")

        # Pozycje dla 5 przycisków w siatce 2x3 (środkowy pusty)
        positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)]

        for i, key in enumerate(self.BUTTON_ORDER):
            if i < len(positions):
                r, c = positions[i]
                module_data = self.MODULES.get(key)

                if not module_data: continue

                btn_container = ctk.CTkFrame(self.buttons_frame, fg_color="transparent")
                btn_container.grid(row=r, column=c, sticky="nsew", padx=10, pady=10)
                btn_container.columnconfigure(0, weight=1)
                btn_container.rowconfigure(0, weight=1)

                button = ctk.CTkButton(
                    btn_container,
                    text=key if key != "Tetekror" else "Wyszukiwarka akordów",
                    command=lambda k=key: self._show_module(k),
                    fg_color=module_data["Color"],
                    hover_color=self._get_darker_color(module_data["Color"]),
                    compound="top",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    image=self._get_icon(module_data["Icon"], size=45),
                    corner_radius=15,
                    text_color="white"
                )
                button.grid(row=0, column=0, sticky="nsew")

    # --- Logika Nawigacji ---

    def _hide_current_view(self):
        """Ukrywa aktualnie wyświetlany widok i niszczy jego ramkę."""
        if self.current_view_frame:
            if hasattr(self.current_view_object, 'destroy') and callable(self.current_view_object.destroy):
                self.current_view_object.destroy()

            self.current_view_frame.destroy()
            self.current_view_frame = None
            self.current_view_object = None

    def _create_module_frame(self, ViewClass: Type, **kwargs) -> Tuple[ctk.CTkFrame, object]:
        """Tworzy ramkę dla nowego widoku i jego instancję z odpowiednimi callbackami."""
        frame = ctk.CTkFrame(self.container, fg_color=self.BG_MAIN)

        callbacks = {
            "back_to_menu_callback": self.show_menu,
            "back_callback": self.show_menu,
            "back_to_calendar_callback": lambda: self._show_module("Kalendarz"),
            "show_day_callback": self._show_day_from_calendar
        }

        all_args = {**kwargs, **callbacks}
        view_args = all_args.copy()

        # --- FILTROWANIE ARGUMENTÓW ---

        if ViewClass == DayView:
            # DayView potrzebuje: selected_date, back_to_menu_callback, back_to_calendar_callback
            view_args.pop("back_callback", None)
            view_args.pop("show_day_callback", None)

        elif ViewClass == CalendarView:
            # CalendarView potrzebuje: show_day_callback i back_callback
            view_args = {
                "show_day_callback": self._show_day_from_calendar,
                "back_callback": self.show_menu,
                **kwargs
            }
            view_args.pop("back_to_menu_callback", None)
            view_args.pop("back_to_calendar_callback", None)

        else:
            # Proste Widoki potrzebują tylko 'back_callback'
            view_args = {
                "back_callback": self.show_menu,
                **kwargs
            }
            view_args.pop("back_to_menu_callback", None)
            view_args.pop("back_to_calendar_callback", None)
            view_args.pop("show_day_callback", None)

        view_instance = ViewClass(frame, **view_args)
        view_instance.pack(fill="both", expand=True)
        return frame, view_instance

    def _show_module(self, module_name: str, **kwargs):
        """Główna metoda do przełączania modułów."""
        module_info = self.MODULES.get(module_name)
        if not module_info:
            return

        # Ukryj ramkę menu
        self.menu_frame.pack_forget()
        self._hide_current_view()

        ViewClass = module_info["View"]
        self.current_view_frame, self.current_view_object = self._create_module_frame(ViewClass, **kwargs)
        self.current_view_frame.pack(fill="both", expand=True)

    def _show_day_from_calendar(self, selected_date: datetime):
        """Obsługuje przekazywanie daty z kalendarza do widoku dziennego."""
        self._show_module("Sesja Dziennna", selected_date=selected_date)

    # --- Metody Publiczne dla Callbacków ---

    def show_menu(self):
        """Wracanie do menu głównego."""
        # Odśwież statystyki i panel
        self._get_day_view_stats()
        self._create_summary_panel(self.menu_frame.winfo_children()[1])  # Odśwież pod-ramkę w menu

        self._hide_current_view()
        self.menu_frame.pack(fill="both", expand=True)  # Pokaż ramkę menu z paskiem nagłówka

    def _toggle_theme(self):
        """Przełącza motyw między jasnym a ciemnym."""
        if ctk.get_appearance_mode() == "Dark":
            ctk.set_appearance_mode("Light")
            self.current_theme = "Light"
        else:
            ctk.set_appearance_mode("Dark")
            self.current_theme = "Dark"

        self.show_menu()