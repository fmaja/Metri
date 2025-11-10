# src/metri/views/rhythm_trainer_view.py - POPRAWIONY

import customtkinter as ctk
import random
import time
import threading
from ..logic.midi_player import get_midi_player
from ..data.quiz_results import save_session, get_last_sessions

import matplotlib

matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt  # Needed for twinx


class RhythmTrainer(ctk.CTkFrame):

    def __init__(self, master, back_callback=None, show_main_quiz_callback=None):
        super().__init__(master)
        self.master = master
        self.original_back_callback = back_callback
        self.original_show_main_quiz_callback = show_main_quiz_callback

        self.midi_player = get_midi_player()

        self.BPM = 100
        self.beat_interval_s = 60.0 / self.BPM

        self.rhythms = self._define_rhythms()
        self.current_rhythm = None

        self.is_recording = False
        self.expected_beats_s = []
        self.user_taps_s = []
        self.start_time = 0

        # Session tracking
        self.session_errors_ms = []  # Stores AVG error (ms) for each question
        self.session_categories = {"perfect": 0, "good": 0, "mistake": 0}

        self.root_window = self.winfo_toplevel()
        self.root_window.bind('<space>', self._handle_space_bar)

        self.after_ids = []

        self._create_widgets()
        self.generate_question()

    # ------------------ RHYTHM PATTERNS ------------------
    def _define_rhythms(self):
        # Removed the single-note pattern
        return [
            {"name": "Ósemki", "pattern_units": [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5], "notation": "♪ ♪ ♪ ♪ ♪ ♪ ♪ ♪"},
            {"name": "Rytm z Pauzą", "pattern_units": [0, 1, 2.5, 3], "notation": "♩ ♩ (♪) ♩"},
            {"name": "Synkopa 1", "pattern_units": [0.5, 1.5, 2.5, 3.5], "notation": "(♪) ♪ (♪) ♪ (♪) ♪ (♪) ♪"},
            {"name": "Synkopa 2", "pattern_units": [0, 0.75, 1.5, 2.25, 3], "notation": "♩. (S) ♪ (S) ♪ ♩"},
        ]

    # ------------------ WIDGETS ------------------
    def _create_widgets(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0), padx=10)

        if self.original_show_main_quiz_callback:
            ctk.CTkButton(
                header, text="← Wybór Quizu",
                command=lambda: self.handle_exit(self.original_show_main_quiz_callback),
                width=120, height=35, fg_color="#555", hover_color="#777"
            ).pack(side="left", padx=(0, 10))

        if self.original_back_callback:
            ctk.CTkButton(
                header, text="← Menu Główne",
                command=lambda: self.handle_exit(self.original_back_callback),
                width=120, height=35, fg_color="#555", hover_color="#777"
            ).pack(side="left")

        ctk.CTkLabel(self, text="Trener Rytmu", font=("Arial", 30, "bold"), text_color="#3498DB").pack(pady=(30, 10))

        self.tempo_label = ctk.CTkLabel(self, text="Tempo: 100 BPM | Rytm: ???",
                                        font=("Arial", 22, "bold"), text_color="#E67E22")
        self.tempo_label.pack(pady=(0, 10))

        self.notation_label = ctk.CTkLabel(self, text="[Notacja rytmiczna]", font=("Arial", 36, "bold"),
                                           text_color="#2C3E50", height=100)
        self.notation_label.pack(pady=(10, 20))

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(pady=10)

        self.play_pattern_button = ctk.CTkButton(buttons, text="1. Odtwórz Próbkę Tempa",
                                                 command=self.play_tempo_sample,
                                                 width=220, height=45, fg_color="#3498DB", hover_color="#2980B9")
        self.play_pattern_button.pack(side="left", padx=10)

        self.play_rhythm_button = ctk.CTkButton(buttons, text="2. Odtwórz Rytm (opcjonalne)",
                                                command=self.play_rhythm_pattern,
                                                width=220, height=45, fg_color="#9B59B6", hover_color="#8E44AD",
                                                state="disabled")
        self.play_rhythm_button.pack(side="left", padx=10)

        self.record_button = ctk.CTkButton(buttons, text="3. Start (Odliczanie 4)",
                                           command=self.start_recording_countdown,
                                           width=200, height=45, fg_color="#1ABC9C", hover_color="#16A085",
                                           state="disabled")
        self.record_button.pack(side="left", padx=10)

        self.next_button = ctk.CTkButton(buttons, text="Następny Rytm", command=self.generate_question,
                                         width=180, height=45, fg_color="#E67E22", hover_color="#D35400",
                                         state="disabled")
        self.next_button.pack(side="left", padx=10)

        self.feedback_label = ctk.CTkLabel(self,
                                           text="Naciśnij [1. Odtwórz Próbkę Tempa], by poczuć tempo.",
                                           font=("Arial", 20, "bold"), text_color="#34495E")
        self.feedback_label.pack(pady=(20, 10))

    # ------------------ QUESTION LOGIC ------------------
    def generate_question(self):
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

    # ------------------ PLAYBACK LOGIC ------------------
    def play_tempo_sample(self):
        self.feedback_label.configure(text="Słuchaj próbki tempa...", text_color="#3498DB")
        self.play_pattern_button.configure(state="disabled")
        threading.Thread(target=self._tempo_thread, daemon=True).start()

    def _tempo_thread(self):
        time.sleep(0.3)
        for i in range(4):  # 4 quarter notes
            note = 72 if i == 0 else 60  # High click on 1
            self.midi_player.play_notes([note], duration=0.05)
            time.sleep(self.beat_interval_s)
        self.master.after(100, self._on_tempo_finished)

    def _on_tempo_finished(self):
        self.feedback_label.configure(
            text="Możesz odsłuchać wzór rytmiczny (2) lub od razu zacząć (3).",
            text_color="#9B59B6"
        )
        self.play_pattern_button.configure(state="normal")
        self.play_rhythm_button.configure(state="normal")
        self.record_button.configure(state="normal")

    def play_rhythm_pattern(self):
        self.feedback_label.configure(text="Słuchaj wzoru rytmicznego...", text_color="#9B59B6")
        self.play_rhythm_button.configure(state="disabled")
        self.record_button.configure(state="disabled")
        threading.Thread(target=self._play_rhythm_thread, daemon=True).start()

    def _play_rhythm_thread(self):
        time.sleep(0.3)
        start_play = time.perf_counter()
        for i, beat_time_s in enumerate(self.expected_beats_s):
            wait_time = (start_play + beat_time_s) - time.perf_counter()
            if wait_time > 0:
                time.sleep(wait_time)
            self.midi_player.play_notes([65], duration=0.08)  # Pattern click

        self.master.after(100, self._on_rhythm_finished)

    def _on_rhythm_finished(self):
        self.feedback_label.configure(text="Kiedy jesteś gotowy, kliknij [3. Start].", text_color="#1ABC9C")
        self.play_rhythm_button.configure(state="normal")
        self.record_button.configure(state="normal")

    # ------------------ RECORDING LOGIC ------------------
    def start_recording_countdown(self):
        self.play_pattern_button.configure(state="disabled")
        self.play_rhythm_button.configure(state="disabled")
        self.record_button.configure(state="disabled")
        threading.Thread(target=self._countdown_thread, daemon=True).start()

    def _countdown_thread(self):
        # 4-beat countdown
        for i in range(1, 5):
            self.master.after(0, lambda i=i: self.feedback_label.configure(
                text=f"Start za {5 - i}...", text_color="#3498DB"))

            # POPRAWKA: Usunięcie dźwięku odliczania
            # note = 72 if i == 1 else 60
            # self.midi_player.play_notes([note], duration=0.05)

            time.sleep(self.beat_interval_s)

        self.master.after(50, self.start_actual_recording)

    def start_actual_recording(self):
        self.is_recording = True
        self.user_taps_s = []  # Clear previous taps
        self.start_time = time.perf_counter()  # Precise start

        self.feedback_label.configure(text="Wystukaj wzór rytmiczny teraz!", text_color="#E74C3C")
        self.record_button.configure(text="NAGRYWANIE (Spacja)", fg_color="#E74C3C")

        # Stop recording after 4 beats (one bar)
        recording_duration_ms = int(self.beat_interval_s * 4 * 1000)
        after_id = self.after(recording_duration_ms, self.stop_recording)
        self.after_ids.append(after_id)

    def _handle_space_bar(self, event):
        if self.is_recording:
            tap_time_s = time.perf_counter() - self.start_time
            self.user_taps_s.append(tap_time_s)
            self.midi_player.play_notes([50], duration=0.02)  # User tap feedback
            self.feedback_label.configure(text=f"Tuk! ({len(self.user_taps_s)})", text_color="#34495E")

    def stop_recording(self):
        if not self.is_recording:
            return
        self.is_recording = False
        self.record_button.configure(text="Ocenianie...", state="disabled", fg_color="#1ABC9C")
        self.calculate_score()

    # ------------------ SCORING ------------------
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
            # Log this as a mistake for the session
            self.session_categories["mistake"] += 1
            self.session_errors_ms.append(500)  # Penalize with high error
            return

        # Calculate error for each tap
        errors_ms = [abs((u - e) * 1000) for u, e in zip(self.user_taps_s, self.expected_beats_s)]
        avg_error = sum(errors_ms) / len(errors_ms)

        # Store average error for this question
        self.session_errors_ms.append(avg_error)

        # Categorize this question's result
        if avg_error <= 50:
            msg, color = f"PERFEKCYJNIE! Śr. błąd: {avg_error:.0f} ms", "#2ECC71"
            self.session_categories["perfect"] += 1
        elif avg_error <= 100:
            msg, color = f"DOBRZE! Śr. błąd: {avg_error:.0f} ms", "#F39C12"
            self.session_categories["good"] += 1
        else:
            msg, color = f"POMYŁKA. Śr. błąd: {avg_error:.0f} ms", "#E74C3C"
            self.session_categories["mistake"] += 1

        self.feedback_label.configure(text=msg, text_color=color)
        self.next_button.configure(state="normal")

    # ------------------ EXIT MODAL AND SAVE ------------------
    def handle_exit(self, final_callback):
        """Handle exit, save session, and show modal."""
        # Check if any questions were attempted
        if self.session_errors_ms:
            # Calculate final session average error
            avg_session_error = sum(self.session_errors_ms) / len(self.session_errors_ms)

            # Prepare data packet for saving
            session_data = {
                "avg_error": avg_session_error,
                "categories": self.session_categories
            }
            save_session("rhythm", session_data)

            # Show modal, passing current data
            self.show_results_modal(final_callback, session_data)
        else:
            # No questions answered, just exit
            if final_callback:
                final_callback()

    def show_results_modal(self, final_callback, current_session_data):
        """Show results modal with a DUAL-AXIS chart."""

        modal = ctk.CTkToplevel(self.master)
        modal.title("Wyniki Sesji Rytmicznej")
        modal.resizable(False, False)
        modal.grab_set()
        modal.focus_set()
        modal.transient(self.master)

        modal_width = 700
        modal_height = 550  # Increased height for current results
        screen_width = modal.winfo_screenwidth()
        screen_height = modal.winfo_screenheight()
        x_pos = (screen_width / 2) - (modal_width / 2)
        y_pos = (screen_height / 2) - (modal_height / 2)
        modal.geometry(f"{modal_width}x{modal_height}+{int(x_pos)}+{int(y_pos)}")

        # --- POPRAWKA: Wyświetlanie wyników bieżącej sesji na górze ---
        avg_error = current_session_data.get("avg_error", 0)
        cats = current_session_data.get("categories", {})
        perfect = cats.get("perfect", 0)
        good = cats.get("good", 0)
        mistake = cats.get("mistake", 0)

        ctk.CTkLabel(modal, text="Wynik Ostatniej Sesji", font=("Arial", 20, "bold")).pack(pady=(20, 10))

        stats_frame = ctk.CTkFrame(modal, fg_color="transparent")
        stats_frame.pack()

        ctk.CTkLabel(stats_frame, text=f"Średni Błąd: {avg_error:.0f} ms", font=("Arial", 16, "bold"),
                     text_color="#3498DB").pack(side="left", padx=10)
        ctk.CTkLabel(stats_frame, text=f"Perfekcyjne: {perfect}", font=("Arial", 16), text_color="#2ECC71").pack(
            side="left", padx=10)
        ctk.CTkLabel(stats_frame, text=f"Dobre: {good}", font=("Arial", 16), text_color="#F39C12").pack(side="left",
                                                                                                        padx=10)
        ctk.CTkLabel(stats_frame, text=f"Pomyłki: {mistake}", font=("Arial", 16), text_color="#D35B58").pack(
            side="left", padx=10)

        ctk.CTkLabel(modal, text="Historia Ostatnich 5 Sesji", font=("Arial", 16, "bold")).pack(pady=(20, 5))
        # --- Koniec Poprawki ---

        # Get last 5 sessions
        last_sessions = get_last_sessions("rhythm", max_sessions=5)

        # --- Chart Setup (Light Theme) ---
        fig = Figure(figsize=(6.5, 3.0), dpi=100, facecolor="#EBEBEB")  # Smaller height
        fig.subplots_adjust(right=0.85)  # Make space for the right Y-axis

        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()  # Create a second Y-axis sharing the same X-axis
        ax1.set_facecolor("#FAFAFA")

        # --- Data Preparation ---
        perf_counts, good_counts, mistake_counts, avg_errors_history = [], [], [], []

        for s in last_sessions:
            cats = s.get("categories", {})  # Get categories dict, or empty dict
            perf_counts.append(cats.get("perfect", 0))
            good_counts.append(cats.get("good", 0))
            mistake_counts.append(cats.get("mistake", 0))
            avg_errors_history.append(s.get("avg_error", 0))

        indices = list(range(1, len(last_sessions) + 1))
        width = 0.25  # Bar width

        # --- AXIS 1 (Left): Bar Chart for Categories ---
        ax1.bar([i - width for i in indices], perf_counts, width=width, color="#2ECC71", label="Perfekcyjnie")
        ax1.bar(indices, good_counts, width=width, color="#F39C12", label="Dobrze")
        ax1.bar([i + width for i in indices], mistake_counts, width=width, color="#D35B58", label="Pomyłka")

        ax1.set_ylabel("Liczba odpowiedzi (Słupki)")
        ax1.set_xlabel("Ostatnie 5 sesji")
        ax1.set_xticks(indices)
        ax1.set_xticklabels([f"Sesja {i}" for i in indices])
        ax1.grid(axis="y", linestyle="--", alpha=0.5)

        # --- AXIS 2 (Right): Line Chart for Average Error ---
        ax2.plot(indices, avg_errors_history, color="#3498DB", marker="o", linestyle="-", linewidth=2,
                 label="Średni błąd (ms)")
        ax2.set_ylabel("Średni błąd [ms] (Linia)")

        # Invert Y axis for error (lower is better)
        if avg_errors_history:
            ax2.set_ylim(max(avg_errors_history) + 20, 0)
        else:
            ax2.set_ylim(200, 0)

        # Set colors for text and spines
        for ax in [ax1, ax2]:
            ax.tick_params(colors="black")
            for spine in ax.spines.values():
                spine.set_color("black")
            ax.yaxis.label.set_color("black")
            ax.xaxis.label.set_color("black")
            ax.title.set_color("black")

        # --- Legends ---
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc=0, fontsize="small")

        fig.tight_layout()

        # --- Tkinter Canvas ---
        canvas = FigureCanvasTkAgg(fig, master=modal)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=(0, 10))

        # --- Close Button ---
        def on_modal_close():
            modal.destroy()
            if final_callback:
                final_callback()

        close_button = ctk.CTkButton(modal, text="Zamknij", command=on_modal_close,
                                     font=("Arial", 16, "bold"), fg_color="#555555", hover_color="#777777")
        close_button.pack(pady=(10, 20))
        modal.protocol("WM_DELETE_WINDOW", on_modal_close)

    def safe_after(self, delay_ms, callback):
        after_id = self.after(delay_ms, callback)
        self.after_ids.append(after_id)
        return after_id

    def destroy(self):
        """Safely unbind spacebar and clear all 'after' callbacks."""
        try:
            self.root_window.unbind('<space>')
        except Exception:
            pass

        for after_id in self.after_ids:
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self.after_ids.clear()

        super().destroy()