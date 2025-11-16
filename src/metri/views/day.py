import customtkinter as ctk
import json
import os
import sys
from datetime import datetime, timedelta
import time
import pygame
from PIL import Image  # <-- DODANE
from typing import Optional, Callable  # <-- DODANE


class DayView(ctk.CTkFrame):
    # Visual settings
    PRACTICE_GOAL = 30  # minutes per day
    WEEKLY_GOAL = 180  # 3 hours per week in minutes

    # Kolory główne (DOPASOWANE DO JASNEGO MOTYWU)
    COLOR_GOAL_NOT_MET = "#34495E"
    COLOR_GOAL_MET = "#27AE60"
    COLOR_TODAY = "#3498DB"
    COLOR_ACCENT = "#E67E22"
    COLOR_METRONOME = "#8E44AD"
    COLOR_METRONOME_ACTIVE = "#9B59B6"

    # Kolory Nagłówka (BIAŁY PASEK, NOWE)
    HEADER_BG = "#FFFFFF"
    ACCENT_CYAN = "#25b4b6"
    ACCENT_GOLD = "#cca839"
    ACCENT_PURPLE = "#552564"
    ACCENT_LAVENDER = "#9b75a7"

    CHECKPOINT_INTERVAL = 60  # Save every 60 seconds (1 minute)

    def __init__(self, master, back_to_menu_callback: Optional[Callable] = None,
                 back_to_calendar_callback: Optional[Callable] = None, selected_date: Optional[datetime] = None,
                 **kwargs):  # <-- UŻYCIE TYPOWANIA
        super().__init__(master, **kwargs)

        # Ustawienie głównego koloru tła (zapewnienie jasnego schematu dla reszty widoków)
        self.configure(fg_color=self._get_main_bg_color())

        # Callbacks
        self.back_to_menu_callback = back_to_menu_callback
        self.back_to_calendar_callback = back_to_calendar_callback

        # Current date (today or selected date)
        self.current_date = selected_date if selected_date else datetime.now()

        # Ustawienie motywu na jasny, aby nowe kolory się zgadzały
        ctk.set_appearance_mode("Light")

        # Stopwatch state
        self.is_running = False
        self.elapsed_seconds = 0
        self.start_time = None
        self.last_checkpoint = time.time()

        # Metronome state
        self.metronome_enabled = False
        self.metronome_bpm = 80
        self.metronome_thread = None
        self.metronome_running = False

        # Audio setup for metronome
        self.mixer_initialized = False
        try:
            pygame.mixer.init()
            self.mixer_initialized = True
            current_dir = os.path.dirname(__file__)
            # Użycie dynamicznej ścieżki
            assets_dir = os.path.abspath(os.path.join(current_dir, '..', 'assets', 'sounds'))

            # W środowisku CTk, '..' często odnosi się do katalogu nadrzędnego projektu,
            # zakładam, że pliki dźwiękowe są na poziomie 'assets/sounds' w stosunku do 'src'.

            click_path = os.path.join(assets_dir, 'click.wav')
            strong_click_path = os.path.join(assets_dir, 'strong_click.wav')

            if os.path.exists(click_path):
                self.click_sound = pygame.mixer.Sound(click_path)
            else:
                self.click_sound = None

            if os.path.exists(strong_click_path):
                self.strong_click_sound = pygame.mixer.Sound(strong_click_path)
            else:
                self.strong_click_sound = None

        except pygame.error:
            self.click_sound = None
            self.strong_click_sound = None
            print("Pygame Mixer Error: Audio disabled.")

        # Load practice data
        self.practice_data = self._load_practice_data()

        # Get initial practice time for today (in seconds)
        today_minutes = self._get_practice_minutes(self.current_date)
        self.elapsed_seconds = today_minutes * 60

        self._create_widgets()

        # Start update loop
        self._update_timer()

    # --- METODY POMOCNICZE DLA KOLORYSTYKI (NOWE) ---
    def _get_main_bg_color(self):
        """Zwraca kolor tła głównego okna (ciemny/jasny)."""
        # Utrzymujemy jasny schemat w tym widoku
        return "#f2f2f2"

    def _get_card_bg_color(self):
        """Zwraca kolor tła kart (stopera, statystyk)."""
        return "#FFFFFF"

    def _get_inner_card_bg_color(self):
        """Zwraca kolor tła wewnętrznych kart (metronom, progress)."""
        return "#F5F5F5"

    def _get_text_color(self, main=True):
        """Zwraca kolor tekstu."""
        return "#4b4b4b" if main else "#7f8c8d"

    # --------------------------------------------------

    def _get_data_file_path(self):
        """Get the path to the practice data file (persistent location for exe)."""
        if getattr(sys, 'frozen', False):
            # Running as exe - use AppData folder
            appdata = os.getenv('APPDATA')
            data_dir = os.path.join(appdata, 'Metri')
        else:
            # Running as script - use project directory
            current_file = os.path.abspath(__file__)
            base_dir = os.path.dirname(os.path.dirname(current_file))
            data_dir = os.path.join(base_dir, 'data')

        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, 'practice_data.json')

    def _load_practice_data(self):
        """Load practice data from JSON file."""
        try:
            data_file = self._get_data_file_path()

            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            print(f"Error loading practice data: {e}")
            return {}

    def _save_practice_data(self):
        """Save practice data to JSON file."""
        try:
            data_file = self._get_data_file_path()

            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.practice_data, f, indent=2)
        except Exception as e:
            print(f"Error saving practice data: {e}")

    def _get_practice_minutes(self, date_obj):
        """Get practice minutes for a specific date."""
        date_str = date_obj.strftime("%Y-%m-%d")
        return self.practice_data.get(date_str, 0)

    def _get_week_total(self, date_obj):
        """Calculate total practice time for the week containing the given date."""
        days_since_monday = date_obj.weekday()
        monday = date_obj - timedelta(days=days_since_monday)

        total = 0
        for i in range(7):
            day = monday + timedelta(days=i)
            total += self._get_practice_minutes(day)

        return total

    def _calculate_daily_streak(self):
        """Calculate current daily streak."""
        streak = 0
        current = datetime.now()

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
        """Calculate current weekly streak."""
        streak = 0
        current = datetime.now()

        days_since_monday = current.weekday()
        monday = current - timedelta(days=days_since_monday)

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
        """Get progress percentage for the current week."""
        week_total = self._get_week_total(datetime.now())
        percentage = int((week_total / self.WEEKLY_GOAL) * 100)
        return min(percentage, 100), week_total

    def _create_widgets(self):
        """Create and layout all widgets."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header with navigation buttons
        self._create_header()

        # Main content frame
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=50, pady=50)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Stopwatch display (left column)
        stopwatch_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        stopwatch_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        stopwatch_container.grid_rowconfigure(0, weight=1)
        stopwatch_container.grid_columnconfigure(0, weight=1)
        self._create_stopwatch(stopwatch_container)

        # Stats panel (right column)
        stats_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        stats_container.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        stats_container.grid_rowconfigure(0, weight=1)
        stats_container.grid_columnconfigure(0, weight=1)
        self._create_stats(stats_container)

    def _create_header(self):
        """Create header with navigation buttons and title. (ZMIENIONY)"""

        self.header = ctk.CTkFrame(self, fg_color=self.HEADER_BG, height=72, corner_radius=12)
        self.header.grid(row=0, column=0, sticky="ew", padx=10, pady=(20, 10))
        self.header.grid_propagate(False)
        self.header.columnconfigure(1, weight=1)
        self.header.rowconfigure(0, weight=1)

        # Lewa strona: Ikona + strzałka powrotu
        left = ctk.CTkFrame(self.header, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=(18, 10))

        # Poprawiona ścieżka do ikony
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(icon_path):
            app_icon = ctk.CTkImage(light_image=Image.open(icon_path), size=(60, 65))
            ctk.CTkLabel(left, image=app_icon, text="").pack(side="left", anchor="center")

        btn_menu = ctk.CTkButton(
            left, text="←", width=44, height=44,
            fg_color=self.ACCENT_LAVENDER, hover_color=self.ACCENT_PURPLE,
            command=self._on_back_to_menu,
            corner_radius=12
        )
        btn_menu.pack(side="left", anchor="center", padx=(10, 0))

        # Środek: Tytuł
        date_str = self.current_date.strftime("%d.%m.%Y")
        title_text = "Dzisiejsza sesja" if self.current_date.date() == datetime.now().date() else f"Sesja {date_str}"

        title = ctk.CTkLabel(
            self.header,
            text=title_text,
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=self.ACCENT_CYAN
        )
        title.grid(row=0, column=1, sticky="w")

        # Prawa strona: Przycisk do kalendarza
        right = ctk.CTkFrame(self.header, fg_color="transparent")
        right.grid(row=0, column=2, sticky="e", padx=(10, 18))

        btn_calendar = ctk.CTkButton(
            right,
            text="Kalendarz →",
            command=self._on_back_to_calendar,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.ACCENT_GOLD,  # Zmieniony kolor
            hover_color="#bba037",
            corner_radius=10
        )
        btn_calendar.pack(side="right", padx=(0, 0))

    def _create_stopwatch(self, parent):
        """Create stopwatch display and controls. (DOPASOWANA KOLORYSTYKA)"""
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        stopwatch_frame = ctk.CTkFrame(parent, fg_color=self._get_card_bg_color(), corner_radius=15)
        stopwatch_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        stopwatch_frame.grid_columnconfigure(0, weight=1)
        stopwatch_frame.grid_rowconfigure(1, weight=1)

        # Title with decorative line
        title_container = ctk.CTkFrame(stopwatch_frame, fg_color="transparent")
        title_container.grid(row=0, column=0, pady=(15, 10), sticky="ew")
        title_container.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            title_container,
            text="━━━",
            font=ctk.CTkFont(size=14),
            text_color=self.COLOR_TODAY
        ).grid(row=0, column=0, padx=(40, 10))

        ctk.CTkLabel(
            title_container,
            text="SESJA ĆWICZEŃ",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self._get_text_color(main=True)
        ).grid(row=0, column=1)

        ctk.CTkLabel(
            title_container,
            text="━━━",
            font=ctk.CTkFont(size=14),
            text_color=self.COLOR_TODAY
        ).grid(row=0, column=2, padx=(10, 40))

        # Time display with shadow effect
        time_container = ctk.CTkFrame(stopwatch_frame, fg_color=self._get_inner_card_bg_color(), corner_radius=10)
        time_container.grid(row=1, column=0, pady=(10, 15), padx=40, sticky="ew")

        self.time_label = ctk.CTkLabel(
            time_container,
            text="00:00:00",
            font=ctk.CTkFont(size=72, weight="bold"),
            text_color=self._get_text_color(main=True)
        )
        self.time_label.pack(pady=20)

        # Control buttons container
        controls_frame = ctk.CTkFrame(stopwatch_frame, fg_color="transparent")
        controls_frame.grid(row=2, column=0, pady=(0, 20))

        # Start/Pause button with icon
        self.toggle_button = ctk.CTkButton(
            controls_frame,
            text="▶  Start",
            command=self._toggle_stopwatch,
            fg_color=self.COLOR_GOAL_MET,
            hover_color="#229954",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=50,
            width=200,
            corner_radius=25
        )
        self.toggle_button.pack(pady=(0, 10))

        # Metronome toggle button
        self.metronome_button = ctk.CTkButton(
            controls_frame,
            text="🎵 Metronom",
            command=self._toggle_metronome_panel,
            fg_color=self.COLOR_METRONOME,
            hover_color=self.COLOR_METRONOME_ACTIVE,
            font=ctk.CTkFont(size=14),
            height=40,
            width=160,
            corner_radius=20
        )
        self.metronome_button.pack()

        # Metronome controls (initially hidden)
        self.metronome_panel = ctk.CTkFrame(stopwatch_frame, fg_color=self._get_inner_card_bg_color(), corner_radius=10)
        self.metronome_panel.grid(row=3, column=0, pady=(10, 20), padx=40, sticky="ew")
        self.metronome_panel.grid_remove()  # Hide initially
        self.metronome_panel.grid_columnconfigure(1, weight=1)

        # BPM Label
        ctk.CTkLabel(
            self.metronome_panel,
            text="Tempo:",
            font=ctk.CTkFont(size=14),
            text_color=self._get_text_color(main=False)
        ).grid(row=0, column=0, padx=(20, 10), pady=15, sticky="w")

        self.bpm_display = ctk.CTkLabel(
            self.metronome_panel,
            text=f"{self.metronome_bpm} BPM",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self._get_text_color(main=True)
        )
        self.bpm_display.grid(row=0, column=1, pady=15)

        # BPM controls
        bpm_controls = ctk.CTkFrame(self.metronome_panel, fg_color="transparent")
        bpm_controls.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 15), sticky="ew")
        bpm_controls.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            bpm_controls,
            text="−",
            command=lambda: self._adjust_metronome_bpm(-5),
            width=40,
            height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#BDC3C7",  # Jasny kolor
            hover_color="#AAB7B8"
        ).grid(row=0, column=0, padx=(0, 10))

        self.bpm_slider = ctk.CTkSlider(
            bpm_controls,
            from_=40,
            to=240,
            number_of_steps=200,
            command=self._on_bpm_slider_change,
            height=20,
            progress_color=self.COLOR_METRONOME,
            button_color=self.COLOR_METRONOME_ACTIVE
        )
        self.bpm_slider.set(self.metronome_bpm)
        self.bpm_slider.grid(row=0, column=1, sticky="ew")

        ctk.CTkButton(
            bpm_controls,
            text="+",
            command=lambda: self._adjust_metronome_bpm(5),
            width=40,
            height=30,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="#BDC3C7",  # Jasny kolor
            hover_color="#AAB7B8"
        ).grid(row=0, column=2, padx=(10, 0))

        # Metronome start/stop button
        self.metronome_toggle = ctk.CTkButton(
            self.metronome_panel,
            text="▶ Włącz metronom",
            command=self._toggle_metronome,
            fg_color="#27AE60",
            hover_color="#229954",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=20
        )
        self.metronome_toggle.grid(row=2, column=0, columnspan=2, pady=(5, 20), padx=20, sticky="ew")

        # Update time display
        self._update_time_display()

    def _create_stats(self, parent):
        """Create statistics display. (DOPASOWANA KOLORYSTYKA)"""
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        stats_frame = ctk.CTkFrame(parent, fg_color=self._get_card_bg_color(), corner_radius=15)
        stats_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)

        # Title with decorative line
        title_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
        title_container.grid(row=0, column=0, columnspan=2, pady=(25, 20), sticky="ew")
        title_container.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            title_container,
            text="━━━",
            font=ctk.CTkFont(size=14),
            text_color=self.COLOR_ACCENT
        ).grid(row=0, column=0, padx=(40, 10))

        ctk.CTkLabel(
            title_container,
            text="STATYSTYKI",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self._get_text_color(main=True)
        ).grid(row=0, column=1)

        ctk.CTkLabel(
            title_container,
            text="━━━",
            font=ctk.CTkFont(size=14),
            text_color=self.COLOR_ACCENT
        ).grid(row=0, column=2, padx=(10, 40))

        # Streak cards container
        streaks_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
        streaks_container.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")
        streaks_container.grid_columnconfigure(0, weight=1)
        streaks_container.grid_columnconfigure(1, weight=1)

        # Daily streak card
        daily_frame = ctk.CTkFrame(streaks_container, fg_color=self._get_inner_card_bg_color(), corner_radius=12)
        daily_frame.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        ctk.CTkLabel(
            daily_frame,
            text="🔥",
            font=ctk.CTkFont(size=28)
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            daily_frame,
            text="PASSA DZIENNA",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self._get_text_color(main=False)
        ).pack(pady=(0, 5))

        daily_streak = self._calculate_daily_streak()
        self.daily_streak_label = ctk.CTkLabel(
            daily_frame,
            text=f"{daily_streak}",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=self.COLOR_ACCENT
        )
        self.daily_streak_label.pack(pady=(0, 5))

        ctk.CTkLabel(
            daily_frame,
            text="dni",
            font=ctk.CTkFont(size=11),
            text_color=self._get_text_color(main=False)
        ).pack(pady=(0, 15))

        # Weekly streak card
        weekly_frame = ctk.CTkFrame(streaks_container, fg_color=self._get_inner_card_bg_color(), corner_radius=12)
        weekly_frame.grid(row=0, column=1, padx=(10, 0), sticky="ew")

        ctk.CTkLabel(
            weekly_frame,
            text="📅",
            font=ctk.CTkFont(size=24)
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            weekly_frame,
            text="PASSA TYGODNIOWA",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self._get_text_color(main=False)
        ).pack(pady=(0, 5))

        weekly_streak = self._calculate_weekly_streak()
        self.weekly_streak_label = ctk.CTkLabel(
            weekly_frame,
            text=f"{weekly_streak}",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=self.COLOR_TODAY
        )
        self.weekly_streak_label.pack(pady=(0, 5))

        ctk.CTkLabel(
            weekly_frame,
            text="tyg.",
            font=ctk.CTkFont(size=11),
            text_color=self._get_text_color(main=False)
        ).pack(pady=(0, 15))

        # Weekly progress section
        progress_section = ctk.CTkFrame(stats_frame, fg_color=self._get_inner_card_bg_color(), corner_radius=12)
        progress_section.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")

        ctk.CTkLabel(
            progress_section,
            text="POSTĘP TYGODNIOWY",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self._get_text_color(main=False)
        ).pack(pady=(15, 10))

        percentage, week_total = self._get_current_week_progress()

        # Progress bar with custom styling
        progress_container = ctk.CTkFrame(progress_section, fg_color="transparent")
        progress_container.pack(fill="x", padx=30, pady=(0, 10))

        progress_color = self.COLOR_GOAL_MET if percentage >= 100 else self.COLOR_ACCENT

        self.progress_bar = ctk.CTkProgressBar(
            progress_container,
            height=25,
            progress_color=progress_color,
            corner_radius=12
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(percentage / 100)

        # Progress text
        self.progress_label = ctk.CTkLabel(
            progress_section,
            text=f"{week_total}/{self.WEEKLY_GOAL} min ({percentage}%)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self._get_text_color(main=True)
        )
        self.progress_label.pack(pady=(10, 20))

    def _update_time_display(self):
        """Update the stopwatch time display."""
        hours = self.elapsed_seconds // 3600
        minutes = (self.elapsed_seconds % 3600) // 60
        seconds = self.elapsed_seconds % 60

        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.time_label.configure(text=time_str)

    def _toggle_stopwatch(self):
        """Toggle stopwatch between running and paused."""
        if self.is_running:
            # Pause
            self.is_running = False
            self.toggle_button.configure(text="▶  Wznów", fg_color=self.COLOR_GOAL_MET, hover_color="#229954")
            self._save_checkpoint()
        else:
            # Start/Resume
            self.is_running = True
            self.start_time = time.time()
            self.toggle_button.configure(text="⏸  Pauza", fg_color=self.COLOR_ACCENT, hover_color="#C96E1B")

    def _toggle_metronome_panel(self):
        """Show/hide metronome controls."""
        if self.metronome_panel.winfo_viewable():
            self.metronome_panel.grid_remove()
            self.metronome_button.configure(fg_color=self.COLOR_METRONOME)
        else:
            self.metronome_panel.grid()
            self.metronome_button.configure(fg_color=self.COLOR_METRONOME_ACTIVE)

    def _toggle_metronome(self):
        """Toggle metronome on/off."""
        if self.metronome_running:
            self._stop_metronome()
            self.metronome_toggle.configure(
                text="▶ Włącz metronom",
                fg_color="#27AE60",
                hover_color="#229954"
            )
        else:
            self._start_metronome()
            self.metronome_toggle.configure(
                text="⏹ Wyłącz metronom",
                fg_color="#E74C3C",
                hover_color="#C0392B"
            )

    def _start_metronome(self):
        """Start the metronome."""
        if not self.click_sound:
            return

        self.metronome_running = True
        self._metronome_tick()

    def _stop_metronome(self):
        """Stop the metronome."""
        self.metronome_running = False

    def _metronome_tick(self):
        """Play metronome tick."""
        if not self.metronome_running:
            return

        if self.click_sound:
            # Prosta implementacja - brak akcentu na beat 1
            self.click_sound.play()

        # Calculate interval in milliseconds
        interval = int((60.0 / self.metronome_bpm) * 1000)

        # Schedule next tick
        self.after(interval, self._metronome_tick)

    def _adjust_metronome_bpm(self, amount):
        """Adjust metronome BPM."""
        self.metronome_bpm = max(40, min(240, self.metronome_bpm + amount))
        self.bpm_slider.set(self.metronome_bpm)
        self.bpm_display.configure(text=f"{self.metronome_bpm} BPM")

    def _on_bpm_slider_change(self, value):
        """Handle BPM slider change."""
        self.metronome_bpm = int(value)
        self.bpm_display.configure(text=f"{self.metronome_bpm} BPM")

    def _update_timer(self):
        """Update timer every 100ms (1s in logic)."""
        if self.is_running:
            # Update elapsed time
            current_time = time.time()
            self.elapsed_seconds += 1
            self._update_time_display()

            # Check if checkpoint needed
            if current_time - self.last_checkpoint >= self.CHECKPOINT_INTERVAL:
                self._save_checkpoint()
                self.last_checkpoint = current_time

        # Schedule next update (co sekundę)
        self.after(1000, self._update_timer)

    def _save_checkpoint(self):
        """Save current practice time to data file."""
        date_str = self.current_date.strftime("%Y-%m-%d")
        minutes = self.elapsed_seconds // 60

        self.practice_data[date_str] = minutes
        self._save_practice_data()

        # Update stats
        self._update_stats()

        # print(f"Checkpoint saved: {minutes} minutes for {date_str}")

    def _update_stats(self):
        """Update all statistics displays."""
        # Update streaks
        daily_streak = self._calculate_daily_streak()
        weekly_streak = self._calculate_weekly_streak()

        self.daily_streak_label.configure(text=f"{daily_streak}")
        self.weekly_streak_label.configure(text=f"{weekly_streak}")

        # Update progress bar and text
        percentage, week_total = self._get_current_week_progress()
        progress_color = self.COLOR_GOAL_MET if percentage >= 100 else self.COLOR_ACCENT

        self.progress_bar.configure(progress_color=progress_color)
        self.progress_bar.set(percentage / 100)
        self.progress_label.configure(text=f"{week_total}/{self.WEEKLY_GOAL} min ({percentage}%)")

    def _on_back_to_menu(self):
        """Handle back to menu button."""
        self._stop_metronome()  # Stop metronome if running
        self._save_checkpoint()  # Save before leaving
        if self.back_to_menu_callback:
            self.back_to_menu_callback()

    def _on_back_to_calendar(self):
        """Handle back to calendar button."""
        self._stop_metronome()  # Stop metronome if running
        self._save_checkpoint()  # Save before leaving
        if self.back_to_calendar_callback:
            self.back_to_calendar_callback()

    def destroy(self):
        """Override destroy to save data when view is destroyed."""
        self._stop_metronome()  # Stop metronome if running
        self._save_checkpoint()
        super().destroy()