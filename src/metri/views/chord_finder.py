import customtkinter as ctk
from typing import List, Dict, Tuple, Optional, Callable
import os
from PIL import Image

# =========================
# Harmonic library
# =========================

CHORD_FORMULAS: Dict[str, List[int]] = {
    "": [0, 4, 7],  # major
    "m": [0, 3, 7],  # minor
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "add11": [0, 4, 5, 7],
    "6": [0, 4, 7, 9],
    "m6": [0, 3, 7, 9],
    "7": [0, 4, 7, 10],
    "maj7": [0, 4, 7, 11],
    "m7": [0, 3, 7, 10],
    "mMaj7": [0, 3, 7, 11],
    "dim7": [0, 3, 6, 9],
    "m7b5": [0, 3, 6, 10],
    "add9": [0, 4, 7, 14],
    "madd9": [0, 3, 7, 14],
    "9": [0, 4, 7, 10, 14],
    "m9": [0, 3, 7, 10, 14],
    "maj9": [0, 4, 7, 11, 14],
    "11": [0, 4, 7, 10, 14, 17],  # theoretical
    "13": [0, 4, 7, 10, 14, 21],  # theoretical
    "7b9": [0, 4, 7, 10, 13],
    "7#9": [0, 4, 7, 10, 15],
    "7b5": [0, 4, 6, 10],
    "7#5": [0, 4, 8, 10],
    "7alt": [0, 4, 7, 10, 13, 15],
}

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]

DEGREE_LABELS_12 = {
    0: "1", 1: "b2", 2: "2", 3: "b3", 4: "3", 5: "4",
    6: "b5/#11", 7: "5", 8: "#5/b13", 9: "6", 10: "b7", 11: "7"
}

REQUIRED_INTERVALS: Dict[str, List[int]] = {
    "": [0, 4],
    "m": [0, 3],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus2": [0, 2],
    "sus4": [0, 5],
    "add11": [0, 4, 5],
    "6": [0, 4, 9],
    "m6": [0, 3, 9],
    "7": [0, 4, 10],
    "maj7": [0, 4, 11],
    "m7": [0, 3, 10],
    "mMaj7": [0, 3, 11],
    "dim7": [0, 3, 6, 9],
    "m7b5": [0, 3, 6, 10],
    "add9": [0, 4, (14 % 12)],
    "madd9": [0, 3, (14 % 12)],
    "9": [0, 4, 10, (14 % 12)],
    "m9": [0, 3, 10, (14 % 12)],
    "maj9": [0, 4, 11, (14 % 12)],
    "11": [0, 10, (17 % 12)],
    "13": [0, 10, (21 % 12)],
    "7b9": [0, 4, 10, (13 % 12)],
    "7#9": [0, 4, 10, (15 % 12)],
    "7b5": [0, 4, 10, 6],
    "7#5": [0, 4, 10, 8],
    "7alt": [0, 4, 10, (13 % 12), (15 % 12)],
}

ALLOWED_EXTRAS: Dict[str, List[int]] = {
    "add11": [2],  # allow 9
    "add9": [5],  # allow 11
}


class ChordFinderView(ctk.CTkFrame):
    # Piano layout helpers
    PIANO_WHITE_ORDER = [0, 2, 4, 5, 7, 9, 11]  # C D E F G A B
    PIANO_BLACK_REL = {1: 0.7, 3: 1.7, 6: 3.7, 8: 4.7, 10: 5.7}  # relative to white-key width

    # Kolory z QuizView
    HEADER_BG = "#FFFFFF"
    ACCENT_CYAN = "#25b4b6"
    ACCENT_GOLD = "#cca839"
    ACCENT_PURPLE = "#552564"
    ACCENT_GREEN = "#61be5f"
    ACCENT_LAVENDER = "#9b75a7"

    # Nowa stała dla koloru tekstu nut na gryfie gitary (ciemny)
    GUITAR_FRET_TEXT_COLOR = "#333333"

    def __init__(self, master,
                 back_callback=None,
                 show_module_callback=None,
                 show_menu_callback=None,
                 sidebar=None):
        super().__init__(master)
        self.configure(fg_color=self._get_main_bg_color())

        self.back_callback = back_callback
        self._show_module = show_module_callback
        self.show_menu = show_menu_callback
        self.sidebar = sidebar

        # State
        self.selected_pitches: List[int] = []
        self.note_visual_map: Dict[int, List[Tuple[str, any]]] = {}

        # Budowanie UI
        self._build_header()

        # Mode selector
        selector_bar = ctk.CTkFrame(self, fg_color="transparent")
        selector_bar.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(selector_bar, text="Instrument:",
                     font=("Arial", 16, "bold"), text_color=self._get_secondary_text_color()).pack(side="left")
        self.mode_selector = ctk.CTkSegmentedButton(
            selector_bar, values=["Pianino", "Gitara"], command=self._switch_mode,
            selected_color=self.ACCENT_CYAN,
            selected_hover_color=self.ACCENT_CYAN,
            unselected_color="#555555" if ctk.get_appearance_mode() == "Dark" else "#bbbbbb",
            unselected_hover_color="#777777" if ctk.get_appearance_mode() == "Dark" else "#dddddd",
            text_color="white",
            font=("Arial", 14, "bold"),
            corner_radius=10
        )
        self.mode_selector.set("Pianino")
        self.mode_selector.pack(side="left", padx=10)

        # Selected indicator - BARDZIEJ WIDOCZNY NAPIS
        self.selection_indicator = ctk.CTkLabel(
            self, text="Wybrane: —", font=("Arial", 20, "bold"),
            text_color=self.ACCENT_GREEN)
        self.selection_indicator.pack(anchor="w", padx=20, pady=(15, 15))

        # Actions
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkButton(action_bar, text="Analizuj", width=140, height=42,
                      fg_color=self.ACCENT_GREEN, hover_color="#4CAF50",
                      command=self._analyze, corner_radius=12).pack(side="left")
        ctk.CTkButton(action_bar, text="Wyczyść", width=140, height=42,
                      fg_color="#E74C3C", hover_color="#C0392B",  # Czerwień
                      command=self._clear, corner_radius=12).pack(side="left", padx=10)

        # Instrument area
        self.instrument_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.instrument_frame.pack(fill="x", padx=20, pady=15)

        # Results area
        self.results_container = ctk.CTkScrollableFrame(
            self, height=380,
            fg_color=self._get_results_container_bg_color(),
            corner_radius=12
        )
        self.results_container.pack(fill="both", expand=True, padx=20, pady=10)
        ctk.CTkLabel(self.results_container, text="Brak wyników",
                     font=("Arial", 16, "italic"),
                     text_color=self._get_secondary_text_color()).pack(pady=10)

        # Build initial
        self._build_piano()

        # Upewnienie się, że ikona motywu jest poprawna przy starcie
        if ctk.get_appearance_mode() == "Dark":
            self.theme_icon.configure(text="🌙")
        else:
            self.theme_icon.configure(text="🌞")

    # =========================
    # Metody pomocnicze (Kolory, UI)
    # =========================

    def _get_main_bg_color(self):
        return "#f2f2f2" if ctk.get_appearance_mode() == "Light" else "#1a1a1a"

    def _get_secondary_text_color(self):
        return "#4b4b4b" if ctk.get_appearance_mode() == "Light" else "#95a5a6"

    def _get_results_container_bg_color(self):
        return "#ffffff" if ctk.get_appearance_mode() == "Light" else "#1e1e1e"

    def _build_header(self):
        """Tworzy nagłówek, skopiowany z QuizView."""
        self.header = ctk.CTkFrame(self, fg_color=self.HEADER_BG, height=72, corner_radius=12)
        self.header.pack(fill="x", padx=10, pady=(20, 10))

        self.header.grid_propagate(False)
        self.header.columnconfigure(1, weight=1)
        self.header.rowconfigure(0, weight=1)

        # Lewa strona: Ikona + strzałka powrotu
        left = ctk.CTkFrame(self.header, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=(18, 10))

        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.png")

        if os.path.exists(icon_path):
            self.app_icon = ctk.CTkImage(light_image=Image.open(icon_path), size=(60, 65))
            self.menu_button = ctk.CTkButton(
                left,
                image=self.app_icon,
                text="",
                width=60,
                height=65,
                fg_color="transparent",
                command=self.sidebar.toggle  # <<< globalny sidebar
            )
            self.menu_button.pack(side="left", anchor="center")

        ctk.CTkButton(
            left, text="←", width=44, height=44,
            fg_color=self.ACCENT_LAVENDER, hover_color=self.ACCENT_PURPLE,
            command=self._go_back,
            corner_radius=12
        ).pack(side="left", anchor="center", padx=(10, 0))

        # Środek: Tytuł
        title = ctk.CTkLabel(
            self.header, text="Detektor Akordów",
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

        # Aktualizuj tło głównego widoku
        self.configure(fg_color=self._get_main_bg_color())

        # Aktualizuj tła instrument_frame i results_container
        self.instrument_frame.configure(fg_color="transparent")  # Zawsze przezroczyste
        self.results_container.configure(fg_color=self._get_results_container_bg_color())

        # Odśwież instrument (przebuduje pianino lub gitarę z nowymi kolorami)
        self._switch_mode(self.mode_selector.get())

        # Aktualizuj kolory tekstu
        for w in self.winfo_children():
            if isinstance(w, ctk.CTkFrame):
                for child in w.winfo_children():
                    if isinstance(child, ctk.CTkLabel) and child is not self.selection_indicator:
                        if child.cget("text_color") not in [self.ACCENT_CYAN, self.ACCENT_GREEN]:
                            child.configure(text_color=self._get_secondary_text_color())
            elif isinstance(w, ctk.CTkLabel) and w is not self.selection_indicator:
                w.configure(text_color=self._get_secondary_text_color())

        self.selection_indicator.configure(text_color=self.ACCENT_GREEN)

        # Odświeżenie przycisków w selektorze instrumentów
        self.mode_selector.configure(
            unselected_color="#555555" if ctk.get_appearance_mode() == "Dark" else "#bbbbbb",
            unselected_hover_color="#777777" if ctk.get_appearance_mode() == "Dark" else "#dddddd"
        )

    # =========================
    # Nawigacja i Budowanie UI Instrumentów
    # =========================

    def _go_back(self):
        if self.back_callback:
            self.back_callback()

    def _switch_mode(self, mode: str):
        """Usuwa stary instrument i buduje nowy."""
        for w in self.instrument_frame.winfo_children():
            w.destroy()
        self.note_visual_map.clear()
        if mode == "Pianino":
            self._build_piano()
        else:
            self._build_guitar()

    def _build_piano(self):
        start_midi = 48
        octaves = 3
        white_key_w = 42
        white_key_h = 200
        black_key_w = 28
        black_key_h = 120
        canvas_width = int(octaves * 7 * white_key_w)
        canvas_height = white_key_h + 20

        piano_bg = "#eaeaea" if ctk.get_appearance_mode() == "Light" else "#2b2b2b"
        key_label_color = "#333" if ctk.get_appearance_mode() == "Light" else "#ccc"

        canvas = ctk.CTkCanvas(self.instrument_frame, width=canvas_width, height=canvas_height,
                               bg=piano_bg, highlightthickness=0)
        canvas.pack(pady=10)

        # Białe klawisze
        for octave_idx in range(octaves):
            base_x = int(octave_idx * 7 * white_key_w)
            base_octave_midi = start_midi + octave_idx * 12
            for i, note_pc in enumerate(self.PIANO_WHITE_ORDER):
                midi = base_octave_midi + note_pc
                x0 = base_x + int(i * white_key_w)
                x1 = x0 + int(white_key_w)
                rect = canvas.create_rectangle(x0, 10, x1, 10 + white_key_h, fill="white", outline="#222", width=2)
                name = self._midi_name(midi)
                canvas.create_text((x0 + white_key_w // 2, 10 + white_key_h - 16),
                                   text=name, font=("Arial", 10, "bold"), fill=key_label_color)
                canvas.tag_bind(rect, "<Button-1>", lambda e, m=midi, r=rect: self._toggle_pitch_visual("piano_rect", m,
                                                                                                        (canvas, r,
                                                                                                         "white")))
                self._register_visual(m=midi, kind="piano_rect", ref=(canvas, rect, "white"))

        # Czarne klawisze
        for octave_idx in range(octaves):
            base_x = int(octave_idx * 7 * white_key_w)
            base_octave_midi = start_midi + octave_idx * 12
            for note_pc, pos in self.PIANO_BLACK_REL.items():
                midi = base_octave_midi + note_pc
                x = base_x + int(pos * white_key_w) - black_key_w // 2
                rect = canvas.create_rectangle(x, 10, x + black_key_w, 10 + black_key_h, fill="black", outline="#111",
                                               width=2)
                canvas.tag_bind(rect, "<Button-1>", lambda e, m=midi, r=rect: self._toggle_pitch_visual("piano_rect", m,
                                                                                                        (canvas, r,
                                                                                                         "black")))
                self._register_visual(m=midi, kind="piano_rect", ref=(canvas, rect, "black"))

        self._apply_highlights_piano()

        ctk.CTkLabel(self.instrument_frame, text="Pianino (3 oktawy) – kliknij klawisz, aby zaznaczyć nutę",
                     font=("Arial", 12), text_color=self._get_secondary_text_color()).pack(pady=(6, 0))

    def _apply_highlights_piano(self):
        for m in self.selected_pitches:
            for kind, ref in self.note_visual_map.get(m, []):
                if kind == "piano_rect":
                    canvas, rect, base = ref
                    canvas.itemconfig(rect, fill=self.ACCENT_CYAN)

    def _build_guitar(self):
        open_strings_midi = [40, 45, 50, 55, 59, 64]
        frets = 14

        guitar_bg = "#f0f0f0" if ctk.get_appearance_mode() == "Light" else "#333333"
        guitar_text_color = "#333" if ctk.get_appearance_mode() == "Light" else "#e0e0e0"
        fret_btn_fg = "#2c3e50" if ctk.get_appearance_mode() == "Dark" else "#cccccc"
        fret_btn_hover = "#34495e" if ctk.get_appearance_mode() == "Dark" else "#aaaaaa"

        fb = ctk.CTkFrame(self.instrument_frame, fg_color=guitar_bg, corner_radius=12)
        fb.pack(fill="x", padx=8, pady=4)

        header = ctk.CTkFrame(fb, fg_color="transparent")
        header.pack(fill="x", pady=(8, 4))
        ctk.CTkLabel(header, text="Gryf gitary – klikaj progi (0 = pusty dźwięk)",
                     font=("Arial", 12), text_color=guitar_text_color).pack(side="left", padx=10)

        nut = ctk.CTkFrame(fb, fg_color="#121212", height=6)
        nut.pack(fill="x")

        # Kontener na siatkę progów
        grid = ctk.CTkFrame(fb, fg_color="transparent")
        grid.pack(expand=True, padx=20, pady=6)  # WYŚRODKOWANIE

        for f in range(frets + 1):
            grid.grid_columnconfigure(f, weight=1, uniform="fret")

        # Budowanie strun
        for s in range(6):
            row = ctk.CTkFrame(grid, fg_color="transparent")
            row.grid(row=s, column=0, columnspan=frets + 1, sticky="ew", pady=2)

            line = ctk.CTkFrame(row, fg_color="#606060", height=2)
            line.pack(fill="x", pady=(0, 4))

            # Budowanie progów
            for f in range(frets + 1):
                midi = open_strings_midi[s] + f
                name = self._midi_name(midi)
                label = "0" if f == 0 else str(f)
                btn = ctk.CTkButton(row, text=f"{name}\n{label}",
                                    width=60, height=38,
                                    fg_color=fret_btn_fg, hover_color=fret_btn_hover,
                                    font=("Arial", 10, "bold"),
                                    command=lambda mm=midi, ss=s, ff=f: self._toggle_pitch_from_guitar(mm, ss, ff),
                                    corner_radius=8,
                                    # Zmiana: Stały ciemny kolor tekstu
                                    text_color=self.GUITAR_FRET_TEXT_COLOR
                                    )
                btn.pack(side="left", padx=1, pady=(2, 0))
                self._register_visual(m=midi, kind="guitar_btn", ref=(s, f, btn))

        self._apply_highlights_guitar()

    def _apply_highlights_guitar(self):
        for m in self.selected_pitches:
            for kind, ref in self.note_visual_map.get(m, []):
                if kind == "guitar_btn":
                    _, _, b = ref
                    b.configure(fg_color=self.ACCENT_GREEN)

    # =========================
    # Logika Zaznaczania i Czyszczenia
    # =========================

    def _register_visual(self, m: int, kind: str, ref: any):
        """Rejestruje wizualny element (przycisk/klawisz) dla danej nuty MIDI."""
        self.note_visual_map.setdefault(m, []).append((kind, ref))

    def _toggle_pitch_visual(self, kind: str, midi: int, ref: any):
        """Obsługuje kliknięcie na klawisz pianina."""
        fret_btn_fg = "#2c3e50" if ctk.get_appearance_mode() == "Dark" else "#cccccc"

        if midi in self.selected_pitches:
            self.selected_pitches.remove(midi)
            if kind == "piano_rect":
                canvas, rect, base = ref
                canvas.itemconfig(rect, fill=base)
            for k, r in self.note_visual_map.get(midi, []):
                if k == "guitar_btn":
                    _, _, b = r
                    b.configure(fg_color=fret_btn_fg)
        else:
            self.selected_pitches.append(midi)
            if kind == "piano_rect":
                canvas, rect, _ = ref
                canvas.itemconfig(rect, fill=self.ACCENT_CYAN)
            for k, r in self.note_visual_map.get(midi, []):
                if k == "guitar_btn":
                    _, _, b = r
                    b.configure(fg_color=self.ACCENT_GREEN)
        self._update_selection_indicator()

    def _toggle_pitch_from_guitar(self, midi: int, string: int, fret: int):
        """Obsługuje kliknięcie na próg gitary."""
        fret_btn_fg = "#2c3e50" if ctk.get_appearance_mode() == "Dark" else "#cccccc"

        if midi in self.selected_pitches:
            self.selected_pitches.remove(midi)
            for k, r in self.note_visual_map.get(midi, []):
                if k == "guitar_btn":
                    s, f, b = r
                    if s == string and f == fret:
                        b.configure(fg_color=fret_btn_fg)
            for k, r in self.note_visual_map.get(midi, []):
                if k == "piano_rect":
                    canvas, rect, base = r
                    canvas.itemconfig(rect, fill=base)
        else:
            self.selected_pitches.append(midi)
            for k, r in self.note_visual_map.get(midi, []):
                if k == "piano_rect":
                    canvas, rect, _ = r
                    canvas.itemconfig(rect, fill=self.ACCENT_CYAN)
                elif k == "guitar_btn":
                    _, _, b = r
                    b.configure(fg_color=self.ACCENT_GREEN)
        self._update_selection_indicator()

    def _midi_to_pc(self, midi: int) -> int:
        return midi % 12

    def _midi_to_octave(self, midi: int) -> int:
        return midi // 12 - 1

    def _midi_name(self, midi: int) -> str:
        pc = self._midi_to_pc(midi)
        octv = self._midi_to_octave(midi)
        return f"{NOTE_NAMES[pc]}{octv}"

    def _update_selection_indicator(self):
        """Aktualizuje etykietę 'Wybrane: ...'."""
        if not self.selected_pitches:
            text = "Wybrane: —"
        else:
            names = [self._midi_name(m) for m in sorted(set(self.selected_pitches))]
            text = "Wybrane: " + ", ".join(names)
        self.selection_indicator.configure(text=text)

    def _clear(self):
        """Czyści zaznaczenie i wyniki."""
        fret_btn_fg = "#2c3e50" if ctk.get_appearance_mode() == "Dark" else "#cccccc"

        for m in list(self.selected_pitches):
            for kind, ref in self.note_visual_map.get(m, []):
                if kind == "piano_rect":
                    canvas, rect, base = ref
                    canvas.itemconfig(rect, fill=base)
                elif kind == "guitar_btn":
                    _, _, b = ref
                    b.configure(fg_color=fret_btn_fg)
        self.selected_pitches.clear()
        self._update_selection_indicator()

        for w in self.results_container.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.results_container, text="Brak wyników",
                     font=("Arial", 16, "italic"),
                     text_color=self._get_secondary_text_color()).pack(pady=10)

    # =========================
    # Logika Analizy Akordów
    # =========================

    def _analyze(self):
        """Uruchamia analizę wybranych dźwięków."""
        for w in self.results_container.winfo_children():
            w.destroy()

        if not self.selected_pitches:
            ctk.CTkLabel(self.results_container, text="Brak wyników",
                         font=("Arial", 16, "italic"),
                         text_color=self._get_secondary_text_color()).pack(pady=10)
            return

        pcs = sorted(set(self._midi_to_pc(m) for m in self.selected_pitches))
        results = self._detect_chords_all_roots(pcs)
        self._render_results(pcs, results)

    def _detect_chords_all_roots(self, pcs: List[int]) -> List[Tuple[str, int, List[int]]]:
        """
        Zwraca listę (nazwa, root_pc, brakujące_interwały) dla wszystkich możliwych prym.
        """
        candidates: List[Tuple[str, int, List[int]]] = []
        for root in pcs:
            intervals = set((p - root) % 12 for p in pcs)
            for suffix, formula in CHORD_FORMULAS.items():
                base_set = set(i % 12 for i in formula)
                allowed = base_set.union(ALLOWED_EXTRAS.get(suffix, []))
                if not intervals.issubset(allowed):
                    continue
                required = REQUIRED_INTERVALS.get(suffix, [0])
                if not set(required).issubset(intervals):
                    continue
                missing = sorted(list(base_set - intervals))
                if len(missing) <= 2:
                    name = f"{NOTE_NAMES[root]}{suffix}"
                    candidates.append((name, root, missing))

        # Deduplikacja
        seen = set()
        unique: List[Tuple[str, int, List[int]]] = []
        for name, r, missing in candidates:
            key = (name, r, tuple(missing))
            if key not in seen:
                unique.append((name, r, missing))
                seen.add(key)

        # Sortowanie: dokładne > mniej brakujących > większe akordy
        order_index = {pc: i for i, pc in enumerate(pcs)}

        def sort_key(item: Tuple[str, int, List[int]]):
            name, r, missing = item
            missing_count = len(missing)
            size = 0
            for suf, f in CHORD_FORMULAS.items():
                if name.startswith(NOTE_NAMES[r] + suf):
                    size = len(set(f))
                    break
            return (missing_count, -size, order_index.get(r, 99), name)

        unique.sort(key=sort_key)
        return unique

    def _render_results(self, pcs: List[int], results: List[Tuple[str, int, List[int]]]):
        """Wyświetla wyniki analizy w kontenerze."""
        if not results:
            ctk.CTkLabel(self.results_container, text="Nie znaleziono pasujących akordów",
                         font=("Arial", 16, "italic"),
                         text_color=self._get_secondary_text_color()).pack(pady=10)
            return

        exact_count = sum(1 for _, _, missing in results if not missing)
        cond_count = len(results) - exact_count
        header_text = f"Znaleziono {len(results)} możliwe akordy:"
        if exact_count:
            header_text += f" ({exact_count} dokładnych)"
        if cond_count:
            header_text += f", {cond_count} warunkowych"

        header = ctk.CTkLabel(self.results_container, text=header_text,
                              font=("Arial", 18, "bold"),
                              text_color=self._get_secondary_text_color())
        header.pack(anchor="w", pady=(0, 10))

        frame_bg_color = "#ffffff" if ctk.get_appearance_mode() == "Light" else "#333333"

        for name, root, missing in results:
            frame = ctk.CTkFrame(self.results_container, fg_color=frame_bg_color, corner_radius=8)
            frame.pack(fill="x", pady=6)
            ctk.CTkLabel(frame, text=name, font=("Arial", 18, "bold"),
                         text_color=self.ACCENT_CYAN).pack(anchor="w", padx=12, pady=(6, 2))

            mapping = self._map_degrees(pcs, root)
            mapping_text = ", ".join(f"{NOTE_NAMES[n]}={d}" for n, d in mapping)
            ctk.CTkLabel(frame, text=mapping_text, font=("Arial", 14),
                         text_color=self._get_secondary_text_color(), wraplength=820,
                         justify="left").pack(anchor="w", padx=12, pady=(0, 6))

            if missing:
                missing_labels = [DEGREE_LABELS_12.get(m, f"?{m}") for m in missing]
                miss_text = "Brakuje: " + ", ".join(missing_labels)
                note_text = "Ten wynik jest warunkowy: akord będzie pełny jeśli dodamy brakujące dźwięki."
                ctk.CTkLabel(frame, text=miss_text, font=("Arial", 13, "italic"),
                             text_color=self.ACCENT_GOLD).pack(anchor="w", padx=12, pady=(0, 2))
                ctk.CTkLabel(frame, text=note_text, font=("Arial", 12),
                             text_color=self._get_secondary_text_color(), wraplength=800,
                             justify="left").pack(anchor="w", padx=12, pady=(0, 8))

    def _map_degrees(self, pcs: List[int], root: int) -> List[Tuple[int, str]]:
        """Mapuje klasy dźwięków na stopnie względem danej prymy."""
        mapping: List[Tuple[int, str]] = []
        sorted_by_interval = sorted(pcs, key=lambda p: (p - root) % 12)
        for p in sorted_by_interval:
            interval = (p - root) % 12
            label = DEGREE_LABELS_12.get(interval, f"?{interval}")
            mapping.append((p, label))
        return mapping