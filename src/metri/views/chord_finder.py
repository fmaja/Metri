import customtkinter as ctk
from typing import List, Dict, Tuple

# Basic chord formula library in semitones relative to root (un-ordered sets)
CHORD_FORMULAS: Dict[str, List[int]] = {
    "": [0, 4, 7],  # Major triad shown as just root name, e.g., "C"
    "m": [0, 3, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "add11": [0, 4, 5, 7],  # same as add4
    "7": [0, 4, 7, 10],
    "maj7": [0, 4, 7, 11],
    "m7": [0, 3, 7, 10],
    "mMaj7": [0, 3, 7, 11],
    "dim7": [0, 3, 6, 9],
    "m7b5": [0, 3, 6, 10],
    "6": [0, 4, 7, 9],
    "m6": [0, 3, 7, 9],
    "add9": [0, 4, 7, 14],
    "madd9": [0, 3, 7, 14],
    "9": [0, 4, 7, 10, 14],
    "m9": [0, 3, 7, 10, 14],
    "maj9": [0, 4, 7, 11, 14],
    "11": [0, 4, 7, 10, 14, 17],  # theoretical (often omit 3)
    "13": [0, 4, 7, 10, 14, 21],  # theoretical (often omit 5 / 11)
    # Altered dominants (we keep base 7 plus alteration)
    "7b9": [0, 4, 7, 10, 13],
    "7#9": [0, 4, 7, 10, 15],
    "7b5": [0, 4, 6, 10],
    "7#5": [0, 4, 8, 10],
    "7alt": [0, 4, 7, 10, 13, 15],  # cluster b9 #9
}

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Labels within one octave; extensions are folded (e.g., 9 -> 2)
DEGREE_LABELS_12 = {
    0: "1", 1: "b2", 2: "2", 3: "b3", 4: "3", 5: "4", 6: "b5/#11", 7: "5", 8: "#5/b13", 9: "6", 10: "b7", 11: "7"
}

# Intervals (mod 12) that must be present for musically sensible partial matches
REQUIRED_INTERVALS: Dict[str, List[int]] = {
    "": [0, 4],          # major triad: need 3rd; 5th optional
    "m": [0, 3],         # minor triad: need b3
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus2": [0, 2],
    "sus4": [0, 5],
    "add11": [0, 4, 5],  # require 3 and 4 present; 5 optional here because add11 doesn't need 5 theoretically, but we include 7 so both paths OK
    "6": [0, 4, 9],
    "m6": [0, 3, 9],
    "7": [0, 4, 10],     # require b7 to call it a 7 chord
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

# Additional tensions allowed alongside a chord without changing its name
# (selection may include these beyond the base formula)
ALLOWED_EXTRAS: Dict[str, List[int]] = {
    "add11": [2],  # allow added 9 with add11
    "add9": [5],   # allow added 11 with add9 (still not sus because 3rd is required)
}

class ChordFinderView(ctk.CTkFrame):
    def __init__(self, master, back_callback=None):
        super().__init__(master)
        self.back_callback = back_callback

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", pady=(10, 5))
        ctk.CTkButton(top, text="← Powrót", width=100, fg_color="#555555", hover_color="#777777", command=self._go_back).pack(side="left")
        ctk.CTkLabel(top, text="Chord Finder", font=("Arial", 28, "bold")).pack(side="left", padx=20)
        desc = ("Wybierz nuty (klikając przyciski).\n"
                "Aplikacja sprawdzi każdą z wybranych nut jako potencjalny prymę i poda dokładnie pasujące akordy.")
        ctk.CTkLabel(self, text=desc, font=("Arial", 14), text_color="#95a5a6", justify="left").pack(anchor="w", padx=20)

        self.selected_notes: List[int] = []
        self.note_buttons: List[ctk.CTkButton] = []

        self.notes_grid = ctk.CTkFrame(self)
        self.notes_grid.pack(pady=15)
        for i, name in enumerate(NOTE_NAMES):
            btn = ctk.CTkButton(self.notes_grid, text=name, width=50, height=40,
                                fg_color="#2c3e50", hover_color="#34495e",
                                command=lambda s=i: self._toggle_note(s))
            btn.grid(row=0, column=i, padx=4)
            self.note_buttons.append(btn)
        # (Usunięto sekcję wyboru basu – analiza działa dla każdej wybranej nuty jako prymy)

        # Selected notes indicator
        self.selection_indicator = ctk.CTkLabel(self, text="Wybrane: —", font=("Arial", 14, "italic"), text_color="#7f8c8d")
        self.selection_indicator.pack(anchor="w", padx=20, pady=(0, 10))

        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=20)
        ctk.CTkButton(action_bar, text="Analizuj", width=140, height=42, fg_color="#1ABC9C", hover_color="#16A085", command=self._analyze).pack(side="left")
        ctk.CTkButton(action_bar, text="Wyczyść", width=140, height=42, fg_color="#D35B58", hover_color="#C77C78", command=self._clear).pack(side="left", padx=10)

        self.results_container = ctk.CTkScrollableFrame(self, height=300)
        self.results_container.pack(fill="both", expand=True, padx=20, pady=15)
        ctk.CTkLabel(self.results_container, text="Brak wyników", font=("Arial", 16, "italic"), text_color="#7f8c8d").pack(pady=10)

    def _go_back(self):
        if self.back_callback:
            self.back_callback()

    def _toggle_note(self, semitone: int):
        if semitone in self.selected_notes:
            self.selected_notes.remove(semitone)
        else:
            self.selected_notes.append(semitone)
        self._refresh_note_buttons()
        self._update_selection_indicator()

    # (brak metod ustawiania/kasowania basu)

    def _clear(self):
        self.selected_notes.clear()
        self._refresh_note_buttons()
        for w in self.results_container.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.results_container, text="Brak wyników", font=("Arial", 16, "italic"), text_color="#7f8c8d").pack(pady=10)
        self._update_selection_indicator()

    def _refresh_note_buttons(self):
        # Refresh main note buttons
        for i, btn in enumerate(self.note_buttons):
            active = i in self.selected_notes
            btn.configure(fg_color="#2980B9" if active else "#2c3e50")
        # (brak przycisków basu)

    def _analyze(self):
        if not self.selected_notes:
            for w in self.results_container.winfo_children():
                w.destroy()
            ctk.CTkLabel(self.results_container, text="Brak wyników", font=("Arial", 16, "italic"), text_color="#7f8c8d").pack(pady=10)
            return
        # Normalize notes modulo 12, sort unique (pitch classes)
        pcs = sorted(set(n % 12 for n in self.selected_notes))
        results = self._detect_chords_all_roots(pcs)
        self._render_results(pcs, results)

    def _detect_chords_all_roots(self, pcs: List[int]) -> List[Tuple[str, int, List[int]]]:
        """Check every selected pitch-class as root. Return list of (name, root, missing_intervals).

        Rules:
        - The user's selected pitch-classes must be a subset of the chord tones (no extra tones).
        - All defining tones for the chord quality must be present (e.g., b7 for 7, 3rd for major/minor).
        - Exact matches (no missing tones) are returned with missing_intervals == [].
        - Conditional/close matches are returned when missing_intervals length <= 2.
        """
        candidates: List[Tuple[str, int, List[int]]] = []
        for root in pcs:  # root must be present
            intervals = set((p - root) % 12 for p in pcs)
            for suffix, formula in CHORD_FORMULAS.items():
                base_set = set(i % 12 for i in formula)
                allowed = base_set.union(ALLOWED_EXTRAS.get(suffix, []))
                # Reject chords when selection contains tones not in chord or its allowed tensions
                if not intervals.issubset(allowed):
                    continue
                # Require defining intervals for the chord quality
                required = REQUIRED_INTERVALS.get(suffix, [0])
                if not set(required).issubset(intervals):
                    continue
                missing = sorted(list(base_set - intervals))
                # allow exact or close matches (missing up to 2 tones)
                if len(missing) <= 2:
                    name = f"{NOTE_NAMES[root]}{suffix}"
                    candidates.append((name, root, missing))

        # Deduplicate keeping first occurrence
        seen = set()
        unique: List[Tuple[str, int, List[int]]] = []
        for name, r, missing in candidates:
            key = (name, r, tuple(missing))
            if key not in seen:
                unique.append((name, r, missing))
                seen.add(key)

        # Sorting: exact matches first, then fewer missing; within same group prefer larger chords and then root order and name
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
        for w in self.results_container.winfo_children():
            w.destroy()
        if not results:
            ctk.CTkLabel(self.results_container, text="Nie znaleziono akordów", font=("Arial", 16, "italic"), text_color="#7f8c8d").pack(pady=10)
            return
        # Count exact vs conditional
        exact_count = sum(1 for _, _, missing in results if not missing)
        cond_count = len(results) - exact_count
        header_text = f"Znaleziono {len(results)} możliwe akordy:"
        if exact_count:
            header_text += f" ({exact_count} dokładnych)"
        if cond_count:
            header_text += f", {cond_count} warunkowych"
        header = ctk.CTkLabel(self.results_container, text=header_text, font=("Arial", 18, "bold"))
        header.pack(anchor="w", pady=(0, 10))
        for name, root, missing in results:
            frame = ctk.CTkFrame(self.results_container, fg_color="#2b2b2b", corner_radius=8)
            frame.pack(fill="x", pady=6)
            ctk.CTkLabel(frame, text=name, font=("Arial", 18, "bold"), text_color="#00BCD4").pack(anchor="w", padx=12, pady=(6, 2))
            mapping = self._map_degrees(pcs, root)
            mapping_text = ", ".join(f"{NOTE_NAMES[n]}={d}" for n, d in mapping)
            ctk.CTkLabel(frame, text=mapping_text, font=("Arial", 14), text_color="#95a5a6", wraplength=820, justify="left").pack(anchor="w", padx=12, pady=(0, 6))
            if missing:
                # show missing degrees (explain conditions)
                missing_labels = [DEGREE_LABELS_12.get(m, f"?{m}") for m in missing]
                miss_text = "Brakuje: " + ", ".join(missing_labels)
                note_text = "Ten wynik jest warunkowy: akord będzie pełny jeśli dodamy brakujące dźwięki."
                ctk.CTkLabel(frame, text=miss_text, font=("Arial", 13, "italic"), text_color="#F39C12").pack(anchor="w", padx=12, pady=(0, 2))
                ctk.CTkLabel(frame, text=note_text, font=("Arial", 12), text_color="#95a5a6", wraplength=800, justify="left").pack(anchor="w", padx=12, pady=(0, 8))

    def _map_degrees(self, pcs: List[int], root: int) -> List[Tuple[int, str]]:
        mapping: List[Tuple[int, str]] = []
        # sort notes by ascending interval from root (0..11)
        sorted_by_interval = sorted(pcs, key=lambda p: (p - root) % 12)
        for p in sorted_by_interval:
            interval = (p - root) % 12
            label = DEGREE_LABELS_12.get(interval, f"?{interval}")
            mapping.append((p, label))
        return mapping

    def _update_selection_indicator(self):
        if not self.selected_notes:
            text = "Wybrane: —"
        else:
            sel = sorted(set(self.selected_notes))
            names = [NOTE_NAMES[n % 12] for n in sel]
            text = "Wybrane: " + ", ".join(names)
        self.selection_indicator.configure(text=text)
