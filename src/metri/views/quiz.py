import customtkinter as ctk
from typing import Optional, Callable
import os
from PIL import Image

# Import sub-quiz views
try:
    from .interval_quiz_view import IntervalQuizView
except Exception:
    IntervalQuizView = None

try:
    from .harmony_quiz_view import HarmonyQuizView
except Exception:
    HarmonyQuizView = None

try:
    from .rhythm_trainer_view import RhythmTrainer
except Exception:
    RhythmTrainer = None

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class CardButton(ctk.CTkFrame):
    """Optional: reuse CardButton for quiz buttons if needed"""
    def __init__(self, master, title: str, description: str, icon_text: str = "🎵",
                 command: Optional[Callable] = None, accent: str = "#00BCD4", **kwargs):
        super().__init__(master, **kwargs)
        self.command = command
        self.accent = accent
        self.default_bg = self._get_bg_color()
        self.configure(fg_color=self.default_bg, corner_radius=20, border_width=0)
        self.columnconfigure(0, weight=1)

        self.icon_label = ctk.CTkLabel(self, text=icon_text, font=ctk.CTkFont(size=40))
        self.icon_label.grid(row=0, column=0, pady=(40, 15))

        self.title_label = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=30, weight="bold"),
                                        text_color=self._title_color())
        self.title_label.grid(row=1, column=0, pady=(0,6))

        self.desc_label = ctk.CTkLabel(self, text=description, font=ctk.CTkFont(size=13),
                                       text_color=self._desc_color(), wraplength=520, justify="center")
        self.desc_label.grid(row=2, column=0, padx=18, pady=(0,40))

        # Bind click + hover
        for w in [self, self.icon_label, self.title_label, self.desc_label]:
            w.bind("<Button-1>", lambda e: self._on_click())
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def _get_bg_color(self):
        return "#ffffff" if ctk.get_appearance_mode() == "Light" else "#1e1e1e"
    def _title_color(self):
        return "#0b0b0b" if ctk.get_appearance_mode() == "Light" else "#ECF0F1"
    def _desc_color(self):
        return "#4b4b4b" if ctk.get_appearance_mode() == "Light" else "#95a5a6"
    def _on_enter(self, event=None): self.configure(border_width=2, border_color=self.accent)
    def _on_leave(self, event=None): self.configure(border_width=0)
    def _on_click(self):
        if callable(self.command): self.command()


class QuizView(ctk.CTkFrame):
    HEADER_BG = "#FFFFFF"
    ACCENT_CYAN = "#25b4b6"
    ACCENT_GOLD = "#cca839"
    ACCENT_PURPLE = "#552564"
    ACCENT_GREEN = "#61be5f"
    ACCENT_LAVENDER = "#9b75a7"

    def __init__(self, master, back_callback: Optional[Callable] = None, **kwargs):
        super().__init__(master, fg_color=self._get_main_bg_color(), **kwargs)
        self.back_callback = back_callback

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Sub-quiz references
        self.interval_quiz_view = None
        self.harmony_quiz_view = None
        self.rhythm_trainer_view = None

        # Build header and main area
        self._build_header()
        self._build_main_area()

        self.bind("<Configure>", self._on_resize)

    def _get_main_bg_color(self):
        return "#f2f2f2" if ctk.get_appearance_mode() == "Light" else "#1a1a1a"
    def _get_subtitle_color(self):
        return self.ACCENT_GREEN if ctk.get_appearance_mode() == "Light" else "#b2b2b2"

    # ================= HEADER =================
    def _build_header(self):
        self.header = ctk.CTkFrame(self, fg_color=self.HEADER_BG, height=72, corner_radius=12)
        self.header.grid(row=0, column=0, sticky="ew", padx=10, pady=(20,10))
        self.header.grid_propagate(False)
        self.header.columnconfigure(1, weight=1)
        self.header.rowconfigure(0, weight=1)

        # Left: Icon + back arrow
        left = ctk.CTkFrame(self.header, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=(18,10))
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets","icon.png")
        if os.path.exists(icon_path):
            app_icon = ctk.CTkImage(light_image=Image.open(icon_path), size=(60,65))
            ctk.CTkLabel(left, image=app_icon, text="").pack(side="left", anchor="center")

        if self.back_callback:
            ctk.CTkButton(
                left, text="←", width=44, height=44,
                fg_color=self.ACCENT_LAVENDER, hover_color=self.ACCENT_PURPLE,
                command=self.back_callback, corner_radius=12
            ).pack(side="left", anchor="center", padx=(10,0))

        # Center: title like TheoryView
        title = ctk.CTkLabel(
            self.header, text="Quiz Muzyczny",
            font=ctk.CTkFont(size=40, weight="bold"), text_color=self.ACCENT_CYAN
        )
        title.grid(row=0, column=1)

        # Right: theme toggle
        right = ctk.CTkFrame(self.header, fg_color="transparent")
        right.grid(row=0, column=2, sticky="e", padx=(10,18))
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
        if ctk.get_appearance_mode()=="Light":
            ctk.set_appearance_mode("Dark")
            self.theme_icon.configure(text="🌙")
        else:
            ctk.set_appearance_mode("Light")
            self.theme_icon.configure(text="🌞")
        self.configure(fg_color=self._get_main_bg_color())
        self.subtitle.configure(text_color=self._get_subtitle_color())

    # ================= MAIN AREA =================
    def _build_main_area(self):
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=1,column=0,sticky="nsew", padx=10,pady=(6,12))
        self.main.columnconfigure(0,weight=1)

        # Subtitle
        self.subtitle = ctk.CTkLabel(
            self.main,
            text="Wybierz quiz aby rozpocząć",
            font=ctk.CTkFont(size=14),
            text_color=self._get_subtitle_color()
        )
        self.subtitle.grid(row=0,column=0,sticky="w", padx=28, pady=(12,18))

        # Cards container (reuse CardButton style)
        self.cards_container = ctk.CTkFrame(self.main, fg_color="transparent")
        self.cards_container.grid(row=1,column=0,sticky="nsew", padx=28, pady=(0,20))
        self.cards_container.columnconfigure(0,weight=1)
        self.cards_container.columnconfigure(1,weight=1)

        # Interval quiz card
        self.interval_card = CardButton(
            self.cards_container,
            title="🎵 Trening Słuchu: Interwały",
            description="Rozpoznawanie odległości między dźwiękami.",
            icon_text="🎼",
            command=self.start_interval_quiz,
            accent=self.ACCENT_CYAN
        )

        # Harmony quiz card
        self.harmony_card = CardButton(
            self.cards_container,
            title="🎸 Harmonia: Funkcje Akordów",
            description="Rozpoznawanie roli akordów w kontekście tonalnym.",
            icon_text="🎹",
            command=self.start_harmony_quiz,
            accent=self.ACCENT_PURPLE
        )

        # Rhythm trainer card
        self.rhythm_card = CardButton(
            self.cards_container,
            title="🥁 Trener Rytmu",
            description="Wystukiwanie rytmów i pomiar precyzji (spacja).",
            icon_text="🥁",
            command=self.start_rhythm_trainer,
            accent=self.ACCENT_GREEN
        )

        # Grid layout
        self.interval_card.grid(row=0,column=0,sticky="nsew", padx=(0,12), pady=10)
        self.harmony_card.grid(row=0,column=1,sticky="nsew", padx=(12,0), pady=10)
        self.rhythm_card.grid(row=1,column=0, columnspan=2, sticky="nsew", pady=10)

        self._current_columns = 2

    def _on_resize(self,event):
        width = self.winfo_width()
        target = 1 if width<720 else 2
        if target != self._current_columns:
            self._current_columns = target
            for w in [self.interval_card,self.harmony_card,self.rhythm_card]:
                w.grid_forget()
            if target==1:
                self.cards_container.columnconfigure(1,weight=0)
                self.interval_card.grid(row=0,column=0,sticky="ew", pady=8)
                self.harmony_card.grid(row=1,column=0,sticky="ew", pady=8)
                self.rhythm_card.grid(row=2,column=0,sticky="ew", pady=8)
            else:
                self.cards_container.columnconfigure(1,weight=1)
                self.interval_card.grid(row=0,column=0,sticky="nsew", padx=(0,12), pady=10)
                self.harmony_card.grid(row=0,column=1,sticky="nsew", padx=(12,0), pady=10)
                self.rhythm_card.grid(row=1,column=0,columnspan=2,sticky="nsew", pady=10)

    # ================= SUB-QUIZ LOGIC =================
    def _show_sub_quiz(self, ViewClass):
        self.main.grid_remove()
        if getattr(self,'chapter_frame',None) is None:
            self.chapter_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
            self.chapter_frame.grid(row=1,column=0,sticky="nsew", padx=10,pady=(6,12))
            self.chapter_frame.columnconfigure(0,weight=1)
        for w in self.chapter_frame.winfo_children(): w.destroy()

        if ViewClass==IntervalQuizView and IntervalQuizView:
            IntervalQuizView(self.chapter_frame, back_callback=self.back_callback, show_main_quiz_callback=self._show_main_quiz_view).pack(fill="both",expand=True)
            return
        if ViewClass==HarmonyQuizView and HarmonyQuizView:
            HarmonyQuizView(self.chapter_frame, back_callback=self.back_callback, show_main_quiz_callback=self._show_main_quiz_view).pack(fill="both",expand=True)
            return
        if ViewClass==RhythmTrainer and RhythmTrainer:
            RhythmTrainer(self.chapter_frame, back_callback=self.back_callback, show_main_quiz_callback=self._show_main_quiz_view).pack(fill="both",expand=True)
            return

    def _show_main_quiz_view(self):
        self.main.grid()
        if getattr(self,'chapter_frame',None):
            self.chapter_frame.grid_forget()
            for w in self.chapter_frame.winfo_children(): w.destroy()

    def start_interval_quiz(self): self._show_sub_quiz(IntervalQuizView)
    def start_harmony_quiz(self): self._show_sub_quiz(HarmonyQuizView)
    def start_rhythm_trainer(self): self._show_sub_quiz(RhythmTrainer)
