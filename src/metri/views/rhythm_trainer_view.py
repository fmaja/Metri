# src/metri/views/rhythm_trainer_view.py
import customtkinter as ctk
import random
import time
import threading
from ..logic.midi_player import get_midi_player


class RhythmTrainer(ctk.CTkFrame):

    def __init__(self, master, back_callback=None, show_main_quiz_callback=None):
        super().__init__(master)
        self.master = master
        self.back_callback = back_callback
        self.show_main_quiz_callback = show_main_quiz_callback

        self.midi_player = get_midi_player()

        self.BPM = 100
        self.beat_interval_s = 60.0 / self.BPM

        self.rhythms = self._define_rhythms()
        self.current_rhythm = None

        self.is_recording = False
        self.expected_beats_s = []
        self.user_taps_s = []
        self.start_time = 0

        self.root_window = self.winfo_toplevel()
        self.root_window.bind('<space>', self._handle_space_bar)

        self._create_widgets()
        self.generate_question()

    # ------------------ WZORY RYTMÓW ------------------
    def _define_rhythms(self):
        """Lista przykładowych patternów rytmicznych."""
        return [
            {"name": "Ćwierćnuty", "pattern_units": [0, 1, 2, 3], "notation": "♩  ♩  ♩  ♩"},
            {"name": "Ósemki", "pattern_units": [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5], "notation": "♪ ♪ ♪ ♪ ♪ ♪ ♪ ♪"},
            {"name": "Synkopa", "pattern_units": [0, 1.5, 2, 3.5], "notation": "♩ (♪) ♩ (♪)"},
            {"name": "Rytm z Pauzą", "pattern_units": [0, 1, 2.5, 3], "notation": "♩ ♩ (♪) ♩"},
        ]

    # ------------------ INTERFEJS ------------------
    def _create_widgets(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0), padx=10)

        if self.show_main_quiz_callback:
            ctk.CTkButton(
                header, text="← Wybór Quizu", command=self.show_main_quiz_callback,
                width=120, height=35, fg_color="#555", hover_color="#777"
            ).pack(side="left", padx=(0, 10))

        if self.back_callback:
            ctk.CTkButton(
                header, text="← Menu Główne", command=self.back_callback,
                width=120, height=35, fg_color="#555", hover_color="#777"
            ).pack(side="left")

        # Tytuł
        ctk.CTkLabel(
            self, text="Trener Rytmu",
            font=("Arial", 30, "bold"), text_color="#3498DB"
        ).pack(pady=(30, 10))

        # Tempo i rytm
        self.tempo_label = ctk.CTkLabel(
            self, text="Tempo: 100 BPM | Rytm: ???",
            font=("Arial", 22, "bold"), text_color="#E67E22"
        )
        self.tempo_label.pack(pady=(0, 10))

        # Notacja rytmu
        self.notation_label = ctk.CTkLabel(
            self, text="[Notacja rytmiczna]",
            font=("Arial", 36, "bold"), text_color="#2C3E50", height=100
        )
        self.notation_label.pack(pady=(10, 20))

        # Przycisk akcji
        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(pady=10)

        self.play_pattern_button = ctk.CTkButton(
            buttons, text="1. Odtwórz Próbkę Tempa", command=self.play_tempo_sample,
            width=220, height=45, fg_color="#3498DB", hover_color="#2980B9"
        )
        self.play_pattern_button.pack(side="left", padx=10)

        self.play_rhythm_button = ctk.CTkButton(
            buttons, text="2. Odtwórz Rytm (opcjonalne)", command=self.play_rhythm_pattern,
            width=220, height=45, fg_color="#9B59B6", hover_color="#8E44AD",
            state="disabled"
        )
        self.play_rhythm_button.pack(side="left", padx=10)

        self.record_button = ctk.CTkButton(
            buttons, text="3. Start (Odliczanie 4)", command=self.start_recording_countdown,
            width=200, height=45, fg_color="#1ABC9C", hover_color="#16A085",
            state="disabled"
        )
        self.record_button.pack(side="left", padx=10)

        self.next_button = ctk.CTkButton(
            buttons, text="Następny Rytm", command=self.generate_question,
            width=180, height=45, fg_color="#E67E22", hover_color="#D35400",
            state="disabled"
        )
        self.next_button.pack(side="left", padx=10)

        # Informacja zwrotna
        self.feedback_label = ctk.CTkLabel(
            self, text="Naciśnij [1. Odtwórz Próbkę Tempa], by poczuć tempo.",
            font=("Arial", 20, "bold"), text_color="#34495E"
        )
        self.feedback_label.pack(pady=(20, 10))

    # ------------------ LOSOWANIE ------------------
    def generate_question(self):
        """Losuje rytm i tempo."""
        self.BPM = random.choice([70, 80, 90, 100, 110, 120, 130])
        self.beat_interval_s = 60.0 / self.BPM
        self.current_rhythm = random.choice(self.rhythms)

        self.expected_beats_s = [self.beat_interval_s * p for p in self.current_rhythm["pattern_units"]]
        self.user_taps_s = []
        self.is_recording = False

        self.tempo_label.configure(text=f"Tempo: {self.BPM} BPM | Rytm: {self.current_rhythm['name']}")
        self.notation_label.configure(text=self.current_rhythm["notation"])

        self.feedback_label.configure(
            text="Naciśnij [1. Odtwórz Próbkę Tempa], by poczuć tempo.",
            text_color="#34495E"
        )

        self.play_pattern_button.configure(state="normal")
        self.play_rhythm_button.configure(state="disabled")
        self.record_button.configure(state="disabled")
        self.next_button.configure(state="disabled")

    # ------------------ ODTWARZANIE ------------------
    def play_tempo_sample(self):
        """Odtwarza 4 bity metronomu w odpowiednim tempie."""
        self.feedback_label.configure(text="Słuchaj próbki tempa...", text_color="#3498DB")
        self.play_pattern_button.configure(state="disabled")

        threading.Thread(target=self._tempo_thread, daemon=True).start()

    def _tempo_thread(self):
        time.sleep(0.3)
        for i in range(4):
            note = 72 if i == 0 else 60
            self.midi_player.play_notes([note], duration=0.05)
            time.sleep(self.beat_interval_s)
        self.master.after(100, self._on_tempo_finished)

    def _on_tempo_finished(self):
        self.feedback_label.configure(
            text="Możesz odsłuchać wzór rytmiczny (2) lub od razu zacząć (3).",
            text_color="#9B59B6"
        )
        self.play_rhythm_button.configure(state="normal")
        self.record_button.configure(state="normal")

    def play_rhythm_pattern(self):
        """Odtwarza wzór rytmiczny (opcjonalnie)."""
        self.feedback_label.configure(text="Słuchaj wzoru rytmicznego...", text_color="#9B59B6")
        self.play_rhythm_button.configure(state="disabled")
        threading.Thread(target=self._play_rhythm_thread, daemon=True).start()

    def _play_rhythm_thread(self):
        time.sleep(0.3)
        for i, beat_time_s in enumerate(self.expected_beats_s):
            if i > 0:
                time.sleep(self.expected_beats_s[i] - self.expected_beats_s[i - 1])
            self.midi_player.play_notes([65], duration=0.08)
        self.master.after(100, self._on_rhythm_finished)

    def _on_rhythm_finished(self):
        self.feedback_label.configure(
            text="Kiedy jesteś gotowy, kliknij [3. Start].",
            text_color="#1ABC9C"
        )
        self.record_button.configure(state="normal")

    # ------------------ NAGRYWANIE ------------------
    def start_recording_countdown(self):
        """Odliczanie przed nagraniem."""
        self.record_button.configure(state="disabled")
        threading.Thread(target=self._countdown_thread, daemon=True).start()

    def _countdown_thread(self):
        for i in reversed(range(1, 5)):
            self.master.after(0, lambda i=i: self.feedback_label.configure(
                text=f"Start za {i}...", text_color="#3498DB"))
            time.sleep(self.beat_interval_s)
        self.master.after(50, self.start_actual_recording)

    def start_actual_recording(self):
        self.is_recording = True
        self.user_taps_s = []
        self.start_time = time.perf_counter()

        self.feedback_label.configure(text="Wystukaj wzór rytmiczny teraz!", text_color="#E74C3C")
        self.record_button.configure(text="NAGRYWANIE (Spacja)", fg_color="#E74C3C")

        recording_duration_s = self.beat_interval_s * 4
        self.after(int(recording_duration_s * 2000), self.stop_recording)

    def _handle_space_bar(self, event):
        if self.is_recording:
            tap_time_s = time.perf_counter() - self.start_time
            self.user_taps_s.append(tap_time_s)
            self.midi_player.play_notes([50], duration=0.02)
            self.feedback_label.configure(text=f"Tuk! ({len(self.user_taps_s)})", text_color="#34495E")

    def stop_recording(self):
        if not self.is_recording:
            return
        self.is_recording = False
        self.record_button.configure(text="Ocenianie...", state="disabled")
        self.calculate_score()

    # ------------------ OCENA ------------------
    def calculate_score(self):
        if len(self.user_taps_s) == 0:
            self.feedback_label.configure(text="Nie zarejestrowano uderzeń.", text_color="#D35B58")
            self.next_button.configure(state="normal")
            return

        if len(self.user_taps_s) != len(self.expected_beats_s):
            self.feedback_label.configure(
                text=f"Zła liczba uderzeń ({len(self.user_taps_s)} zamiast {len(self.expected_beats_s)}).",
                text_color="#D35B58"
            )
            self.next_button.configure(state="normal")
            return

        errors_ms = [abs((u - e) * 1000) for u, e in zip(self.user_taps_s, self.expected_beats_s)]
        avg_error = sum(errors_ms) / len(errors_ms)

        if avg_error <= 50:
            msg, color = f"PERFEKCYJNIE! Śr. błąd: {avg_error:.0f} ms", "#2ECC71"
        elif avg_error <= 100:
            msg, color = f"DOBRZE! Śr. błąd: {avg_error:.0f} ms", "#F39C12"
        else:
            msg, color = f"POMYŁKA. Śr. błąd: {avg_error:.0f} ms", "#E74C3C"

        self.feedback_label.configure(text=msg, text_color=color)
        self.next_button.configure(state="normal")

    def destroy(self):
        try:
            self.root_window.unbind('<space>')
        except Exception:
            pass
        super().destroy()
