
import customtkinter as ctk
import json
import os
import sys
from datetime import datetime, timedelta
import calendar
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class CalendarView(ctk.CTkFrame):
    # Cele
    PRACTICE_GOAL = 30   # min/dzień
    WEEKLY_GOAL = 180    # min/tydzień

    # Kolory
    COLOR_GOAL_NOT_MET = "#34495E"
    COLOR_GOAL_MET = "#27AE60"
    COLOR_TODAY = "#3498DB"
    COLOR_HEADER = "#1ABC9C"
    COLOR_ACCENT = "#E67E22"
    COLOR_FOCUS = "#F39C12"

    # Rozmiar komórek dni
    DAY_CELL_SIZE = 40
    DAY_CELL_RADIUS = 20

    def __init__(self, master, show_day_callback=None, back_callback=None, **kwargs):
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
        self.back_callback = back_callback

        # Budowa UI
        self._create_widgets()

        # Render
        self._render_calendar()
        self._render_chart()

        # Autowybór dzisiaj
        self.after(120, self._select_today)

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
    def _create_widgets(self):
        # Siatka główna
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1, uniform="grid")
        self.grid_rowconfigure(2, weight=1, uniform="grid")
        self.grid_columnconfigure(0, weight=1, uniform="grid")
        self.grid_columnconfigure(1, weight=1, uniform="grid")

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=64)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(18, 8))
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=0)
        header_frame.grid_columnconfigure(1, weight=1)
        header_frame.grid_columnconfigure(2, weight=0)

        if self.back_callback:
            back_button = ctk.CTkButton(
                header_frame, text="← Powrót", command=self.back_callback,
                width=120, height=40, fg_color="#555555", hover_color="#777777",
                font=("Arial", 14)
            )
            back_button.grid(row=0, column=0, padx=(0, 18), sticky="w")

        title_label = ctk.CTkLabel(
            header_frame, text="Kalendarz Ćwiczeń",
            font=("Arial", 28, "bold"), text_color=self.COLOR_HEADER
        )
        title_label.grid(row=0, column=1, sticky="w")

        if self.show_day_callback:
            self.go_to_day_header_button = ctk.CTkButton(
                header_frame, text="Dzisiejsze ćwiczenia→",
                command=self._go_to_selected_day, width=180, height=40,
                font=("Arial", 14, "bold"), fg_color=self.COLOR_HEADER,
                hover_color="#16A085", corner_radius=10
            )
            self.go_to_day_header_button.grid(row=0, column=2, padx=(18, 0), sticky="e")

        # Lewo-góra: Statystyki
        self.stats_frame = ctk.CTkFrame(self, fg_color="#2c2c2c", corner_radius=14)
        self.stats_frame.grid(row=1, column=0, sticky="nsew", padx=(24, 12), pady=(8, 12))
        self._build_stats(self.stats_frame)

        # Prawo-góra: Kalendarz
        self.calendar_container = ctk.CTkFrame(self, fg_color="#2c2c2c", corner_radius=14)
        self.calendar_container.grid(row=1, column=1, sticky="nsew", padx=(12, 24), pady=(8, 12))
        self._build_calendar_container(self.calendar_container)

        # Lewo-dół: Wykres
        self.chart_frame = ctk.CTkFrame(self, fg_color="#2c2c2c", corner_radius=14)
        self.chart_frame.grid(row=2, column=0, sticky="nsew", padx=(24, 12), pady=(12, 24))
        self.chart_frame.bind("<Configure>", lambda e: self._render_chart())

        # Prawo-dół: Szczegóły dnia
        self.details_panel = ctk.CTkFrame(self, fg_color="#2c2c2c", corner_radius=14)
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
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#ECF0F1"
        ).grid(row=0, column=0, sticky="w")

        cards = ctk.CTkFrame(parent, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="nsew", padx=16, pady=(8, 8))
        cards.grid_columnconfigure(0, weight=1)
        cards.grid_columnconfigure(1, weight=1)
        cards.grid_rowconfigure(0, weight=1)

        daily = ctk.CTkFrame(cards, fg_color="#1e1e1e", corner_radius=12)
        daily.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=4)
        ctk.CTkLabel(daily, text="🔥", font=ctk.CTkFont(size=24)).pack(pady=(16, 4))
        ctk.CTkLabel(daily, text="PASSA DZIENNA",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#95a5a6").pack(pady=(0, 4))
        self.daily_streak_label = ctk.CTkLabel(daily, text="0",
                                               font=ctk.CTkFont(size=30, weight="bold"),
                                               text_color=self.COLOR_ACCENT)
        self.daily_streak_label.pack(pady=(0, 4))
        ctk.CTkLabel(daily, text="dni",
                     font=ctk.CTkFont(size=11), text_color="#7f8c8d").pack(pady=(0, 12))

        weekly = ctk.CTkFrame(cards, fg_color="#1e1e1e", corner_radius=12)
        weekly.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=4)
        ctk.CTkLabel(weekly, text="📅", font=ctk.CTkFont(size=24)).pack(pady=(16, 4))
        ctk.CTkLabel(weekly, text="PASSA TYGODNIOWA",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#95a5a6").pack(pady=(0, 4))
        self.weekly_streak_label = ctk.CTkLabel(weekly, text="0",
                                                font=ctk.CTkFont(size=30, weight="bold"),
                                                text_color=self.COLOR_TODAY)
        self.weekly_streak_label.pack(pady=(0, 4))
        ctk.CTkLabel(weekly, text="tyg.",
                     font=ctk.CTkFont(size=11), text_color="#7f8c8d").pack(pady=(0, 12))

        progress_section = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=12)
        progress_section.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 16))
        ctk.CTkLabel(progress_section, text="POSTĘP TYGODNIOWY",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#95a5a6").pack(pady=(12, 8))

        self.week_progress_bar = ctk.CTkProgressBar(progress_section, height=18, corner_radius=10)
        self.week_progress_bar.pack(fill="x", padx=16)
        self.week_progress_label = ctk.CTkLabel(progress_section, text="",
                                                font=ctk.CTkFont(size=14, weight="bold"),
                                                text_color="#ECF0F1")
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

        self.month_label = ctk.CTkLabel(nav, text="", font=ctk.CTkFont(size=18, weight="bold"), text_color="#ECF0F1")
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
        for day_name in day_names:
            ctk.CTkLabel(
                header_row, text=day_name, font=("Arial", 12, "bold"),
                width=self.DAY_CELL_SIZE, height=20, fg_color="#1e1e1e", corner_radius=6, anchor="center"
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

                day_label = ctk.CTkLabel(
                    day_frame, text=str(day), font=("Arial", 14, "bold"), text_color="white"
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

                ctk.CTkLabel(indicator, text=symbol, font=("Arial", 16, "bold"),
                             text_color=symbol_color).place(relx=0.5, rely=0.35, anchor="center")
                ctk.CTkLabel(indicator, text=f"{percentage}%",
                             font=("Arial", 10, "bold"),
                             text_color="white" if goal_met else "#E74C3C").place(relx=0.5, rely=0.75, anchor="center")

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

        # ZMNIEJSZENIE WYKRESU: Zmniejszenie współczynników figsize do 0.65
        # Wykres będzie miał około 65% szerokości i wysokości ramki.
        CHART_SIZE_RATIO = 0.65

        fig = Figure(figsize=(w_px * CHART_SIZE_RATIO / dpi, h_px * CHART_SIZE_RATIO / dpi), facecolor='none', dpi=dpi)
        ax = fig.add_subplot(111)

        bars = ax.bar(days, minutes_list, color='#34495E', edgecolor='none', width=0.8)
        for i, m in enumerate(minutes_list):
            if m >= self.PRACTICE_GOAL:
                bars[i].set_color('#27AE60')

        ax.axhline(y=self.PRACTICE_GOAL, color=self.COLOR_FOCUS, linestyle='--',
                   linewidth=2, label=f'Cel ({self.PRACTICE_GOAL} min)', alpha=0.8)

        # Oś i styl
        ax.set_xlabel('Dni miesiąca', color='white', fontsize=10, fontweight='bold')
        ax.set_ylabel('Minuty', color='white', fontsize=10, fontweight='bold')
        ax.set_title('Przegląd miesiąca', color='white', fontsize=12, fontweight='bold', pad=10)
        ax.set_facecolor('#1e1e1e')
        ax.tick_params(colors='white', labelsize=9)
        ax.spines['bottom'].set_color('#555')
        ax.spines['left'].set_color('#555')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.legend(facecolor='#2B2B2B', edgecolor='#555', labelcolor='white',
                  fontsize=9, loc='upper right')
        ax.grid(True, alpha=0.15, color='white', linestyle='-', linewidth=0.5)

        # Dopasowanie marginesów
        fig.subplots_adjust(left=0.15, right=0.9, top=0.90, bottom=0.22)

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg='#2B2B2B', highlightthickness=0)

        # WYŚRODKOWANIE WYKRESU: Użycie place z relx/rely i anchor="center"
        # Upewnij się, że ramka chart_frame jest poprawnie skonfigurowana w metodzie _create_widgets
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
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#ECF0F1"
        ).grid(row=0, column=0, sticky="w")

        details_content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        details_content_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        details_content_frame.grid_columnconfigure(0, weight=1)

        self.details_label = ctk.CTkLabel(
            details_content_frame, text="", font=ctk.CTkFont(size=13),
            text_color="#ECF0F1", justify="left"
        )
        self.details_label.grid(row=0, column=0, sticky="nw", pady=(0, 8))

        edit_frame = ctk.CTkFrame(parent, fg_color="#1e1e1e", corner_radius=12)
        edit_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))

        edit_inner = ctk.CTkFrame(edit_frame, fg_color="transparent")
        edit_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(edit_inner, text="Zmień czas ćwiczeń:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#95a5a6").pack(anchor="w", pady=(0, 8))

        time_input_frame = ctk.CTkFrame(edit_inner, fg_color="transparent")
        time_input_frame.pack(anchor="w")

        self.minutes_entry = ctk.CTkEntry(time_input_frame, width=100, height=36,
                                          font=ctk.CTkFont(size=14), placeholder_text="0")
        self.minutes_entry.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(time_input_frame, text="minut",
                     font=ctk.CTkFont(size=13), text_color="#ECF0F1").pack(side="left", padx=(0, 12))

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
        week_time_text = f"{week_hours}h {week_mins}m" if week_mins > 0 else f"{week_hours}h"

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


