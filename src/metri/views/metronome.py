import customtkinter as ctk
import threading
import time
import os
import pygame


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
    MAIN_COLOR = "#3db0ad"
    HOVER_COLOR = "#27AE60"
    ACCENT_COLOR = "#deb536"
    STRONG_BEAT_COLOR = "#E67E22"
    STOP_COLOR = "#E74C3C"
    STOP_HOVER_COLOR = "#C0392B"
    DISABLED_COLOR = "#34495E"
    BACKGROUND_COLOR = "transparent"
    GREEN = "#61be5f"

    BEAT_BUTTON_NORMAL = "#5D6D7E"
    BEAT_BUTTON_ACTIVE = "#3498DB"

    MAX_BEATS = 12

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

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
        current_dir = os.path.dirname(__file__)
        assets_dir = os.path.abspath(os.path.join(current_dir, '..', 'assets', 'sounds'))
        self.click_path = os.path.join(assets_dir, 'click.wav')
        self.strong_click_path = os.path.join(assets_dir, 'strong_click.wav')

        try:
            self.click_obj = pygame.mixer.Sound(self.click_path)
            self.strong_click_obj = pygame.mixer.Sound(self.strong_click_path)
        except Exception as e:
            print(f"Audio loading error: {e}")
            self.click_obj = None
            self.strong_click_obj = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Header
        header_label = ctk.CTkLabel(
            self, text="Metronom", font=("Arial", 36, "bold"), text_color="#1ABC9C"
        )
        header_label.grid(row=0, column=0, pady=(20, 10), sticky="n")

        main_content = ctk.CTkFrame(self, fg_color=self.BACKGROUND_COLOR)
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
        bpm_control_frame = ctk.CTkFrame(main_content, fg_color=self.BACKGROUND_COLOR)
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
            fg_color="#AEB6BF", progress_color=self.MAIN_COLOR,
            button_color=self.ACCENT_COLOR, button_hover_color="#cca839"
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
            fg_color="#6e3480", hover_color="#552564"
        )
        self.tap_tempo_button.grid(row=3, column=0, pady=(10, 0))

        # Beat selector buttons
        rhythm_control_frame = ctk.CTkFrame(main_content, fg_color=self.BACKGROUND_COLOR)
        rhythm_control_frame.grid(row=4, column=0, pady=(20, 0), sticky="ew")
        rhythm_control_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            rhythm_control_frame, text="Metrum:", font=("Arial", 16, "bold")
        ).grid(row=0, column=0, pady=(0, 10))

        beat_buttons_container = ctk.CTkFrame(rhythm_control_frame, fg_color=self.BACKGROUND_COLOR)
        beat_buttons_container.grid(row=1, column=0, pady=(0, 10))

        for i in range(1, self.MAX_BEATS + 1):
            beat_value = f"{i}/4"
            button = ctk.CTkButton(
                beat_buttons_container, text=str(i),
                command=lambda val=beat_value: self._set_time_signature(val),
                width=35, height=35, corner_radius=20,
                font=("Arial", 16, "bold"),
                fg_color=self.BEAT_BUTTON_NORMAL, hover_color=self.ACCENT_COLOR,
            )
            button.grid(row=0, column=i - 1, padx=4)
            self.beat_buttons.append(button)

        self._update_beat_buttons_color()

        # Beat indicators
        self.indicator_frame = ctk.CTkFrame(main_content, fg_color=self.BACKGROUND_COLOR)
        self.indicator_frame.grid(row=5, column=0, pady=(20, 20))
        self.create_beat_indicators()

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
        current_beat_str = self.time_signature_var.get().split('/')[0]
        for i, button in enumerate(self.beat_buttons):
            color = self.BEAT_BUTTON_ACTIVE if str(i + 1) == current_beat_str else self.BEAT_BUTTON_NORMAL
            button.configure(fg_color=color)

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
                corner_radius=10, fg_color=self.DISABLED_COLOR
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
        if self.start_stop_button:
            self.start_stop_button.configure(
                text="START", fg_color=self.MAIN_COLOR, hover_color=self.HOVER_COLOR
            )

    def _reset_indicators(self):
        """Reset beat indicator colors."""
        if not self.winfo_exists():
            return
        for indicator in self.beat_indicators:
            indicator.configure(fg_color=self.DISABLED_COLOR)

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
                if self.winfo_exists() and indicator.winfo_exists() and indicator.cget("fg_color") == color:
                    indicator.configure(fg_color=self.DISABLED_COLOR)

            self.after(100, fade_out)
