import customtkinter as ctk
import json
import os
import sys
from datetime import datetime, timedelta
import calendar
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from PIL import Image  # <-- DODANE
from typing import Optional, Callable  # <-- DODANE


class CalendarView(ctk.CTkFrame):
    # Cele
    PRACTICE_GOAL = 30  # min/dzień
    WEEKLY_GOAL = 180  # min/tydzień

    # Kolory główne (DOPASOWANE DO JASNEGO MOTYWU)
    COLOR_GOAL_NOT_MET = "#E5E7E9"  # Light gray
    COLOR_GOAL_MET = "#27AE60"
    COLOR_TODAY = "#3498DB"
    COLOR_ACCENT = "#F39C12"
    COLOR_FOCUS = "#E67E22"

    # Kolory Nagłówka (BIAŁY PASEK)
    HEADER_BG = "#FFFFFF"
    ACCENT_CYAN = "#25b4b6"
    ACCENT_GOLD = "#cca839"
    ACCENT_PURPLE = "#552564"
    ACCENT_LAVENDER = "#9b75a7"

    # Rozmiar komórek dni
    DAY_CELL_SIZE = 40
    DAY_CELL_RADIUS = 20

    def __init__(self, master, sidebar=None, back_callback=None, show_module_callback=None, show_menu_callback=None, show_day_callback: Optional[Callable] = None,
                 **kwargs):  # <-- ZMIENIONA SYGNATURA
        super().__init__(master, **kwargs)

        # Dane
        self.practice_data = self._load_practice_data()
        self.current_date = datetime.now()
        self.current_year = self.current_date.year
        self.current_month = self.current_date.month

        # Cache
        self.week_totals_cache = {}

        # Fokus
        self.focused_day = self.current_date
        self.focused_day_frame = None

        # Callbacki
        self.show_day_callback = show_day_callback
        self.sidebar = sidebar
        self.back_callback = back_callback
        self._show_module = show_module_callback
        self.show_menu = show_menu_callback

        # Budowa UI
        self.configure(fg_color=self._get_main_bg_color())  # <-- Ustawienie tła na dynamiczne
        self._create_widgets()

        # Render
        self._render_calendar()
        self._render_chart()

        # Autowybór dzisiaj
        self.after(120, self._select_today)

        # Ustawienie ikony motywu przy starcie
        if ctk.get_appearance_mode() == "Dark":
            self.theme_icon.configure(text="🌙")
        else:
            self.theme_icon.configure(text="🌞")

    # =========================
    # Dane: load / save / utils
    # =========================
    def _get_data_file_path(self):
        if getattr(sys, 'frozen', False):
            appdata = os.getenv('APPDATA')
            data_dir = os.path.join(appdata, 'Metri')
        else:
            current_file = os.path.abspath(__file__)
            base_dir = os.path.dirname(os.path.dirname(current_file))
            data_dir = os.path.join(base_dir, 'data')

        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, 'practice_data.json')

    def _load_practice_data(self):
        try:
            data_file = self._get_data_file_path()
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _save_practice_data(self):
        try:
            data_file = self._get_data_file_path()
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.practice_data, f, indent=2)
        except Exception:
            pass

    def _get_practice_minutes(self, date_obj):
        return self.practice_data.get(date_obj.strftime("%Y-%m-%d"), 0)

    def _get_week_total(self, date_obj):
        monday = date_obj - timedelta(days=date_obj.weekday())
        week_key = monday.strftime("%Y-%m-%d")
        if week_key in self.week_totals_cache:
            return self.week_totals_cache[week_key]
        total = 0
        for i in range(7):
            d = monday + timedelta(days=i)
            total += self._get_practice_minutes(d)
        total = max(0, total)
        self.week_totals_cache[week_key] = total
        return total

    def _calculate_daily_streak(self):
        streak = 0
        current = self.current_date
        while True:
            minutes = self._get_practice_minutes(current)
            if minutes >= self.PRACTICE_GOAL:
                streak += 1
                current -= timedelta(days=1)
            else:
                break
            if streak > 365:
                break
        return streak

    def _calculate_weekly_streak(self):
        streak = 0
        current = self.current_date
        monday = current - timedelta(days=current.weekday())
        while True:
            week_total = self._get_week_total(monday)
            if week_total >= self.WEEKLY_GOAL:
                streak += 1
                monday -= timedelta(days=7)
            else:
                break
            if streak > 52:
                break
        return streak

    def _get_current_week_progress(self):
        # Gdy brak ćwiczeń w tygodniu => 0/0% bez „magicznych” wartości
        week_total = self._get_week_total(self.current_date)
        if week_total <= 0:
            return 0, 0
        percentage = int((week_total / self.WEEKLY_GOAL) * 100)
        percentage = max(0, min(percentage, 100))
        return percentage, week_total

    # =========================
    # UI layout
    # =========================

    # --- DODANE METODY POMOCNICZE (Theming) ---
    def _get_main_bg_color(self):
        """Zwraca kolor tła głównego okna (ciemny/jasny)."""
        return "#f2f2f2" if ctk.get_appearance_mode() == "Light" else "#1a1a1a"

    def _get_card_bg_color(self):
        """Zwraca kolor tła kart (statystyki, kalendarz, wykres)."""
        return "#FFFFFF" if ctk.get_appearance_mode() == "Light" else "#2c2c2c"

    def _get_inner_card_bg_color(self):
        """Zwraca kolor tła wewnętrznych kart (passa)."""
        return "#F5F5F5" if ctk.get_appearance_mode() == "Light" else "#1e1e1e"

    def _get_text_color(self, main=True):
        """Zwraca kolor tekstu."""
        if main:
            return "#4b4b4b" if ctk.get_appearance_mode() == "Light" else "#ECF0F1"
        return "#7f8c8d" if ctk.get_appearance_mode() == "Light" else "#95a5a6"

    def _go_back(self):
        """Callback dla przycisku powrotu."""
        if self.back_callback:
            self.back_callback()

    def _toggle_theme(self):
        """Przełącza motyw Light/Dark i aktualizuje UI."""
        if ctk.get_appearance_mode() == "Light":
            ctk.set_appearance_mode("Dark")
            self.theme_icon.configure(text="🌙")
        else:
            ctk.set_appearance_mode("Light")
            self.theme_icon.configure(text="🌞")

        # Aktualizuj wszystkie relevantne widżety
        self.configure(fg_color=self._get_main_bg_color())

        # Karty tła
        card_bg = self._get_card_bg_color()
        inner_bg = self._get_inner_card_bg_color()
        text_color = self._get_text_color(main=True)
        secondary_color = self._get_text_color(main=False)

        self.stats_frame.configure(fg_color=card_bg)
        self.calendar_container.configure(fg_color=card_bg)
        self.chart_frame.configure(fg_color=card_bg)
        self.details_panel.configure(fg_color=card_bg)

        # Aktualizacja elementów w statystykach
        for child in self.stats_frame.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                child.configure(fg_color="transparent")
                for grand_child in child.winfo_children():
                    if isinstance(grand_child, ctk.CTkFrame):
                        grand_child.configure(fg_color=inner_bg)
                        for great_grand_child in grand_child.winfo_children():
                            if isinstance(great_grand_child, ctk.CTkLabel):
                                if great_grand_child not in [self.daily_streak_label, self.weekly_streak_label]:
                                    current_text = great_grand_child.cget("text")
                                    if "PASSA" in current_text or "STATYSTYKI" in current_text:
                                        great_grand_child.configure(text_color=secondary_color)
                                    elif "dni" in current_text or "tyg." in current_text:
                                        great_grand_child.configure(text_color=secondary_color)
                                    elif "POSTĘP" in current_text:
                                        great_grand_child.configure(text_color=secondary_color)
                                    else:
                                        great_grand_child.configure(text_color=text_color)

        # Aktualizacja elementów w kalendarzu
        self.month_label.configure(text_color=text_color)

        # Aktualizacja elementów w panelu szczegółów
        for child in self.details_panel.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                child.configure(fg_color="transparent")
                for grand_child in child.winfo_children():
                    if isinstance(grand_child, ctk.CTkFrame) and grand_child.cget("fg_color") != "transparent":
                        grand_child.configure(fg_color=inner_bg)

        self.details_label.configure(text_color=text_color)
        self._render_calendar()
        self._render_chart()
        self._update_stats()

    def _build_header(self):
        """Tworzy nowy, biały nagłówek."""
        self.header = ctk.CTkFrame(self, fg_color=self.HEADER_BG, height=72, corner_radius=12)
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(20, 10))
        self.header.grid_propagate(False)
        self.header.columnconfigure(1, weight=1)
        self.header.rowconfigure(0, weight=1)

        # Lewa strona: Ikona + strzałka powrotu
        left = ctk.CTkFrame(self.header, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=(18, 10))

        # Poprawiona ścieżka do ikony
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.app_icon = ctk.CTkImage(light_image=Image.open(icon_path), size=(60, 65))
            self.menu_button = ctk.CTkButton(
                left,
                image=self.app_icon,
                text="",
                width=60,
                height=65,
                fg_color="transparent",
                command=self.sidebar.toggle  # <<< zawsze ten sam sidebar
            )
            self.menu_button.pack(side="left", anchor="center")

        if self.back_callback:
            ctk.CTkButton(
                left, text="←", width=44, height=44,
                fg_color=self.ACCENT_LAVENDER, hover_color=self.ACCENT_PURPLE,
                command=self._go_back,
                corner_radius=12
            ).pack(side="left", anchor="center", padx=(10, 0))

        # Środek: Tytuł
        title = ctk.CTkLabel(
            self.header, text="Kalendarz Ćwiczeń",  # Tytuł
            font=ctk.CTkFont(size=40, weight="bold"), text_color=self.ACCENT_CYAN
        )
        title.grid(row=0, column=1, sticky="w")

        # Prawa strona: Przycisk do dnia + Przełącznik motywu
        right = ctk.CTkFrame(self.header, fg_color="transparent")
        right.grid(row=0, column=2, sticky="e", padx=(10, 18))

        self.go_to_day_header_button = ctk.CTkButton(
            right, text="Dzisiejsze ćwiczenia→",
            command=self._go_to_selected_day, width=180, height=40,
            font=("Arial", 14, "bold"), fg_color=self.ACCENT_CYAN,
            hover_color="#16A085", corner_radius=10
        )
        self.go_to_day_header_button.pack(side="left", padx=(0, 10))

        self.theme_icon = ctk.CTkButton(
            right, width=44, height=44,
            fg_color=self.ACCENT_GOLD,
            hover_color=self.ACCENT_CYAN,
            text="🌞",
            command=self._toggle_theme,
            corner_radius=12,
            font=ctk.CTkFont(size=22)
        )
        self.theme_icon.pack(side="right", anchor="center")

    # --- KONIEC DODANYCH METOD POMOCNICZYCH ---

    def _create_widgets(self):
        # Siatka główna
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1, uniform="grid")
        self.grid_rowconfigure(2, weight=1, uniform="grid")
        self.grid_columnconfigure(0, weight=1, uniform="grid")
        self.grid_columnconfigure(1, weight=1, uniform="grid")

        # Header (NOWY)
        self._build_header()  # <-- ZASTĄPIENIE STAREGO NAGŁÓWKA

        # Lewo-góra: Statystyki
        self.stats_frame = ctk.CTkFrame(self, fg_color=self._get_card_bg_color(),
                                        corner_radius=14)  # <-- DYNAMICZNE TŁO
        self.stats_frame.grid(row=1, column=0, sticky="nsew", padx=(24, 12), pady=(8, 12))
        self._build_stats(self.stats_frame)

        # Prawo-góra: Kalendarz
        self.calendar_container = ctk.CTkFrame(self, fg_color=self._get_card_bg_color(),
                                               corner_radius=14)  # <-- DYNAMICZNE TŁO
        self.calendar_container.grid(row=1, column=1, sticky="nsew", padx=(12, 24), pady=(8, 12))
        self._build_calendar_container(self.calendar_container)

        # Lewo-dół: Wykres
        self.chart_frame = ctk.CTkFrame(self, fg_color=self._get_card_bg_color(),
                                        corner_radius=14)  # <-- DYNAMICZNE TŁO
        self.chart_frame.grid(row=2, column=0, sticky="nsew", padx=(24, 12), pady=(12, 24))
        self.chart_frame.bind("<Configure>", lambda e: self._render_chart())

        # Prawo-dół: Szczegóły dnia
        self.details_panel = ctk.CTkFrame(self, fg_color=self._get_card_bg_color(),
                                          corner_radius=14)  # <-- DYNAMICZNE TŁO
        self.details_panel.grid(row=2, column=1, sticky="nsew", padx=(12, 24), pady=(12, 24))
        self._build_details_panel(self.details_panel)
        self.details_panel.grid_remove()  # domyślnie ukryty

    # ---------------------
    # Sekcja: Statystyki
    # ---------------------
    def _build_stats(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)

        title_container = ctk.CTkFrame(parent, fg_color="transparent")
        title_container.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        title_container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_container, text="STATYSTYKI",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=self._get_text_color(main=False)  # <-- ZMIANA
        ).grid(row=0, column=0, sticky="w")

        cards = ctk.CTkFrame(parent, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="nsew", padx=16, pady=(8, 8))
        cards.grid_columnconfigure(0, weight=1)
        cards.grid_columnconfigure(1, weight=1)
        cards.grid_rowconfigure(0, weight=1)

        daily = ctk.CTkFrame(cards, fg_color=self._get_inner_card_bg_color(), corner_radius=12)  # <-- DYNAMICZNE TŁO
        daily.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=4)
        ctk.CTkLabel(daily, text="🔥", font=ctk.CTkFont(size=24)).pack(pady=(16, 4))
        ctk.CTkLabel(daily, text="PASSA DZIENNA",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=self._get_text_color(main=False)).pack(pady=(0, 4))  # <-- ZMIANA
        self.daily_streak_label = ctk.CTkLabel(daily, text="0",
                                               font=ctk.CTkFont(size=30, weight="bold"),
                                               text_color=self.COLOR_ACCENT)
        self.daily_streak_label.pack(pady=(0, 4))
        ctk.CTkLabel(daily, text="dni",
                     font=ctk.CTkFont(size=11), text_color=self._get_text_color(main=False)).pack(
            pady=(0, 12))  # <-- ZMIANA

        weekly = ctk.CTkFrame(cards, fg_color=self._get_inner_card_bg_color(), corner_radius=12)  # <-- DYNAMICZNE TŁO
        weekly.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=4)
        ctk.CTkLabel(weekly, text="📅", font=ctk.CTkFont(size=24)).pack(pady=(16, 4))
        ctk.CTkLabel(weekly, text="PASSA TYGODNIOWA",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=self._get_text_color(main=False)).pack(pady=(0, 4))  # <-- ZMIANA
        self.weekly_streak_label = ctk.CTkLabel(weekly, text="0",
                                                font=ctk.CTkFont(size=30, weight="bold"),
                                                text_color=self.COLOR_TODAY)
        self.weekly_streak_label.pack(pady=(0, 4))
        ctk.CTkLabel(weekly, text="tyg.",
                     font=ctk.CTkFont(size=11), text_color=self._get_text_color(main=False)).pack(
            pady=(0, 12))  # <-- ZMIANA

        progress_section = ctk.CTkFrame(parent, fg_color=self._get_inner_card_bg_color(),
                                        corner_radius=12)  # <-- DYNAMICZNE TŁO
        progress_section.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 16))
        ctk.CTkLabel(progress_section, text="POSTĘP TYGODNIOWY",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=self._get_text_color(main=False)).pack(pady=(12, 8))  # <-- ZMIANA

        self.week_progress_bar = ctk.CTkProgressBar(progress_section, height=18, corner_radius=10)
        self.week_progress_bar.pack(fill="x", padx=16)
        self.week_progress_label = ctk.CTkLabel(progress_section, text="",
                                                font=ctk.CTkFont(size=14, weight="bold"),
                                                text_color=self._get_text_color(main=True))  # <-- ZMIANA
        self.week_progress_label.pack(pady=(8, 12))

        self._update_stats()

    # ---------------------
    # Sekcja: Kalendarz
    # ---------------------
    def _build_calendar_container(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)

        nav = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        nav.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        nav.grid_columnconfigure(0, weight=1)
        nav.grid_columnconfigure(1, weight=0)
        nav.grid_columnconfigure(2, weight=0)

        self.month_label = ctk.CTkLabel(nav, text="", font=ctk.CTkFont(size=18, weight="bold"),
                                        text_color=self._get_text_color(main=True))  # <-- ZMIANA
        self.month_label.grid(row=0, column=0, sticky="w")

        prev_button = ctk.CTkButton(
            nav, text="◄", command=self._previous_month, width=40, height=32,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=self.COLOR_TODAY, hover_color="#2980B9", corner_radius=8
        )
        prev_button.grid(row=0, column=1, padx=(8, 6), sticky="e")

        next_button = ctk.CTkButton(
            nav, text="►", command=self._next_month, width=40, height=32,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=self.COLOR_TODAY, hover_color="#2980B9", corner_radius=8
        )
        next_button.grid(row=0, column=2, padx=(6, 0), sticky="e")

        self.calendar_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.calendar_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(4, 16))

    def _render_calendar(self):
        self.week_totals_cache.clear()

        for w in self.calendar_frame.winfo_children():
            w.destroy()
        self.focused_day_frame = None

        month_names = [
            "Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
            "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"
        ]
        self.month_label.configure(text=f"{month_names[self.current_month - 1]} {self.current_year}")

        cal = calendar.monthcalendar(self.current_year, self.current_month)

        # Nagłówki dni
        day_names = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nie"]
        header_row = ctk.CTkFrame(self.calendar_frame, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 6))
        header_bg_color = self._get_inner_card_bg_color()  # <-- DYNAMICZNE TŁO
        header_text_color = self._get_text_color(main=True)  # <-- DYNAMICZNY KOLOR

        for day_name in day_names:
            ctk.CTkLabel(
                header_row, text=day_name, font=("Arial", 12, "bold"),
                width=self.DAY_CELL_SIZE, height=20, fg_color=header_bg_color, corner_radius=6, anchor="center",
                text_color=header_text_color
            ).pack(side="left", padx=3)

        # Wiersze tygodni
        for week in cal:
            row_frame = ctk.CTkFrame(self.calendar_frame, fg_color="transparent")
            row_frame.pack(pady=3)

            week_start_date = None
            for day in week:
                if day == 0:
                    spacer = ctk.CTkFrame(row_frame, fg_color="transparent",
                                          width=self.DAY_CELL_SIZE, height=self.DAY_CELL_SIZE)
                    spacer.pack(side="left", padx=3)
                    continue

                date_obj = datetime(self.current_year, self.current_month, day)
                minutes = self._get_practice_minutes(date_obj)
                if week_start_date is None:
                    week_start_date = date_obj

                is_today = (
                        date_obj.year == self.current_date.year and
                        date_obj.month == self.current_date.month and
                        date_obj.day == self.current_date.day
                )
                is_focused = (
                        self.focused_day is not None and
                        date_obj.year == self.focused_day.year and
                        date_obj.month == self.focused_day.month and
                        date_obj.day == self.focused_day.day
                )

                if is_today:
                    bg_color = self.COLOR_TODAY
                    border_width = 2
                    border_color = "white"
                elif minutes >= self.PRACTICE_GOAL:
                    bg_color = self.COLOR_GOAL_MET
                    border_width = 2 if is_focused else 0
                    border_color = self.COLOR_FOCUS
                else:
                    bg_color = self.COLOR_GOAL_NOT_MET
                    border_width = 2 if is_focused else 0
                    border_color = self.COLOR_FOCUS

                day_frame = ctk.CTkFrame(
                    row_frame, fg_color=bg_color,
                    width=self.DAY_CELL_SIZE, height=self.DAY_CELL_SIZE,
                    corner_radius=self.DAY_CELL_RADIUS,
                    border_width=border_width,
                    border_color=border_color if is_focused else ("white" if is_today else "")
                )
                day_frame.pack(side="left", padx=3)
                day_frame.grid_propagate(False)

                if is_focused:
                    self.focused_day_frame = day_frame

                # Tekst w środku dnia jest ZAWSZE biały lub ciemny w zależności od tła komórki
                text_color = "white" if bg_color in [self.COLOR_TODAY, self.COLOR_GOAL_MET] else self._get_text_color(
                    main=True)

                day_label = ctk.CTkLabel(
                    day_frame, text=str(day), font=("Arial", 14, "bold"), text_color=text_color
                )
                day_label.place(relx=0.5, rely=0.5, anchor="center")

                day_frame.bind("<Button-1>", lambda e, d=date_obj, f=day_frame: self._on_day_click(d, f))
                day_label.bind("<Button-1>", lambda e, d=date_obj, f=day_frame: self._on_day_click(d, f))

            # Indykator tygodnia (✓/✗ + %)
            if week_start_date is not None:
                week_total = self._get_week_total(week_start_date)
                goal_met = week_total >= self.WEEKLY_GOAL
                percentage = 0 if week_total <= 0 else int((week_total / self.WEEKLY_GOAL) * 100)
                percentage = max(0, min(percentage, 100))

                indicator = ctk.CTkFrame(row_frame, fg_color="transparent",
                                         width=self.DAY_CELL_SIZE, height=self.DAY_CELL_SIZE)
                indicator.pack(side="left", padx=(8, 0))

                symbol = "✓" if goal_met else "✗"
                symbol_color = self.COLOR_GOAL_MET if goal_met else "#E74C3C"
                percentage_color = "white" if goal_met and ctk.get_appearance_mode() == "Dark" else symbol_color

                ctk.CTkLabel(indicator, text=symbol, font=("Arial", 16, "bold"),
                             text_color=symbol_color).place(relx=0.5, rely=0.35, anchor="center")
                ctk.CTkLabel(indicator, text=f"{percentage}%",
                             font=("Arial", 10, "bold"),
                             text_color=percentage_color).place(relx=0.5, rely=0.75, anchor="center")

    # ---------------------
    # Sekcja: Wykres
    # ---------------------
    def _render_chart(self):
        for w in self.chart_frame.winfo_children():
            w.destroy()

        # Dane
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        days = []
        minutes_list = []
        for week in cal:
            for day in week:
                if day != 0:
                    d = datetime(self.current_year, self.current_month, day)
                    days.append(day)
                    minutes_list.append(self._get_practice_minutes(d))

        # Rozmiar figury zależny od ramki – zmniejszony do 65%
        self.chart_frame.update_idletasks()
        w_px = max(self.chart_frame.winfo_width(), 300)
        h_px = max(self.chart_frame.winfo_height(), 220)
        dpi = 100

        CHART_SIZE_RATIO = 0.65

        # Kolory Matplotlib zależne od motywu
        if ctk.get_appearance_mode() == "Dark":
            face_color = '#2c2c2c'
            bar_color = '#34495E'
            text_color = 'white'
            grid_color = '#555'
        else:  # Light
            face_color = '#FFFFFF'
            bar_color = '#BDC3C7'
            text_color = '#4b4b4b'
            grid_color = '#ccc'

        fig = Figure(figsize=(w_px * CHART_SIZE_RATIO / dpi, h_px * CHART_SIZE_RATIO / dpi), facecolor='none', dpi=dpi)
        ax = fig.add_subplot(111)

        bars = ax.bar(days, minutes_list, color=bar_color, edgecolor='none', width=0.8)  # <-- DYNAMICZNY KOLOR SŁUPKÓW
        for i, m in enumerate(minutes_list):
            if m >= self.PRACTICE_GOAL:
                bars[i].set_color('#27AE60')  # Cel osiągnięty jest stały

        ax.axhline(y=self.PRACTICE_GOAL, color=self.COLOR_FOCUS, linestyle='--',
                   linewidth=2, label=f'Cel ({self.PRACTICE_GOAL} min)', alpha=0.8)

        # Oś i styl
        ax.set_xlabel('Dni miesiąca', color=text_color, fontsize=10, fontweight='bold')
        ax.set_ylabel('Minuty', color=text_color, fontsize=10, fontweight='bold')
        ax.set_title('Przegląd miesiąca', color=text_color, fontsize=12, fontweight='bold', pad=10)
        ax.set_facecolor(face_color)
        ax.tick_params(colors=text_color, labelsize=9)
        ax.spines['bottom'].set_color(grid_color)
        ax.spines['left'].set_color(grid_color)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.legend(facecolor=face_color, edgecolor=grid_color, labelcolor=text_color,
                  fontsize=9, loc='upper right')
        ax.grid(True, alpha=0.15, color=grid_color, linestyle='-', linewidth=0.5)

        # Dopasowanie marginesów
        fig.subplots_adjust(left=0.15, right=0.9, top=0.90, bottom=0.22)

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg=face_color, highlightthickness=0)

        # WYŚRODKOWANIE WYKRESU: Użycie place z relx/rely i anchor="center"
        widget.place(relx=0.5, rely=0.5, anchor="center")

    # ---------------------
    # Szczegóły dnia
    # ---------------------
    def _build_details_panel(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_rowconfigure(2, weight=0)

        title_container = ctk.CTkFrame(parent, fg_color="transparent")
        title_container.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        ctk.CTkLabel(
            title_container, text="SZCZEGÓŁY DNIA",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=self._get_text_color(main=False)  # <-- ZMIANA
        ).grid(row=0, column=0, sticky="w")

        details_content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        details_content_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        details_content_frame.grid_columnconfigure(0, weight=1)

        self.details_label = ctk.CTkLabel(
            details_content_frame, text="", font=ctk.CTkFont(size=13),
            text_color=self._get_text_color(main=True), justify="left"  # <-- ZMIANA
        )
        self.details_label.grid(row=0, column=0, sticky="nw", pady=(0, 8))

        edit_frame = ctk.CTkFrame(parent, fg_color=self._get_inner_card_bg_color(),
                                  corner_radius=12)  # <-- DYNAMICZNE TŁO
        edit_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))

        edit_inner = ctk.CTkFrame(edit_frame, fg_color="transparent")
        edit_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(edit_inner, text="Zmień czas ćwiczeń:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=self._get_text_color(main=False)).pack(anchor="w", pady=(0, 8))  # <-- ZMIANA

        time_input_frame = ctk.CTkFrame(edit_inner, fg_color="transparent")
        time_input_frame.pack(anchor="w")

        self.minutes_entry = ctk.CTkEntry(time_input_frame, width=100, height=36,
                                          font=ctk.CTkFont(size=14), placeholder_text="0")
        self.minutes_entry.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(time_input_frame, text="minut",
                     font=ctk.CTkFont(size=13), text_color=self._get_text_color(main=True)).pack(side="left", padx=(
        0, 12))  # <-- ZMIANA

        self.save_time_button = ctk.CTkButton(
            time_input_frame, text="Zapisz", command=self._save_practice_time,
            width=90, height=36, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.COLOR_GOAL_MET, hover_color="#229954", corner_radius=18
        )
        self.save_time_button.pack(side="left")

    # =========================
    # Interakcje
    # =========================
    def _previous_month(self):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.focused_day = None
        self.focused_day_frame = None
        self._render_calendar()
        self._render_chart()
        self._update_stats()

    def _next_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.focused_day = None
        self.focused_day_frame = None
        self._render_calendar()
        self._render_chart()
        self._update_stats()

    def _on_day_click(self, date_obj, day_frame):
        if self.focused_day_frame is not None and self.focused_day_frame.winfo_exists():
            is_prev_today = (
                    self.focused_day is not None and
                    self.focused_day.year == self.current_date.year and
                    self.focused_day.month == self.current_date.month and
                    self.focused_day.day == self.current_date.day
            )

            # Wyczyść poprzedni fokus
            if self.focused_day.year == self.current_month and self.focused_day.month == self.current_month:
                if is_prev_today:
                    self.focused_day_frame.configure(border_width=2, border_color="white")
                else:
                    self.focused_day_frame.configure(border_width=0)

        self.focused_day = date_obj
        self.focused_day_frame = day_frame
        day_frame.configure(border_width=2, border_color=self.COLOR_FOCUS)
        self._show_day_details(date_obj)

    def _show_day_details(self, date_obj):
        minutes = self._get_practice_minutes(date_obj)
        week_total = self._get_week_total(date_obj)

        date_str = date_obj.strftime("%d %B %Y")
        day_names_polish = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
        day_name = day_names_polish[date_obj.weekday()]

        if minutes > 0:
            hours = minutes // 60
            mins = minutes % 60
            time_text = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
        else:
            time_text = "Brak ćwiczeń"

        if minutes >= self.PRACTICE_GOAL:
            goal_status = "✓ Cel dzienny osiągnięty"
        else:
            remaining = max(0, self.PRACTICE_GOAL - minutes)
            goal_status = f"✗ Do celu brakuje: {remaining} min"

        week_hours = week_total // 60
        week_mins = week_total % 60
        week_time_text = f"{week_hours}h {week_mins}m" if week_mins > 0 or week_hours > 0 else "0m"

        week_percentage = 0 if week_total <= 0 else int((week_total / self.WEEKLY_GOAL) * 100)
        week_percentage = max(0, min(week_percentage, 100))
        if week_total >= self.WEEKLY_GOAL:
            week_status = f"✓ Cel tygodniowy osiągnięty ({week_percentage}%)"
        else:
            week_status = f"Postęp tygodniowy: {week_percentage}%"

        details_text = f"""📅 {day_name}, {date_str}

⏱️  Czas ćwiczeń: {time_text}
{goal_status}

📊 Tydzień: {week_time_text} ({week_status})"""

        self.details_label.configure(text=details_text)
        self.minutes_entry.delete(0, 'end')
        self.minutes_entry.insert(0, str(minutes))

        self.details_panel.grid()  # pokaż panel (ma stałe miejsce w siatce)

    def _save_practice_time(self):
        if not self.focused_day:
            return
        try:
            minutes = int(self.minutes_entry.get())
            minutes = max(0, min(1440, minutes))
            self.practice_data[self.focused_day.strftime("%Y-%m-%d")] = minutes
            self._save_practice_data()

            # Odśwież wszystko, wyczyść cache
            self.week_totals_cache.clear()
            focused_date = self.focused_day

            self._render_calendar()
            self._render_chart()
            self._update_stats()
            self._show_day_details(focused_date)
        except ValueError:
            pass

    def _update_stats(self):
        daily_streak = self._calculate_daily_streak()
        weekly_streak = self._calculate_weekly_streak()
        week_progress, week_total = self._get_current_week_progress()

        self.daily_streak_label.configure(text=f"{daily_streak}")
        self.weekly_streak_label.configure(text=f"{weekly_streak}")
        self.week_progress_label.configure(text=f"{week_total}/{self.WEEKLY_GOAL} min ({week_progress}%)")

        progress_value = week_progress / 100.0
        self.week_progress_bar.set(progress_value)
        progress_color = self.COLOR_GOAL_MET if week_progress >= 100 else self.COLOR_ACCENT
        self.week_progress_bar.configure(progress_color=progress_color)

    def _go_to_selected_day(self):
        if self.show_day_callback:
            self.show_day_callback(self.current_date)

    def _select_today(self):
        if self.focused_day:
            self._show_day_details(self.focused_day)