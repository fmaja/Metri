import customtkinter as ctk
from .interwaly import InterwalyView
from .akordy import AkordyView


class TheoryView(ctk.CTkFrame):
    """Theory menu view styled to match the calendar screen.

    Uses a scrollable layout, decorative header lines and dark panels similar
    to `calendar.py` so the visual language is consistent across the app.
    """

    COLOR_HEADER = "#1ABC9C"
    COLOR_PANEL = "#2c2c2c"
    COLOR_CARD = "#1e1e1e"
    # Replaced orange accent with cyan to align with blue/cyan palette
    COLOR_ACCENT = "#00BCD4"

    def __init__(self, master, back_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.back_callback = back_callback
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._create_widgets()

    def _create_widgets(self):
        # Scrollable frame like calendar
        self.scrollable = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.scrollable.columnconfigure(0, weight=1)

        # Back button at the top
        if self.back_callback:
            back_btn = ctk.CTkButton(
                self.scrollable,
                text="← Powrót",
                command=self.back_callback,
                width=130,
                height=40,
                fg_color="#555555",
                hover_color="#777777",
                font=("Arial", 14)
            )
            back_btn.grid(row=0, column=0, pady=(10, 0), sticky="w", padx=40)

        # Title directly on scrollable (no wrapper frame)
        ctk.CTkLabel(
            self.scrollable,
            text="Teoria Muzyki",
            font=("Arial", 36, "bold"),
            text_color=self.COLOR_HEADER
        ).grid(row=1, column=0, pady=(20, 20), sticky="w", padx=40)

        # Removed decorative subtitle lines and label per request

        # Cards frame directly on scrollable
        cards_frame = ctk.CTkFrame(self.scrollable, fg_color="transparent")
        cards_frame.grid(row=2, column=0, sticky="ew", padx=40, pady=(0, 20))
        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)

        # Interwały card
        interval_card = ctk.CTkFrame(cards_frame, fg_color=self.COLOR_PANEL, corner_radius=15)
        interval_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        interval_card.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            interval_card,
            text="🎵",
            font=ctk.CTkFont(size=28)
        ).pack(pady=(18, 6))

        ctk.CTkLabel(
            interval_card,
            text="Interwały",
            font=("Arial", 18, "bold"),
            text_color="#ECF0F1"
        ).pack()

        ctk.CTkLabel(
            interval_card,
            text="Podstawy interwałów — definicje i przykłady.",
            font=("Arial", 12),
            text_color="#95a5a6",
            wraplength=400
        ).pack(padx=12, pady=(6, 12))

        ctk.CTkButton(
            interval_card,
            text="Otwórz",
            command=lambda: self._show_chapter("Interwały"),
            width=140,
            height=40,
            fg_color=self.COLOR_HEADER,
            hover_color="#16A085",
            corner_radius=10
        ).pack(pady=(0, 18))

        # Akordy card
        chords_card = ctk.CTkFrame(cards_frame, fg_color=self.COLOR_PANEL, corner_radius=15)
        chords_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        chords_card.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            chords_card,
            text="🎹",
            font=ctk.CTkFont(size=28)
        ).pack(pady=(18, 6))

        ctk.CTkLabel(
            chords_card,
            text="Akordy",
            font=("Arial", 18, "bold"),
            text_color="#ECF0F1"
        ).pack()

        ctk.CTkLabel(
            chords_card,
            text="Wprowadzenie do akordów i ich budowy.",
            font=("Arial", 12),
            text_color="#95a5a6",
            wraplength=400
        ).pack(padx=12, pady=(6, 12))

        ctk.CTkButton(
            chords_card,
            text="Otwórz",
            command=lambda: self._show_chapter("Akordy"),
            width=140,
            height=40,
            fg_color="#8E44AD",
            hover_color="#7d3c98",
            corner_radius=10
        ).pack(pady=(0, 18))

        # Hidden chapter frame (fills same area when opened)
        self.chapter_frame = ctk.CTkFrame(self.scrollable, fg_color="transparent")

    def _show_chapter(self, chapter_name: str):
        """Show a chapter view."""
        # Hide main scrollable content (all non-chapter-frame children)
        for child in self.scrollable.winfo_children():
            if child is not self.chapter_frame:
                child.grid_forget()

        # Clear chapter frame
        for w in self.chapter_frame.winfo_children():
            w.destroy()

        # If Interwały is requested, embed the dedicated InterwalyView directly with full control
        if chapter_name == "Interwały":
            iv = InterwalyView(self.chapter_frame, on_back=self._back_to_menu)
            iv.pack(fill="both", expand=True)
            self.chapter_frame.grid(row=4, column=0, sticky="nsew")
            return

        # If Akordy is requested, embed the dedicated AkordyView directly with full control
        if chapter_name == "Akordy":
            av = AkordyView(self.chapter_frame, on_back=self._back_to_menu)
            av.pack(fill="both", expand=True)
            self.chapter_frame.grid(row=4, column=0, sticky="nsew")
            return

        # Build chapter header with decorative lines (only for placeholder chapters)
        header = ctk.CTkFrame(self.chapter_frame, fg_color="transparent")
        header.pack(fill="x", pady=(10, 10), padx=40)
        header.columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="━━━",
            font=ctk.CTkFont(size=14),
            text_color=self.COLOR_ACCENT
        ).grid(row=0, column=0, padx=(0, 10))

        ctk.CTkLabel(
            header,
            text=chapter_name,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.COLOR_HEADER
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            header,
            text="━━━",
            font=ctk.CTkFont(size=14),
            text_color=self.COLOR_ACCENT
        ).grid(row=0, column=2, padx=(10, 0))

        # Placeholder content for other chapters (no wrapping panel)
        body = ctk.CTkLabel(
            self.chapter_frame,
            text=("Tutaj znajdą się materiały do nauki dotyczące wybranego rozdziału.\n\n"
                  "To jest widok tymczasowy — dodaj konkretne treści później."),
            font=("Arial", 13),
            text_color="#ECF0F1",
            wraplength=800,
            justify="left",
        )
        body.pack(padx=40, pady=20)

        # Back button
        back_btn = ctk.CTkButton(
            self.chapter_frame,
            text="← Wróć do rozdziałów",
            command=self._back_to_menu,
            width=200,
            height=40,
            fg_color="#555555",
            hover_color="#777777",
            font=("Arial", 12)
        )
        back_btn.pack(pady=(0, 24))

        # Pack chapter frame (place under cards)
        self.chapter_frame.grid(row=4, column=0, sticky="nsew")

    def _back_to_menu(self):
        """Return to the theory menu from a chapter."""
        # Destroy chapter frame children and hide it
        for w in self.chapter_frame.winfo_children():
            w.destroy()
        self.chapter_frame.grid_forget()

        # Recreate the whole view to restore layout
        for child in self.scrollable.winfo_children():
            child.destroy()

        self._create_widgets()

