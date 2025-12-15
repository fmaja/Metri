import customtkinter as ctk
from .calendar import CalendarView
from .day import DayView
from .theory import TheoryView
from .quiz import QuizView
from .metronome import MetronomeView
from .chord_finder import ChordFinderView
from .songbook import SongbookView
from .sidebar import Sidebar
import os
from PIL import Image
from datetime import datetime
from typing import Optional, Type, Tuple, Callable


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
    COLOR_LIGHT_GREEN = "#A8E6A8"
    COLOR_BLUE = "#3498DB"
    ACCENT_PURPLE = "#552564"

    # NOWY KOLOR: Jasny szary dla niezrobionej części paska postępu
    COLOR_PROGRESS_TRACK = "#E0E0E0"

    # Mapowanie modułów na przyciski w menu i ich ikony (ZAKTUALIZOWANE O EMOTIKONY)
    MODULES = {
        "Sesja Dziennna": {"View": DayView, "Icon": "practice", "Color": COLOR_BLUE, "Emoji": "🎸"},
        "Quizy": {"View": QuizView, "Icon": "quiz", "Color": COLOR_LIGHT_GREEN, "Emoji": "🧠"},
        "Teoria": {"View": TheoryView, "Icon": "theory", "Color": ACCENT_CYAN, "Emoji": "📚"},
        "Metronom": {"View": MetronomeView, "Icon": "metronome", "Color": ACCENT_GOLD, "Emoji": "⏱️"},
        "Detektor": {"View": ChordFinderView, "Icon": "search", "Color": ACCENT_PURPLE, "Emoji": "🔎"},
        "Śpiewnik": {"View": SongbookView, "Icon": "theory", "Color": COLOR_RED, "Emoji": "📖"},
        "Kalendarz": {"View": CalendarView, "Icon": "calendar", "Color": ACCENT_CYAN, "Emoji": "📅"},
    }

    BUTTON_ORDER = [
        "Sesja Dziennna",
        "Quizy",
        "Teoria",
        "Metronom",
        "Detektor",
        "Śpiewnik"
    ]

    def __init__(self, master: ctk.CTk):
        self.master = master
        master.title("Metri - Menu Główne")
        master.geometry("1000x800")

        ctk.set_appearance_mode("Light")
        self.current_theme = ctk.get_appearance_mode()

        self.container = ctk.CTkFrame(master, fg_color=self._get_main_bg_color())
        self.container.pack(fill="both", expand=True)

        self.sidebar = Sidebar(
            master=self.master,
            modules=self.MODULES,
            show_module_callback=self._show_module,
            show_menu_callback=self.show_menu,
            header_height=100)

        self.current_view_frame: Optional[ctk.CTkFrame] = None
        self.current_view_object = None
        self.stats = {}
        self.content_frame: Optional[ctk.CTkFrame] = None

        self._get_day_view_stats()
        self._create_menu_frame()


    # --- Narzędzia ---

    def _get_main_bg_color(self):
        """Pobiera kolor tła dla głównego kontenera w zależności od motywu."""
        return self.BG_MAIN if ctk.get_appearance_mode() == "Light" else "#1a1a1a"

    def _get_icon(self, name: str, size: int = 40) -> Optional[ctk.CTkImage]:
        """Ładuje ikonę na podstawie nazwy."""
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                     "assets", "icons", f"{name}.png")
            return ctk.CTkImage(light_image=Image.open(icon_path), size=(size, size))
        except:
            return None

    def _get_text_color(self):
        """Pobiera główny kolor tekstu. Ustawiony na BIAŁY dla Cyjanowej karty."""
        return "white"

    def _get_secondary_text_color(self):
        """Pobiera drugorzędny kolor tekstu (nagłówki)."""
        return "#EEEEEE"  # Jasnoszary

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
    # ... (metody _create_header_bar, _get_theme_icon, _create_menu_frame bez zmian) ...
    def _create_header_bar(self, master_frame: ctk.CTkFrame):
        self.header = ctk.CTkFrame(master_frame, fg_color=self.HEADER_BG, height=72, corner_radius=12)
        self.header.pack(fill="x", side="top", padx=10, pady=(20, 10))
        self.header.grid_propagate(False)
        self.header.columnconfigure(1, weight=1)
        self.header.rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self.header, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=(18, 10))

        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.app_icon = ctk.CTkImage(light_image=Image.open(icon_path), size=(60, 65))
            self.menu_button = ctk.CTkButton(
                left,
                image=self.app_icon,
                text="",
                width=60,
                height=65,
                fg_color="transparent",
                command=self.sidebar.toggle
            )
            self.menu_button.pack(side="left", anchor="center")

        title_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "name.png")
        if os.path.exists(title_path):
            self.title_icon = ctk.CTkImage(light_image=Image.open(title_path), size=(160, 40))
            ctk.CTkLabel(left, image=self.title_icon, text="").pack(side="left", anchor="center", padx=(50, 18))

        # --- PRAWA STRONA: PRZEŁĄCZNIK MOTYWU I WYJDŹ ---
        right = ctk.CTkFrame(self.header, fg_color="transparent")
        right.grid(row=0, column=2, sticky="e", padx=(10, 18))

        # 1. Przycisk Wyjdź
        ctk.CTkButton(
            right,
            text="✕",
            command=self.master.quit,
            width=44, height=44,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#C0392B",
            hover_color="#A93226",
            corner_radius=12
        ).pack(side="right", anchor="center", padx=(10, 0))

        # 2. Przełącznik Motywu (Ikona)
        self.theme_icon_button = ctk.CTkButton(
            right,
            width=44, height=44,
            fg_color=self.ACCENT_GOLD,
            hover_color=self.ACCENT_PURPLE,
            text=self._get_theme_icon(),
            command=self._toggle_theme,
            corner_radius=12,
            font=ctk.CTkFont(size=22),
        )
        self.theme_icon_button.pack(side="right", anchor="center")

    def _get_theme_icon(self) -> str:
        """Zwraca odpowiednią ikonę w zależności od aktualnego motywu."""
        return "🌙" if ctk.get_appearance_mode() == "Light" else "🌞"

    def _create_menu_frame(self):
        """Tworzy główną ramkę menu."""

        self.menu_frame = ctk.CTkFrame(self.container, fg_color=self._get_main_bg_color())
        self.menu_frame.pack(fill="both", expand=True)

        # 1. Pasek Nagłówka (część menu_frame)
        self._create_header_bar(self.menu_frame)

        # Ramka na zawartość pod paskiem nagłówka
        self.content_frame = ctk.CTkFrame(self.menu_frame, fg_color=self._get_main_bg_color())
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Podział ekranu
        self.content_frame.grid_rowconfigure(0, weight=40, uniform="a")
        self.content_frame.grid_rowconfigure(1, weight=60, uniform="a")
        self.content_frame.grid_columnconfigure(0, weight=1)

        # --- Sekcja 1: Podsumowanie Kalendarza (Góra) ---
        self._create_summary_panel(self.content_frame)

        # --- Sekcja 2: Przyciski Modułów (Dół) ---
        self.buttons_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.buttons_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(15, 0))
        self._create_module_buttons()


    def _create_sidebar(self):
        if self.sidebar and self.sidebar.winfo_exists():
            return

        header_height = 100  # wysokość nagłówka
        self.sidebar = ctk.CTkFrame(
            self.master,
            fg_color="white",  # białe tło
            width=250
        )
        # rozciągnięcie na cały ekran w dół, ale start poniżej headera
        self.sidebar.place(x=-250, y=header_height, relheight=1)

        for name, data in self.MODULES.items():
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{data.get('Emoji', '')} {name}",
                fg_color="white",  # tło zawsze białe
                text_color="black",
                corner_radius=0,
                border_width=2,
                border_color="white",  # brak obramowania na start
                command=lambda k=name: self._sidebar_action(k)
            )
            btn.pack(fill="x", padx=10, pady=5)

            # efekt hover: zmiana obramowania
            btn.bind("<Enter>", lambda e, b=btn: b.configure(border_color=data["Color"]))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(border_color="white"))

    def _toggle_sidebar(self):
        header_height = 100
        if not self.sidebar or not self.sidebar.winfo_exists():
            self._create_sidebar()

        if self.sidebar.winfo_x() >= 0:
            # schowaj
            self.sidebar.place(x=-250, y=header_height, relheight=1)
        else:
            # pokaż
            self.sidebar.place(x=0, y=header_height, relheight=1)

    def _sidebar_action(self, module_name: str):
        """Obsługa kliknięcia w przycisk sidebaru."""
        if module_name == "Menu":
            # wróć do głównego menu
            self.show_menu()
        else:
            # pokaż wybrany moduł
            self._show_module(module_name)
        # schowaj sidebar po kliknięciu
        self._toggle_sidebar()
    def _create_summary_panel(self, master_frame: ctk.CTkFrame):
        """Tworzy klikalny panel podsumowania z postępem tygodniowym i dziennym. Tło: CYJAN. Tekst: BIAŁY."""

        initial_border_color = self._get_main_bg_color()

        self.summary_card = ctk.CTkFrame(
            master_frame,
            fg_color=self.ACCENT_CYAN,  # TŁO ZAWSZE CYJAN
            corner_radius=15,
            cursor="hand2",
            border_width=2,
            border_color=initial_border_color
        )
        self.summary_card.grid(row=0, column=0, sticky="nsew", padx=10, pady=(0, 15))
        self.summary_card.grid_columnconfigure(0, weight=1)
        self.summary_card.grid_columnconfigure(1, weight=1)

        self.summary_card.bind("<Button-1>", lambda e: self._show_module("Kalendarz"))
        # Obramowanie na hover ZŁOTE
        self.summary_card.bind("<Enter>", lambda e: self.summary_card.configure(border_color=self.ACCENT_GOLD))
        self.summary_card.bind("<Leave>", lambda e: self.summary_card.configure(
            border_color=self._get_main_bg_color()))

        # --- Lewa strona: Postęp Tygodniowy ---
        progress_panel = ctk.CTkFrame(self.summary_card, fg_color=self.ACCENT_CYAN)  # Tło ramki na Cyjan
        progress_panel.grid(row=0, column=0, sticky="nsew", padx=40, pady=30)
        progress_panel.columnconfigure(0, weight=1)

        # Nagłówek dynamiczny (Jasnoszary)
        ctk.CTkLabel(progress_panel, text="🎯 CEL TYGODNIOWY", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self._get_secondary_text_color()).grid(row=0, column=0, sticky="w", pady=(0, 10))

        percentage = self.stats.get('week_progress', 0)
        # Pasek postępu na ZŁOTY/ZIELONY
        progress_color = self.ACCENT_GOLD if percentage < 100 else self.COLOR_GREEN

        # Pasek postępu - użycie jaśniejszego tła dla niezrobionej części
        self.progress_bar_main = ctk.CTkProgressBar(progress_panel, height=30, progress_color=progress_color,
                                                    fg_color=self.COLOR_PROGRESS_TRACK,  # Jasna ścieżka
                                                    corner_radius=15)
        self.progress_bar_main.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        self.progress_bar_main.set(percentage / 100)

        progress_text = f"{self.stats.get('week_total_min', 0)} / {self.stats.get('week_goal_min', 180)} min osiągnięte ({percentage}%)"

        # Tekst dynamiczny (Biały)
        ctk.CTkLabel(progress_panel, text=progress_text, font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=self._get_text_color()).grid(row=2, column=0, sticky="nw", pady=(0, 10))

        # Tekst akcentujący na ZŁOTY
        ctk.CTkLabel(progress_panel, text="KLIKNIJ, ABY OTWORZYĆ KALENDARZ", font=ctk.CTkFont(size=12),
                     text_color=self.ACCENT_GOLD).grid(row=3, column=0, sticky="sw", pady=(10, 0))

        # --- Prawa strona: Wynik Dzienny ---
        daily_panel = ctk.CTkFrame(self.summary_card, fg_color=self.ACCENT_CYAN)  # Tło ramki na Cyjan
        daily_panel.grid(row=0, column=1, sticky="nsew", padx=40, pady=30)
        daily_panel.columnconfigure(0, weight=1)

        # Nagłówek dynamiczny (Jasnoszary)
        ctk.CTkLabel(daily_panel, text="📅 DZISIEJSZY WYNIK", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self._get_secondary_text_color()).grid(row=0, column=0, sticky="w", pady=(0, 10))

        daily_min = self.stats.get('daily_min', 0)
        daily_goal = self.stats.get('daily_goal', 30)

        # ZMIENIONE NA FIOLETOWY:
        color_daily = self.ACCENT_PURPLE

        ctk.CTkLabel(daily_panel, text=f"{daily_min}", font=ctk.CTkFont(size=60, weight="bold"),
                     text_color=color_daily).grid(row=1, column=0, sticky="w")
        # Tekst dynamiczny (Biały)
        ctk.CTkLabel(daily_panel, text=f"Minut ćwiczeń / Cel: {daily_goal} min", font=ctk.CTkFont(size=18),
                     text_color=self._get_text_color()).grid(row=2, column=0, sticky="nw")
        daily_panel.grid_rowconfigure(3, weight=1)

    def _create_module_buttons(self):
        """Tworzy kwadratowe przyciski dla głównych modułów w dwóch rzędach (3 na górze, 3 na dole)."""

        # Zapewnienie, że wszystkie 3 kolumny mają równą wagę
        num_buttons = len(self.BUTTON_ORDER)
        for i in range(3):
            self.buttons_frame.columnconfigure(i, weight=1, uniform="b")
        self.buttons_frame.rowconfigure(0, weight=1)
        self.buttons_frame.rowconfigure(1, weight=1)

        # Rozmieszczenie w dwóch rzędach: 3 na górze, 3 na dole
        positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]

        for i, key in enumerate(self.BUTTON_ORDER):
            if i < len(positions):
                r, c = positions[i]
                module_data = self.MODULES.get(key)

                if not module_data: continue

                # Dodanie emotikony do nazwy przycisku
                button_text = f"{module_data.get('Emoji', '')} {key if key != 'Tetekror' else 'Wyszukiwarka akordów'}"

                btn_container = ctk.CTkFrame(self.buttons_frame, fg_color="transparent")
                # Ustawienie w odpowiednim rzędzie i kolumnie
                btn_container.grid(row=r, column=c, sticky="nsew", padx=10, pady=10)
                btn_container.columnconfigure(0, weight=1)
                btn_container.rowconfigure(0, weight=1)

                button = ctk.CTkButton(
                    btn_container,
                    text=button_text,  # Użycie tekstu z emotikoną
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

    # ... (logika nawigacji i motywu bez zmian) ...
    def _hide_current_view(self):
        """Ukrywa aktualnie wyświetlany widok i niszczy jego ramkę."""
        if self.current_view_frame:
            if hasattr(self.current_view_object, 'destroy') and callable(self.current_view_object.destroy):
                self.current_view_object.destroy()

            self.current_view_frame.destroy()
            self.current_view_frame = None
            self.current_view_object = None

    def _create_module_frame(self, ViewClass: Type, **kwargs) -> Tuple[ctk.CTkFrame, object]:
        frame = ctk.CTkFrame(self.container, fg_color=self._get_main_bg_color())

        callbacks = {
            "back_to_menu_callback": self.show_menu,
            "back_callback": self.show_menu,
            "back_to_calendar_callback": lambda: self._show_module("Kalendarz"),
            "show_day_callback": self._show_day_from_calendar
        }

        all_args = {**kwargs, **callbacks}
        view_args = all_args.copy()

        # --- filtrowanie argumentów dla różnych widoków ---
        if ViewClass == DayView:
            view_args.pop("back_callback", None)
            view_args.pop("show_day_callback", None)

        elif ViewClass == CalendarView:
            view_args = {
                "show_day_callback": self._show_day_from_calendar,
                "back_callback": self.show_menu,
                **kwargs
            }
            view_args.pop("back_to_menu_callback", None)
            view_args.pop("back_to_calendar_callback", None)

        else:
            view_args = {
                "back_callback": self.show_menu,
                **kwargs
            }
            view_args.pop("back_to_menu_callback", None)
            view_args.pop("back_to_calendar_callback", None)
            view_args.pop("show_day_callback", None)

        # <<< tutaj tworzysz instancję widoku
        view_instance = ViewClass(frame, sidebar=self.sidebar, **view_args)
        view_instance.pack(fill="both", expand=True)
        return frame, view_instance

    def _show_module(self, module_name: str, **kwargs):
        """Główna metoda do przełączania modułów."""
        module_info = self.MODULES.get(module_name)
        if not module_info:
            return

        self.menu_frame.pack_forget()
        self._hide_current_view()

        ViewClass = module_info["View"]
        self.current_view_frame, self.current_view_object = self._create_module_frame(ViewClass, **kwargs)
        self.current_view_frame.pack(fill="both", expand=True)

    def _show_day_from_calendar(self, selected_date: datetime):
        self._show_module("Sesja Dziennna", selected_date=selected_date)

    def show_menu(self):
        """Wracanie do menu głównego i odświeżanie kolorów po zmianie motywu."""

        # 1. Zaktualizuj tła kontenerów
        main_bg = self._get_main_bg_color()
        self.container.configure(fg_color=main_bg)

        if self.menu_frame:
            self.menu_frame.configure(fg_color=main_bg)

        if self.content_frame:
            self.content_frame.configure(fg_color=main_bg)

        if hasattr(self, 'theme_icon_button'):
            self.theme_icon_button.configure(text=self._get_theme_icon())

        # 2. Odśwież statystyki
        self._get_day_view_stats()

        # 3. Usuń starą zawartość i przebuduj menu
        if self.content_frame:
            for widget in self.content_frame.winfo_children():
                widget.destroy()

            self._create_summary_panel(self.content_frame)
            self.buttons_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            self.buttons_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(15, 0))
            self._create_module_buttons()

        # 4. Ukryj aktualny widok i pokaż menu
        self._hide_current_view()
        if self.menu_frame:
            self.menu_frame.pack(fill="both", expand=True)

    def _toggle_theme(self):
        """Przełącza motyw i wymusza odświeżenie UI."""
        if ctk.get_appearance_mode() == "Light":
            ctk.set_appearance_mode("Dark")
            self.current_theme = "Dark"
        else:
            ctk.set_appearance_mode("Light")
            self.current_theme = "Light"

        # Po zmianie motywu odśwież menu
        self.show_menu()

    def _toggle_theme(self):
        """Przełącza motyw i odświeża tylko kolory."""
        if ctk.get_appearance_mode() == "Light":
            ctk.set_appearance_mode("Dark")
            self.current_theme = "Dark"
        else:
            ctk.set_appearance_mode("Light")
            self.current_theme = "Light"

        # NIE wywołuj show_menu tutaj!
        # Odśwież tylko kolory istniejących ramek
        self._refresh_colors()
    def _refresh_colors(self):
        """Aktualizuje kolory wszystkich głównych ramek i przycisków."""
        main_bg = self._get_main_bg_color()
        self.container.configure(fg_color=main_bg)

        if self.menu_frame:
            self.menu_frame.configure(fg_color=main_bg)

        if self.content_frame:
            self.content_frame.configure(fg_color=main_bg)

        if hasattr(self, 'theme_icon_button'):
            self.theme_icon_button.configure(text=self._get_theme_icon())
