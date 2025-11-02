# src/metri/views/quiz.py - FULLY REVISED FILE

import customtkinter as ctk
import os
from PIL import Image
from .interval_quiz_view import IntervalQuizView
from .harmony_quiz_view import HarmonyQuizView
from .rhythm_trainer_view import RhythmTrainer


class QuizView(ctk.CTkFrame):
    def __init__(self, master, back_callback=None):
        super().__init__(master)
        self.master = master
        self.back_callback = back_callback  # Callback to main menu

        # References to sub-quiz views
        self.interval_quiz_view = None
        self.harmony_quiz_view = None
        self.rhythm_trainer_view = None

        HEADER_COLOR = "#00ADB5"

        # Title
        ctk.CTkLabel(
            self,
            text="Wybierz Quiz Muzyczny",
            font=("Arial", 28, "bold"),
            text_color=HEADER_COLOR
        ).pack(pady=(30, 20))

        # --- Button container ---
        button_container = ctk.CTkFrame(self, fg_color="transparent")
        button_container.pack(pady=10, padx=50, fill="x")

        # Interval Quiz Button
        self._create_quiz_button(
            button_container,
            text="🎵 Trening Słuchu: Interwały",
            command=self.start_interval_quiz,
            description="Rozpoznawanie odległości między dźwiękami.",
            color="#E67E22"
        ).pack(fill="x", pady=10)

        # Harmony Quiz Button
        self._create_quiz_button(
            button_container,
            text="🎸 Harmonia: Funkcje Akordów",
            command=self.start_harmony_quiz,
            description="Rozpoznawanie roli akordów w kontekście tonalnym.",
            color="#9B59B6"
        ).pack(fill="x", pady=10)

        # Rhythm Trainer Button
        self._create_quiz_button(
            button_container,
            text="🥁 Trener Rytmu: Dokładność Metryczna",
            command=self.start_rhythm_trainer,
            description="Wystukiwanie rytmów i pomiar precyzji (spacja).",
            color="#3498DB"
        ).pack(fill="x", pady=10)

        # Back Button
        if self.back_callback:
            ctk.CTkButton(
                self,
                text="← Powrót do menu",
                command=self.back_callback,
                width=200,
                fg_color="#555555",
                hover_color="#777777"
            ).pack(pady=(30, 20))

    def _create_quiz_button(self, master, text, command, description, color):
        """Helper function to create styled quiz buttons."""

        button_frame = ctk.CTkFrame(master, fg_color=color, corner_radius=10)
        button_frame.columnconfigure(0, weight=1)

        main_button = ctk.CTkButton(
            button_frame,
            text=text,
            command=command,
            height=60,
            corner_radius=10,
            fg_color=None,  # Inherit color from button_frame
            hover_color=None,  # Inherit color from button_frame
            font=("Arial", 18, "bold"),
            anchor="w",
            text_color="white"
        )
        main_button.grid(row=0, column=0, sticky="ew", padx=15, pady=(5, 0))

        ctk.CTkLabel(
            button_frame,
            text=description,
            font=("Arial", 12),
            text_color="#F2F4F4",
            anchor="w"
        ).grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 5))

        return button_frame

    # --- View Switching Logic ---

    def _show_sub_quiz(self, ViewClass):
        """Generic method to hide this view and show a sub-quiz view."""
        self._hide_sub_quiz()
        self.pack_forget()

        common_params = {
            "master": self.master,
            "back_callback": self.back_callback,
            "show_main_quiz_callback": self._show_main_quiz_view
        }

        if ViewClass == IntervalQuizView:
            self.interval_quiz_view = ViewClass(**common_params)
            self.interval_quiz_view.pack(fill="both", expand=True)

        elif ViewClass == HarmonyQuizView:
            self.harmony_quiz_view = ViewClass(**common_params)
            self.harmony_quiz_view.pack(fill="both", expand=True)

        elif ViewClass == RhythmTrainer:
            self.rhythm_trainer_view = ViewClass(**common_params)
            self.rhythm_trainer_view.pack(fill="both", expand=True)

    def _hide_sub_quiz(self):
        """Hides and destroys all sub-quiz views."""
        views = [self.interval_quiz_view, self.harmony_quiz_view, self.rhythm_trainer_view]
        attrs = ["interval_quiz_view", "harmony_quiz_view", "rhythm_trainer_view"]

        for i, view in enumerate(views):
            if view:
                view.pack_forget()
                # Safely destroy the view
                try:
                    view.destroy()
                except Exception as e:
                    print(f"Error destroying view {attrs[i]}: {e}")
                setattr(self, attrs[i], None)

    def _show_main_quiz_view(self):
        """Callback for sub-quizzes to return to this (QuizView) screen."""
        self._hide_sub_quiz()
        self.pack(fill="both", expand=True)

    # --- Button Commands ---

    def start_interval_quiz(self):
        self._show_sub_quiz(IntervalQuizView)

    def start_harmony_quiz(self):
        self._show_sub_quiz(HarmonyQuizView)

    def start_rhythm_trainer(self):
        self._show_sub_quiz(RhythmTrainer)