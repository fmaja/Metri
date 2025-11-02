# src/metri/views/interval_quiz_view.py

import customtkinter as ctk
import random
from ..logic.music_theory import MusicTheory
from ..logic.midi_player import get_midi_player


class IntervalQuizView(ctk.CTkFrame):
    def __init__(self, master, back_callback=None, show_main_quiz_callback=None):
        super().__init__(master)
        self.master = master
        self.back_callback = back_callback
        self.show_main_quiz_callback = show_main_quiz_callback

        self.midi_player = get_midi_player()
        self.music_theory = MusicTheory()

        self.current_question = None
        self.selected_notes = []

        self._create_widgets()
        self.generate_question()

    def _create_widgets(self):
        # Header and back buttons
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 0), padx=10)

        if self.show_main_quiz_callback:
            back_to_quizzes_button = ctk.CTkButton(
                header_frame, text="← Wybór Quizu", command=self.show_main_quiz_callback,
                width=120, height=35, fg_color="#555555", hover_color="#777777"
            )
            back_to_quizzes_button.pack(side="left", pady=5, padx=(0, 10))

        if self.back_callback:
            back_to_menu_button = ctk.CTkButton(
                header_frame, text="← Menu Główne", command=self.back_callback,
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

    def _create_piano_keyboard(self):
        # Simplified keyboard (C3 to C5)
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
        """Handle piano key selection."""
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
        """Generate a new interval question."""
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

        correct_name = self.music_theory.get_interval_name(interval_semitones)
        note1_name = self.music_theory.midi_to_note_name(note1_midi)
        note2_name = self.music_theory.midi_to_note_name(note2_midi)

        print(f"[DEBUG] Poprawna odpowiedź: {correct_name}")
        print(f"[DEBUG] Naciśnij: {note1_name} → {note2_name}")

        self.after(800, self.play_current_interval)

    def play_current_interval(self):
        """Play the current interval (sequentially)."""
        if self.current_question:
            note1 = self.current_question["note1_midi"]
            note2 = self.current_question["note2_midi"]
            # Play sequentially (easier to hear)
            self.midi_player.play_notes([note1], duration=0.7)
            self.after(800, lambda: self.midi_player.play_notes([note2], duration=0.7))

    def check_answer(self):
        """Check the user's answer from the piano."""
        if len(self.selected_notes) != 2:
            return

        user_notes_midi = sorted([self.music_theory.note_name_to_midi(n) for n in self.selected_notes])
        user_interval_semitones = user_notes_midi[1] - user_notes_midi[0]

        is_correct = (user_interval_semitones % 12) == (self.current_question["correct_interval_semitones"] % 12)

        if is_correct:
            self.feedback_label.configure(text="BRAWO!", text_color="#2ECC71")
            border_color = "#2ECC71"
        else:
            correct_name = self.music_theory.get_interval_name(self.current_question["correct_interval_semitones"])
            self.feedback_label.configure(text=f"BŁĄD. Poprawny interwał: {correct_name}", text_color="#D35B58")
            border_color = "#D35B58"

        for note_name in self.selected_notes:
            if note_name in self.key_buttons:
                self.key_buttons[note_name].configure(border_color=border_color, border_width=3)

        for btn in self.key_buttons.values():
            btn.configure(state="disabled")
        self.check_button.configure(state="disabled")
        self.next_button.configure(state="normal")
