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

        # --- Theory sections ---
        theory_container = ctk.CTkFrame(self, fg_color="transparent")
        theory_container.pack(fill="x", padx=30, pady=(0, 10))

        intro_text = (
            "Interwał w muzyce to podstawowa jednostka struktury dźwiękowej, określająca odległość pomiędzy dwoma dźwiękami – "
            "zarówno w sensie wysokościowym (liczba półtonów), jak i nazewnictwa stopniowego (liczba nazw dźwięków obejmowanych "
            "przez interwał, włącznie z dźwiękiem początkowym i końcowym). Interwały stanowią fundament harmonii, melodii oraz "
            "budowy akordów, a ich rozumienie jest kluczowe dla analizy i komponowania muzyki."
        )
        ctk.CTkLabel(
            theory_container, text=intro_text, font=("Arial", 14), text_color="#ECF0F1",
            wraplength=820, justify="left"
        ).pack(anchor="w", pady=(0, 15))

        # --- Collapsible sections ---
        self.section_states = {}
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
        self._create_collapsible_section(theory_container, "rodzaje", "Rodzaje interwałów", rodzaje_text)

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
        self._create_collapsible_section(theory_container, "konsonanse", "Konsonanse i dysonanse", konsonanse_text)

        zastosowanie_text = (
            "Interwały są podstawą:\n\n"
            "• Melodii – określają odległości pomiędzy kolejnymi dźwiękami linii melodycznej, wpływając na jej ekspresję "
            "(np. duże skoki są dramatyczne, małe kroki – płynne).\n\n"
            "• Harmonii – stanowią budulec akordów i współbrzmień; zrozumienie relacji między interwałami jest konieczne "
            "przy analizie funkcji harmonicznych.\n\n"
            "• Intonacji i temperacji – w praktyce wykonawczej różne systemy strojenia (np. czystość pitagorejska, "
            "temperacja równomierna) wpływają na rzeczywiste proporcje interwałów."
        )
        self._create_collapsible_section(theory_container, "zastosowanie", "Zastosowanie interwałów", zastosowanie_text)

        klasyfikacja_text = (
            "Interwały można określić również jako:\n\n"
            "• Proste – nie przekraczają oktawy (np. seksta wielka, kwinta czysta).\n\n"
            "• Złożone (komponowane) – większe niż oktawa, np. nona (sekunda + oktawa), decyma (tercja + oktawa).\n\n"
            "Zrozumienie interwałów pozwala na logiczne budowanie progresji akordów, konstrukcji skal, "
            "a także rozpoznawanie relacji tonalnych pomiędzy dźwiękami."
        )
        self._create_collapsible_section(theory_container, "klasyfikacja", "Klasyfikacja interwałów", klasyfikacja_text)

        # --- Interactive Examples Section ---
        ctk.CTkLabel(
            self, text="Interaktywne Przykłady", font=("Arial", 20, "bold"), text_color="#00BCD4"
        ).pack(pady=(10, 5), padx=30)

        # Store interval data as instance variables
        self.intervals = [
            ("Pryma (unison)", 0, "konsonans doskonały",
             "Podstawowy dźwięk akordu. Używana we wszystkich akordach jako punkt odniesienia.",
             ["C (dur)", "Cm (mol)", "wszystkie akordy"]),
            ("Mała sekunda / Mała nona", 1, "dysonans ostry",
             "Bardzo napięty interwał, rzadko używany jako składnik akordu. Najczęściej pojawia się jako b9 w dominantach lub jako dźwięk przejściowy/opóźnienie.",
             ["C7b9", "akordy z b9/alterowane"]),
            ("Wielka sekunda / Wielka nona", 2, "dysonans łagodny",
             "Napięcie wymagające rozwiązania. Używana w akordach sus2 jako zamiennik tercji.",
             ["Csus2", "akordy z dodaną 9"]),
            ("Mała tercja / Mała decyma", 3, "konsonans niedoskonały",
             "Podstawa akordów molowych, daje smutny, melancholijny charakter.", ["Cm", "Cm7", "Cdim"]),
            ("Wielka tercja / Wielka decyma", 4, "konsonans niedoskonały",
             "Podstawa akordów durowych, daje radosny, jasny charakter.", ["C (dur)", "C7", "Cmaj7"]),
            (
            "Kwarta / Undecyma", 5, "konsonans doskonały", "Stabilny interwał, używany w akordach sus4 zamiast tercji.",
            ["Csus4", "akordy kwartowe"]),
            ("Tryton", 6, "dysonans", "Najbardziej niestabilny interwał, dzieli oktawę na pół. Wymaga rozwiązania.",
             ["C7", "Cdim7"]),
            ("Kwinta / Duodecyma", 7, "konsonans doskonały",
             "Najważniejszy interwał po prymie, podstawa większości akordów. Bardzo stabilny.",
             ["C (dur)", "Cm", "C7", "prawie wszystkie akordy"]),
            ("Mała seksta / Mała tercdecyma", 8, "konsonans niedoskonały",
             "Ciepły, melancholijny interwał. Inwersja wielkiej tercji.", ["Cm6", "akordy z sekstą"]),
            ("Wielka seksta / Wielka tercdecyma", 9, "konsonans niedoskonały",
             "Jasny, otwarty interwał. Często dodawany do akordów durowych.", ["C6", "C13"]),
            (
            "Mała septyma", 10, "dysonans", "Napięcie dominantowe, wymaga rozwiązania. Podstawa akordów dominantowych.",
            ["C7", "Cm7"]),
            (
            "Wielka septyma", 11, "dysonans ostry", "Bardzo napięty interwał, charakterystyczny dla akordów jazzowych.",
            ["Cmaj7"]),
            ("Oktawa", 12, "konsonans doskonały", "Ten sam dźwięk o oktawę wyżej, absolutna stabilność.",
             ["wszystkie akordy (rozszerzenia)"]),
        ]
        self.note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B", "C"]

        # Main container for master-detail layout
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=30, pady=(0, 10))
        main_container.grid_columnconfigure(1, weight=1)
        main_container.grid_rowconfigure(0, weight=1)

        # Master frame (left, scrollable list)
        self.master_frame = ctk.CTkScrollableFrame(main_container, width=300, label_text="Interwały")
        self.master_frame.grid(row=0, column=0, sticky="ns", padx=(0, 20))

        # Detail frame (right, content changes)
        self.detail_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        self.detail_frame.grid(row=0, column=1, sticky="nsew")

        # Populate the master list
        for index, (name, *_) in enumerate(self.intervals):
            btn = ctk.CTkButton(
                self.master_frame,
                text=name.split("/")[0].strip(),  # Show the simple name
                command=lambda i=index: self._show_details(i)
            )
            btn.pack(fill="x", pady=2, padx=5)

        # Show the first interval by default
        self._show_details(0)

    def _show_details(self, index):
        """Clear the detail frame and render the selected interval's info."""
        # Clear any existing widgets
        for widget in self.detail_frame.winfo_children():
            widget.destroy()

        # Get the selected interval data
        name, semitones, konsonans_type, theory_info, chord_examples = self.intervals[index]

        # --- Header ---
        header_frame = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        note = self.note_names[semitones % len(self.note_names)]
        ctk.CTkLabel(header_frame, text=name, font=("Arial", 24, "bold"), text_color="#00BCD4").pack(anchor="w")
        ctk.CTkLabel(header_frame, text=f"C — {note} ({semitones} półtonów)", font=("Arial", 16),
                     text_color="#ECF0F1").pack(anchor="w", pady=(2, 0))

        # --- Play Button ---
        ctk.CTkButton(
            self.detail_frame, text="▶ Odtwórz", width=120, height=40,
            font=("Arial", 16), fg_color="#0097A7", hover_color="#00838F",
            command=lambda s=semitones: self._play_interval(s)
        ).pack(anchor="w", pady=(0, 20))

        # --- Details Content ---
        content_frame = ctk.CTkFrame(self.detail_frame, fg_color="#2b2b2b", corner_radius=8)
        content_frame.pack(fill="both", expand=True, pady=(0, 10))

        if "/" in name:
            ctk.CTkLabel(
                content_frame,
                text="ℹ️  Interwał złożony: nazwa po lewej stronie / to interwał prosty (w obrębie oktawy), "
                     "nazwa po prawej to interwał złożony (przekracza oktawę o te same stopnie).",
                font=("Arial", 12, "italic"), text_color="#4FC3F7", wraplength=500, justify="left"
            ).pack(anchor="w", padx=20, pady=(12, 8))

        is_consonance = "konsonans" in konsonans_type.lower()
        type_color = "#00BCD4" if is_consonance else "#0288D1"

        ctk.CTkLabel(
            content_frame, text=f"Typ: {konsonans_type}", font=("Arial", 14, "bold"), text_color=type_color
        ).pack(anchor="w", padx=20, pady=(6, 6))

        ctk.CTkLabel(
            content_frame, text=theory_info, font=("Arial", 13), text_color="#ECF0F1",
            wraplength=500, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 10))

        chords_text = "Występuje w akordach: " + ", ".join(chord_examples)
        ctk.CTkLabel(
            content_frame, text=chords_text, font=("Arial", 12, "italic"), text_color="#95a5a6",
            wraplength=500, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 12))

    def _on_back(self):
        if callable(self.on_back):
            self.on_back()

    def _create_collapsible_section(self, parent, section_id, title, content):
        """Create a collapsible theory section."""
        section_container = ctk.CTkFrame(parent, fg_color="transparent")
        section_container.pack(fill="x", pady=(0, 10))

        header = ctk.CTkFrame(section_container, fg_color="#2c2c2c", corner_radius=10)
        header.pack(fill="x")

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="x", padx=20, pady=12)

        ctk.CTkLabel(
            header_content, text=title, font=("Arial", 17, "bold"), text_color="#00BCD4"
        ).pack(side="left")

        expand_btn = ctk.CTkButton(
            header_content, text="▼", width=35, height=30, font=("Arial", 14),
            fg_color="#0277BD", hover_color="#01579B",
            command=lambda: self._toggle_section(section_id)
        )
        expand_btn.pack(side="right")

        content_frame = ctk.CTkFrame(section_container, fg_color="#2c2c2c", corner_radius=10)
        ctk.CTkLabel(
            content_frame, text=content, font=("Arial", 13), text_color="#ECF0F1",
            wraplength=800, justify="left"
        ).pack(anchor="w", padx=25, pady=(10, 15))

        self.section_states[section_id] = {
            "container": section_container,
            "button": expand_btn,
            "content_frame": content_frame,
            "expanded": False
        }
        content_frame.pack_forget()

    def _toggle_section(self, section_id):
        """Toggle a theory section."""
        state = self.section_states[section_id]
        if state["expanded"]:
            state["content_frame"].pack_forget()
            state["button"].configure(text="▼")
            state["expanded"] = False
        else:
            state["content_frame"].pack(fill="x", pady=(2, 0))
            state["button"].configure(text="▲")
            state["expanded"] = True

    @staticmethod
    def _build_sound(freq: float, duration: float, sr: int):
        """Synthesize a richer tone and return it as a Pygame Sound object."""
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)

        # Harmonics for a richer tone
        harmonics = 6
        amps = np.array([1.0 / (n ** 1.1) for n in range(1, harmonics + 1)])

        wave = np.zeros_like(t)
        for i, a in enumerate(amps, start=1):
            wave += a * np.sin(2 * np.pi * i * freq * t)

        # ADSR envelope
        attack = min(0.02, duration * 0.15)
        decay = min(0.06, duration * 0.15)
        release = min(0.12, duration * 0.25)
        sustain_level = 0.78
        sustain_time = max(0.0, duration - (attack + decay + release))

        env = np.zeros_like(t)
        idx = 0
        a_end = int(sr * attack)
        if a_end > 0:
            env[:a_end] = np.linspace(0.0, 1.0, a_end)
            idx = a_end

        d_end = idx + int(sr * decay)
        if d_end > idx:
            env[idx:d_end] = np.linspace(1.0, sustain_level, d_end - idx)
            idx = d_end

        s_end = idx + int(sr * sustain_time)
        if s_end > idx:
            env[idx:s_end] = sustain_level
            idx = s_end

        if idx < len(env):
            env[idx:] = np.linspace(sustain_level, 0.0, len(env) - idx)

        wave *= env

        # Normalize and convert to 16-bit PCM
        maxv = np.max(np.abs(wave))
        if maxv > 0:
            wave = wave * (0.9 / maxv)
        audio = (wave * 32767).astype(np.int16)

        # Handle stereo/mono output
        init = pygame.mixer.get_init()
        channels = init[2] if init else 1
        if channels == 2:
            stereo = np.column_stack((audio, audio))
            return pygame.sndarray.make_sound(stereo)
        return pygame.sndarray.make_sound(audio)

    def _play_interval(self, semitones: int, duration: float = 0.8):
        """Play base note (C4) and a target note sequentially in a background thread."""
        if not self.audio_ok:
            print("Audio not available")
            return

        def prepare_and_play():
            sr = 44100
            f_base = self.BASE_FREQ_C4
            f_target = f_base * (2 ** (semitones / 12.0))

            # Check cache first
            key1 = f"note_{int(round(f_base))}_{int(duration * 1000)}"
            key2 = f"note_{int(round(f_target))}_{int(duration * 1000)}"

            snd1 = self._sound_cache.get(key1)
            if snd1 is None:
                snd1 = self._build_sound(f_base, duration, sr)
                self._sound_cache[key1] = snd1

            snd2 = self._sound_cache.get(key2)
            if snd2 is None:
                snd2 = self._build_sound(f_target, duration, sr)
                self._sound_cache[key2] = snd2

            # Play sequence
            try:
                ch = snd1.play()
                if ch:
                    while ch.get_busy():
                        pygame.time.wait(10)
                snd2.play()
            except Exception as e:
                print(f"Playback failed: {e}")

        # Run in a background thread to keep UI responsive
        threading.Thread(target=prepare_and_play, daemon=True).start()