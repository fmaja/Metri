# src/metri/views/harmony_quiz_view.py

import customtkinter as ctk
import random
from ..logic.music_theory import MusicTheory
from ..logic.midi_player import get_midi_player


class HarmonyQuizView(ctk.CTkFrame):
    def __init__(self, master, back_callback=None, show_main_quiz_callback=None):
        super().__init__(master)
        self.master = master
        self.back_callback = back_callback
        self.show_main_quiz_callback = show_main_quiz_callback

        self.midi_player = get_midi_player()
        self.music_theory = MusicTheory()

        self.current_question = None
        self.tonic_midi = 60  # Default C4
        self.selected_notes = []

        self._create_widgets()
        self.generate_question()

    def _create_widgets(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 0), padx=10)

        if self.show_main_quiz_callback:
            ctk.CTkButton(
                header_frame, text="← Wybór Quizu", command=self.show_main_quiz_callback,
                width=120, height=35, fg_color="#555555", hover_color="#777777"
            ).pack(side="left", pady=5, padx=(0, 10))

        if self.back_callback:
            ctk.CTkButton(
                header_frame, text="← Menu Główne", command=self.back_callback,
                width=120, height=35, fg_color="#555555", hover_color="#777777"
            ).pack(side="left", pady=5)

        # Title and context
        self.tonic_label = ctk.CTkLabel(
            self,
            text=f"Aktualna Tonacja: {self.music_theory.midi_to_note_name(self.tonic_midi)[:-1]} Dur",
            font=("Arial", 26, "bold"),
            text_color="#ad8d0c",
            fg_color="#ffffff",
            corner_radius=10,
            padx=12, pady=6
        )
        self.tonic_label.pack(pady=(20, 5))

        ctk.CTkLabel(
            self, text="Zbuduj usłyszany akord na pianinie",
            font=("Arial", 28, "bold"), text_color="#9B59B6"
        ).pack(pady=(0, 20))

        # Piano
        self.piano_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.piano_frame.pack(pady=10)
        self._create_piano_keyboard()

        # Feedback
        self.feedback_label = ctk.CTkLabel(self, text="", font=("Arial", 20, "bold"))
        self.feedback_label.pack(pady=(20, 10))

        # Action buttons
        action_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_buttons_frame.pack(pady=10)

        self.play_button = ctk.CTkButton(
            action_buttons_frame, text="Odtwórz Ponownie", command=self.play_sequence,
            width=150, height=40, fg_color="#3498DB", hover_color="#2980B9"
        )
        self.play_button.pack(side="left", padx=10)

        self.check_button = ctk.CTkButton(
            action_buttons_frame, text="Sprawdź Akord", command=self.check_answer,
            width=150, height=40, fg_color="#1ABC9C", hover_color="#16A085",
            font=("Arial", 16, "bold"), state="disabled"
        )
        self.check_button.pack(side="left", padx=10)

        self.next_button = ctk.CTkButton(
            action_buttons_frame, text="Następny Akord", command=self.generate_question,
            width=180, height=40, fg_color="#E67E22", hover_color="#D35400",
            state="disabled"
        )
        self.next_button.pack(side="left", padx=10)

    def _create_piano_keyboard(self):
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        octaves = [3, 4, 5]

        self.key_buttons = {}
        col_idx = 0
        for octave in octaves:
            for note_name in notes:
                full_note_name = f"{note_name}{octave}"

                is_black = "#" in note_name
                fg_color = "black" if is_black else "white"
                text_color = "white" if is_black else "black"
                hover_color = "#333333" if is_black else "#DDDDDD"

                btn = ctk.CTkButton(
                    self.piano_frame, text=note_name.replace('#', 's'),
                    width=40 if not is_black else 30, height=80 if not is_black else 50,
                    fg_color=fg_color, hover_color=hover_color, text_color=text_color,
                    border_color="#555555", border_width=1,
                    command=lambda n=full_note_name: self._on_key_press(n)
                )
                btn.grid(row=0, column=col_idx, padx=1, pady=1)
                col_idx += 1
                self.key_buttons[full_note_name] = btn

    def _on_key_press(self, note_name):
        if note_name in self.selected_notes:
            self.selected_notes.remove(note_name)
            self.key_buttons[note_name].configure(border_color="#555555", border_width=1)
        else:
            if len(self.selected_notes) < 4:
                self.selected_notes.append(note_name)
                self.key_buttons[note_name].configure(border_color="#9B59B6", border_width=3)
            else:
                old_note = self.selected_notes.pop(0)
                self.key_buttons[old_note].configure(border_color="#555555", border_width=1)
                self.selected_notes.append(note_name)
                self.key_buttons[note_name].configure(border_color="#9B59B6", border_width=3)

        self.check_button.configure(state="normal" if len(self.selected_notes) >= 3 else "disabled")

    def generate_question(self):
        """Generate a new harmonic context question."""
        self.feedback_label.configure(text="")

        all_tonics = self.music_theory.get_all_midi_notes(min_octave=3, max_octave=3)
        self.tonic_midi = random.choice([n for n in all_tonics if (n % 12) in [0, 2, 4, 5, 7, 9, 11]])

        self.tonic_label.configure(
            text=f"Aktualna Tonacja: {self.music_theory.midi_to_note_name(self.tonic_midi)[:-1]} Dur"
        )

        degree = random.choice([1, 2, 4, 5, 6])
        self.current_question = self.music_theory.generate_diatonic_chord(self.tonic_midi, degree)

        # Reset piano
        self.selected_notes = []
        for btn in self.key_buttons.values():
            btn.configure(border_color="#555555", border_width=1, state="normal")

        self.check_button.configure(state="disabled")
        self.next_button.configure(state="disabled")
        self.play_button.configure(state="normal")

        # Debug info
        chord_name = self.current_question["display_name"]
        chord_notes = [self.music_theory.midi_to_note_name(n) for n in self.current_question["chord_midi"]]
        tonic_name = self.music_theory.midi_to_note_name(self.tonic_midi)
        print(f"[DEBUG] Tonika: {tonic_name}")
        print(f"[DEBUG] Poprawna odpowiedź: {chord_name}")
        print(f"[DEBUG] Naciśnij nuty: {' + '.join(chord_notes)}")

        # 🎧 Delay playing (UI loads first)
        self.after(800, self.play_sequence)

    def play_sequence(self):
        """Play tonic chord, then the target chord."""
        if self.current_question:
            tonic_chord = self.music_theory.generate_diatonic_chord(self.tonic_midi, 1)
            self.midi_player.play_notes(tonic_chord["chord_midi"], duration=1.0)
            self.after(1200, self.play_current_chord)

    def play_current_chord(self):
        if self.current_question:
            self.midi_player.play_notes(self.current_question["chord_midi"], duration=1.5)

    def check_answer(self):
        """Check user's chord against the correct one."""
        user_notes_midi = sorted([self.music_theory.note_name_to_midi(n) for n in self.selected_notes])
        correct_notes_midi = sorted(self.current_question["chord_midi"])

        is_correct = (set(user_notes_midi) == set(correct_notes_midi))
        correct_name = self.current_question["display_name"]

        for btn in self.key_buttons.values():
            btn.configure(state="disabled")

        if is_correct:
            self.feedback_label.configure(text="DOSKONALE! Prawidłowo zbudowany akord.", text_color="#2ECC71")
            for note_name in self.selected_notes:
                self.key_buttons[note_name].configure(border_color="#2ECC71", border_width=3)
        else:
            self.feedback_label.configure(text=f"BŁĄD. To jest akord {correct_name}.", text_color="#D35B58")

            for note_midi in correct_notes_midi:
                note_name = self.music_theory.midi_to_note_name(note_midi)
                if note_name in self.key_buttons:
                    self.key_buttons[note_name].configure(border_color="#2ECC71", border_width=3)

            for note_name in self.selected_notes:
                note_midi = self.music_theory.note_name_to_midi(note_name)
                if note_midi not in correct_notes_midi:
                    self.key_buttons[note_name].configure(border_color="#D35B58", border_width=3)

        self.check_button.configure(state="disabled")
        self.next_button.configure(state="normal")
