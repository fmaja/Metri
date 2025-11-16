import customtkinter as ctk
import pygame
import numpy as np
import threading


class AkordyView(ctk.CTkFrame):
    """Dedicated Akordy (Chords) view with explanations and playable examples.

    This view is intended to be embedded by `TheoryView` into the chapter
    frame. It accepts an `on_back` callback to return to the parent menu.
    """

    BASE_FREQ_C4 = 261.6256

    def __init__(self, master, on_back=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_back = on_back
        self.configure(fg_color="transparent")

        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2)
            self.audio_ok = True
        except Exception as e:
            print(f"pygame.mixer init failed: {e}")
            self.audio_ok = False

        self._sound_cache = {}

        self._build()

    def _build(self):
        # Top bar with back button and header
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 20), padx=30)

        back_btn = ctk.CTkButton(
            top_bar,
            text="← Powrót",
            command=self._on_back,
            width=130,
            height=40,
            fg_color="#555555",
            hover_color="#777777",
            font=("Arial", 14)
        )
        back_btn.pack(side="left")

        title_label = ctk.CTkLabel(
            top_bar,
            text="Akordy",
            font=("Arial", 28, "bold"),
            text_color="#00BCD4"
        )
        title_label.pack(side="left", padx=(20, 0))

        # Theory container with collapsible sections
        theory_container = ctk.CTkFrame(self, fg_color="transparent")
        theory_container.pack(fill="x", padx=30, pady=(0, 20))

        # Introduction (always visible)
        intro_text = (
            "Akord to równoczesne brzmienie trzech lub więcej dźwięków. "
            "Podstawowe akordy buduje się z tercji, tworząc struktury, które są fundamentem harmonii muzycznej. "
            "Akordy można klasyfikować według ich budowy, funkcji harmonicznej oraz charakteru brzmieniowego."
        )
        intro_label = ctk.CTkLabel(
            theory_container,
            text=intro_text,
            font=("Arial", 14),
            wraplength=820,
            justify="left",
            text_color="#e0e0e0"
        )
        intro_label.pack(pady=(0, 15), anchor="w")

        # Dictionary to track section states
        self.section_states = {}

        # Collapsible sections
        rodzaje_content = (
            "• Trójdźwięki – najprostsze pełne akordy (3 składniki), np. C dur, c mol\n"
            "• Czterodźwięki – akordy z czterema składnikami (np. C7, Cmaj7, Cdim7, Cm7b5/ø)\n"
            "• Akordy rozszerzone – zawierają dodatkowe składniki: nony (9), undecymy (11), tercdecymy (13); \n"
            "  11 zwykle bez tercji (sus4), 13 najczęściej bez 11 (ze względu na konflikt 3–11)\n"
            "• Akordy zmienione – z podwyższonymi/obniżonymi składnikami (#5, b9, #11, itp.); \n"
            "  oznaczenie ‘alt’ wskazuje zestaw możliwych alteracji – nie wszystkie muszą brzmieć jednocześnie\n"
            "• Dyady (power chords) – interwał 1–5 (czasem z oktawą); w klasycznej teorii nie uznawane za pełne akordy"
        )
        self._create_collapsible_section("rodzaje", "Rodzaje akordów", rodzaje_content, theory_container)

        funkcje_content = (
            "• Tonika (I) – akord stabilny, punkt odniesienia w tonacji\n"
            "• Dominanta (V, V7) – tworzy napięcie, prowadzi do toniki\n"
            "• Subdominanta (IV) – przygotowuje dominantę lub tonikę\n"
            "• Akordy poboczne – pełnią role pomocnicze w progresji harmonicznej"
        )
        self._create_collapsible_section("funkcje", "Funkcje harmoniczne", funkcje_content, theory_container)

        zastosowanie_content = (
            "• Muzyka klasyczna – progresje funkcyjne, modulacje, prowadzenie głosów\n"
            "• Jazz – akordy rozszerzone i zmienione, substytucje trytonowe, voicingi\n"
            "• Pop/Rock – proste progresje (I–V–vi–IV), dyady 1–5 (power chords)\n"
            "• Blues – dominanta (7) jako akord podstawowy stopni I–IV–V, napięcia b9/#9"
        )
        self._create_collapsible_section("zastosowanie", "Zastosowanie w muzyce", zastosowanie_content,
                                         theory_container)

        barwa_content = (
            "• Tercja definiuje charakter: wielka (3) – jaśniej; mała (b3) – ciemniej\n"
            "• Akordy molowe – ciemniejsze (b3); durowe – jaśniejsze (3); sus (1–4–5) – neutralne (brak tercji)\n"
            "• Akordy zmniejszone (1–b3–b5, 1–b3–b5–bb7) – silne napięcie, brak stabilnej kwinty\n"
            "• Akordy zwiększone (1–3–#5) – symetryczne (dwie wielkie tercje), niejednoznaczne tonalnie\n"
            "• Barwę silnie kształtują voicing, rejestr i kontekst harmoniczny (to samo oznaczenie może brzmieć różnie)"
        )
        self._create_collapsible_section("barwa", "Barwa i charakter", barwa_content, theory_container)

        # Store chord data as instance variables
        self.chords = [
            ("C dur (major)", [0, 4, 7], "Podstawowy akord durowy – radosny, jasny.",
             "Najpopularniejszy akord, podstawa harmonii dur-moll. Składa się z prymy, tercji wielkiej i kwinty czystej."),
            ("c mol (minor)", [0, 3, 7], "Podstawowy akord molowy – smutny, ciemny.",
             "Fundament harmonii molowej, wyraża emocje smutku. Składa się z prymy, tercji małej i kwinty czystej."),
            ("Cdim (diminished)", [0, 3, 6], "Akord zmniejszony – niestabilny, napięty.",
             "Wykorzystywany jako akord przejściowy. Składa się z prymy, tercji małej i kwinty zmniejszonej."),
            ("Caug (augmented)", [0, 4, 8], "Akord zwiększony – tajemniczy, nieokreślony.",
             "Rzadko używany, dodaje napięcie harmoniczne. Składa się z prymy, tercji wielkiej i kwinty zwiększonej."),
            ("Csus2", [0, 2, 7], "Akord zawieszony z sekundą – otwarty, lekki.",
             "Popularny w rocku, tworzy przestrzenne brzmienie. Sekunda zastępuje tercję."),
            ("Csus4", [0, 5, 7], "Akord zawieszony z kwartą – neutralny, oczekujący.",
             "Zawiesza tercję, tworzy napięcie przed rozwiązaniem. Kwarta prowadzi do tercji."),
            ("C7 (dominant 7th)", [0, 4, 7, 10], "Akord dominanty z septymą – napięty, prowadzący.",
             "Kluczowy w blues i jazzie, tworzy rozwiązanie do toniki. Tercja wielka + septyma mała."),
            ("Cmaj7 (major 7th)", [0, 4, 7, 11], "Akord durowy z wielką septymą – delikatny, jazzowy.",
             "Stosowany w jazzie i muzyce filmowej. Tercja wielka + septyma wielka."),
            ("Cm7 (minor 7th)", [0, 3, 7, 10], "Akord molowy z septymą – melancholijny, jazzowy.",
             "Popularny w muzyce funkowej i soul. Tercja mała + septyma mała."),
            ("Cm(maj7)", [0, 3, 7, 11], "Akord molowy z septymą wielką – dramatyczny, filmowy.",
             "Brzmi tajemniczo, często w muzyce filmowej. Tercja mała + septyma wielka."),
            ("Cdim7", [0, 3, 6, 9], "Czterodźwięk zmniejszony – bardzo napięty, symetryczny.",
             "Struktura symetryczna, każdy interwał to mała tercja. Używany jako przejście chromatyczne."),
            ("Cm7b5 (half-dim)", [0, 3, 6, 10], "Akord półzmniejszony – mroczny, niestabilny.",
             "Kluczowy w progresji ii-V-I w trybie molowym. Znany jako m7b5 lub ø."),
            ("C6", [0, 4, 7, 9], "Akord durowy z sekstą – ciepły, nostalgiczny.",
             "Charakterystyczny dla jazzu lat 40. i 50. Często zastępuje Cmaj7."),
            ("Cm6", [0, 3, 7, 9], "Akord molowy z sekstą – subtelny, jazzowy.",
             "Często używany w bossa novie i jazzie. Alternatywa dla Cm7."),
            ("C6/9", [0, 4, 7, 9, 14], "Akord durowy z sekstą i noną – bogaty, jazzowy.",
             "Rozszerzenie C6 o nonę wielką. Popularne zakończenie w jazzie."),
            ("Cadd9", [0, 4, 7, 14], "Akord durowy z dodaną noną – przestrzenny, pełny.",
             "Popularny w popie i rocku. Nona dodaje barwy bez zmiany funkcji."),
            ("Cadd4", [0, 4, 5, 7], "Akord durowy z dodaną kwartą – otwarty, folkowy.",
             "Bardziej naturalny niż add11 w układach bez nony; często spotykany w gitarowych voicingach."),
            ("C9", [0, 4, 7, 10, 14], "Akord dominanty z noną – jazzowy, kolorowy.",
             "Rozszerzenie C7 o nonę wielką. Kluczowy w blues i jazzie."),
            ("Cmaj9", [0, 4, 7, 11, 14], "Akord durowy z septymą i noną – delikatny, przestrzenny.",
             "Rozszerzenie Cmaj7, często w balladach i smooth jazzie."),
            ("Cm9", [0, 3, 7, 10, 14], "Akord molowy z septymą i noną – melancholijny, bogaty.",
             "Rozszerzenie Cm7, używany w neo-soul i R&B."),
            ("C11", [0, 4, 7, 10, 14, 17], "Akord dominanty z undecymą – gęsty, modalny.",
             "Zwykle bez tercji; częsty zapis i voicing: C9sus4 (dominanta zawieszona z 9)."),
            ("C13", [0, 4, 7, 10, 14, 21], "Akord dominanty z tercedecymą – bardzo bogaty, jazzowy.",
             "Pełne brzmienie dominanty; zwykle bez 11, często zawiera 9. Wymaga dobrego głosowania."),
            ("Cmaj7#11", [0, 4, 7, 11, 18], "Akord durowy z #11 – barwa lidyjska, przestrzenna.",
             "Typowy dla skali lidyjskiej (maj7#11). #11 dodaje napięcie bez utraty jasności durowej."),
            ("C7#11", [0, 4, 7, 10, 14, 18], "Akord dominanty z #11 – lydian dominant.",
             "Powiązany ze skalą lidyjską dominantową (mixolydian #11). Często łączy 9 i #11, bez 11 naturalnej."),
            ("C7b9", [0, 4, 7, 10, 13], "Akord dominanty z noną małą – napięty, alterowany.",
             "Używany w progresji V-I, dodaje chromatyczne napięcie."),
            ("C7#9", [0, 4, 7, 10, 15], "Akord dominanty z noną zwiększoną – ostry, bluesy.",
             "Znany jako 'Hendrix chord', popularny w blues-rocku."),
            ("C7b5", [0, 4, 6, 10], "Akord dominanty z kwintą zmniejszoną – trytony, jazzowy.",
             "Dwa trytony tworzą silne napięcie harmoniczne."),
            ("C7#5 (C7aug)", [0, 4, 8, 10], "Akord dominanty z kwintą zwiększoną – nieokreślony, jazzowy.",
             "Łączy dominantę ze zwiększeniem, często w jazzie."),
            ("C7alt", [0, 4, 6, 10, 13, 15], "Akord dominanty alterowany – maksymalne napięcie.",
             "Przykładowe voicing: b5, b9, #9. Alternatywnie można użyć #5/b13 zamiast b5. ‘alt’ oznacza wybór jednej lub kilku alteracji, nie wszystkich naraz."),
            ("C5 (power chord)", [0, 7], "Power chord – surowy, gitarowy.",
             "Używany w rocku i metalu. Brak tercji = neutralny charakter dur/mol."),
            ("C(add2)", [0, 2, 4, 7], "Akord durowy z dodaną sekundą – jasny, brzęczący.",
             "Sekunda w niskim rejestrze tworzy charakterystyczne brzmienie."),
            ("Cm(add9)", [0, 3, 7, 14], "Akord molowy z dodaną noną – przestrzenny, nowoczesny.",
             "Rozszerza c mol o nonę bez septymy."),
            ("C7sus4", [0, 5, 7, 10], "Akord dominanty zawieszony – oczekujący, funkowy.",
             "Popularne w funku i soul, kwarta nie rozwiązuje się do tercji."),
        ]

        # Main container for master-detail layout
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=30, pady=10)
        main_container.grid_columnconfigure(1, weight=1)
        main_container.grid_rowconfigure(0, weight=1)

        # Master frame (left, scrollable list)
        self.master_frame = ctk.CTkScrollableFrame(main_container, width=300, label_text="Wybierz Akord")
        self.master_frame.grid(row=0, column=0, sticky="ns", padx=(0, 20))

        # Detail frame (right, content changes)
        self.detail_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        self.detail_frame.grid(row=0, column=1, sticky="nsew")

        # Populate the master list with chord buttons
        for index, (name, *_) in enumerate(self.chords):
            btn = ctk.CTkButton(
                self.master_frame,
                text=name,
                command=lambda i=index: self._show_chord_details(i)
            )
            btn.pack(fill="x", pady=2, padx=5)

        # Show the first chord by default
        if self.chords:
            self._show_chord_details(0)

    def _show_chord_details(self, index):
        """Clear the detail frame and render the selected chord's info."""
        # Clear any existing widgets
        for widget in self.detail_frame.winfo_children():
            widget.destroy()

        # Get the selected chord data
        name, semitones, desc, theory_info = self.chords[index]

        # --- Header ---
        header_frame = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(header_frame, text=name, font=("Arial", 24, "bold"), text_color="#00BCD4").pack(anchor="w")

        notes_str = " — ".join([self._note_pc(st) for st in semitones])
        intervals_str = self._format_intervals(semitones)
        ctk.CTkLabel(header_frame, text=f"Nuty: {notes_str} ({intervals_str})", font=("Arial", 16),
                     text_color="#e0e0e0").pack(anchor="w", pady=(2, 0))

        # --- Play Button ---
        ctk.CTkButton(
            self.detail_frame, text="▶ Odtwórz", width=120, height=40,
            font=("Arial", 16), fg_color="#0097A7", hover_color="#00838F",
            command=lambda s=semitones: self._play_chord(s)
        ).pack(anchor="w", pady=(0, 20))

        # --- Details Content ---
        content_frame = ctk.CTkFrame(self.detail_frame, fg_color="#2b2b2b", corner_radius=8)
        content_frame.pack(fill="both", expand=True, pady=(0, 10))

        ctk.CTkLabel(
            content_frame, text=f"Opis: {desc}", font=("Arial", 13), text_color="#e0e0e0",
            wraplength=500, justify="left"
        ).pack(anchor="w", padx=20, pady=(10, 5))

        ctk.CTkLabel(
            content_frame, text=f"Teoria: {theory_info}", font=("Arial", 13), text_color="#e0e0e0",
            wraplength=500, justify="left"
        ).pack(anchor="w", padx=20, pady=(5, 10))

    def _create_collapsible_section(self, section_id, title, content, parent):
        """Create a collapsible section with header and content."""
        section_frame = ctk.CTkFrame(parent, fg_color="transparent")
        section_frame.pack(fill="x", pady=5)

        # Header
        header = ctk.CTkFrame(section_frame, fg_color="#2c2c2c", corner_radius=8)
        header.pack(fill="x")

        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=("Arial", 14, "bold"),
            text_color="#00BCD4"
        )
        title_label.pack(side="left", padx=15, pady=8)

        toggle_btn = ctk.CTkButton(
            header,
            text="▼",
            width=40,
            height=30,
            fg_color="#0277BD",
            hover_color="#01579B",
            font=("Arial", 12),
            command=lambda: self._toggle_section(section_id)
        )
        toggle_btn.pack(side="right", padx=10, pady=5)

        # Content container (initially hidden)
        content_container = ctk.CTkFrame(section_frame, fg_color="transparent")

        content_frame = ctk.CTkFrame(content_container, fg_color="#1e1e1e", corner_radius=8)
        content_frame.pack(fill="x", padx=0, pady=(5, 0))

        content_label = ctk.CTkLabel(
            content_frame,
            text=content,
            font=("Arial", 13),
            text_color="#e0e0e0",
            justify="left",
            anchor="w",
            wraplength=780
        )
        content_label.pack(padx=20, pady=15, anchor="w")

        # Store state
        self.section_states[section_id] = {
            "container": content_container,
            "button": toggle_btn,
            "expanded": False,
            "content": content
        }

    def _toggle_section(self, section_id):
        """Toggle visibility of a collapsible section."""
        state = self.section_states[section_id]
        container = state["container"]
        button = state["button"]

        if state["expanded"]:
            # Collapse
            container.pack_forget()
            button.configure(text="▼")
            state["expanded"] = False
        else:
            # Expand
            container.pack(fill="x", pady=(0, 5))
            button.configure(text="▲")
            state["expanded"] = True

    def _note_pc(self, semitones: int) -> str:
        """Return pitch-class note name (no octave)."""
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        return note_names[semitones % 12]

    def _format_intervals(self, semitones: list[int]) -> str:
        """Return a compact numeric interval representation like '1–3–5–b7' for a chord.

        Rules:
        - Base mapping relative to root (C): 0:1, 1:b2, 2:2, 3:b3, 4:3, 5:4, 6:b5, 7:5, 8:#5, 9:6, 10:b7, 11:7
        - Extensions: 2→9, 4→11, 6→13 when above octave (>=12 semitones)
        - Accidentals are preserved when extending (b2→b9, #4→#11, etc.)
        - Keeps ascending order as provided in the chord definition
        """
        base_map = {
            0: ("1", 1),
            1: ("b2", 2),
            2: ("2", 2),
            3: ("b3", 3),
            4: ("3", 3),
            5: ("4", 4),
            6: ("b5", 5),
            7: ("5", 5),
            8: ("#5", 5),
            9: ("6", 6),
            10: ("b7", 7),
            11: ("7", 7),
        }

        # Special case: fully diminished seventh chord 1–b3–b5–bb7 (enharmonically 1–b3–b5–6)
        if len(semitones) == 4 and set([x % 12 for x in semitones]) == {0, 3, 6, 9}:
            return "1–b3–b5–bb7"

        tokens: list[str] = []
        for s in semitones:
            r = s % 12
            octs = s // 12
            token, deg = base_map.get(r, ("?", None))
            if octs >= 1:
                # Handle altered tensions explicitly
                if r == 3:
                    # 15 semitones above root -> #9
                    token = "#9"
                    tokens.append(token)
                    continue
                if deg == 2:
                    token = token.replace("2", "9")  # b2->b9, 2->9
                elif deg == 4:
                    # handle #4 vs 4
                    if token.startswith("#"):
                        token = token.replace("4", "11")  # #4 -> #11
                    else:
                        token = token.replace("4", "11")
                elif deg == 6:
                    token = token.replace("6", "13")
                # 1,3,5,7 remain 1,3,5,7 by convention
            tokens.append(token)

        return "–".join(tokens)

    def _on_back(self):
        if callable(self.on_back):
            self.on_back()

    @staticmethod
    def _build_sound(semitone_list: list, duration: float, sr: int, base_freq: float):
        """Synthesize a chord sound and return it as a Pygame Sound object."""
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)

        harmonics = 6
        amps = np.array([1.0 / (n ** 1.1) for n in range(1, harmonics + 1)])

        wave = np.zeros_like(t)
        for st in semitone_list:
            freq = base_freq * (2 ** (st / 12.0))
            for i, a in enumerate(amps, start=1):
                wave += (a / len(semitone_list)) * np.sin(2 * np.pi * i * freq * t)

        # ADSR envelope
        attack = min(0.03, duration * 0.1)
        decay = min(0.08, duration * 0.15)
        release = min(0.3, duration * 0.3)
        sustain_level = 0.7
        sustain_time = max(0.0, duration - (attack + decay + release))

        env = np.zeros_like(t)
        idx, a_end = 0, int(sr * attack)
        if a_end > 0:
            env[:a_end] = np.linspace(0.0, 1.0, a_end);
            idx = a_end
        d_end = idx + int(sr * decay)
        if d_end > idx:
            env[idx:d_end] = np.linspace(1.0, sustain_level, d_end - idx);
            idx = d_end
        s_end = idx + int(sr * sustain_time)
        if s_end > idx:
            env[idx:s_end] = sustain_level;
            idx = s_end
        if idx < len(env):
            env[idx:] = np.linspace(sustain_level, 0.0, len(env) - idx)

        wave *= env

        maxv = np.max(np.abs(wave))
        if maxv > 0:
            wave *= (0.85 / maxv)

        audio = (wave * 32767).astype(np.int16)

        init = pygame.mixer.get_init()
        channels = init[2] if init else 2
        if channels == 2:
            return pygame.sndarray.make_sound(np.column_stack((audio, audio)))
        return pygame.sndarray.make_sound(audio)

    def _play_chord(self, semitones: list, duration: float = 0.8):
        """Play a chord by mixing multiple frequencies simultaneously in a background thread."""
        if not self.audio_ok:
            print("Audio not available")
            return

        def prepare_and_play():
            key = f"chord_{'_'.join(map(str, semitones))}_{int(duration * 1000)}"

            snd = self._sound_cache.get(key)
            if snd is None:
                snd = self._build_sound(semitones, duration, 44100, self.BASE_FREQ_C4)
                self._sound_cache[key] = snd

            try:
                snd.play()
            except Exception as e:
                print(f"Playback failed: {e}")

        threading.Thread(target=prepare_and_play, daemon=True).start()