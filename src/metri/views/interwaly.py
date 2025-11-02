import customtkinter as ctk
import pygame
import numpy as np
import threading


class InterwalyView(ctk.CTkFrame):
    """Dedicated Interwały view with explanations and playable examples.

    This view is intended to be embedded by `TheoryView` into the chapter
    frame. It accepts an `on_back` callback to return to the parent menu.
    """

    BASE_FREQ_C4 = 261.6256

    def __init__(self, master, on_back=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_back = on_back

        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1)
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
        
        # Back button on the left
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
        
        # Header title on the right
        ctk.CTkLabel(
            top_bar,
            text="Interwały",
            font=("Arial", 28, "bold"),
            text_color="#00BCD4"
        ).pack(side="left", padx=(20, 0))

        # Track which sections are expanded (all collapsed by default)
        self.section_states = {
            "rodzaje": False,
            "konsonanse": False,
            "zastosowanie": False,
            "klasyfikacja": False
        }

        # Theory sections container
        self.theory_container = ctk.CTkFrame(self, fg_color="transparent")
        self.theory_container.pack(fill="x", padx=30, pady=(0, 10))

        # Introduction (always visible, not collapsible)
        intro_text = (
            "Interwał w muzyce to podstawowa jednostka struktury dźwiękowej, określająca odległość pomiędzy dwoma dźwiękami – "
            "zarówno w sensie wysokościowym (liczba półtonów), jak i nazewnictwa stopniowego (liczba nazw dźwięków obejmowanych "
            "przez interwał, włącznie z dźwiękiem początkowym i końcowym). Interwały stanowią fundament harmonii, melodii oraz "
            "budowy akordów, a ich rozumienie jest kluczowe dla analizy i komponowania muzyki."
        )
        ctk.CTkLabel(
            self.theory_container,
            text=intro_text,
            font=("Arial", 14),
            text_color="#171616",
            wraplength=820,
            justify="left"
        ).pack(anchor="w", pady=(0, 15))

        # Section: Rodzaje interwałów (collapsible)
        rodzaje_text = (
            "Interwały dzieli się ze względu na ich rozpiętość oraz charakter brzmieniowy:\n\n"
            "• Czyste (1, 4, 5, 8) – prymę, kwartę, kwintę i oktawę określa się jako czyste, ponieważ w systemie naturalnym "
            "(ośmiotonowa skala diatoniczna) ich proporcje częstotliwości są proste i stabilne, np. kwinta 3:2, oktawa 2:1.\n\n"
            "• Wielkie i małe (2, 3, 6, 7) – dotyczą sekund, tercji, sekst i septym. Interwał wielki jest o półton większy od małego.\n\n"
            "• Zwiększone i zmniejszone – powstają przez powiększenie lub pomniejszenie interwału o półton w stosunku do formy "
            "podstawowej (czystej lub wielkiej/małej).\n\n"
            "Każdy interwał można także odwrócić: np. tercja wielka (C–E) staje się przy odwróceniu sekstą małą (E–C). "
            "Wartość interwału odwrotnego zawsze daje w sumie dziewięć (3 + 6 = 9), a jego charakter: "
            "czysty ↔ czysty, wielki ↔ mały, zwiększony ↔ zmniejszony."
        )
        self._create_collapsible_section("rodzaje", "Rodzaje interwałów", rodzaje_text)

        # Section: Konsonanse i dysonanse (collapsible)
        konsonanse_text = (
            "Pod względem brzmieniowym interwały dzielą się na:\n\n"
            "• Konsonanse – współbrzmienia łagodne i stabilne: prymę, oktawę, kwintę, tercję i sekstę (małą lub wielką); "
            "kwartę uznaje się za konsonans głównie w ruchu melodycznym, natomiast w harmonii (gdy leży nad basem) "
            "traktuje się ją jako dysonans wymagający rozwiązania.\n\n"
            "• Dysonanse – współbrzmienia napięciowe, wymagające rozwiązania: sekundy, septymy oraz interwały "
            "zwiększone i zmniejszone.\n\n"
            "W muzyce tonalnej dysonanse pełnią rolę elementów napięcia, które kierują przebieg harmoniczny, "
            "podczas gdy konsonanse stanowią punkty odpoczynku i stabilizacji."
        )
        self._create_collapsible_section("konsonanse", "Konsonanse i dysonanse", konsonanse_text)

        # Section: Zastosowanie interwałów (collapsible)
        zastosowanie_text = (
            "Interwały są podstawą:\n\n"
            "• Melodii – określają odległości pomiędzy kolejnymi dźwiękami linii melodycznej, wpływając na jej ekspresję "
            "(np. duże skoki są dramatyczne, małe kroki – płynne).\n\n"
            "• Harmonii – stanowią budulec akordów i współbrzmień; zrozumienie relacji między interwałami jest konieczne "
            "przy analizie funkcji harmonicznych.\n\n"
            "• Intonacji i temperacji – w praktyce wykonawczej różne systemy strojenia (np. czystość pitagorejska, "
            "temperacja równomierna) wpływają na rzeczywiste proporcje interwałów."
        )
        self._create_collapsible_section("zastosowanie", "Zastosowanie interwałów", zastosowanie_text)

        # Section: Klasyfikacja interwałów (collapsible)
        klasyfikacja_text = (
            "Interwały można określić również jako:\n\n"
            "• Proste – nie przekraczają oktawy (np. seksta wielka, kwinta czysta).\n\n"
            "• Złożone (komponowane) – większe niż oktawa, np. nona (sekunda + oktawa), decyma (tercja + oktawa).\n\n"
            "Zrozumienie interwałów pozwala na logiczne budowanie progresji akordów, konstrukcji skal, "
            "a także rozpoznawanie relacji tonalnych pomiędzy dźwiękami."
        )
        self._create_collapsible_section("klasyfikacja", "Klasyfikacja interwałów", klasyfikacja_text)

        # Examples section header
        examples_header = ctk.CTkLabel(
            self.theory_container, 
            text="Poniżej znajdują się przykłady interwałów z dźwiękiem bazowym C, przedstawiające różne rodzaje i wielkości interwałów w odniesieniu do tego samego dźwięku podstawowego.",
            font=("Arial", 14, "italic"),
            text_color="#95a5a6",
            wraplength=820,
            justify="left"
        )
        examples_header.pack(anchor="w", pady=(15, 15))

        intervals = [
            ("Pryma (unison)", 0, "konsonans doskonały", "Podstawowy dźwięk akordu. Używana we wszystkich akordach jako punkt odniesienia.", ["C (dur)", "Cm (mol)", "wszystkie akordy"]),
            ("Mała sekunda / Mała nona", 1, "dysonans ostry", "Bardzo napięty interwał, rzadko używany jako składnik akordu. Najczęściej pojawia się jako b9 w dominantach lub jako dźwięk przejściowy/opóźnienie.", ["C7b9", "akordy z b9/alterowane"]),
            ("Wielka sekunda / Wielka nona", 2, "dysonans łagodny", "Napięcie wymagające rozwiązania. Używana w akordach sus2 jako zamiennik tercji.", ["Csus2", "akordy z dodaną 9"]),
            ("Mała tercja / Mała decyma", 3, "konsonans niedoskonały", "Podstawa akordów molowych, daje smutny, melancholijny charakter.", ["Cm", "Cm7", "Cdim"]),
            ("Wielka tercja / Wielka decyma", 4, "konsonans niedoskonały", "Podstawa akordów durowych, daje radosny, jasny charakter.", ["C (dur)", "C7", "Cmaj7"]),
            ("Kwarta / Undecyma", 5, "konsonans doskonały", "Stabilny interwał, używany w akordach sus4 zamiast tercji.", ["Csus4", "akordy kwartowe"]),
            ("Tryton", 6, "dysonans", "Najbardziej niestabilny interwał, dzieli oktawę na pół. Wymaga rozwiązania.", ["C7", "Cdim7"]),
            ("Kwinta / Duodecyma", 7, "konsonans doskonały", "Najważniejszy interwał po prymie, podstawa większości akordów. Bardzo stabilny.", ["C (dur)", "Cm", "C7", "prawie wszystkie akordy"]),
            ("Mała seksta / Mała tercdecyma", 8, "konsonans niedoskonały", "Ciepły, melancholijny interwał. Inwersja wielkiej tercji.", ["Cm6", "akordy z sekstą"]),
            ("Wielka seksta / Wielka tercdecyma", 9, "konsonans niedoskonały", "Jasny, otwarty interwał. Często dodawany do akordów durowych.", ["C6", "C13"]),
            ("Mała septyma", 10, "dysonans", "Napięcie dominantowe, wymaga rozwiązania. Podstawa akordów dominantowych.", ["C7", "Cm7"]),
            ("Wielka septyma", 11, "dysonans ostry", "Bardzo napięty interwał, charakterystyczny dla akordów jazzowych.", ["Cmaj7"]),
            ("Oktawa", 12, "konsonans doskonały", "Ten sam dźwięk o oktawę wyżej, absolutna stabilność.", ["wszystkie akordy (rozszerzenia)"]),
        ]

        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B", "C"]

        tbl = ctk.CTkFrame(self, fg_color="transparent")
        tbl.pack(fill="x", padx=30, pady=(6, 18))

        # Track expanded intervals
        self.expanded_intervals = {}

        for name, semitones, konsonans_type, theory_info, chord_examples in intervals:
            # Main row container
            row_container = ctk.CTkFrame(tbl, fg_color="transparent")
            row_container.pack(fill="x", pady=3)

            # Determine if this is a primary interval (pryma, tercja, kwinta)
            is_primary = any(keyword in name.lower() for keyword in ["pryma", "tercja", "kwinta"])
            
            # Determine if consonance or dissonance for coloring (only for primary intervals)
            is_consonance = "konsonans" in konsonans_type.lower()
            if is_primary:
                name_color = "#00BCD4" if is_consonance else "#0288D1"  # Bright cyan for consonance, Dark blue for dissonance
            else:
                name_color = "#808080"  # Gray for non-primary intervals
            
            # Collapsed row (always visible)
            row = ctk.CTkFrame(row_container, fg_color="#2b2b2b", corner_radius=8)
            row.pack(fill="x", pady=3)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=18, pady=10)
            note = note_names[semitones] if semitones < len(note_names) else "?"
            
            # Interval name with color coding
            ctk.CTkLabel(left, text=f"{name}", font=("Arial", 16, "bold"), text_color=name_color).pack(anchor="w")

            # Right side: example notes, semitone count, Play and Expand buttons
            right = ctk.CTkFrame(row, fg_color="transparent")
            right.pack(side="right", padx=18, pady=10)
            
            right_top = ctk.CTkFrame(right, fg_color="transparent")
            right_top.pack()
            
            ctk.CTkLabel(right_top, text=f"C — {note}", font=("Arial", 16, "bold"), text_color="#ECF0F1").pack(side="left", padx=(0, 20))
            ctk.CTkLabel(right_top, text=f"{semitones} półtonów", font=("Arial", 13), text_color="#95a5a6").pack(side="left", padx=(0, 15))
            
            btn = ctk.CTkButton(
                right_top, 
                text="▶", 
                width=45, 
                height=36, 
                font=("Arial", 16),
                fg_color="#0097A7",
                hover_color="#00838F",
                command=lambda s=semitones: self._play_interval(s)
            )
            btn.pack(side="left", padx=(0, 10))
            
            # Expand/collapse button
            expand_btn = ctk.CTkButton(
                right_top, 
                text="▼", 
                width=38, 
                height=36,
                font=("Arial", 16),
                fg_color="#555555",
                hover_color="#777777",
                command=lambda rc=row_container, n=name, st=semitones, kt=konsonans_type, ti=theory_info, ce=chord_examples: self._toggle_details(rc, n, st, kt, ti, ce)
            )
            expand_btn.pack(side="left")

            # Store reference for toggling
            self.expanded_intervals[semitones] = {"container": row_container, "expanded": False, "button": expand_btn}
            self.expanded_intervals[semitones] = {"container": row_container, "expanded": False, "button": expand_btn}

    def _on_back(self):
        if callable(self.on_back):
            self.on_back()

    def _create_collapsible_section(self, section_id, title, content):
        """Create a collapsible theory section."""
        # Section container
        section_container = ctk.CTkFrame(self.theory_container, fg_color="transparent")
        section_container.pack(fill="x", pady=(0, 10))

        # Header with title and expand button
        header = ctk.CTkFrame(section_container, fg_color="#2c2c2c", corner_radius=10)
        header.pack(fill="x")

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="x", padx=20, pady=12)

        ctk.CTkLabel(
            header_content,
            text=title,
            font=("Arial", 17, "bold"),
            text_color="#00BCD4"
        ).pack(side="left")

        expand_btn = ctk.CTkButton(
            header_content,
            text="▼",
            width=35,
            height=30,
            font=("Arial", 14),
            fg_color="#0277BD",
            hover_color="#01579B",
            command=lambda: self._toggle_section(section_id, section_container, expand_btn, content)
        )
        expand_btn.pack(side="right")

        # Store reference
        self.section_states[section_id] = {
            "container": section_container,
            "button": expand_btn,
            "expanded": False,
            "content": content
        }

    def _toggle_section(self, section_id, container, button, content):
        """Toggle a theory section."""
        state = self.section_states[section_id]
        
        if state["expanded"]:
            # Collapse: remove content frame
            for widget in container.winfo_children():
                if widget != container.winfo_children()[0]:  # Keep header
                    widget.destroy()
            button.configure(text="▼")
            state["expanded"] = False
        else:
            # Expand: create content frame
            content_frame = ctk.CTkFrame(container, fg_color="#2c2c2c", corner_radius=10)
            content_frame.pack(fill="x", pady=(2, 0))

            ctk.CTkLabel(
                content_frame,
                text=content,
                font=("Arial", 13),
                text_color="#ECF0F1",
                wraplength=800,
                justify="left"
            ).pack(anchor="w", padx=25, pady=(10, 15))

            button.configure(text="▲")
            state["expanded"] = True

    def _toggle_details(self, row_container, name, semitones, konsonans_type, theory_info, chord_examples):
        """Toggle the expanded details panel for an interval."""
        interval_data = self.expanded_intervals[semitones]
        
        if interval_data["expanded"]:
            # Collapse: remove details frame
            for widget in row_container.winfo_children():
                if isinstance(widget, ctk.CTkFrame) and widget.cget("fg_color") == "#1e1e1e":
                    widget.destroy()
            interval_data["expanded"] = False
            interval_data["button"].configure(text="▼")
        else:
            # Expand: create details frame
            details_frame = ctk.CTkFrame(row_container, fg_color="#1e1e1e", corner_radius=8)
            details_frame.pack(fill="x", pady=(0, 3), padx=25)
            
            # Check if this is a compound interval (has /)
            if "/" in name:
                compound_explanation = ctk.CTkLabel(
                    details_frame,
                    text="ℹ️  Interwał złożony: nazwa po lewej stronie / to interwał prosty (w obrębie oktawy), "
                         "nazwa po prawej to interwał złożony (przekracza oktawę o te same stopnie).",
                    font=("Arial", 12, "italic"),
                    text_color="#4FC3F7",
                    wraplength=780,
                    justify="left"
                )
                compound_explanation.pack(anchor="w", padx=20, pady=(12, 8))
            
            # Type of consonance/dissonance with color
            is_consonance = "konsonans" in konsonans_type.lower()
            type_color = "#00BCD4" if is_consonance else "#0288D1"
            
            type_label = ctk.CTkLabel(
                details_frame,
                text=f"Typ: {konsonans_type}",
                font=("Arial", 14, "bold"),
                text_color=type_color
            )
            type_label.pack(anchor="w", padx=20, pady=(6, 6))
            
            # Theoretical info
            info_label = ctk.CTkLabel(
                details_frame,
                text=theory_info,
                font=("Arial", 13),
                text_color="#ECF0F1",
                wraplength=780,
                justify="left"
            )
            info_label.pack(anchor="w", padx=20, pady=(0, 10))
            
            # Chord examples
            chords_text = "Występuje w akordach: " + ", ".join(chord_examples)
            chords_label = ctk.CTkLabel(
                details_frame,
                text=chords_text,
                font=("Arial", 12, "italic"),
                text_color="#95a5a6",
                wraplength=780,
                justify="left"
            )
            chords_label.pack(anchor="w", padx=20, pady=(0, 12))
            
            interval_data["expanded"] = True
            interval_data["button"].configure(text="▲")

    def _play_interval(self, semitones: int, duration: float = 0.8):
        """Play base note (C4) then the target note sequentially in a background thread."""
        if not self.audio_ok:
            print("Audio not available")
            return

        sr = 44100
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        f_base = self.BASE_FREQ_C4
        f_target = f_base * (2 ** (semitones / 12.0))

        # Helper to build a pygame Sound for a given frequency
        def build_sound(freq: float):
            """Synthesize a richer tone: harmonics, ADSR envelope (no vibrato).

            Returns a pygame Sound. Caches by rounded frequency and duration.
            """
            key = f"note_{int(round(freq))}_{int(duration*1000)}"
            if key in self._sound_cache:
                return self._sound_cache[key]

            # synthesis params
            sr_local = sr
            t_local = t
            # harmonics: fundamental + partials
            harmonics = 6
            # amplitude rolloff for partials (gentle)
            amps = np.array([1.0 / (n ** 1.1) for n in range(1, harmonics + 1)])

            # No vibrato: use unity modulation
            freq_mod = np.ones_like(t_local)

            wave = np.zeros_like(t_local)
            for i, a in enumerate(amps, start=1):
                # each partial uses the modulated fundamental multiplied by partial index
                wave += a * np.sin(2 * np.pi * i * freq * freq_mod * t_local)

            # ADSR envelope
            attack = min(0.02, duration * 0.15)
            decay = min(0.06, duration * 0.15)
            release = min(0.12, duration * 0.25)
            sustain_level = 0.78
            sustain_time = max(0.0, duration - (attack + decay + release))

            env = np.zeros_like(t_local)
            idx = 0
            # attack
            a_end = int(sr_local * attack)
            if a_end > 0:
                env[:a_end] = np.linspace(0.0, 1.0, a_end)
                idx = a_end

            # decay
            d_end = idx + int(sr_local * decay)
            if d_end > idx:
                env[idx:d_end] = np.linspace(1.0, sustain_level, d_end - idx)
                idx = d_end

            # sustain
            s_end = idx + int(sr_local * sustain_time)
            if s_end > idx:
                env[idx:s_end] = sustain_level
                idx = s_end

            # release
            if idx < len(env):
                env[idx:] = np.linspace(sustain_level, 0.0, len(env) - idx)

            wave = wave * env

            # subtle global gain and normalization
            maxv = np.max(np.abs(wave))
            if maxv > 0:
                wave = wave * (0.9 / maxv)

            audio = (wave * 32767).astype(np.int16)

            init = pygame.mixer.get_init()
            channels = init[2] if init and len(init) >= 3 else 2

            if channels == 2:
                stereo = np.column_stack((audio, audio))
                snd = pygame.sndarray.make_sound(stereo)
            else:
                snd = pygame.sndarray.make_sound(audio)

            self._sound_cache[key] = snd
            return snd

        snd1 = build_sound(f_base)
        snd2 = build_sound(f_target)

        # Play sequentially without blocking the UI
        def play_sequence():
            try:
                ch = snd1.play()
                # Use sound length; fallback to duration argument
                length = snd1.get_length() if hasattr(snd1, 'get_length') else duration
                # Wait for the first sound to finish (reduced wait time)
                threading.Event().wait(length + 0.02)
                snd2.play()
            except Exception as e:
                print(f"play sequence failed: {e}")

        thr = threading.Thread(target=play_sequence, daemon=True)
        thr.start()
