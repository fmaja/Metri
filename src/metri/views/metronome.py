import customtkinter as ctk
import threading
import time
import os
import pygame
from PIL import Image  # <-- DODANE
from typing import Optional, Callable  # <-- DODANE


# --- LOGIC ---
class MetronomeLogic(threading.Thread):
    def __init__(self, bpm_var, is_running_var, time_signature_var, beat_indicator_callback, click_obj,
                 strong_click_obj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bpm_var = bpm_var
        self.is_running_var = is_running_var
        self.time_signature_var = time_signature_var
        self.beat_indicator_callback = beat_indicator_callback
        self.daemon = True
        self._stop_event = threading.Event()
        self.click_obj = click_obj
        self.strong_click_obj = strong_click_obj

    def stop(self):
        self._stop_event.set()

    def run(self):
        beat_counter = 0
        while not self._stop_event.is_set():
            if not self.is_running_var.get():
                self._stop_event.wait(0.1)
                continue

            bpm = self.bpm_var.get()
            try:
                interval = 60.0 / bpm
            except ZeroDivisionError:
                self._stop_event.wait(0.1)
                continue

            try:
                beats_per_measure = int(self.time_signature_var.get().split('/')[0])
            except:
                beats_per_measure = 4

            beat_counter = (beat_counter % beats_per_measure) + 1
            self.beat_indicator_callback(beat_counter)

            if self.click_obj:
                if beat_counter == 1 and self.strong_click_obj:
                    self.strong_click_obj.play()
                else:
                    self.click_obj.play()

            time.sleep(interval)

        self.beat_indicator_callback(0)


# --- UI ---
class MetronomeView(ctk.CTkFrame):
    # Kolory Metronomu
    MAIN_COLOR = "#3db0ad"
    HOVER_COLOR = "#27AE60"
    ACCENT_COLOR = "#deb536"
    STRONG_BEAT_COLOR = "#E67E22"
    STOP_COLOR = "#E74C3C"
    STOP_HOVER_COLOR = "#C0392B"
    GREEN = "#61be5f"
    BEAT_BUTTON_ACTIVE = "#3498DB"

    # Kolory tła wskaźników
    DISABLED_COLOR_DARK = "#34495E"
    DISABLED_COLOR_LIGHT = "#BDC3C7"

    # Kolory przycisków metrum
    BEAT_BUTTON_NORMAL_DARK = "#5D6D7E"
    BEAT_BUTTON_NORMAL_LIGHT = "#D0D3D4"

    # --- DODANE STAŁE Z INNYCH MODUŁÓW ---
    HEADER_BG = "#FFFFFF"
    ACCENT_CYAN = "#25b4b6"
    ACCENT_GOLD = "#cca839"
    ACCENT_PURPLE = "#552564"
    ACCENT_LAVENDER = "#9b75a7"
    # --- KONIEC DODANYCH STAŁYCH ---

    MAX_BEATS = 12

    def __init__(self, master, sidebar=None, back_callback=None, show_module_callback=None, show_menu_callback=None, **kwargs):  # <-- DODANE back_callback
        super().__init__(master, **kwargs)
        self.sidebar = sidebar
        self.back_callback = back_callback
        self._show_module = show_module_callback
        self.show_menu = show_menu_callback

        # State variables
        self.bpm_var = ctk.IntVar(value=78)
        self.is_running_var = ctk.BooleanVar(value=False)
        self.time_signature_var = ctk.StringVar(value="4/4")
        self.metronome_thread = None

        self.tap_intervals = []
        self.last_tap_time = 0

        self.beat_buttons = []
        self.beat_indicators = []
        self.indicator_frame = None

        # Audio setup
        pygame.mixer.init()
        # Poprawiona ścieżka do assets (zakładając, że assets jest w katalogu nadrzędnym)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.abspath(os.path.join(current_dir, '..', 'assets', 'sounds'))

        self.click_path = os.path.join(assets_dir, 'click.wav')
        self.strong_click_path = os.path.join(assets_dir, 'strong_click.wav')

        try:
            self.click_obj = pygame.mixer.Sound(self.click_path)
            self.strong_click_obj = pygame.mixer.Sound(self.strong_click_path)
        except Exception as e:
            print(f"Błąd ładowania audio metronomu: {e}")
            self.click_obj = None
            self.strong_click_obj = None

        # Konfiguracja UI
        self.configure(fg_color=self._get_main_bg_color())  # <-- DODANE tło
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # --- NOWY NAGŁÓWEK ---
        self._build_header()
        # --- KONIEC NOWEGO NAGŁÓWKA ---

        # Stary nagłówek (usunięty)
        # header_label = ctk.CTkLabel(...)
        # header_label.grid(...)

        main_content = ctk.CTkFrame(self, fg_color="transparent")  # <-- ZMIANA TŁA
        main_content.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        main_content.columnconfigure(0, weight=1)

        # BPM display
        bpm_display_frame = ctk.CTkFrame(main_content, fg_color=self.MAIN_COLOR, corner_radius=15)
        bpm_display_frame.grid(row=0, column=0, pady=(10, 30), padx=50, sticky="ew")

        self.bpm_label = ctk.CTkLabel(
            bpm_display_frame, textvariable=self.bpm_var, font=("Arial", 120, "bold"), text_color="white"
        )
        self.bpm_label.pack(pady=(20, 0))

        bpm_text_label = ctk.CTkLabel(
            bpm_display_frame, text="BPM", font=("Arial", 24), text_color="white"
        )
        bpm_text_label.pack(pady=(0, 20))

        # BPM controls
        bpm_control_frame = ctk.CTkFrame(main_content, fg_color="transparent")  # <-- ZMIANA TŁA
        bpm_control_frame.grid(row=1, column=0, pady=10, sticky="ew", padx=20)
        bpm_control_frame.columnconfigure(1, weight=1)

        self.tap_down_button = ctk.CTkButton(
            bpm_control_frame, text="−", command=lambda: self._adjust_bpm(-1),
            width=50, height=30, font=("Arial", 20, "bold"),
            fg_color=self.MAIN_COLOR, hover_color=self.HOVER_COLOR
        )
        self.tap_down_button.grid(row=0, column=0, padx=(0, 10))

        self.bpm_slider = ctk.CTkSlider(
            bpm_control_frame, from_=40, to=240, variable=self.bpm_var,
            command=self._update_bpm_label, height=30,
            **self._get_slider_colors()  # <-- ZMIANA: Dynamiczne kolory
        )
        self.bpm_slider.grid(row=0, column=1, sticky="ew")
        self.bpm_slider.set(self.bpm_var.get())

        self.tap_up_button = ctk.CTkButton(
            bpm_control_frame, text="+", command=lambda: self._adjust_bpm(1),
            width=50, height=30, font=("Arial", 20, "bold"),
            fg_color=self.MAIN_COLOR, hover_color=self.HOVER_COLOR
        )
        self.tap_up_button.grid(row=0, column=2, padx=(10, 0))

        # Start/Stop button
        self.start_stop_button = ctk.CTkButton(
            main_content, text="START", command=self.toggle_metronome,
            height=60, width=200, font=("Arial", 24, "bold"),
            fg_color=self.GREEN, hover_color=self.HOVER_COLOR, corner_radius=30
        )
        self.start_stop_button.grid(row=2, column=0, pady=(30, 10))

        # Tap tempo button
        self.tap_tempo_button = ctk.CTkButton(
            main_content, text="Wystukaj rytm", command=self._on_tap_tempo,
            height=40, width=150, font=("Arial", 16),
            fg_color="#6e3480", hover_color=self.ACCENT_PURPLE  # Użycie stałej
        )
        self.tap_tempo_button.grid(row=3, column=0, pady=(10, 0))

        # Beat selector buttons
        rhythm_control_frame = ctk.CTkFrame(main_content, fg_color="transparent")  # <-- ZMIANA TŁA
        rhythm_control_frame.grid(row=4, column=0, pady=(20, 0), sticky="ew")
        rhythm_control_frame.columnconfigure(0, weight=1)

        self.rhythm_label = ctk.CTkLabel(  # <-- Zapisanie referencji
            rhythm_control_frame, text="Metrum:", font=("Arial", 16, "bold"),
            text_color=self._get_secondary_text_color()  # <-- Dynamiczny kolor
        )
        self.rhythm_label.grid(row=0, column=0, pady=(0, 10))

        beat_buttons_container = ctk.CTkFrame(rhythm_control_frame, fg_color="transparent")  # <-- ZMIANA TŁA
        beat_buttons_container.grid(row=1, column=0, pady=(0, 10))

        for i in range(1, self.MAX_BEATS + 1):
            beat_value = f"{i}/4"
            button = ctk.CTkButton(
                beat_buttons_container, text=str(i),
                command=lambda val=beat_value: self._set_time_signature(val),
                width=35, height=35, corner_radius=20,
                font=("Arial", 16, "bold"),
                fg_color=self.BEAT_BUTTON_NORMAL_DARK,  # Ustawienie domyślne
                hover_color=self.ACCENT_COLOR,
            )
            button.grid(row=0, column=i - 1, padx=4)
            self.beat_buttons.append(button)

        self._update_beat_buttons_color()

        # Beat indicators
        self.indicator_frame = ctk.CTkFrame(main_content, fg_color="transparent")  # <-- ZMIANA TŁA
        self.indicator_frame.grid(row=5, column=0, pady=(20, 20))
        self.create_beat_indicators()

        # Ustawienie ikony motywu przy starcie
        if ctk.get_appearance_mode() == "Dark":
            self.theme_icon.configure(text="🌙")
        else:
            self.theme_icon.configure(text="🌞")

    # ==========================================================
    # START: DODANE METODY (z QuizView/ChordFinderView)
    # ==========================================================

    def _get_main_bg_color(self):
        """Zwraca kolor tła głównego okna."""
        return "#f2f2f2" if ctk.get_appearance_mode() == "Light" else "#1a1a1a"

    def _get_secondary_text_color(self):
        """Zwraca kolor drugorzędnego tekstu."""
        return "#4b4b4b" if ctk.get_appearance_mode() == "Light" else "#95a5a6"

    def _get_disabled_color(self):
        """Zwraca kolor nieaktywnego wskaźnika."""
        return self.DISABLED_COLOR_LIGHT if ctk.get_appearance_mode() == "Light" else self.DISABLED_COLOR_DARK

    def _get_slider_colors(self):
        """Zwraca kolory dla suwaka BPM."""
        if ctk.get_appearance_mode() == "Light":
            return {
                "fg_color": "#AEB6BF",
                "progress_color": self.MAIN_COLOR,
                "button_color": self.ACCENT_COLOR,
                "button_hover_color": "#cca839"
            }
        else:  # Dark
            return {
                "fg_color": "#333",
                "progress_color": self.MAIN_COLOR,
                "button_color": self.ACCENT_COLOR,
                "button_hover_color": "#cca839"
            }

    def _get_beat_button_colors(self):
        """Zwraca kolory dla przycisków metrum."""
        if ctk.get_appearance_mode() == "Light":
            return {"normal": self.BEAT_BUTTON_NORMAL_LIGHT, "active": self.BEAT_BUTTON_ACTIVE,
                    "hover": self.ACCENT_COLOR}
        else:  # Dark
            return {"normal": self.BEAT_BUTTON_NORMAL_DARK, "active": self.BEAT_BUTTON_ACTIVE,
                    "hover": self.ACCENT_COLOR}

    def _go_back(self):
        """Callback dla przycisku powrotu."""
        self.stop_metronome_thread()  # Zatrzymaj metronom przed powrotem
        if self.back_callback:
            self.back_callback()

    def _build_header(self):
        """Tworzy nowy, biały nagłówek."""
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
            self.header, text="Metronom",  # ZMIENIONY TYTUŁ
            font=ctk.CTkFont(size=40, weight="bold"), text_color=self.ACCENT_CYAN
        )
        title.grid(row=0, column=1)

        # Prawa strona: Przełącznik motywu
        right = ctk.CTkFrame(self.header, fg_color="transparent")
        right.grid(row=0, column=2, sticky="e", padx=(10, 18))
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
        self.rhythm_label.configure(text_color=self._get_secondary_text_color())
        self.bpm_slider.configure(**self._get_slider_colors())
        self._update_beat_buttons_color()
        self.create_beat_indicators()  # Przebuduj wskaźniki z nowym kolorem tła

    # ==========================================================
    # KONIEC: DODANE METODY
    # ==========================================================

    def _update_bpm_label(self, value):
        """Update BPM label."""
        self.bpm_var.set(int(float(value)))

    def _set_time_signature(self, beat_value):
        """Set selected time signature."""
        if self.is_running_var.get():
            return
        self.time_signature_var.set(beat_value)
        self.create_beat_indicators()
        self._update_beat_buttons_color()

    def _update_beat_buttons_color(self):
        """Highlight selected beat button."""
        colors = self._get_beat_button_colors()  # <-- ZMIANA: Pobierz kolory motywu
        current_beat_str = self.time_signature_var.get().split('/')[0]
        for i, button in enumerate(self.beat_buttons):
            color = colors["active"] if str(i + 1) == current_beat_str else colors["normal"]
            button.configure(fg_color=color, hover_color=colors["hover"])

    def create_beat_indicators(self):
        """Create beat indicator dots."""
        for widget in self.indicator_frame.winfo_children():
            widget.destroy()
        self.beat_indicators = []

        try:
            beats_to_show = int(self.time_signature_var.get().split('/')[0])
        except:
            beats_to_show = 4

        for i in range(beats_to_show):
            indicator = ctk.CTkLabel(
                self.indicator_frame, text="", width=20, height=20,
                corner_radius=10, fg_color=self._get_disabled_color()  # <-- ZMIANA: Dynamiczny kolor
            )
            indicator.grid(row=0, column=i, padx=5)
            self.beat_indicators.append(indicator)

    def toggle_metronome(self):
        """Toggle metronome on/off."""
        if self.is_running_var.get():
            self._stop_and_cleanup_thread()
            self._reset_indicators()
            self.start_stop_button.configure(
                text="START", fg_color=self.GREEN, hover_color=self.HOVER_COLOR
            )
        else:
            self.is_running_var.set(True)
            self.start_stop_button.configure(
                text="STOP", fg_color=self.STOP_COLOR, hover_color=self.STOP_HOVER_COLOR
            )
            if self.metronome_thread is None or not self.metronome_thread.is_alive():
                self.metronome_thread = MetronomeLogic(
                    self.bpm_var, self.is_running_var,
                    self.time_signature_var, self.update_beat_indicator,
                    self.click_obj, self.strong_click_obj
                )
                self.metronome_thread.start()

    def _adjust_bpm(self, amount):
        """Increment or decrement BPM."""
        new_bpm = max(40, min(240, self.bpm_var.get() + amount))
        self.bpm_var.set(new_bpm)
        self.bpm_slider.set(new_bpm)

    def _on_tap_tempo(self):
        """Calculate BPM from tapping."""
        current_time = time.time()
        if self.click_obj:
            self.click_obj.play()

        if (current_time - self.last_tap_time) > 2.0:
            self.tap_intervals = []

        self.last_tap_time = current_time
        self.tap_intervals.append(current_time)
        if len(self.tap_intervals) < 2:
            return

        deltas = [self.tap_intervals[i] - self.tap_intervals[i - 1] for i in range(1, len(self.tap_intervals))]
        avg_interval = sum(deltas) / len(deltas)
        new_bpm = max(40, min(240, int(60.0 / avg_interval)))
        self.bpm_var.set(new_bpm)
        self.bpm_slider.set(new_bpm)

    def stop_metronome_thread(self):
        """Stop metronome safely (called from MainScreen)."""
        self._stop_and_cleanup_thread()
        self._reset_indicators()

    def _stop_and_cleanup_thread(self):
        """Stop the thread and reset state."""
        if self.metronome_thread and self.metronome_thread.is_alive():
            self.is_running_var.set(False)
            self.metronome_thread.stop()
            self.metronome_thread.join(timeout=0.2)
            self.metronome_thread = None

        # Sprawdź, czy przycisk istnieje (na wypadek zamknięcia okna)
        if hasattr(self, 'start_stop_button') and self.start_stop_button.winfo_exists():
            self.start_stop_button.configure(
                text="START", fg_color=self.GREEN, hover_color=self.HOVER_COLOR  # Zmieniono na GREEN
            )

    def _reset_indicators(self):
        """Reset beat indicator colors."""
        if not self.winfo_exists():
            return
        disabled_color = self._get_disabled_color()  # <-- ZMIANA
        for indicator in self.beat_indicators:
            indicator.configure(fg_color=disabled_color)

    def update_beat_indicator(self, beat_number):
        """Thread callback for updating beat UI."""
        if not self.winfo_exists():
            return
        if beat_number == 0:
            self.after(0, self._reset_indicators)
        else:
            self.after(0, lambda: self._animate_indicator(beat_number))

    def _animate_indicator(self, beat_number):
        """Highlight the active beat indicator."""
        if not self.winfo_exists():
            return
        self._reset_indicators()

        try:
            beats_per_measure = int(self.time_signature_var.get().split('/')[0])
        except:
            beats_per_measure = 4

        if 1 <= beat_number <= beats_per_measure and beat_number <= len(self.beat_indicators):
            color = self.STRONG_BEAT_COLOR if beat_number == 1 else self.ACCENT_COLOR
            indicator = self.beat_indicators[beat_number - 1]
            indicator.configure(fg_color=color)

            def fade_out():
                disabled_color = self._get_disabled_color()  # <-- ZMIANA
                if self.winfo_exists() and indicator.winfo_exists() and indicator.cget("fg_color") == color:
                    indicator.configure(fg_color=disabled_color)

            self.after(100, fade_out)