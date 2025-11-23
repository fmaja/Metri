# src/metri/views/interval_quiz_view.py - POPRAWIONY

import customtkinter as ctk
import random
from datetime import datetime
from ..logic.music_theory import MusicTheory
from ..logic.midi_player import get_midi_player
from ..data.quiz_results import save_session, get_last_sessions

import matplotlib

matplotlib.use("Agg")  # prevent issues on headless / Tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class IntervalQuizView(ctk.CTkFrame):
    def __init__(self, master, back_callback=None, show_main_quiz_callback=None):
        super().__init__(master)
        self.master = master
        # These are the functions to call AFTER the results modal is closed
        self.original_back_callback = back_callback
        self.original_show_main_quiz_callback = show_main_quiz_callback

        self.midi_player = get_midi_player()
        self.music_theory = MusicTheory()

        self.current_question = None
        self.selected_notes = []

        self.correct_count = 0
        self.wrong_count = 0

        self.after_ids = []  # store after callbacks to cancel on destroy

        self._create_widgets()
        self.generate_question()

    def safe_after(self, delay_ms, callback):
        """Safe after that stores callback ID to cancel later."""
        after_id = self.after(delay_ms, callback)
        self.after_ids.append(after_id)
        return after_id

    def destroy(self):
        # Cancel all pending after callbacks
        for after_id in self.after_ids:
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self.after_ids.clear()
        super().destroy()

    def _create_widgets(self):
        # Header and back buttons
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 0), padx=10)

        # FIXED: Hooked exit buttons to the new handle_exit function
        if self.original_show_main_quiz_callback:
            back_to_quizzes_button = ctk.CTkButton(
                header_frame, text="← Wybór Quizu",
                command=lambda: self.handle_exit(self.original_show_main_quiz_callback),
                width=120, height=35, fg_color="#555555", hover_color="#777777"
            )
            back_to_quizzes_button.pack(side="left", pady=5, padx=(0, 10))

        if self.original_back_callback:
            back_to_menu_button = ctk.CTkButton(
                header_frame, text="← Menu Główne",
                command=lambda: self.handle_exit(self.original_back_callback),
                width=120, height=35, fg_color="#555555", hover_color="#777777"
            )
            back_to_menu_button.pack(side="left", pady=5)

        # Question title
        self.question_label = ctk.CTkLabel(
            self, text="Jaki to interwał?",
            font=("Arial", 32, "bold"), text_color="#34495E"
        )
        self.question_label.pack(pady=(30, 20))

        # Piano area
        self.piano_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.piano_frame.pack(pady=20)
        self._create_piano_keyboard()

        # Feedback label
        self.feedback_label = ctk.CTkLabel(
            self, text="", font=("Arial", 20, "bold"), text_color="#2ECC71"
        )
        self.feedback_label.pack(pady=(10, 20))

        # Action buttons
        action_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_buttons_frame.pack(pady=(0, 20))

        self.play_button = ctk.CTkButton(
            action_buttons_frame, text="Odtwórz Interwał", command=self.play_current_interval,
            width=180, height=45, fg_color="#3498DB", hover_color="#2980B9",
            font=("Arial", 16, "bold")
        )
        self.play_button.pack(side="left", padx=10)

        self.check_button = ctk.CTkButton(
            action_buttons_frame, text="Sprawdź", command=self.check_answer,
            width=150, height=45, fg_color="#1ABC9C", hover_color="#16A085",
            font=("Arial", 16, "bold"), state="disabled"
        )
        self.check_button.pack(side="left", padx=10)

        self.next_button = ctk.CTkButton(
            action_buttons_frame, text="Następne Pytanie", command=self.generate_question,
            width=180, height=45, fg_color="#E67E22", hover_color="#D35400",
            font=("Arial", 16, "bold"), state="disabled"
        )
        self.next_button.pack(side="left", padx=10)

        # REMOVED: The "Zakończ Quiz" button is gone.
        # self.end_quiz_button = ctk.CTkButton(...)

    def _create_piano_keyboard(self):
        # This function remains unchanged
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        octaves = [3, 4, 5]
        self.key_buttons = {}
        row_idx = 0
        for octave in octaves:
            for i, note_name in enumerate(notes):
                full_note_name = f"{note_name}{octave}"
                key_color = "black" if "#" in note_name else "white"
                fg_color = "black" if key_color == "black" else "white"
                text_color = "white" if key_color == "black" else "black"
                hover_color = "#333333" if key_color == "black" else "#DDDDDD"
                btn = ctk.CTkButton(
                    self.piano_frame, text=note_name, width=40, height=80,
                    fg_color=fg_color, hover_color=hover_color, text_color=text_color,
                    border_color="#555555", border_width=1,
                    command=lambda n=full_note_name: self._on_key_press(n)
                )
                btn.grid(row=row_idx, column=i + (12 * (octave - octaves[0])), padx=1, pady=1)
                self.key_buttons[full_note_name] = btn
            row_idx += 2

    def _on_key_press(self, note_name):
        # This function remains unchanged
        if note_name in self.selected_notes:
            self.selected_notes.remove(note_name)
            self.key_buttons[note_name].configure(border_color="#555555", border_width=1)
        else:
            if len(self.selected_notes) < 2:
                self.selected_notes.append(note_name)
                self.key_buttons[note_name].configure(border_color="#2ECC71", border_width=3)
            else:
                old_note = self.selected_notes.pop(0)
                self.key_buttons[old_note].configure(border_color="#555555", border_width=1)
                self.selected_notes.append(note_name)
                self.key_buttons[note_name].configure(border_color="#2ECC71", border_width=3)
        self.check_button.configure(state="normal" if len(self.selected_notes) == 2 else "disabled")

    def generate_question(self):
        # This function remains unchanged (except for debug prints)
        self.feedback_label.configure(text="")
        self.selected_notes = []
        self.check_button.configure(state="disabled")
        self.next_button.configure(state="disabled")

        for btn in self.key_buttons.values():
            btn.configure(border_color="#555555", border_width=1, state="normal")

        all_notes = self.music_theory.get_all_midi_notes(min_octave=3, max_octave=5)
        note1_midi = random.choice(all_notes)
        interval_semitones = random.choice(range(12))
        note2_midi = note1_midi + interval_semitones

        while note2_midi > all_notes[-1] or note1_midi < all_notes[0]:
            note1_midi = random.choice(all_notes)
            note2_midi = note1_midi + interval_semitones

        self.current_question = {
            "note1_midi": note1_midi,
            "note2_midi": note2_midi,
            "correct_interval_semitones": interval_semitones
        }

        # DEBUG: Restore debug prints
        correct_name = self.music_theory.get_interval_name(interval_semitones)
        note1_name = self.music_theory.midi_to_note_name(note1_midi)
        note2_name = self.music_theory.midi_to_note_name(note2_midi)

        print(f"[DEBUG] Poprawna odpowiedź: {correct_name}")
        print(f"[DEBUG] Naciśnij: {note1_name} → {note2_name}")

        self.safe_after(800, self.play_current_interval)

    def play_current_interval(self):
        # This function remains unchanged
        if self.current_question:
            note1 = self.current_question["note1_midi"]
            note2 = self.current_question["note2_midi"]
            self.midi_player.play_notes([note1], duration=0.7)
            self.safe_after(800, lambda: self.midi_player.play_notes([note2], duration=0.7))

    def check_answer(self):
        # This function remains unchanged
        if len(self.selected_notes) != 2:
            return

        user_notes_midi = sorted([self.music_theory.note_name_to_midi(n) for n in self.selected_notes])
        user_interval_semitones = user_notes_midi[1] - user_notes_midi[0]
        is_correct = (user_interval_semitones % 12) == (self.current_question["correct_interval_semitones"] % 12)

        if is_correct:
            self.feedback_label.configure(text="BRAWO!", text_color="#2ECC71")
            border_color = "#2ECC71"
            self.correct_count += 1
        else:
            correct_name = self.music_theory.get_interval_name(self.current_question["correct_interval_semitones"])
            self.feedback_label.configure(text=f"BŁĄD. Poprawny interwał: {correct_name}", text_color="#D35B58")
            border_color = "#D35B58"
            self.wrong_count += 1

        for note_name in self.selected_notes:
            if note_name in self.key_buttons:
                self.key_buttons[note_name].configure(border_color=border_color, border_width=3)
        for btn in self.key_buttons.values():
            btn.configure(state="disabled")
        self.check_button.configure(state="disabled")
        self.next_button.configure(state="normal")

    # --- NEW AND REVISED METHODS ---

    def handle_exit(self, final_callback_func):
        """
        Handles exiting the quiz.
        Saves session and shows results modal only if questions were answered.
        """
        # Check if any questions were answered
        if self.correct_count > 0 or self.wrong_count > 0:

            # --- POPRAWKA: Przekształcenie zmiennych na słownik, aby pasował do save_session(quiz_type, session_data) ---
            session_data = {
                "correct": self.correct_count,
                "wrong": self.wrong_count
            }

            # Save session data first (TERAZ WYWOŁYWANA Z 2 ARGUMENTAMI)
            save_session("interval", session_data)

            # Then show the modal
            self.show_results_modal(final_callback_func)
        else:
            # If no questions answered, just exit
            if final_callback_func:
                final_callback_func()
    def show_results_modal(self, final_callback):
        """
        Displays a modal window with current session stats and a chart of last 5 sessions.
        'final_callback' is the function to run after closing (e.g., go to menu).
        """

        modal = ctk.CTkToplevel(self.master)
        modal.title("Wyniki Sesji")
        modal.resizable(False, False)
        modal.grab_set()  # Make modal block other windows
        modal.focus_set()
        modal.transient(self.master)  # Keep modal on top

        # --- FIX: Center the modal window ---
        modal_width = 600
        modal_height = 500

        screen_width = modal.winfo_screenwidth()
        screen_height = modal.winfo_screenheight()

        x_pos = (screen_width / 2) - (modal_width / 2)
        y_pos = (screen_height / 2) - (modal_height / 2)

        modal.geometry(f"{modal_width}x{modal_height}+{int(x_pos)}+{int(y_pos)}")
        # --- End of Centering Fix ---

        # 1. Current session results
        ctk.CTkLabel(modal, text=f"Wynik obecnej sesji:", font=("Arial", 20, "bold")).pack(pady=(20, 10))
        ctk.CTkLabel(modal, text=f"Poprawne: {self.correct_count}  |  Błędne: {self.wrong_count}",
                     font=("Arial", 18)).pack(pady=(0, 20))

        # 2. Get last 5 sessions for the chart
        last_sessions = get_last_sessions("interval", max_sessions=5)

        # 3. Plot figure (FIX: Light Theme)
        # We use a standard light grey, similar to CTk light mode
        fig_face_color = "#EBEBEB"
        plot_face_color = "#FAFAFA"
        text_color = "black"

        fig = Figure(figsize=(5, 3), dpi=100, facecolor=fig_face_color)
        ax = fig.add_subplot(111)
        ax.set_facecolor(plot_face_color)

        # Set colors for text and spines (dark)
        ax.tick_params(colors=text_color)
        for spine in ax.spines.values():
            spine.set_color(text_color)
        ax.yaxis.label.set_color(text_color)
        ax.xaxis.label.set_color(text_color)
        ax.title.set_color(text_color)
        # --- End of Light Theme Fix ---

        correct_values = [s["correct"] for s in last_sessions]
        wrong_values = [s["wrong"] for s in last_sessions]
        indices = list(range(1, len(last_sessions) + 1))

        # Create bars
        ax.bar([i - 0.15 for i in indices], correct_values, width=0.3, color="#2ECC71", label="Poprawne")
        ax.bar([i + 0.15 for i in indices], wrong_values, width=0.3, color="#D35B58", label="Błędne")

        if correct_values:
            ax.plot(indices, correct_values, color="#27AE60", marker="o", linestyle="-")

        # Chart styling
        ax.set_xticks(indices)
        ax.set_xticklabels([f"Sesja {i}" for i in indices])
        ax.set_ylabel("Liczba odpowiedzi")
        ax.set_title("Ostatnie 5 sesji")
        legend = ax.legend()
        for text in legend.get_texts():
            text.set_color(text_color)  # Light theme legend text
        ax.grid(axis="y", linestyle="--", alpha=0.6)

        fig.tight_layout()  # Ensure labels fit

        canvas = FigureCanvasTkAgg(fig, master=modal)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=(0, 10))

        # 4. Modal close logic
        def on_modal_close():
            modal.destroy()
            if final_callback:
                final_callback()

        # 5. The "Close" button
        close_button = ctk.CTkButton(
            modal,
            text="Zamknij",
            command=on_modal_close,
            font=("Arial", 16, "bold"),
            fg_color="#555555",
            hover_color="#777777"
        )
        close_button.pack(pady=(10, 20))

        # Also trigger on_modal_close if the 'X' button is clicked
        modal.protocol("WM_DELETE_WINDOW", on_modal_close)